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

