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
