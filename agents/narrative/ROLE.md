# ROLE: narrative agent (integrator)

Read `CLAUDE.md` first. Your status issue is `[status] narrative`, and you poll `gh issue list --label to:narrative`.

## You own
- `CLAUDE.md`, `README.md`, `Makefile`, `requirements.txt`
- `scripts/`, `.github/`, `.claude/`, `docs/`, `submission/`, `agents/narrative/`, `tests/test_repo_*.py`
- the contracts until v1
- `logs/ai/narrative.md`

## Added duties (human request, Thu Nov 5); these come before memo and deck work
- **`crosscheck/`:** an independent recompute of the headline statistics straight from `data/raw/`. It is simple code that shares nothing with `agents/data/`. It covers:
  - post agreement on the 3 knowledge items;
  - the retrospective pre ratings and the pre→post change;
  - the 3 quality items;
  - the recommend score (mean, NPS) and call-988 likelihood;
  - key subgroup cuts (county, role, language);
  - missingness (n_missing).

  `make crosscheck` diffs against `outputs/findings.json` and opens one `to:data` issue per mismatch, with both values and both denominators. Re-run it whenever findings.json changes, and record the results in `docs/verification.md`.
- **`fixtures/`:** a synthetic, schema-faithful raw-format generator plus drift variants (new county, new Likert label, extra rows, missing column, shifted dates). `make fixtures` writes them to `tests/fixtures/`. Its README is written for the data agent.

## After bootstrap, in order
1. **`scripts/verify.py`** (run by `make verify`). It checks:
   - filename regex for the five deliverables;
   - memo PDF ≤2 pages;
   - appendix PDF exactly 1 page;
   - mp4 ≤120 s via `ffprobe`;
   - presentation is .pptx (and no PDF deck);
   - metadata scrub: PDF Info/XMP author fields, pptx `docProps/core.xml` and `app.xml`, mp4 tags;
   - identity-string grep inside PDFs/pptx text (team git names and emails, `umd`, `terpmail`);
   - `scripts/check_numbers.py`.
2. **`scripts/check_numbers.py`.** Every `NUMBER [F:id]` in `agents/narrative/drafts/*.md` (and the tool's narration script) must match `outputs/findings.json` or `outputs/themes.json` as displayed (rounded). An unknown ID fails, and so does a number with no tag in a findings sentence.
3. **`scripts/submit.py`** (run by `make submit`). It renders the drafts to `submission/Team17_Memo.pdf`, `Team17_AIAppendix.pdf` and `Team17_Presentation.pptx` with tags stripped and metadata scrubbed, copies the tool's zip and mp4, then runs verify.
4. **Memo** (`agents/narrative/drafts/memo.md`), 1–2 pages, non-technical:
   - key findings (with n);
   - methodology;
   - **prioritized** recommendations, each with an owner, frequency, what's needed and an impact measure;
   - implementation (who runs the tool, how often, what they need);
   - limitations, flagging thin findings.
5. **AI appendix** (`agents/narrative/drafts/appendix.md`), exactly 1 page, built only from `logs/ai/*.md` and `docs/verification.md`. It covers tools, representative prompts, at least one *real* AI error or limitation, how outputs were refined, what was verified or corrected manually, and how findings were validated against the data. **Nothing invented.**
6. **Deck** (`agents/narrative/drafts/deck.md` → pptx): solution, findings, AI use and recommendations, using the dashboard's charts.
7. **Run the board.** Keep the milestone issues current, chase blockers, and record decisions in `docs/decisions.md`. Keep the human-gate issues accurate, and close a gate only when the human confirms.

## Milestones (ET)
- **Fri 12:00** verify + check_numbers + submit scaffolding, plus outlines
- **Fri 20:00** memo, appendix and deck v0 from findings v1
- **Sat 12:00** FREEZE: numbers locked to IDs
- **Sat 20:00** all five in `submission/`, `make verify` green
- **Sat 23:00–Sun 02:00** fold in human verification
- **Sun 06:00** hard freeze, final `make submit`, hand to humans
