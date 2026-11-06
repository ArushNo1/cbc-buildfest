#!/usr/bin/env python3
"""Browser test of the static website (site/), the way a judge or staff member uses it.

Serves site/ on localhost, then in headless Chromium checks:
  load       the page and the embedded dashboard load with no script errors (light, dark, 375 px)
  layout     no horizontal scroll at 375 px; the update button stays visible
  keyboard   Tab reaches the update button; Enter opens the panel; aria-expanded follows
  bad file   a non-Excel file gives a plain-language message
  update     dropping a synthetic export (tests/fixtures) rebuilds the dashboard in the browser via Pyodide,
             the download link appears, and unknown labels are flagged in the rebuilt dashboard
  broken     an .xlsx without the survey sheet gives a plain-language message, not a traceback
Needs: Playwright + Chromium, network access to the Pyodide CDN and PyPI, and `make fixtures`.

  python3 scripts/site_check.py [--real data/raw/<export>.xlsx]   # --real also compares numbers with outputs/
"""
from __future__ import annotations

import argparse
import functools
import http.server
import json
import re
import socketserver
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
FIX = ROOT / "tests" / "fixtures"
RESULTS: list[tuple[str, bool, str]] = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail else ""), flush=True)


def serve():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):  # keep the report readable
            pass

    handler = functools.partial(Quiet, directory=str(SITE))
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, f"http://127.0.0.1:{httpd.server_address[1]}/"


