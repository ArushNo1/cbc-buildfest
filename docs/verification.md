# Verification log

Record only checks that actually happened. This file feeds the AI appendix (hard rule 4).

## Automated (every push / `make verify`)
- `scripts/check_repo.sh`: no AI attribution in commits, no data files tracked, no identity strings in `submission/`.
- `make test`: commit-msg hook, contract schemas + examples, data drift tests (data), classifier tests (text).
- `scripts/verify.py` (narrative, pending): filenames, page counts, video length, pptx, metadata, identity strings, check_numbers.

## Human recompute of headline numbers (gate: to:human issue)
Recompute from the raw xlsx in Excel, independently of the pipeline. Steps per ID: `agents/data/recompute.md`.

| Finding ID | Pipeline value (n) | Human value (n) | Match? | Who / when | Notes |
|---|---|---|---|---|---|

## Comment classifier validation (text)
| Field | Sample size | How drawn | Coded by | Agreement % | Kappa | Notes |
|---|---|---|---|---|---|---|

## Quotes PII review (gate: to:human issue)
| Date | Reviewer | # candidates | # approved | # removed (reason) |
|---|---|---|---|---|

## Submission checks
| Check | Result | When |
|---|---|---|
| Judge links "Anyone with the link", no owner name shown | | |
| Video recorded/approved by a human | | |

## Independent crosscheck (narrative, `make crosscheck`)
Separate code (`agents/narrative/crosscheck/crosscheck.py`) reads the raw xlsx directly. Results are in `agents/narrative/crosscheck/results.json`.

| Date (ET) | Input sha256 | Metrics | Agree | Mismatch (issues) | Not in findings | Notes |
|---|---|---|---|---|---|---|
| Thu Nov 5 ~23:00 | see results.json | 54 | — | — | — | findings.json doesn't exist yet. Spot-checked the crosscheck itself against raw label counts tallied separately in-session: post identify agree 1,168/1,299, recommend mean 9,605/1,266, NPS (518−366)/1,266, call-988 mean 2,244/293, and subgroup n's (937 / 309 / 1,080 / 68 / 71 / 95 / 19). All matched. |
