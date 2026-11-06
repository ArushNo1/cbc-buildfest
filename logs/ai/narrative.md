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
