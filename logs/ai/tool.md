# AI process log: tool agent

Append-only. Record only what actually happened. This feeds the AI appendix (hard rule 4).

Entry template:

## <date> <time ET>: <short title>
- **Prompt (representative):** "..."
- **What the AI produced:**
- **Error / limitation (if any), and how it was caught:**
- **Revision:**
- **Manually verified against data:** what, how, result


## 2026-11-05 23:15 ET: dashboard builder v1 (M1 skeleton, then wired to real outputs)
- **Tool:** Claude Code (Claude Opus model), running in the Claude desktop app on this machine.
- **Prompt (representative):** "You are the tool agent. Read CLAUDE.md and agents/tool/ROLE.md, check issues labeled to:tool, and work toward your milestones: a self-contained HTML dashboard built from outputs/findings.json and outputs/themes.json, with honest axes, n everywhere, small-group flags, accessibility and plain language."
- **What the AI produced:** `agents/tool/build.py` (reads both JSON files, validates them against `contracts/*.schema.json`, groups findings by metric and group, writes one self-contained `outputs/dashboard.html`), `agents/tool/web/` (HTML template, CSS, vanilla JS renderer, no CDN), `agents/tool/tests/` (19 tests plus a synthetic findings and themes generator), and `agents/tool/RUN.md`. Design rule: the page only formats, sorts and selects numbers from the two JSON files. It never computes a statistic.
- **Errors / limitations caught, and how:**
  - **Visual review in a browser** (synthetic data, then real outputs):
    - The "Before" legend swatch had no color. The CSS rule was missing.
    - The "everyone" reference line ran through the value labels. Fixed with a label background.
    - Month labels on the time axis overlapped. Changed to collision-based thinning.
    - The long "Measure" dropdown overflowed the screen at phone width.
    - The time line joined points across months with no trainings, which implied continuity. It now breaks the line there.
    - The caveat box showed "value suppressed" boilerplate instead of the item's real caveat.
    - The group dropdown lost its intended order (county, role, language). Cause: `json.dumps(sort_keys=True)` re-sorts dict keys. Fixed with an explicit `dim_order` list.
  - **Unit test caught a real bug:** an explicitly named `--themes` file that didn't exist was silently skipped, because a `try/except` swallowed the error. It now fails with a message.
  - **First integration with the real `outputs/themes.json`:**
    - Its `group.level` values are display names ("Prince George's") while its IDs use slugs. The first ID parser would have mis-grouped them. The level slug is now taken from the ID.
    - Its `source.file_sha256` fingerprints the cleaned CSV, not the xlsx. A naive equality check would have shown a false "different export" warning. A hash difference now counts as "unconfirmed" and only differing row counts count as a mismatch.
  - **Summary wording:**
    - The auto-generated "most common suggestion" picked catch-all buckets ("Question, not a suggestion", "No substantive comment"). Those are now excluded from that sentence and sorted last.
    - The "highest group" summary named Queen Anne's on n = 12 without its wide range. Summaries now show n and the 95% range.
    - I had written a static claim ("most respondents are students in two counties") that no finding backs. It was replaced with generic wording.
  - **Palette validator:** run on after-blue and before-grey. Grey fails only the chroma floor, as expected for a deliberate de-emphasis color. CVD and normal-vision separation and contrast pass in light and dark.
- **Revision:** all of the above fixed. `make test`: 37 passed.
- **Manually verified against data:**
  - `make run DATA=data/raw/BuildFest_EveryMind_Survey_Data_FULL.xlsx` ran end to end, exit 0.
  - The rebuilt `outputs/findings.json` was byte-identical to the committed file.
  - The rebuilt `outputs/themes.json` differed only in its `validation` block, which was nulled because the hand labels exist only on the text machine. I restored the committed file and reported it to text.
  - Spot-checked tiles against `outputs/findings.json`: post identify-crisis 89.9 of 1,299; recommend mean 7.59 of 1,266; NPS +12.0; call-988 mean 7.66 of 293, with 1,006 missing.
  - No numbers were hand-recomputed from the xlsx. That is the human check in issue 29.
