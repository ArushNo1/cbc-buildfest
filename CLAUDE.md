# Team 17 · EveryMind BuildFest: rules for every agent

Read this whole file at the start of every session, then read `agents/<you>/ROLE.md`.
Four agents (data, text, tool, narrative) run on four separate computers and sync only through git and GitHub Issues.

## HARD RULES (verbatim, no exceptions)

1. Commits, PRs, issues and files must show only the human whose machine you're on. Never add Co-Authored-By, "Generated with Claude", or any Claude/Anthropic mention anywhere. Commit a .claude/settings.json that turns Claude Code attribution off (attribution.commit and attribution.pr empty; also includeCoAuthoredBy false for older versions; verify against current docs). Add scripts/hooks/commit-msg rejecting those strings, enabled by `make setup` via `git config core.hooksPath scripts/hooks`, plus a GitHub Action that fails on them. Before your first commit confirm `git config user.name/email` is the human's; if not, stop and ask.
2. Raw survey data never enters git or any service outside Claude Code. Gitignore data/ and any xlsx/csv with row-level data. Only aggregates and findings.json are committed. Organizers allow using Claude on the data if the use is documented.
3. Judging is anonymous. No personal names, emails, university identifiers (umd, terpmail), or GitHub handles in anything under submission/, including file metadata. Filenames: Team17_Memo.pdf, Team17_AIAppendix.pdf, Team17_Presentation.pptx, Team17_Demo.mp4, Team17_TechnicalArtifact(.zip or link).
4. Never fabricate AI errors, validation steps, or numbers. The AI appendix must be true.
5. Agents never submit the Google Form. Humans do.

How these are enforced here:
- `.claude/settings.json` turns attribution off. `make setup` (once per machine) enables `scripts/hooks/commit-msg`, which rejects `co-authored-by`, `claude`, `anthropic` and the robot emoji. The paths `CLAUDE.md` and `.claude/` are allowed.
- CI (`.github/workflows/ci.yml` → `scripts/check_repo.sh`) fails on attribution in commit messages or authors, on any tracked data file (`data/`, `*.xlsx`, `*.csv`, …), and on identity strings under `submission/`.
- Rule 1 is about **attribution**. The AI appendix (deliverable 4) and `logs/ai/` must name the AI tools used. That is required documentation, not attribution. Keep Claude/Anthropic out of commit messages, PR text and issue text.
- Never `git push --force`. If a bad commit lands, open a `type:blocker` + `to:human` issue. Don't rewrite history.

## Context

**Client:** EveryMind, a Maryland mental-health nonprofit that runs 988 (Suicide & Crisis Lifeline) awareness trainings.
**Business question:** How can EveryMind use post-training survey data to build an actionable solution for evaluating training effectiveness, identifying gaps across communities, and continuously improving trainings?
**Reference:** `docs/reference/` (case brief PDF, workshop slides PDF).
**Due:** Sun Nov 8, 09:00 ET. No late submissions. Finalists are announced Fri Nov 13; finals are Tue Nov 17.

### Deliverables (filenames fixed; see `docs/requirements.md`)
1. **Technical artifact** (`Team17_TechnicalArtifact.zip` or link): runs without errors on the provided data, handles reasonable data updates, has clear outputs and run instructions.
2. **Demo video** (`Team17_Demo.mp4`): 120 s max.
3. **Memo** (`Team17_Memo.pdf`): 1–2 pages for a non-technical reader. Covers key findings, methodology, recommendations, implementation (who runs it, how often, what they need) and limitations.
4. **AI appendix** (`Team17_AIAppendix.pdf`): exactly 1 page. Covers tools, representative prompts, at least one AI error or limitation, how outputs were refined, what was verified or corrected manually, and how findings were validated against the data.
5. **Presentation** (`Team17_Presentation.pptx`): .pptx only, no PDF. Covers the solution, findings, AI use and recommendations.

### Rubric
- **Business/Social Impact, 35%.** Prioritized recommendations with feasible implementation and impact measures. Flags thin findings. Protects privacy.
- **Technical Soundness, 30%.** Reproducible, with justified methods. Reports sample sizes, handles small groups and data inconsistencies, analyzes open-ended comments, and addresses limits such as retrospective ratings.
- **Functionality, 20%.** Correct numbers, runs from instructions, handles data updates.
- **AI Process, 15%.** Documents tools, prompts, revisions and errors. Independently verifies against the data.
- **Track awards:** Best Technical Tool, Most Effective Visualization, EveryMind's Choice.