def embedded(html: str) -> dict:
    m = re.search(r'<script id="dash-data" type="application/json">(.*?)</script>', html, re.S)
    return json.loads(m.group(1)) if m else {}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--real", type=Path, help="also rebuild from this export and compare with outputs/")
    ap.add_argument("--url", help="test a deployed copy (e.g. the Vercel URL) instead of serving site/ locally")
    args = ap.parse_args(argv)
    from playwright.sync_api import sync_playwright

    if not (SITE / "index.html").exists():
        print("site_check: run `make site` first", file=sys.stderr)
        return 1
    fixture = FIX / "fixture_new_county.xlsx"
    if not fixture.exists():
        print("site_check: run `make fixtures` first", file=sys.stderr)
        return 1
    httpd, url = (None, args.url.rstrip("/") + "/") if args.url else serve()
    with sync_playwright() as p:
        b = p.chromium.launch()
        for scheme, width in (("light", 1280), ("dark", 1280), ("light", 375)):
            ctx = b.new_context(viewport={"width": width, "height": 860}, color_scheme=scheme)
            page = ctx.new_page()
            errs = []
            page.on("pageerror", lambda e: errs.append(str(e)))
            page.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
            resp = page.goto(url)
            if not resp or resp.status != 200:
                check(f"load: {url} answers 200", False, f"HTTP {resp.status if resp else 'no response'}")
                ctx.close()
                b.close()
                print("site_check: the site does not load; stopping")
                return 1
            page.wait_for_timeout(800)
            frame = page.frame_locator("#dash")
            tiles = frame.locator(".tile").count()
            check(f"load: {scheme} {width}px, page and dashboard load without script errors", not errs and tiles > 0,
                  f"errors={errs[:2]} tiles={tiles}")
            if width == 375:
                sw = page.evaluate("document.documentElement.scrollWidth")
                visible = page.locator("#open").is_visible()
                check("layout: 375 px has no horizontal scroll and the update button is visible", sw <= 375 and visible,
                      f"scrollWidth={sw}")
            ctx.close()

        ctx = b.new_context(viewport={"width": 1280, "height": 860})
        page = ctx.new_page()
        off_errs, off_reqs = [], []
        page.on("pageerror", lambda e: off_errs.append(str(e)))
        page.on("console", lambda m: off_errs.append(m.text) if m.type == "error" else None)

        def no_internet(route):  # simulate no internet: only the site's own server answers
            if route.request.url.startswith(url):
                route.continue_()
            else:
                off_reqs.append(route.request.url)
                route.abort()

        page.route("**/*", no_internet)
        page.goto(url)
        page.wait_for_timeout(600)
        tiles = page.frame_locator("#dash").locator(".tile").count()
        check("privacy: viewing the dashboard makes no third-party request and needs no internet",
              tiles > 0 and not off_reqs and not off_errs, f"tiles={tiles} requests={off_reqs[:2]} errors={off_errs[:2]}")
        ctx.close()

        ctx = b.new_context(viewport={"width": 1280, "height": 860})
        page = ctx.new_page()
        errs = []
        page.on("pageerror", lambda e: errs.append(str(e)))
        page.goto(url)
        page.wait_for_timeout(500)
        for _ in range(6):
            page.keyboard.press("Tab")
            if page.evaluate("document.activeElement.id") == "open":
                break
        reached = page.evaluate("document.activeElement.id") == "open"
        page.keyboard.press("Enter")
        opened = page.evaluate("document.getElementById('panel').classList.contains('open')")
        expanded = page.get_attribute("#open", "aria-expanded")
        check("keyboard: Tab reaches the update button, Enter opens the panel", reached and opened and expanded == "true",
              f"reached={reached} opened={opened} aria-expanded={expanded}")

        href = page.get_attribute("#code", "href") or ""
        resp = page.request.get(url + href) if href else None
        body = resp.body() if resp and resp.ok else b""
        names = []
        if body[:2] == b"PK":
            import io
            import zipfile
            names = zipfile.ZipFile(io.BytesIO(body)).namelist()
        bad = [n for n in names if re.search(r"^(?:[^/]+/)?data/|\.(xlsx|csv)$", n)]
        check("code: 'Source code (.zip)' downloads a valid zip with no data files",
              bool(names) and not bad and any(n.endswith("agents/data/pipeline.py") for n in names),
              f"HTTP {resp.status if resp else 'none'}, {len(names)} files, data files={bad[:2]}")

        with tempfile.TemporaryDirectory() as d:
            txt = Path(d) / "notes.txt"
            txt.write_text("not a spreadsheet")
            page.set_input_files("#file", str(txt))
            page.wait_for_timeout(300)
            msg = page.inner_text("#status")
            check("bad file: a non-Excel file gets a plain-language message", "isn't an Excel file" in msg, msg[:80])

            page.set_input_files("#file", str(fixture))
            try:
                page.wait_for_function("['ok','bad'].includes(document.getElementById('status').className)", timeout=300_000)
            except Exception as e:  # noqa: BLE001
                check("update: rebuilt from a synthetic export in the browser", False, f"timed out: {e.__class__.__name__}")
            msg = page.inner_text("#status")
            srcdoc = page.get_attribute("#dash", "srcdoc") or ""
            vm = embedded(srcdoc)
            flagged = [r for r in (vm.get("validation_report") or []) if "unknown_county" in r[0]]
            dl = page.locator("#dl")
            check("update: dropping a synthetic export rebuilds the dashboard in the browser",
                  msg.startswith("Done") and vm.get("meta", {}).get("source", {}).get("n_rows") == 300 and dl.is_visible(),
                  msg[:90])
            check("update: the new county in the export is flagged in the rebuilt dashboard", bool(flagged), str(flagged[:1]))

            page.evaluate("() => { const s = document.getElementById('status'); s.textContent = ''; s.className = ''; }")
            page.set_input_files("#file", str(fixture))  # the same file again, as after fixing an export
            try:
                page.wait_for_function("['ok','bad'].includes(document.getElementById('status').className)", timeout=120_000)
                again = page.inner_text("#status")
            except Exception:  # noqa: BLE001
                again = "no response"
            check("update: choosing the same file a second time updates again", again.startswith("Done"), again[:60])

            import openpyxl
            wb = openpyxl.Workbook()
            wb.active.title = "Sheet1"
            wb.active["A1"] = "hello"
            broken = Path(d) / "wrong_workbook.xlsx"
            wb.save(broken)
            page.set_input_files("#file", str(broken))
            page.wait_for_function("['ok','bad'].includes(document.getElementById('status').className) && "
                                   "!document.getElementById('status').textContent.startsWith('Reading')", timeout=120_000)
            msg = page.inner_text("#status")
            check("broken: an .xlsx without the survey sheet gets a plain-language message",
                  "no sheet named" in msg and "Traceback" not in msg and "/app/" not in msg, msg[:220])

            if args.real:
                page.set_input_files("#file", str(args.real))
                page.wait_for_function("document.getElementById('status').textContent.startsWith('Done') || "
                                       "document.getElementById('status').textContent.startsWith(\"Couldn't\")", timeout=300_000)
                got = embedded(page.get_attribute("#dash", "srcdoc") or "")
                want = embedded((ROOT / "outputs/dashboard.html").read_text(encoding="utf-8"))
                gm = {m["key"]: m for m in got.get("metrics", [])}
                wm = {m["key"]: m for m in want.get("metrics", [])}
                same = gm.keys() == wm.keys() and all(
                    json.dumps(gm[k]["overall"], sort_keys=True) == json.dumps(wm[k]["overall"], sort_keys=True) and
                    json.dumps(gm[k]["dims"], sort_keys=True) == json.dumps(wm[k]["dims"], sort_keys=True) for k in wm)
                check("real: numbers rebuilt in the browser equal outputs/dashboard.html", same,
                      f"metrics {len(gm)} vs {len(wm)}")
        check("update: no script errors during the update flow", not [e for e in errs if "Traceback" not in e], str(errs[:2]))
        ctx.close()
        b.close()
    if httpd:
        httpd.shutdown()
    failed = [r for r in RESULTS if not r[1]]
    print(f"site_check: {len(RESULTS) - len(failed)}/{len(RESULTS)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
