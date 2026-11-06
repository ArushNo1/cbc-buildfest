"""Build Team17_Presentation.pptx from agents/narrative/drafts/deck.md (called by scripts/render.py).

Layouts: title, question, solution, stats, chart, table, cards, closing (see deck.md for the syntax).
Charts are the dashboard's own chart images (agents/tool/dist/deck_assets/), so slides show the same
numbers and conventions as the dashboard. [F:id] tags are stripped; author metadata stays empty (rule 3).
"""
from __future__ import annotations

import re
from pathlib import Path

from lxml import etree
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
TAG = re.compile(r"\s*\[F:[^\]]+\]")

# Palette: deep teal dominates, one warm accent for key numbers, near-black ink. Fonts are Office-safe.
INK, MUTED, TEAL, TEAL_D, TINT, ACCENT = "1B2A33", "4E5D65", "0E5E6F", "0B3F4C", "E8F1F3", "B4510F"
WHITE, ON_DARK = "FFFFFF", "D3E6EA"
HEAD, BODY = "Cambria", "Calibri"
W, H, M = 13.333, 7.5, 0.6


def clean(t: str) -> str:
    return re.sub(r"`", "", TAG.sub("", t)).strip()


# ----------------------------------------------------------------------------- parse deck.md

def parse(md: str) -> list[dict]:
    slides, cur = [], None
    for raw in md.splitlines():
        line = raw.rstrip()
        if line.startswith("## "):
            cur = {"title": clean(line[3:]), "layout": "cards", "notes": [], "bullets": [], "multi": {}}
            slides.append(cur)
            continue
        if cur is None or not line.strip():
            continue
        if line.startswith("- "):
            cur["bullets"].append(clean(line[2:]))
            continue
        m = re.match(r"^([a-z]+):\s*(.*)$", line)
        if not m:
            continue
        key, val = m.group(1), m.group(2)
        if key == "notes":
            cur["notes"].append(clean(val))
        elif key in ("card", "step", "stat", "callout", "quote", "row"):
            cur["multi"].setdefault(key, []).append([clean(x) for x in val.split("|")])
        else:
            cur[key] = val.strip() if key in ("image", "layout") else clean(val)
    return slides


# ----------------------------------------------------------------------------- drawing helpers

def rgb(h: str) -> RGBColor:
    return RGBColor.from_string(h)


def box(slide, x, y, w, h, fill=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE, name=None, radius=0.07):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    s.shadow.inherit = False
    if fill:
        s.fill.solid()
        s.fill.fore_color.rgb = rgb(fill)
    else:
        s.fill.background()
    s.line.fill.background()
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = radius
    if name:
        s.name = name
    s.text_frame.text = ""
    return s