### Data
File: `data/raw/BuildFest_EveryMind_Survey_Data_FULL.xlsx`, sheet `Survey Data`. It has 1,299 rows and 20 columns. It is local only and never committed.

| Raw column(s) | Notes |
|---|---|
| Id, start time, completion time | |
| language | 19 Spanish responses |
| role | multi-select, trailing semicolons; ~83% students |
| training date | 3 missing; spans Oct 2025–Oct 2026; clusters in Apr–May and Sep–Oct 2026 |
| county | ~72% Anne Arundel, ~24% Prince George's, every other county ≤31 rows. Variants: Montgomery / Montgomery County / "Montgomery County with NAMI MC", plus Fairfax, Harris, Queen Anne's |
| 3 post items | identify crises / describe 988 / know when to use 988 |
| 3 retrospective "before training" items | asked *after* training, so biased; always caveat |
| 3 training-quality items | engaging / knowledgeable / organized; ~12% missing |
| recommend 0–10 | |
| likelihood to call 988 0–10 | 77% missing |
| comment: most valuable | ~1,060 present |
| comment: improve | ~650 present |

Known mess:
- Likert variants ("Very agree", "Satisfied", "Neither agree or disagree" vs "nor").
- Non-breaking spaces.
- County variants (see table).
- Small groups. **Small-group handling is mandatory:** flag n<10, suppress or pool, and show n and uncertainty everywhere.

### Workshop lessons (apply everywhere)
- State denominators explicitly ("72% of the 1,041 respondents who answered").
- Bars start at zero.
- Use bars for categories, lines for time, histograms for distributions, scatter for relationships.
- Treat AI as a skeptical reviewer, not a source of confidence. Check its output against the data.

## Topology and sync

- **Sync:** git on `main` only, plus GitHub Issues. Run `git pull --rebase` before every push. Never force-push.
- **Ownership:** each agent writes only to `agents/<name>/` plus the shared paths it owns (table below). To change anything else, open an issue labeled `to:<owner>` + `type:request`.
- **Message board = Issues.** The first line of every issue body and comment is `[agent:<name>]`.
  - Labels: `to:data|text|tool|narrative|human`, `type:request|blocker|handoff|decision|status`, `needs-human`, `deliverable:artifact|video|memo|appendix|deck`.
- **Status:** each agent keeps one status issue titled `[status] <name>` (label `type:status`) and updates it at every milestone. GitHub pins at most 3, so data, text and tool are pinned. Find all four with `gh issue list --label type:status`.
- **Polling:** agents can't be pinged. Run `gh issue list --label to:<me> --state open` at the start of every work unit and before every push.
- **Blocking:** block only when truly blocked. Otherwise decide, log it in `docs/decisions.md`, and move on.

### Ownership

| Path | Owner |
|---|---|
| `CLAUDE.md`, `README.md`, `Makefile`, `requirements.txt`, `scripts/`, `.github/`, `.claude/`, `docs/`, `submission/`, `tests/test_repo_*.py` | narrative |
| `contracts/cleaned_data.schema.json`, `contracts/findings.schema.json` | narrative (v0), then **data** from v1 |
| `contracts/themes.schema.json` | narrative (v0), then **text** from v1 |
| `agents/data/`, `tests/fixtures/`, `outputs/findings.json`, `outputs/validation_report.json` | data |
| `agents/text/`, `outputs/themes.json`, `outputs/quotes_reviewed.json` | text |
| `agents/tool/`, `outputs/dashboard.html` and any other dashboard/video outputs | tool |
| `logs/ai/<name>.md` | that agent (append-only) |

Need a new dependency? Request it from narrative (`requirements.txt`), or keep it in `agents/<you>/requirements.txt` and say so in your issue.

### Work loop (every unit of work)
1. `git pull --rebase`
2. `gh issue list --label to:<me> --state open`. Answer or act.
3. Work inside your owned paths.
4. Append to `logs/ai/<me>.md`: representative prompt, what the AI produced, real errors and how they were caught, manual checks.
5. `make test`, plus `make verify` once it exists.
6. `git pull --rebase && git push`
7. At a milestone, update `[status] <me>` and close your milestone issue.

