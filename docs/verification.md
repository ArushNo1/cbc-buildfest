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
| post.identify_crisis.agree_pct.overall | 89.92% (1299) | 89.92% (1299) | Yes | Human verified / Nov 5 | 1,168 agree / 1,299 |
| post.describe_988.agree_pct.overall | 90.45% (1299) | 90.45% (1299) | Yes | Human verified / Nov 5 | 1,175 agree / 1,299 |
| post.know_when_to_use.agree_pct.overall | 92.30% (1299) | 92.30% (1299) | Yes | Human verified / Nov 5 | 1,199 agree / 1,299 |
| pre.identify_crisis.agree_pct.overall | 72.21% (1299) | 72.21% (1299) | Yes | Human verified / Nov 5 | 938 agree / 1,299 |
| pre.describe_988.agree_pct.overall | 46.50% (1299) | 46.50% (1299) | Yes | Human verified / Nov 5 | 604 agree / 1,299 |
| pre.know_when_to_use.agree_pct.overall | 55.66% (1299) | 55.66% (1299) | Yes | Human verified / Nov 5 | 723 agree / 1,299 |
| change.describe_988.mean_points.overall | +1.11 pts (1299) | +1.11 pts (1299) | Yes | Human verified / Nov 5 | Mean post 4.34 - pre 3.23 |
| quality.engaging.agree_pct.overall | 88.15% (1148) | 88.15% (1148) | Yes | Human verified / Nov 5 | 1,012 agree / 1,148 (151 missing) |
| quality.knowledgeable.agree_pct.overall | 90.31% (1145) | 90.31% (1145) | Yes | Human verified / Nov 5 | 1,034 agree / 1,145 (154 missing) |
| quality.organized.agree_pct.overall | 91.76% (1141) | 91.76% (1141) | Yes | Human verified / Nov 5 | 1,047 agree / 1,141 (158 missing) |
| recommend.score.mean.overall | 7.59 (1266) | 7.59 (1266) | Yes | Human verified / Nov 5 | Sum 9,605 / 1,266 (33 missing) |
| recommend.score.nps.overall | +12.01 (1266) | +12.01 (1266) | Yes | Human verified / Nov 5 | 518 promoters - 366 detractors |
| call_988.likelihood.mean.overall | 7.66 (293) | 7.66 (293) | Yes | Human verified / Nov 5 | Sum 2,244 / 293 (1,006 missing) |
| missing.training_date.count.overall | 3 (1299) | 3 (1299) | Yes | Human verified / Nov 5 | 3 blank date cells |

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
