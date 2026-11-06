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
