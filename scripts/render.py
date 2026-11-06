"""Render narrative drafts to submission/: memo + appendix -> PDF, deck -> pptx.
Strips [F:...] tags and leaves author/creator metadata empty (rule 3)."""
import re, sys
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from pptx import Presentation
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
DRAFTS = ROOT / "agents/narrative/drafts"
OUT = ROOT / "submission"
TAG = re.compile(r"\s*\[F:[^\]]+\]")


def inline(t):
    t = escape(TAG.sub("", t))
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"\*(.+?)\*", r"<i>\1</i>", t)
    return re.sub(r"`(.+?)`", r"\1", t)


def pdf(md, out, size):
    ss = getSampleStyleSheet()
    body = ParagraphStyle("b", parent=ss["BodyText"], fontSize=size, leading=size * 1.25, spaceAfter=2)
    h1 = ParagraphStyle("h1", parent=ss["Heading1"], fontSize=size + 5, spaceAfter=4)
    h2 = ParagraphStyle("h2", parent=ss["Heading2"], fontSize=size + 2, spaceBefore=5, spaceAfter=2)
    cell = ParagraphStyle("c", parent=body, fontSize=size - 1, leading=(size - 1) * 1.2)
    flow, table = [], []

    def flush():
        if table:
            rows = [[Paragraph(inline(c), cell) for c in r] for r in table if not set("".join(r)) <= set("-: ")]
            t = Table(rows, repeatRows=1)
            t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                                   ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eef5")),
                                   ("VALIGN", (0, 0), (-1, -1), "TOP")]))
            flow.append(t); table.clear()

    for line in md.splitlines():
        s = line.strip()
        if s.startswith("|"):
            table.append([c.strip() for c in s.strip("|").split("|")]); continue
        flush()
        if not s or re.match(r"\*v\d", s):  # internal draft notes
            continue
        if s.startswith("# "):
            flow.append(Paragraph(inline(s[2:]), h1))
        elif s.startswith("## "):
            flow.append(Paragraph(inline(s[3:]), h2))
        elif s.startswith("- "):
            indent = 10 + (len(line) - len(line.lstrip())) * 4
            flow.append(Paragraph(inline(s[2:]), body, bulletText="•") if indent == 10 else
                        Paragraph(inline(s[2:]), ParagraphStyle("i", parent=body, leftIndent=indent), bulletText="–"))
        else:
            flow.append(Paragraph(inline(s), body))
    flush()
    doc = SimpleDocTemplate(str(out), pagesize=letter, leftMargin=50, rightMargin=50, topMargin=40, bottomMargin=40,
                            title="Team 17", author="", creator="", producer="", subject="", keywords="")
    doc.build(flow)


def deck(md, out):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    cp = prs.core_properties
    cp.author = cp.last_modified_by = cp.comments = cp.keywords = cp.subject = ""
    cp.title = "Team 17"
    slides = re.findall(r"^\d+\. \*\*(.+?)\*\*(.*?)(?=^\d+\. \*\*|\Z)", md, re.M | re.S)
    for title, rest in slides:
        s = prs.slides.add_slide(prs.slide_layouts[1])
        s.shapes.title.text = TAG.sub("", title).rstrip(".")
        lines = [l.strip() for l in rest.strip().splitlines() if l.strip()]
        lead, bullets = (lines[0] if lines and not lines[0].startswith("- ") else ""), [l[2:] for l in lines if l.startswith("- ")]
        tf = s.placeholders[1].text_frame
        tf.text = ""
        for i, t in enumerate(([lead] if lead else []) + bullets):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = re.sub(r"\*+|`", "", TAG.sub("", t))
            p.font.size = Pt(22)
    prs.save(out)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    pdf((DRAFTS / "memo.md").read_text(), OUT / "Team17_Memo.pdf", 9.5)
    pdf((DRAFTS / "appendix.md").read_text(), OUT / "Team17_AIAppendix.pdf", 8.5)
    deck((DRAFTS / "deck.md").read_text(), OUT / "Team17_Presentation.pptx")
    print("render: wrote memo, appendix, deck to", OUT, file=sys.stderr)
