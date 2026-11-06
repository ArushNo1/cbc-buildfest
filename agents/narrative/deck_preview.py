#!/usr/bin/env python3
"""Approximate slide previews + layout checks for a .pptx, without LibreOffice or PowerPoint automation.

Draws each slide to PNG with the real Calibri/Cambria metrics and reports:
  - text that needs more height than its box (overflow), with the shortfall in inches
  - shapes that run past the slide edge
  - text boxes overlapping pictures
  - tables whose rows grow past the footer once text is wrapped
It approximates PowerPoint's wrapping (word wrap, 1.2x line height, paragraph spacing), so a pass here
means "fits with a small margin", not a pixel-exact render.

  python3 agents/narrative/deck_preview.py deck.pptx out_dir/
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.oxml.ns import qn
from pptx.util import Emu

PX = 110  # pixels per inch
FONT_DIRS = [Path("/Applications/Microsoft PowerPoint.app/Contents/Resources/Fonts"), Path("/Library/Fonts"),
             Path("/System/Library/Fonts/Supplemental")]
FILES = {("Calibri", False, False): "Calibri.ttf", ("Calibri", True, False): "Calibrib.ttf",
         ("Calibri", False, True): "Calibrii.ttf", ("Calibri", True, True): "Calibriz.ttf",
         ("Cambria", False, False): "Cambria.ttc", ("Cambria", True, False): "Cambriab.ttf",
         ("Cambria", False, True): "Cambriai.ttf", ("Cambria", True, True): "Cambriaz.ttf"}
_cache: dict = {}


def font(name, bold, italic, size_pt):
    key = (name or "Calibri", bool(bold), bool(italic), round(size_pt * PX / 72))
    if key not in _cache:
        fn = FILES.get((key[0], key[1], key[2]), "Calibri.ttf")
        path = next((d / fn for d in FONT_DIRS if (d / fn).exists()), None)
        _cache[key] = ImageFont.truetype(str(path), key[3]) if path else ImageFont.load_default()
    return _cache[key]


def inch(v) -> float:
    return Emu(v).inches if v is not None else 0.0


def hexcolor(fill_or_color, default=None):
    try:
        return "#" + str(fill_or_color.rgb)
    except Exception:  # noqa: BLE001 - no explicit colour
        return default


def para_runs(p):
    runs = []
    for r in p.runs:
        f = r.font
        size = f.size.pt if f.size else 18
        runs.append((r.text, f.name or "Calibri", f.bold, f.italic, size, hexcolor(f.color, "#000000") if f.color and f.color.type else "#000000"))
    return runs


def layout_text(tf, width_in):
    """Return (lines, total_height_in). lines: (x_offset_in, y_in, text, font, color)."""
    lines, y = [], 0.0
    last_after = 0.0
    for p in tf.paragraphs:
        runs = para_runs(p)
        if not runs:
            y += 18 / 72 * 1.2
            continue
        _, name, bold, italic, size, color = runs[0]
        f = font(name, bold, italic, size)
        pPr = p._p.find(qn("a:pPr"))
        indent = inch(int(pPr.get("marL"))) if pPr is not None and pPr.get("marL") else 0.0
        bullet = pPr is not None and pPr.find(qn("a:buChar")) is not None
        avail = (width_in - indent) * PX
        words = "".join(r[0] for r in runs).split()
        spacing = p.line_spacing if isinstance(p.line_spacing, float) else 1.0
        lh = size / 72 * 1.2 * spacing
        cur = ""
        first = True
        for w in words:
            trial = (cur + " " + w).strip()
            if cur and f.getlength(trial) > avail:
                lines.append((indent, y, ("• " if bullet and first else "") + cur, f, color, p.alignment))
                y += lh
                first = False
                cur = w
            else:
                cur = trial
        lines.append((indent, y, ("• " if bullet and first else "") + cur, f, color, p.alignment))
        y += lh
        last_after = (p.space_after.pt if p.space_after is not None else 0) / 72
        y += last_after
    return lines, y - last_after  # space after the last paragraph never clips text


def draw_textframe(d, shape, x, y, w, h, problems, label):
    tf = shape.text_frame
    ml, mr = inch(tf.margin_left), inch(tf.margin_right)
    mt, mb = inch(tf.margin_top), inch(tf.margin_bottom)
    lines, th = layout_text(tf, w - ml - mr)
    avail = h - mt - mb
    if th > avail + 0.04 and any(t.strip("• ") for _, _, t, *_ in lines):
        problems.append(f"{label}: text needs {th:.2f}in but box is {avail:.2f}in (short by {th - avail:.2f}in): "
                        f"'{lines[0][2][:40]}'")
    anchor = tf.vertical_anchor
    oy = (avail - th) / 2 if anchor is not None and int(anchor) == 3 else 0  # MIDDLE
    for ix, iy, t, f, color, align in lines:
        tx = (x + ml + ix) * PX
        if align is not None and int(align) == 2:  # CENTER
            tx = (x + ml) * PX + ((w - ml - mr) * PX - f.getlength(t)) / 2
        elif align is not None and int(align) == 3:  # RIGHT
            tx = (x + w - mr) * PX - f.getlength(t)
        d.text((tx, (y + mt + oy + iy) * PX), t, font=f, fill=color)


def render(path: Path, out_dir: Path) -> list[str]:
    prs = Presentation(str(path))
    SW, SH = inch(prs.slide_width), inch(prs.slide_height)
    out_dir.mkdir(parents=True, exist_ok=True)
    problems: list[str] = []
    for n, slide in enumerate(prs.slides, start=1):
        bg = "#FFFFFF"
        try:
            if slide.background.fill.type == 1:
                bg = "#" + str(slide.background.fill.fore_color.rgb)
        except Exception:  # noqa: BLE001
            pass
        img = Image.new("RGB", (int(SW * PX), int(SH * PX)), bg)
        d = ImageDraw.Draw(img)
        pics, texts = [], []
        for sh in slide.shapes:
            x, y, w, h = inch(sh.left), inch(sh.top), inch(sh.width), inch(sh.height)
            label = f"slide {n} '{sh.name}'"
            if x < -0.01 or y < -0.01 or x + w > SW + 0.01 or y + h > SH + 0.01:
                problems.append(f"{label}: runs past the slide edge")
            if sh.shape_type == MSO_SHAPE_TYPE.PICTURE:
                im = Image.open(io.BytesIO(sh.image.blob)).convert("RGB").resize((int(w * PX), int(h * PX)))
                img.paste(im, (int(x * PX), int(y * PX)))
                pics.append((x, y, w, h))
                continue
            if sh.has_table:
                tbl = sh.table
                cy = y
                for r_i, row in enumerate(tbl.rows):
                    rh = inch(row.height)
                    need = 0.0
                    for c_i, cell in enumerate(row.cells):
                        cw = inch(tbl.columns[c_i].width)
                        _, th = layout_text(cell.text_frame, cw - inch(cell.margin_left) - inch(cell.margin_right))
                        need = max(need, th + inch(cell.margin_top) + inch(cell.margin_bottom))
                    rh = max(rh, need)
                    cx = x
                    for c_i, cell in enumerate(row.cells):
                        cw = inch(tbl.columns[c_i].width)
                        fill = hexcolor(cell.fill.fore_color, "#FFFFFF") if cell.fill.type == 1 else "#FFFFFF"
                        d.rectangle([cx * PX, cy * PX, (cx + cw) * PX, (cy + rh) * PX], fill=fill, outline="#C9D6DA")
                        draw_textframe(d, cell, cx, cy, cw, rh, [], label)
                        cx += cw
                    cy += rh
                if cy > SH - 0.55:
                    problems.append(f"{label}: table grows to {cy:.2f}in, into the footer (limit {SH - 0.55:.2f}in)")
                continue
            if sh.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE:
                try:
                    fill = "#" + str(sh.fill.fore_color.rgb) if sh.fill.type == 1 else None
                except Exception:  # noqa: BLE001
                    fill = None
                if fill:
                    box = [x * PX, y * PX, (x + w) * PX, (y + h) * PX]
                    if "OVAL" in str(sh.auto_shape_type):
                        d.ellipse(box, fill=fill)
                    else:
                        d.rounded_rectangle(box, radius=int(min(w, h) * PX * 0.07), fill=fill)
            if sh.has_text_frame and sh.text_frame.text.strip():
                draw_textframe(d, sh, x, y, w, h, problems, label)
                if sh.shape_type == MSO_SHAPE_TYPE.TEXT_BOX or sh.is_placeholder:
                    texts.append((label, x, y, w, h))
        for label, x, y, w, h in texts:
            for px, py, pw, ph in pics:
                if x < px + pw - 0.02 and px < x + w - 0.02 and y < py + ph - 0.02 and py < y + h - 0.02:
                    problems.append(f"{label}: overlaps a picture")
        img.save(out_dir / f"slide-{n:02d}.png")
    return problems


if __name__ == "__main__":
    probs = render(Path(sys.argv[1]), Path(sys.argv[2]))
    for p in probs:
        print("PROBLEM", p)
    print(f"deck_preview: {len(probs)} problem(s); images in {sys.argv[2]}")
    sys.exit(1 if probs else 0)
