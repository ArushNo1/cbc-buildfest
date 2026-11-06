#!/usr/bin/env python3
"""Export slide-ready PNGs of dashboard charts for the presentation (agents/tool/dist/deck_assets/).

Each image is a screenshot of a real dashboard chart, so slides show exactly the dashboard's numbers
and conventions (bars from zero, n on every row, 95% ranges, small groups hidden). Aggregates only.

  python3 agents/tool/deck_assets.py
Needs Playwright + Chromium (`python3 -m playwright install --only-shell chromium`).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DASH = ROOT / "outputs" / "dashboard.html"
OUT = ROOT / "agents" / "tool" / "dist" / "deck_assets"

# (file name, what to show). Each spec: optional compare filters, then a CSS selector to capture.
ASSETS = [
    ("01_dashboard_overview.png", {"clip_top": "#glance", "height": 760}),
    ("02_post_agreement_before_after.png", {"selector": "#learning .rchart"}),
    ("03_recommend_by_role.png", {"compare": ("recommend.score.mean", "role"), "selector": "#compare .rchart"}),
    ("04_recommend_by_county.png", {"compare": ("recommend.score.mean", "county"), "selector": "#compare .rchart"}),
    ("05_recommend_by_month.png", {"compare": ("recommend.score.mean", "training_month"), "selector": "#compare .svgchart >> xpath=.."}),  # include its legend
    ("06_themes_improve.png", {"selector": "#comments .rchart >> nth=1"}),
    ("07_themes_valuable.png", {"selector": "#comments .rchart >> nth=0"}),
    ("08_recommend_distribution.png", {"selector": "#recommend .svgchart >> nth=0"}),
    ("09_call988_tiles.png", {"selector": "#recommend .tiles"}),
    ("10_who_answered_county.png", {"selector": "#glance .rchart >> nth=0"}),
]


def main() -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("deck_assets: Playwright not installed", file=sys.stderr)
        return 1
    html = DASH.read_text(encoding="utf-8")
    if "(EXAMPLE DATA)</title>" in html:
        print("deck_assets: dashboard is stamped EXAMPLE DATA; run make run first", file=sys.stderr)
        return 1
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900}, device_scale_factor=2, color_scheme="light")
        page.goto(DASH.resolve().as_uri())
        page.wait_for_timeout(400)
        page.add_style_tag(content="#tip{display:none!important} .rrow:hover{background:none}")
        for name, spec in ASSETS:
            if "compare" in spec:
                metric, dim = spec["compare"]
                page.select_option("#cmp-metric", metric)
                page.select_option("#cmp-dim", dim)
                page.wait_for_timeout(250)
            if "clip_top" in spec:
                page.evaluate("window.scrollTo(0, 0)")
                page.wait_for_timeout(100)
                top = page.evaluate(f"document.querySelector('{spec['clip_top']}').getBoundingClientRect().top + window.scrollY")
                page.screenshot(path=str(OUT / name), full_page=True,
                                clip={"x": 0, "y": 0, "width": 1280, "height": top + spec["height"]})
            else:
                loc = page.locator(spec["selector"])
                if ">> nth=" not in spec["selector"]:
                    loc = loc.first
                # Element screenshots scroll and crop by themselves (page coordinates handled by Playwright).
                loc.screenshot(path=str(OUT / name))
            print(f"deck_assets: {name}")
        site = ROOT / "site" / "index.html"
        if site.exists():  # the website itself (header, Update button, drop zone, dashboard), for the solution slide
            import functools
            import http.server
            import socketserver
            import threading

            class Quiet(http.server.SimpleHTTPRequestHandler):
                def log_message(self, *args):
                    pass

            httpd = socketserver.TCPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(site.parent)))
            threading.Thread(target=httpd.serve_forever, daemon=True).start()
            wpage = browser.new_page(viewport={"width": 1280, "height": 820}, device_scale_factor=2, color_scheme="light")
            wpage.goto(f"http://127.0.0.1:{httpd.server_address[1]}/")
            wpage.wait_for_timeout(700)
            wpage.click("#open")
            wpage.wait_for_timeout(250)
            wpage.screenshot(path=str(OUT / "00_website.png"))
            httpd.shutdown()
            print("deck_assets: 00_website.png")
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
