# AI Process Appendix

*v0. Every statement is traceable to logs/ai/*.md or docs/verification.md. Limit: 1 page.*

## Tools and how we used them

**Claude Code** (Claude Opus) ran as four coordinated agents (data, text, tool, narrative), each on a team member's machine. They synced only through a shared repository and its issue board.

Claude read the survey file only inside Claude Code; the organizers allow this when it is documented. No response-level data was uploaded or committed, and only group totals appear in outputs.

## Representative prompts

- "Build the pipeline to clean the survey data and produce findings.json matching the contract, with explicit denominators, confidence ranges and small-group suppression."
- "Code the two comment fields into a theme taxonomy with an offline, reproducible classifier, and validate it against a hand-checked sample."
- "Independently recompute the headline statistics directly from the raw file, using separate code that shares nothing with the data pipeline."

## AI errors we caught

Errors were caught by tests, by cross-checks, or by a person reading the output.

- **A wrong missing-date count.** The pipeline reported 0 missing training dates instead of 3. The independent recompute flagged it, and it was fixed.
- **An unsupported number.** An AI-written limitations note claimed excluding 31 suspicious "Strongly disagree on everything" respondents raises agreement by "about 2.4 points". Recomputed, it is 2.2, and the claim had no source in the findings file. It was corrected.
- **A classifier that missed too much.** The first version left about half of all comments unclassified. Against a hand-coded sample of 80 comments, exact agreement was 75 percent. After rules were added from the codebook, it was 90 percent (mean kappa 0.87). Caveat: the same agent wrote both the rules and the labels.
- **A privacy-screen gap.** The PII screen missed "Dr. Rivera" because of a capitalization bug, and it still misses bare first names. So every quote goes through human review.
- **A misleading chart.** A trend line joined months with no trainings, which implied continuity, and a summary named a 12-person county as "highest" without showing its wide range. Both were fixed after visual review.
- **A data leak in our own inspection script.** It printed two short comment snippets into the session because of a pandas data-type change. Nothing left the session, and the script was fixed.

## How we refined outputs

- Every number in the memo, deck and dashboard carries an ID from one findings file. An automated check rejects any number that doesn't match, or any percentage with no ID. It caught a fabricated tag in our first memo draft.
- The dashboard formats numbers but never computes them.

## What we verified independently

- **Separate recompute.** Code written separately from the pipeline recomputed all 62 metrics from the raw file, and all of them matched.
- **Reproducible rebuild.** A rebuild on a second machine reproduced the findings file byte-for-byte.
- **Robustness.** Synthetic test files (a new county, new answer labels, extra rows, a missing column, shifted dates) confirm the tool flags these cases rather than crashing.
- **Hand recompute.** A team member recomputed the headline numbers by hand in Excel from the raw file (*pending, see docs/verification.md*).
- **Quote review.** A team member reviewed every quote for personal information (*pending*).
