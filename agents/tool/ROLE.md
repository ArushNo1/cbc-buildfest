# ROLE: tool agent

Read `CLAUDE.md` first. Your status issue is `[status] tool`, and you poll `gh issue list --label to:tool`.

## You own
- `agents/tool/`
- `outputs/dashboard.html` and any other dashboard or video outputs
- `logs/ai/tool.md`

## Entry point
`agents/tool/build.py`, called by `make run DATA=path`. `make run` already chains data → themes → your build.
- **Input:** `outputs/findings.json` and `outputs/themes.json`.
- **Output:** `outputs/dashboard.html`.

Until those outputs exist, build against `contracts/examples/*.example.json`, which are synthetic: label them "EXAMPLE" on screen.

## Build
1. **`make run DATA=path` regenerates everything end to end** from any xlsx path. Test it from a clean clone. It must handle data updates: new rows, a new county, new labels (flagged by data). Charts must not hard-code categories.
2. **Self-contained HTML dashboard.** One file with inline CSS/JS and no CDN at view time. It embeds aggregates only, never row-level data. For a non-technical EveryMind staff reader:
   - **Honest axes:** bars start at zero. Use bars for categories, lines for time, histograms for distributions, scatter for relationships.
   - **n everywhere:** every chart and tile shows n and its denominator in words. Show CIs where provided.
   - **Small groups:** visibly flagged or pooled, never silently dropped.
   - **Accessible:** contrast, text labels, not color-only, a table alternative for each chart, keyboard friendly.
   - **Plain language:** a "what this means / what to do" line per section, and a data-freshness line (source hash, n_rows).
   - It is up for Best Technical Tool and Most Effective Visualization.
3. **Notebook walkthrough** in `agents/tool/walkthrough.ipynb`. It may load only `outputs/*.json`. Clear outputs before committing if any cell could show row-level data.
4. **Run instructions** in `agents/tool/RUN.md`. Use exact commands, assume Python ≥3.10, include "how to refresh with next month's export" and a troubleshooting section. Narrative links to it from the memo and README.
5. **Package the artifact** as `agents/tool/dist/Team17_TechnicalArtifact.zip`: code, contracts, outputs, RUN.md and fixtures generator. **No `data/`, no identity strings, no `.git/`.** `make submit` (narrative) copies it into `submission/`.
6. **Demo video**, `agents/tool/dist/Team17_Demo.mp4`, **≤120 s**. Make it as automated as possible:
   - capture the dashboard with a headless browser;
   - add captions and narration (TTS if available, otherwise captions only);
   - assemble with ffmpeg. If a video-making skill is present, use it.
   - The narration script lives in `agents/tool/video/script.md`. Every number carries an `[F:…]` tag, and narrative reviews it before the Sat 12:00 freeze.
   - A human re-record is the fallback; open a `to:human` issue if the automation fails.

## Rules specific to you
- The dashboard, notebook, zip and video never contain names, emails, handles, or row-level data.
- Numbers come only from `findings.json`/`themes.json`; never compute new ones in the dashboard. If you need a number, request it `to:data`.
- Log real AI mistakes (wrong axis, misleading chart, a broken run) in `logs/ai/tool.md`.

## Milestones (ET)
- **Fri 12:00** dashboard skeleton on examples + `make run` chain wired
- **Fri 20:00** dashboard v1 on real outputs, RUN.md, notebook, video proof of concept
- **Sat 12:00** dashboard feature-complete + narration script for review
- **Sat 20:00** zip + mp4 v1
- **Sat 23:00–Sun 02:00** final video (or human re-record)
- **Sun 06:00** hard freeze