def text(slide, x, y, w, h, runs, size=16, color=INK, font=BODY, bold=False, italic=False, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, bullets=False, space_after=6, name=None, line=None):
    """runs: a string, or a list of paragraphs; each paragraph a string or a list of (text, {overrides})."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        tb.name = name
    tf = tb.text_frame
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.05)
    tf.margin_top = tf.margin_bottom = Inches(0.03)
    paras = runs if isinstance(runs, list) else [runs]
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(space_after)
        if line:
            p.line_spacing = line
        parts = para if isinstance(para, list) else [(para, {})]
        for t, o in parts:
            r = p.add_run()
            r.text = t
            f = r.font
            f.name = o.get("font", font)
            f.size = Pt(o.get("size", size))
            f.bold = o.get("bold", bold)
            f.italic = o.get("italic", italic)
            f.color.rgb = rgb(o.get("color", color))
        if bullets:
            pPr = p._p.get_or_add_pPr()
            pPr.set("marL", str(Emu(Inches(0.28))))
            pPr.set("indent", str(-Emu(Inches(0.22))))
            for tagname in ("a:buNone", "a:buChar", "a:buAutoNum"):
                for el in pPr.findall(qn(tagname)):
                    pPr.remove(el)
            bu_clr = etree.SubElement(pPr, qn("a:buClr"))
            etree.SubElement(bu_clr, qn("a:srgbClr")).set("val", TEAL)
            ch = etree.SubElement(pPr, qn("a:buChar"))
            ch.set("char", "•")
    return tb


def circle_num(slide, x, y, d, label, fill=TEAL, color=WHITE, size=18):
    c = box(slide, x, y, d, d, fill=fill, shape=MSO_SHAPE.OVAL)
    tf = c.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = label
    r.font.name, r.font.size, r.font.bold = HEAD, Pt(size), True
    r.font.color.rgb = rgb(color)
    return c


def picture(slide, path: str, x, y, maxw, maxh, alt: str, pad=0.16, crop=(0.0, 0.0, 0.0, 0.0)):
    """Chart image in a tinted rounded frame that hugs it (aspect kept). Returns the frame (x, y, w, h)."""
    src = ROOT / path
    if not src.exists():
        raise SystemExit(f"deck: missing chart image {path}; run python3 agents/tool/deck_assets.py")
    iw, ih = Image.open(src).size
    l, t, r, b = crop
    aspect = (iw * (1 - l - r)) / (ih * (1 - t - b))
    pw = maxw - 2 * pad
    ph = pw / aspect
    if ph > maxh - 2 * pad:
        ph = maxh - 2 * pad
        pw = ph * aspect
    w, h = pw + 2 * pad, ph + 2 * pad
    box(slide, x, y, w, h, fill=TINT, name="Chart frame", radius=0.04)
    pic = slide.shapes.add_picture(str(src), Inches(x + pad), Inches(y + pad), Inches(pw), Inches(ph))
    pic.crop_left, pic.crop_top, pic.crop_right, pic.crop_bottom = l, t, r, b
    pic._element.nvPicPr.cNvPr.set("descr", alt)
    pic.name = "Dashboard chart"
    return x, y, w, h


def set_title(slide, title: str, dark=False, y=0.42, size=34):
    t = slide.shapes.title
    t.left, t.top, t.width, t.height = Inches(M), Inches(y), Inches(W - 2 * M), Inches(0.85)
    tf = t.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.TOP
    tf.margin_left = tf.margin_right = Inches(0.05)
    tf.text = ""
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    r = p.add_run()
    r.text = title
    r.font.name, r.font.size, r.font.bold = HEAD, Pt(size), True
    r.font.color.rgb = rgb(WHITE if dark else INK)


def footer(slide, n: int):
    text(slide, M, H - 0.5, 4, 0.3, "Team 17 · EveryMind 988 training", size=11, color=MUTED, name="Footer")
    text(slide, W - M - 1, H - 0.5, 1, 0.3, str(n), size=11, color=MUTED, align=PP_ALIGN.RIGHT, name="Slide number")


def dark(slide):
    bg = slide.background.fill
    bg.solid()
    bg.fore_color.rgb = rgb(TEAL_D)


# ----------------------------------------------------------------------------- layouts

def l_title(s, d):
    dark(s)
    set_title(s, d["title"], dark=True, y=2.15, size=44)
    s.shapes.title.height = Inches(2.0)
    text(s, M, 1.45, 11.5, 0.5, d.get("kicker", ""), size=16, color=ON_DARK, name="Kicker")
    text(s, M, 4.45, 10.6, 1.2, d.get("sub", ""), size=20, color=ON_DARK, line=1.1, name="Subtitle")
    text(s, M, 6.3, 6, 0.5, d.get("foot", ""), size=18, color=WHITE, bold=True, name="Team")


def l_question(s, d):
    set_title(s, d["title"])
    text(s, M, 1.75, 5.5, 3.6, d.get("big", ""), size=32, color=TEAL, font=HEAD, bold=True, line=1.05, name="Question")
    x, w = 6.55, W - M - 6.55
    for i, (num, head, body) in enumerate(d["multi"].get("card", [])):
        y = 1.75 + i * 1.55
        box(s, x, y, w, 1.35, fill=TINT, name=f"Card {num}")
        circle_num(s, x + 0.25, y + 0.32, 0.7, num)
        text(s, x + 1.15, y + 0.17, w - 1.35, 0.45, head, size=20, bold=True, color=TEAL)
        text(s, x + 1.15, y + 0.62, w - 1.35, 0.65, body, size=15, color=INK)
    text(s, M, 5.75, 5.5, 0.9, d.get("foot", ""), size=13, color=MUTED, line=1.05, name="Data note")


def l_solution(s, d):
    set_title(s, d["title"])
    x, w = M, 5.45
    for i, (num, head, body) in enumerate(d["multi"].get("step", [])):
        y = 1.5 + i * 1.22
        box(s, x, y, w, 1.08, fill=TINT, name=f"Step {num}")
        circle_num(s, x + 0.2, y + 0.24, 0.6, num, size=16)
        text(s, x + 0.95, y + 0.08, w - 1.1, 0.4, head, size=17, bold=True, color=TEAL, space_after=0)
        text(s, x + 0.95, y + 0.46, w - 1.1, 0.58, body, size=13.5, color=INK, line=1.0, space_after=0)
    text(s, x, 5.25, w, 1.5, d["bullets"], size=14, bullets=True, space_after=5, name="Features")
    crop = tuple(float(v) for v in d["crop"].split(",")) if d.get("crop") else (0.0, 0.0, 0.0, 0.0)
    maxh = 4.75 if d.get("url") else 5.2
    fx, fy, fw, fh = picture(s, d["image"], 6.35, 1.5, W - M - 6.35, maxh, d.get("alt", ""), crop=crop)
    if d.get("url"):
        text(s, fx, fy + fh + 0.12, fw, 0.4, [[("Live: ", {"color": MUTED, "bold": False}), (d["url"], {})]],
             size=16, bold=True, color=TEAL, name="Website address")


def l_stats(s, d):
    set_title(s, d["title"])
    if d.get("lead"):
        text(s, M, 1.28, W - 2 * M, 0.5, d["lead"], size=18, color=MUTED, name="Lead")
    stats = d["multi"].get("stat", [])
    gap = 0.3
    cw = (W - 2 * M - gap * (len(stats) - 1)) / max(1, len(stats))
    for i, (value, label, subtext) in enumerate(stats):
        x, y = M + i * (cw + gap), 2.05
        box(s, x, y, cw, 3.35, fill=TINT, name=f"Stat {i + 1}")
        text(s, x + 0.3, y + 0.3, cw - 0.6, 1.15, value, size=58, font=HEAD, bold=True, color=TEAL)
        text(s, x + 0.3, y + 1.55, cw - 0.6, 0.85, label, size=19, bold=True, color=INK, line=1.0)
        text(s, x + 0.3, y + 2.42, cw - 0.6, 0.8, subtext, size=13.5, color=MUTED, line=1.0)
    if d.get("note"):
        text(s, M, 5.7, W - 2 * M, 0.8, d["note"], size=15, color=INK, name="Note")


def l_chart(s, d):
    set_title(s, d["title"])
    iw, ih = Image.open(ROOT / d["image"]).size
    callouts, quotes = d["multi"].get("callout", []), d["multi"].get("quote", [])
    if iw / ih >= 2.5:  # wide chart: full width on top, callouts in a row underneath
        fx, fy, fw, fh = picture(s, d["image"], M, 1.45, W - 2 * M, 3.25, d.get("alt", ""))
        y = fy + fh + 0.3
        gap = 0.3
        cw = (W - 2 * M - gap * (len(callouts) - 1)) / max(1, len(callouts))
        for i, (value, label) in enumerate(callouts):
            x = M + i * (cw + gap)
            box(s, x, y, cw, 1.3, fill=TINT, name="Callout")
            text(s, x + 0.25, y + 0.12, cw - 0.5, 0.5, value, size=26, font=HEAD, bold=True, color=ACCENT, space_after=0)
            text(s, x + 0.25, y + 0.66, cw - 0.5, 0.6, label, size=13.5, color=INK, line=1.0, space_after=0)
        if d.get("caveat"):
            text(s, M, y + 1.45, W - 2 * M, 0.55, d["caveat"], size=13, color=MUTED, line=1.0, name="Caveat")
        return
    fx, fy, fw, fh = picture(s, d["image"], M, 1.45, 7.6, 5.25, d.get("alt", ""))
    x = fx + fw + 0.35
    w = W - M - x
    y = 1.45
    for value, label in callouts:
        box(s, x, y, w, 1.3, fill=TINT, name="Callout")
        text(s, x + 0.22, y + 0.12, w - 0.44, 0.5, value, size=26, font=HEAD, bold=True, color=ACCENT, space_after=0)
        text(s, x + 0.22, y + 0.64, w - 0.44, 0.62, label, size=13, color=INK, line=1.0, space_after=0)
        y += 1.45
    for q in quotes:
        text(s, x + 0.05, y, w - 0.1, 0.62, f"“{q[0].strip(chr(34))}”", size=14, italic=True, color=TEAL, line=1.0,
             space_after=0, name="Participant quote")
        y += 0.7
    if d.get("caveat"):
        top = max(y + 0.1, 5.6)
        text(s, x, top, w, 6.75 - top, d["caveat"], size=12, color=MUTED, line=1.0, space_after=0, name="Caveat")


def l_table(s, d):
    set_title(s, d["title"])
    rows = d["multi"].get("row", [])
    widths = [0.5, 5.35, 3.05, 3.23]
    tbl = s.shapes.add_table(len(rows), 4, Inches(M), Inches(1.5), Inches(sum(widths)), Inches(5.0)).table
    for j, wd in enumerate(widths):
        tbl.columns[j].width = Inches(wd)
    for i, r in enumerate(rows):
        tbl.rows[i].height = Inches(0.5 if i == 0 else 0.9)
        for j, val in enumerate(r):
            c = tbl.cell(i, j)
            c.margin_left = c.margin_right = Inches(0.1)
            c.margin_top = c.margin_bottom = Inches(0.05)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            c.fill.solid()
            c.fill.fore_color.rgb = rgb(TEAL if i == 0 else (TINT if i % 2 == 0 else WHITE))
            tf = c.text_frame
            tf.word_wrap = True
            tf.text = ""
            run = tf.paragraphs[0].add_run()
            run.text = val
            run.font.name = BODY
            run.font.size = Pt(14 if i == 0 else 13)
            run.font.bold = i == 0 or j == 0
            run.font.color.rgb = rgb(WHITE if i == 0 else INK)


def l_cards(s, d):
    set_title(s, d["title"])
    top = 1.5
    if d.get("lead"):
        text(s, M, 1.28, W - 2 * M, 0.5, d["lead"], size=18, color=MUTED, name="Lead")
        top = 1.95
    cards = d["multi"].get("card", [])
    cols = 3 if len(cards) in (3, 6) else 2
    nrows = -(-len(cards) // cols)
    gap = 0.3
    cw = (W - 2 * M - gap * (cols - 1)) / cols
    ch = (6.75 - top - gap * (nrows - 1)) / nrows
    for i, (head, body) in enumerate(cards):
        x, y = M + (i % cols) * (cw + gap), top + (i // cols) * (ch + gap)
        box(s, x, y, cw, ch, fill=TINT, name=f"Card {i + 1}")
        text(s, x + 0.3, y + 0.2, cw - 0.6, 0.45, head, size=19, bold=True, color=TEAL)
        text(s, x + 0.3, y + 0.7, cw - 0.6, ch - 0.85, body, size=14.5, color=INK, line=1.05)


def l_closing(s, d):
    dark(s)
    set_title(s, d["title"], dark=True, y=1.0, size=40)
    for i, b in enumerate(d["bullets"]):
        y = 2.35 + i * 1.0
        circle_num(s, M, y, 0.62, str(i + 1), fill=WHITE, color=TEAL_D, size=18)
        text(s, M + 0.9, y + 0.07, 10.8, 0.6, b, size=22, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
    text(s, M, 5.9, 8, 0.7, d.get("foot", ""), size=26, font=HEAD, bold=True, color=WHITE, name="Thanks")


LAYOUTS = {"title": l_title, "question": l_question, "solution": l_solution, "stats": l_stats, "chart": l_chart,
           "table": l_table, "cards": l_cards, "closing": l_closing}


def build(md: str, out: Path) -> None:
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(W), Inches(H)
    cp = prs.core_properties
    cp.author = cp.last_modified_by = cp.comments = cp.keywords = cp.subject = cp.category = ""
    cp.title = "Team 17"
    title_only = prs.slide_layouts[5]
    slides = parse(md)
    for n, d in enumerate(slides, start=1):
        s = prs.slides.add_slide(title_only)
        LAYOUTS[d["layout"]](s, d)
        if d["layout"] not in ("title", "closing"):
            footer(s, n)
        if d["notes"]:
            s.notes_slide.notes_text_frame.text = " ".join(d["notes"])
    prs.save(out)
