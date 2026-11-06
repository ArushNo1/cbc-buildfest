# AI process log: text agent

Append-only. Record only what actually happened. This feeds the AI appendix (hard rule 4).

Entry template:

## <date> <time ET>: <short title>
- **Prompt (representative):** "..."
- **What the AI produced:**
- **Error / limitation (if any), and how it was caught:**
- **Revision:**
- **Manually verified against data:** what, how, result

## 2026-11-05 22:30 ET: codebook and classifier skeleton
- **Prompt (representative):** "You are the text agent. Read the team rules and agents/text/ROLE.md, check issues labeled to:text, and work toward the Friday noon milestone: codebook, offline classifier skeleton, themes schema decision, PII screen."
- **What the AI produced:** `agents/text/codebook.md`, `agents/text/themes.py`, and `agents/text/test_themes.py`. v0 of the themes schema is kept as the v1 contract. The classifier is keyword/regex, multi-label, offline. `--fixture` writes a synthetic `outputs/themes.json` that must not be cited.
- **Error / limitation (if any), and how it was caught:** The name screen used a lowercase honorific pattern, so "Dr. Rivera" was not flagged. `test_pii_flags_and_ignores_988` failed. The pattern now allows a capital honorific. The screen still misses names with no honorific. That limit is stated in the codebook and in `pii_screen.method`.
- **Revision:** Honorific pattern updated. Tests re-run: 12 passed (`agents/text/test_themes.py` and `tests/`).
- **Manually verified against data:** Not against the survey workbook. That xlsx is not on this machine, so counts were checked only on the synthetic fixture (Anne Arundel crisis theme 10 of 10, Spanish group n=2 suppressed, Calvert pooled, one email flagged). No agreement rate is claimed. `validation.agreement_pct` is null.

## 2026-11-05 22:45 ET: align rules to the synthetic comment list
- **Prompt (representative):** "Keep going as the text agent. The machine identity is confirmed. Pull, set up, and move the milestone."
- **What the AI produced:** Rule updates so the classifier covers the synthetic comments in `agents/narrative/fixtures/make_fixtures.py`, including shorter sessions, real-life examples, Spanish activity requests, filler phrases, 7-digit phone numbers, "my school", and "trainer" plus a name. Language values like "English (United States)" and "Español (México)" map to en and es.
- **Error / limitation (if any), and how it was caught:** Reading that generator showed the first rules missed "Make it shorter", "Nothing, it was great", "Más actividades", "555-0100", and "trainer Jane Doe". Those strings are synthetic, not survey responses. Tests now cover them. Names with no role word and no honorific are still missed.
- **Revision:** Patterns and tests updated. `pytest` on `agents/text/test_themes.py` and `tests/`: 12 passed.
- **Manually verified against data:** Still not against the survey workbook. It is not on this machine. Checked the synthetic phrases by hand against the new patterns, then by the unit tests.

## 2026-11-05 23:10 ET: themes v1 from the local workbook
- **Prompt (representative):** "The survey workbook is at the Downloads path. Put it in data/raw and keep going."
- **What the AI produced:** Revised `agents/text/codebook.md` and `agents/text/themes.py` after reading the comment columns locally, then wrote `outputs/themes.json`. The improve field is often "no questions" or a question about how 988 works, so `no_substantive` and `audience_question` are real themes. Group cuts use a provisional county, role, and language map until `survey_clean.csv` exists.
- **Error / limitation (if any), and how it was caught:** The first rules left 552 of 1,063 valuable comments and 547 of 651 improve comments in `other_unclear`. That was counted from the workbook, not guessed. A hand-coded sample of 80 comments (seed 17, every non-empty Spanish comment, plus 25 English comments per field) matched the classifier exactly on 75.0 percent before a follow-up. The follow-up added phrases the codebook already named. Exact match on the same sample then was 90.0 percent, and the mean per-theme kappa was 0.87. The 90.0 figure is not a locked test. The same agent wrote the rules and the labels. Single names with no role word are still missed. The screen flagged 11 comment fields.
- **Revision:** Rules widened to the phrases people actually used. `outputs/themes.json` records both agreement figures in `validation.procedure`.
- **Manually verified against data:** Workbook has 1,299 rows. Non-empty valuable comments: 1,063. Non-empty improve comments: 651. Of 1,063 valuable comments, 498 (46.8 percent) are `themes.valuable.what_988_is.pct.overall`. Of 651 improve comments, 229 (35.2 percent) are `themes.improve.audience_question.pct.overall` and 155 (23.8 percent) are `themes.improve.no_substantive.pct.overall`. 17 Spanish-language rows have at least one comment. The output validates against the themes schema and contains no comment text. `other_unclear` is still 316 of 1,063 valuable comments and 147 of 651 improve comments.

## 2026-11-05 23:20 ET: data v1 handoff and curly apostrophes
- **Prompt (representative):** "Look at the GitHub issues for the text agent and fix the ones that can be fixed."
- **What the AI produced:** Rebuilt `outputs/themes.json` from `data/processed/survey_clean.csv` after the data handoff. Straight and curly apostrophes now fold the same way. Candidate quote response ids were chosen for human review. No comment text goes in the issue.
- **Error / limitation (if any), and how it was caught:** A comment that the codebook calls "not only a crisis" stayed out of that theme because the apostrophe was curly, so the pattern missed it. Checked by classifying that sentence both ways.
- **Revision:** `fold` now maps curly apostrophes and quotes to straight ones. `themes.valuable.not_only_crisis.pct.overall` moved from 37 (3.5 percent) to 38 (3.6 percent) of 1,063. The hand-check agreement stayed 90.0 on the same 80 comments. Rebuilt from the clean file, the other overall counts matched the previous file.
- **Manually verified against data:** Schema still validates. Source row count is still 1,299. The clean file and the raw workbook produce the same theme counts aside from that one apostrophe fix.