## Single source of truth: numbers

- `make data` deterministically rebuilds row-level data **locally** from `data/raw/` into `data/processed/` (gitignored), then writes aggregates to `outputs/`. Only `outputs/` aggregates are committed.
- `outputs/findings.json` (schema: `contracts/findings.schema.json`) has stable metric IDs, value, n, denominator, CI where applicable, and caveat text. `outputs/themes.json` follows `contracts/themes.schema.json`.
- **Every number in the memo, deck, dashboard, narration and video cites an ID.** In markdown drafts, write the number followed by its tag: `78% [F:post.identify_crisis.agree_pct.overall]`. `scripts/check_numbers.py` fails if a tagged number doesn't match `findings.json` or `themes.json` as displayed (rounded). Tags are stripped when rendering final files.
- **IDs are stable.** Never reuse an ID for a different metric. After the findings freeze (Sat 12:00 ET), changing a value needs a `type:decision` issue.
- **Small n:** `small_n = n < 10`. Small groups are suppressed (value null) or pooled into an "Other" group. n is always shown.
- **Never fabricate.** If a number isn't in `findings.json`/`themes.json`, it doesn't go in a deliverable.
- **Quotes:** only from `outputs/quotes_reviewed.json`, and only after the human PII review issue is closed.

## Make targets

| Target | What it does | Owner of the entry point |
|---|---|---|
| `make setup` | deps + commit-msg hook (once per machine) | narrative |
| `make data DATA=path.xlsx` | clean + analyze → `data/processed/`, `outputs/findings.json` | data: `agents/data/pipeline.py` |
| `make themes` | comments → `outputs/themes.json` | text: `agents/text/themes.py` |
| `make run DATA=path.xlsx` | data + themes + dashboard, end to end | tool: `agents/tool/build.py` |
| `make test` | pytest over `tests/` and `agents/` | everyone |
| `make verify` | repo guards + submission checks | narrative: `scripts/verify.py` |
| `make submit` | assemble `submission/` | narrative: `scripts/submit.py` |

A target whose entry point doesn't exist yet fails loudly with the owner's name. Create your entry point; don't edit the Makefile.

## Schedule (all ET)

| When | Milestone |
|---|---|
| Fri Nov 6 12:00 | **M1** contracts v1 + pipeline v1 (data is critical path) |
| Fri Nov 6 20:00 | **M2** findings v1, themes v1, dashboard v1 |
| Sat Nov 7 12:00 | **M3 FINDINGS FREEZE** |
| Sat Nov 7 20:00 | **M4** all five deliverables v1 in `submission/` |
| Sat 23:00 – Sun 02:00 | **M5** human verification + final video |
| Sun Nov 8 06:00 | **M6 HARD FREEZE** |
| Sun Nov 8 by 08:00 | humans submit (form closes 09:00, no late) |

## Definition of done

- **Artifact:**
  - `make setup && make run DATA=<provided xlsx>` runs with no errors from a clean clone.
  - It also runs on the synthetic drift fixtures (new county, new label, extra rows), where unknown labels are flagged, not crashed on.
  - Run instructions are written, `make test` is green, and it is packaged as `Team17_TechnicalArtifact.zip` with no data and no identity strings.
- **Findings:** every metric has n, a denominator description, a CI where it's a proportion or mean, small-n flags and a caveat (retrospective items always). Headline numbers are hand-recomputed by a human (`docs/verification.md`).
- **Themes:**
  - The taxonomy is documented.
  - The offline classifier is reproducible with no API key.
  - It is validated on a hand-checked sample, with sample size and agreement reported.
  - Spanish responses are handled, and quotes pass the human PII review.
- **Dashboard:** self-contained HTML, aggregates only. Honest axes, n shown, small-group flags, accessible (contrast, text alternatives, not color-only), readable by non-technical staff.
- **Memo / appendix / deck / video:**
  - They meet the specs above, and every number carries an `[F:…]` tag that passes `check_numbers`.
  - `make verify` is green (filenames, page counts, video length ≤120 s, pptx not pdf, metadata scrubbed, no identity strings).
  - The human-gate issues are closed.
- **Nothing is submitted by an agent.** Humans submit the form.
