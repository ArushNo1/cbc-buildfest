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
| `call_988.likelihood.mean.overall` | 7.66 (n=293) | 7.66 (n=293) | Yes | Daksh / Nov 5 | Verified in Excel |
| `change.describe_988.mean_points.overall` | 1.11 (n=1299) | 1.11 (n=1299) | Yes | Daksh / Nov 5 | Verified in Excel |
| `change.identify_crisis.mean_points.overall` | 0.46 (n=1299) | 0.46 (n=1299) | Yes | Daksh / Nov 5 | Verified in Excel |
| `change.know_when_to_use.mean_points.overall` | 1.01 (n=1299) | 1.01 (n=1299) | Yes | Daksh / Nov 5 | Verified in Excel |
| `post.describe_988.agree_pct.overall` | 90.45 (n=1299) | 90.45 (n=1299) | Yes | Daksh / Nov 5 | Verified in Excel |
| `post.identify_crisis.agree_pct.county.queen_annes` | 91.67 (n=12) | 91.67 (n=12) | Yes | Daksh / Nov 5 | Verified in Excel |
| `post.identify_crisis.agree_pct.language.es` | 84.21 (n=19) | 84.21 (n=19) | Yes | Daksh / Nov 5 | Verified in Excel |
| `post.identify_crisis.agree_pct.overall` | 89.92 (n=1299) | 89.92 (n=1299) | Yes | Daksh / Nov 5 | Verified in Excel |
| `post.identify_crisis.agree_pct.role.student` | 89.54 (n=1080) | 89.54 (n=1080) | Yes | Daksh / Nov 5 | Verified in Excel |
| `post.know_when_to_use.agree_pct.overall` | 92.30 (n=1299) | 92.30 (n=1299) | Yes | Daksh / Nov 5 | Verified in Excel |
| `pre.describe_988.agree_pct.overall` | 46.50 (n=1299) | 46.50 (n=1299) | Yes | Daksh / Nov 5 | Verified in Excel |
| `pre.identify_crisis.agree_pct.overall` | 72.21 (n=1299) | 72.21 (n=1299) | Yes | Daksh / Nov 5 | Verified in Excel |
| `pre.know_when_to_use.agree_pct.overall` | 55.66 (n=1299) | 55.66 (n=1299) | Yes | Daksh / Nov 5 | Verified in Excel |
| `quality.engaging.agree_pct.overall` | 88.15 (n=1148) | 88.15 (n=1148) | Yes | Daksh / Nov 5 | Verified in Excel |
| `quality.organized.agree_pct.overall` | 91.76 (n=1141) | 91.76 (n=1141) | Yes | Daksh / Nov 5 | Verified in Excel |
| `recommend.score.mean.county.anne_arundel` | 7.15 (n=923) | 7.15 (n=923) | Yes | Daksh / Nov 5 | Verified in Excel |
| `recommend.score.mean.county.prince_georges` | 8.74 (n=291) | 8.74 (n=291) | Yes | Daksh / Nov 5 | Verified in Excel |
| `recommend.score.mean.role.caregiver_parent` | 9.46 (n=69) | 9.46 (n=69) | Yes | Daksh / Nov 5 | Verified in Excel |
| `recommend.score.mean.role.school_staff` | 9.52 (n=67) | 9.52 (n=67) | Yes | Daksh / Nov 5 | Verified in Excel |
| `recommend.score.mean.role.student` | 7.22 (n=1051) | 7.22 (n=1051) | Yes | Daksh / Nov 5 | Verified in Excel |

## Comment classifier validation (text)
| Field | Sample size | How drawn | Coded by | Agreement % | Kappa | Notes |
|---|---|---|---|---|---|---|

## Quotes PII review (gate: to:human issue)
| Date | Reviewer | # candidates | # approved | # removed (reason) |
|---|---|---|---|---|
| Nov 5 | Arush | 11 | 11 | 0 (text agent had already dropped id 71, a local place name) |

## Submission checks
| Check | Result | When |
|---|---|---|
| Judge links "Anyone with the link", no owner name shown | | |
| Video recorded/approved by a human | Approved (Arush): 95.7 s, content complete. **Superseded:** that was the command-line version, replaced on Nov 6. | Nov 5 |
| Video recorded/approved by a human: re-recorded website version (97.5 s, website flow, synthetic upload) | **Pending.** Needs a person's re-approval in #32. | Nov 6 |
| Live site opens logged out, serves only the site (agent, automated; not the human check above) | `scripts/site_check.py --url https://team17-everymind.vercel.app`: 12/12; `/` 200; repo files 404 | Nov 6, 12:47 ET |

## Independent crosscheck (narrative, `make crosscheck`)
Separate code (`agents/narrative/crosscheck/crosscheck.py`) reads the raw xlsx directly. Results are in `agents/narrative/crosscheck/results.json`.

| Date (ET) | Input sha256 | Metrics | Agree | Mismatch (issues) | Not in findings | Notes |
|---|---|---|---|---|---|---|
| Thu Nov 5 ~23:00 | see results.json | 54 | — | — | — | findings.json doesn't exist yet. Spot-checked the crosscheck itself against raw label counts tallied separately in-session: post identify agree 1,168/1,299, recommend mean 9,605/1,266, NPS (518−366)/1,266, call-988 mean 2,244/293, and subgroup n's (937 / 309 / 1,080 / 68 / 71 / 95 / 19). All matched. |
| Thu Nov 5 22:52 | 72b08ff71ede | 54 | 54 | 0 | 0 | All 54 crosscheck metrics match outputs/findings.json within ±0.05 tolerance. Numerators and denominators match exactly. |
