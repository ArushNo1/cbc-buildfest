# Decisions log

Append-only. Format: `D-NNN (date, agent) Decision — why — impact.` Revise by adding a new entry that supersedes an old one.

- **D-001 (Thu Nov 5, narrative)** Makefile targets delegate to per-agent entry points (`agents/data/pipeline.py`, `agents/text/themes.py`, `agents/tool/build.py`, `scripts/verify.py`, `scripts/submit.py`). A missing entry point fails loudly with its owner's name. Why: agents never edit the shared Makefile, so no merge conflicts.
- **D-002 (Thu Nov 5, narrative)** Aggregates are committed as **JSON only**. All `*.csv`, `*.xlsx`, `*.tsv`, `*.parquet` etc. are gitignored and blocked by CI repo-wide; mapping tables are JSON. Why: one simple rule beats per-path exceptions for keeping row-level data out of git (hard rule 2).
- **D-003 (Thu Nov 5, narrative)** Small-n v0 default: `small_n = n < 10`; small cells are suppressed (value null) or pooled into level `other_pooled`; n is always reported. The data agent may revise in v1 with a new entry.
- **D-004 (Thu Nov 5, narrative)** Hard rule 1 is read as an **attribution** ban. The commit-msg hook rejects `co-authored-by`, `claude`, `anthropic` and the robot emoji, but allows the paths `CLAUDE.md` and `.claude/`. The AI appendix and `logs/ai/` must name the AI tools, because the rubric requires it.
- **D-005 (Thu Nov 5, narrative)** GitHub pins at most 3 issues: the status issues for data, text and tool are pinned; narrative's isn't. All four carry the label `type:status`.
- **D-006 (Thu Nov 5, narrative)** `findings.json`/`themes.json` carry no timestamps; provenance is the input file's sha256. Why: byte-identical reruns, clean diffs.
- **D-007 (Thu Nov 5, narrative)** Hand-coded validation labels for the comment classifier are row-level, so they stay in gitignored `data/processed/`; only agreement statistics are committed.
- **D-008 (Thu Nov 5, narrative)** Drafts tag every number as `NUMBER [F:finding_id]`; `scripts/check_numbers.py` enforces it and render strips the tags.
- **D-009 (Thu Nov 5, narrative, human request)** Narrative now owns (a) `agents/narrative/crosscheck/`, an independent recompute of the headline numbers from the raw xlsx that shares no code with `agents/data/` (`make crosscheck` opens a `to:data` issue per mismatch), and (b) `agents/narrative/fixtures/`, the synthetic raw-format generator plus drift variants (`make fixtures` → `tests/fixtures/`, gitignored). The data agent no longer writes a fixture generator; it writes drift tests that use this one.
- **D-010 (Thu Nov 5, narrative)** Crosscheck definitions:
  - Likert 1–5, with "Very agree" = 5, "Satisfied" = 4, and "Neither agree or disagree" = "Neither agree nor disagree" = 3.
  - agree = score ≥ 4; n = recognized answers; n_missing = blanks + unrecognized labels.
  - Roles are counted by any mention of the multi-select.
  - NPS = %(9–10) − %(0–6).
  - Values match within ±0.05; n, n_missing and numerator must match exactly.

  If data defines something differently, the mismatch issue is where the difference gets explained.
- **D-011 (Thu Nov 5, narrative)** `findings.json` percentages are on a 0–100 scale (added to the v0 schema description).
- **D-012 (Fri Nov 6, narrative)** The presentation is built by `scripts/deck_build.py` from a structured `agents/narrative/drafts/deck.md`. Layouts: title, question, solution, stats, chart, table, cards and closing. Charts are the dashboard's own images from `agents/tool/dist/deck_assets/`, and every slide has speaker notes. Why: the outline-to-bullets renderer had shipped placeholder text ("Title", "Screenshot of the dashboard", an internal note about issue #30) with no images (#45). Impact: `tests/test_repo_deck.py` guards that the deck has no tags or internal notes left in it, a title on every slide, alt text on every chart, and empty author metadata.
- **D-013 (Fri Nov 6, narrative)** `make submit` now renders the drafts itself (`scripts/render.py`), then copies the tool's zip and mp4, then runs verify. `verify.py` falls back to `ffmpeg -i` (including imageio-ffmpeg) for the video length and metadata when `ffprobe` is missing. Why: `submit.py` pointed at a build folder that was never produced, and verify failed outright on machines without `ffprobe`.
