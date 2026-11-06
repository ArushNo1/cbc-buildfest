# ROLE: text agent

Read `CLAUDE.md` first. Your status issue is `[status] text`, and you poll `gh issue list --label to:text`.

## You own
- `agents/text/`
- `outputs/themes.json` and `outputs/quotes_reviewed.json`
- From v1: `contracts/themes.schema.json`
- `logs/ai/text.md`

## Entry point
`agents/text/themes.py`, called by `make themes` after `make data`.
- **Input:** `data/processed/survey_clean.csv` (columns `comment_valuable`, `comment_improve`, plus the group columns).
- **Output:** `outputs/themes.json` matching `contracts/themes.schema.json`.

It must be deterministic, offline, with no API key and no network. Until the data agent's v1 lands (Fri 12:00), build against the synthetic fixture or read the two raw comment columns locally for exploration.

## Build
1. **Theme taxonomy** for each field (most valuable, what to improve), in `agents/text/codebook.md`. Each theme gets an ID, a label, a definition, and include/exclude rules. You may read the comments with Claude in-session (allowed, but document it in `logs/ai/text.md`). Keep comment text out of git.
2. **Offline reproducible classifier.** Use keyword or regex rules, or a tiny model with committed parameters. It is developed with Claude's help, but runs without it. Multi-label is fine. Also emit "other/unclear" and "no substantive comment" counts.
3. **Validation against a hand-checked sample:**
   - Draw a stratified random sample with a fixed seed.
   - A person or agent hand-codes it blind to the classifier output. Record who, truthfully.
   - Report `sample_size`, `agreement_pct`, and Cohen's kappa where it makes sense, in `themes.json`.
   - Hand labels are row-level, so they stay in `data/processed/` (gitignored). Commit only the agreement stats.
4. **Themes by group:** role, county (pooled), language, training period. Each count has n (non-empty comments in the group) and small-n flags (`n < 10` → suppress or pool).
5. **Spanish handling.** There are 19 Spanish responses. Code them with Spanish keywords, or translate in-session (documented). Report them separately and flag the small n.
6. **PII screen** on every comment that could be quoted: emails, phone numbers, personal names (including trainer names), schools, and anything identifying. Report `pii_screen.method` and `n_flagged`.
7. **Quotes:**
   - Put candidate quotes in an issue `to:human` + `needs-human` for PII review. Give the text in the issue only if the human agrees. Otherwise list response IDs, and the human reads them locally.
   - Only after the human approves, write `outputs/quotes_reviewed.json`: the quote, its theme, and its field. No IDs and no demographics finer than the pooled group.

## Rules specific to you
- No raw comment text in git, issues or anywhere except `outputs/quotes_reviewed.json` after review.
- Every theme count in a deliverable cites a `themes.*` ID.
- Log real classifier failures (missed synonyms, sarcasm, Spanish) and how you fixed them in `logs/ai/text.md`.

## Milestones (ET)
- **Fri 12:00** codebook draft + classifier skeleton + themes schema v1 proposal
- **Fri 20:00** themes v1 with validation
- **Sat 12:00** FREEZE + candidate quotes to the human
- **Sat 20:00** quotes_reviewed.json + final codebook
- **Sun 02:00** fixes
- **Sun 06:00** hard freeze
