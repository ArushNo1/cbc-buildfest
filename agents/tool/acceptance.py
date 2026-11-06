#!/usr/bin/env python3
"""Acceptance checks for the tool's deliverables: the checks a human reviewer would do by eye, automated.

  python3 agents/tool/acceptance.py            # prints PASS/FAIL per check, exit 1 on any FAIL
  python3 agents/tool/acceptance.py --report agents/tool/ACCEPTANCE.md

Checks (aggregate outputs only; never opens the survey export):
  numbers   every value, 95% range and n in the dashboard's "All numbers" table and every headline tile
            equals outputs/findings.json / themes.json as formatted; small groups never show a value
  offline   the page makes no network request and throws no script error (light, dark, phone width)
  a11y      lang, heading order, labelled controls, named SVG charts, a table for every chart,
            keyboard focus shows the tooltip, WCAG contrast of the text/graphic colour tokens
  layout    no horizontal scroll at 375 px
  video     length <= 120 s, no identity strings in metadata, narration numbers match outputs
  identity  no team identity strings in the dashboard, captions, notebook or artifact zip
Needs Playwright + Chromium for the page checks (`python3 -m playwright install --only-shell chromium`).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DASH = ROOT / "outputs" / "dashboard.html"
MP4 = ROOT / "agents" / "tool" / "dist" / "Team17_Demo.mp4"
SRT = MP4.with_suffix(".srt")
ZIP = ROOT / "agents" / "tool" / "dist" / "Team17_TechnicalArtifact.zip"
RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((name, bool(ok), detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail else ""))


def load(mod: str, path: Path):
    spec = importlib.util.spec_from_file_location(mod, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ------------------------------------------------------------------ formatting, mirrored from dashboard.js
def _signed(v: float, digits: int | None) -> str:
    body = str(abs(int(v))) if digits is None else f"{abs(v):.{digits}f}"
    return ("+" if v > 0 else "−" if v < 0 else "") + body


def fmt(v, unit: str) -> str:
    if v is None:
        return "—"
    if unit == "pct":
        return f"{v:.1f}%"
    if unit == "count":
        return f"{v:,.0f}" if float(v).is_integer() else f"{v:,}"
    if unit == "points":
        return _signed(v, 2)
    if unit == "nps":
        return _signed(v, None if float(v).is_integer() else 1)
    if unit in ("mean", "median"):
        return f"{v:.2f}"
    return str(round(v * 100) / 100)


def expected_rows(threshold: int) -> dict[str, dict]:
    out = {}
    findings = json.loads((ROOT / "outputs/findings.json").read_text(encoding="utf-8"))
    for f in findings["findings"]:
        out[f["id"]] = {"value": f["value"], "unit": f["unit"], "n": f["n"], "lo": f.get("ci_low"), "hi": f.get("ci_high"),
                        "hidden": f["value"] is None or f["suppressed"] or f["n"] < threshold}
    tpath = ROOT / "outputs/themes.json"
    if tpath.exists():
        for c in json.loads(tpath.read_text(encoding="utf-8"))["counts"]:
            out[c["id"]] = {"value": c["pct"], "unit": "pct", "n": c["n"], "lo": c.get("ci_low"), "hi": c.get("ci_high"),
                            "hidden": c["pct"] is None or c["suppressed"] or c["n"] < threshold}
    return out


def contrast(a: str, b: str) -> float:
    def lum(hexc: str) -> float:
        hexc = hexc.strip().lstrip("#")
        rgb = [int(hexc[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
        return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
    hi, lo = sorted([lum(a), lum(b)], reverse=True)
    return (hi + 0.05) / (lo + 0.05)


# ------------------------------------------------------------------ page checks
def page_checks() -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        check("page checks", False, "Playwright not installed")
        return
    threshold = json.loads((ROOT / "outputs/findings.json").read_text(encoding="utf-8"))["small_n_threshold"]
    exp = expected_rows(threshold)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for scheme, width in (("light", 1200), ("dark", 1200), ("light", 375)):
            ctx = browser.new_context(viewport={"width": width, "height": 900}, color_scheme=scheme, offline=True)
            page = ctx.new_page()
            errs, reqs = [], []
            page.on("pageerror", lambda e: errs.append(str(e)))
            page.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
            page.on("request", lambda r: reqs.append(r.url) if not r.url.startswith(("file:", "data:", "blob:")) else None)
            page.goto(DASH.resolve().as_uri())
            page.wait_for_timeout(400)
            broken = page.locator("text=could not be drawn").count()
            check(f"offline: {scheme} {width}px loads with no network, no script errors, no broken sections",
                  not errs and not reqs and broken == 0, f"errors={errs[:2]} requests={reqs[:2]} broken={broken}")
            if width == 375:
                sw = page.evaluate("document.documentElement.scrollWidth")
                check("layout: no horizontal scroll at 375 px", sw <= 375, f"scrollWidth={sw}")
            if scheme == "light" and width == 1200:
                numbers(page, exp)
                a11y(page)
            if scheme == "dark":
                tokens(page, "dark")
            elif width == 1200:
                tokens(page, "light")
            ctx.close()
        browser.close()


def numbers(page, exp: dict) -> None:
    sel = page.locator("#all select")
    dims = sel.evaluate("s => [...s.options].map(o => o.value).filter(v => v !== 'all')")
    seen, bad = {}, []
    for d in dims:
        sel.select_option(d)
        page.wait_for_timeout(50)
        line = page.locator("#all .count-line").inner_text()
        m = re.search(r"Showing ([\d,]+) of ([\d,]+)", line)
        if m and m.group(1) != m.group(2):
            bad.append(f"{d}: table truncated ({line})")
        rows = page.evaluate("""() => [...document.querySelectorAll('#all tbody tr')].map(tr =>
            [...tr.children].map(td => td.innerText.trim()))""")
        for cells in rows:
            seen[cells[7]] = cells
    missing = sorted(set(exp) - set(seen))
    extra = sorted(set(seen) - set(exp))
    for fid, cells in seen.items():
        e = exp.get(fid)
        if not e:
            continue
        want_v = "not shown" if e["hidden"] else fmt(e["value"], e["unit"])
        want_ci = "" if e["hidden"] or e["lo"] is None or e["hi"] is None else f"{fmt(e['lo'], e['unit'])} to {fmt(e['hi'], e['unit'])}"
        want_n = f"{e['n']:,}"
        if (cells[2], cells[3], cells[4]) != (want_v, want_ci, want_n):
            bad.append(f"{fid}: page {cells[2:5]} vs json {[want_v, want_ci, want_n]}")
    check(f"numbers: all {len(seen)} rows in 'All numbers' match findings/themes (value, 95% range, n)",
          not bad and not missing and not extra, f"mismatches={bad[:3]} missing={missing[:3]} extra={extra[:3]}")
    tiles = page.evaluate("""() => [...document.querySelectorAll('.tile')].map(t =>
        [t.title.replace(/^ID /, ''), t.querySelector('.t-value').childNodes[0].textContent.trim()])""")
    tbad = [f"{fid}: {shown}" for fid, shown in tiles
            if fid in exp and shown != ("Not shown" if exp[fid]["hidden"] else fmt(exp[fid]["value"], exp[fid]["unit"]))]
    check(f"numbers: all {len(tiles)} headline tiles match findings", tiles and not tbad, f"{tbad[:3]}")
    leaks = page.evaluate("""() => [...document.querySelectorAll('.rrow')].filter(r =>
        r.querySelector('.supp') && r.querySelector('.vlab')).length""")
    check("numbers: hidden small groups show no value on any chart", leaks == 0, f"rows={leaks}")


def a11y(page) -> None:
    lang = page.evaluate("document.documentElement.lang")
    check("a11y: page language set", bool(lang), lang)
    levels = page.evaluate("[...document.querySelectorAll('h1,h2,h3,h4')].map(h => +h.tagName[1])")
    jumps = [(a, b) for a, b in zip(levels, levels[1:]) if b > a + 1]
    check("a11y: one h1 and no skipped heading levels", levels.count(1) == 1 and not jumps, f"jumps={jumps[:3]}")
    unlabelled = page.evaluate("""() => [...document.querySelectorAll('select, input, button')].filter(el =>
        !((el.labels && el.labels.length) || el.getAttribute('aria-label') || el.textContent.trim())).length""")
    check("a11y: every control has a label", unlabelled == 0, f"unlabelled={unlabelled}")
    unnamed = page.evaluate("""() => [...document.querySelectorAll('.svgchart[role=img], .rchart')].filter(el =>
        !el.getAttribute('aria-label')).length""")
    check("a11y: every chart has an accessible name", unnamed == 0, f"unnamed={unnamed}")
    no_table = page.evaluate("""() => {
        const charts = [...document.querySelectorAll('main .rchart, main .svgchart')];
        return charts.filter(c => {
          let el = c.closest('div[aria-live]') ? c : c;
          for (let n = el.nextElementSibling, k = 0; n && k < 12; n = n.nextElementSibling, k++) {
            if (n.matches('details.tbl')) return false;
            if (n.matches('.rchart, .svgchart')) break;
          }
          const parent = c.parentElement;
          for (let n = parent && parent.nextElementSibling, k = 0; n && k < 6; n = n.nextElementSibling, k++) {
            if (n.matches('details.tbl')) return false;
          }
          return !(c.closest('#glance'));   // who-answered bars: numbers are in their labels and in All numbers
        }).length; }""")
    check("a11y: every chart has a table view next to it", no_table == 0, f"charts without table={no_table}")
    page.keyboard.press("Tab")
    first = page.evaluate("document.activeElement.textContent.trim()")
    check("a11y: first Tab reaches 'Skip to content'", first == "Skip to content", first)
    page.locator("#learning .rrow").first.focus()
    page.wait_for_timeout(50)
    tip = page.evaluate("(() => { const t = document.getElementById('tip'); return t.hidden ? '' : t.innerText; })()")
    page.keyboard.press("Escape")
    hidden_after = page.evaluate("document.getElementById('tip').hidden")
    check("a11y: keyboard focus on a bar shows its numbers; Escape hides them", bool(tip) and hidden_after, tip.split("\n")[0][:40])


def tokens(page, mode: str) -> None:
    get = page.evaluate("""() => { const s = getComputedStyle(document.documentElement);
        const o = {}; for (const k of ['ink','ink-2','muted','surface','surface-2','page','accent-ink','warn','warn-ink','crit','s-after','s-before'])
          o[k] = s.getPropertyValue('--' + k).trim(); return o; }""")
    text_pairs = [("ink", "surface"), ("ink", "page"), ("ink-2", "surface"), ("ink-2", "surface-2"), ("ink-2", "page"),
                  ("accent-ink", "surface"), ("accent-ink", "surface-2"), ("warn-ink", "warn")]
    low = [f"{a}/{b} {contrast(get[a], get[b]):.2f}" for a, b in text_pairs if contrast(get[a], get[b]) < 4.5]
    if mode == "light":
        c = contrast("#ffffff", get["crit"])
        if c < 4.5:
            low.append(f"banner white/crit {c:.2f}")
    check(f"a11y: text contrast >= 4.5:1 ({mode})", not low, "; ".join(low))
    glow = [f"{a} {contrast(get[a], get['surface']):.2f}" for a in ("s-after", "s-before") if contrast(get[a], get["surface"]) < 3]
    check(f"a11y: chart marks contrast >= 3:1 against the background ({mode})", not glow, "; ".join(glow))


# ------------------------------------------------------------------ video, identity
def ffmpeg() -> str | None:
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return None


def video_checks(pats, hits) -> None:
    if not MP4.exists():
        check("video: mp4 exists", False, str(MP4))
        return
    ff = ffmpeg()
    if ff:
        info = subprocess.run([ff, "-hide_banner", "-i", str(MP4)], capture_output=True, text=True).stderr
        m = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", info)
        dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)) if m else None
        check("video: length <= 120 s", dur is not None and dur <= 120, f"{dur} s")
        meta = "\n".join(l for l in info.splitlines() if re.match(r"\s+\w+\s*:", l))
        found = hits(meta, pats)
        check("video: no identity strings in metadata", not found, ", ".join(found))
    else:
        check("video: length <= 120 s", False, "no ffmpeg to read it")
    cn = load("check_numbers", ROOT / "scripts/check_numbers.py")
    errs = cn.check_text((ROOT / "agents/tool/video/script.md").read_text(encoding="utf-8"), cn.load_index(), "script.md")
    check("video: every narrated number matches outputs (check_numbers)", not errs, "; ".join(errs[:2]))
    check("video: captions file present", SRT.exists() and SRT.stat().st_size > 0)


def identity_checks(pats, hits) -> None:
    targets = {p.relative_to(ROOT).as_posix(): p.read_text(encoding="utf-8", errors="ignore")
               for p in (DASH, SRT, ROOT / "agents/tool/walkthrough.ipynb") if p.exists()}
    if ZIP.exists():
        with zipfile.ZipFile(ZIP) as z:
            for info in z.infolist():
                if not info.is_dir():
                    targets[f"zip:{info.filename}"] = z.read(info).decode("utf-8", "ignore")
            data = [n for n in z.namelist() if re.search(r"^(?:[^/]+/)?data/|\.(xlsx|csv)$", n)]
        check("identity: zip contains no data files", not data, ", ".join(data[:3]))
    found = {k: hits(v, pats) for k, v in targets.items()}
    found = {k: v for k, v in found.items() if v}
    check(f"identity: no team identity strings in {len(targets)} files", not found, str(dict(list(found.items())[:3])))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--report", type=Path, help="also write the results as a markdown table")
    args = ap.parse_args(argv)
    verify = load("verify", ROOT / "scripts/verify.py")
    pats, hits = verify.identity_patterns(), verify.identity_hits
    page_checks()
    video_checks(pats, hits)
    identity_checks(pats, hits)
    failed = [r for r in RESULTS if not r[1]]
    print(f"\nacceptance: {len(RESULTS) - len(failed)}/{len(RESULTS)} passed")
    if args.report:
        src = json.loads((ROOT / "outputs/findings.json").read_text(encoding="utf-8"))["source"]
        lines = ["# Tool acceptance checks", "",
                 f"Automated by `agents/tool/acceptance.py` on outputs built from input fingerprint `{src['file_sha256'][:12]}` "
                 f"({src['n_rows']:,} rows). Re-run: `python3 agents/tool/acceptance.py --report agents/tool/ACCEPTANCE.md`.", "",
                 "| Check | Result | Detail |", "|---|---|---|"]
        lines += [f"| {n} | {'PASS' if ok else 'FAIL'} | {d.replace('|', '/')} |" for n, ok, d in RESULTS]
        args.report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
