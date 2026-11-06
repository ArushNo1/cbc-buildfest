# AI process log: narrative agent

Append-only. Record only what actually happened. This feeds the AI appendix (hard rule 4).

Entry template:

## <date> <time ET>: <short title>
- **Prompt (representative):** "..."
- **What the AI produced:**
- **Error / limitation (if any), and how it was caught:**
- **Revision:**
- **Manually verified against data:** what, how, result

## Thu Nov 5 ~22:00 ET: repo bootstrap
- **Prompt (representative):** the team's bootstrap brief: "time-boxed 45-minute bootstrap … CLAUDE.md, contracts v0, roles, CI, labels, issues, milestones".
- **What the AI produced:** repo scaffolding, v0 JSON Schemas derived from the case's column list (the data file was not opened), role briefs, CI guards, the GitHub board script.
- **Limitation:** the `.claude/settings.json` attribution keys (`attribution.commit/pr`, `includeCoAuthoredBy`) were written from the model's own knowledge. Checking them against the current docs was skipped for time. Mitigation: the commit-msg hook and CI attribution check catch any trailer regardless.
- **Manually verified:** `git config user.name/email` is the human's; `data/` is gitignored (`git check-ignore`); the hook rejects attribution and allows `CLAUDE.md` paths (pytest); `make data` fails loudly before its entry point exists.
## Thu Nov 5 ~22:30 ET: errors caught during bootstrap
- **Error 1 (AI-written .gitignore):** the pattern `data/` (meant for the raw-data folder) also ignored `agents/data/`, so the data agent's ROLE.md was silently left out of the first staging. **Caught by** reading `git status` before committing (the file was missing from the list). **Fix:** anchored to `/data/` and re-checked with `git check-ignore` that the raw xlsx is still ignored.
- **Error 2 (AI-written Makefile):** `submit` depended on `verify`, but verify can only pass after submit has assembled the files, so `make submit` could never succeed. **Caught by** review while writing `scripts/submit.py`. **Fix:** submit.py copies the files, then runs verify itself.
- **Manually verified:** `scripts/verify.py` was run against deliberately bad fake files (3-page memo, author metadata, an email in slide text, a 121 s video with an artist tag, data inside the artifact zip, a stray PDF deck). All 11 planted problems were reported, and a valid 1-page appendix passed. `check_numbers.py` is unit-tested for matches, mismatches, suppressed values, unknown IDs and untagged percentages.
## Thu Nov 5 ~23:00 ET: crosscheck + synthetic fixtures (role change requested by the human)
- **Prompt (representative):** "independently recompute the headline survey statistics … directly from data/raw/ using separate simple code that shares nothing with agents/data/ … plus a synthetic schema-faithful data generator plus drift variants."
- **What the AI produced:** `agents/narrative/crosscheck/crosscheck.py` (54 metrics: post/pre agree % and means, pre→post change, quality agree %, recommend mean + NPS, call-988 mean, missing training dates, cuts by county/role/language, n_missing everywhere; diff + `to:data` issue per mismatch) and `agents/narrative/fixtures/make_fixtures.py` (base + 5 drift variants), with tests.
- **Error 3 (AI inspection script):** to learn the label vocabularies, the AI wrote a script meant to print value counts for categorical columns and to skip free text. It tested for the `object` dtype, but pandas 3 reports text columns as `str`, so the guard never fired. The script printed min/max for every text column, which put the alphabetically first and last answer of each comment field (two short comment snippets) into the session. **Caught by** reading the output. Nothing left Claude Code. **Fix:** re-ran with explicit column exclusions (`Id` and both comment fields) and a numeric-dtype test.
- **Error 4 (AI fixture generator):** missing training dates were drawn at random (p=0.25%), so the n=300 base fixture had **zero** missing dates, while the real export has 3. It looked faithful but missed a known edge case. **Caught by** reading the missing-value counts per column. **Fix:** a fixed minimum of 1 missing date, and a test asserting ≥1.
- **Manually verified:** (1) the crosscheck matched label counts tallied separately in-session from the raw file (see docs/verification.md); (2) the base fixture has the same 20 headers (byte-for-byte, NBSPs included), the same dtypes, and label sets that are subsets of the real ones. This is asserted by a test that runs whenever the raw file is present locally.
- **Observation passed to data (aggregate only):** 31 of 1,299 respondents chose "Strongly disagree" on all 3 post items (17 on all 6 knowledge items). Possible misread scale or same-answer-throughout responses; worth a data-quality flag. Not adjudicated here.
