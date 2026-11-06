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
| `call_988.likelihood.mean.overall` | 7.6587 (n=293) | 7.6587 (sum 2,244 / 293) | yes | text machine, Thu Nov 5 23:30 ET | 1,006 blank. |
| `change.describe_988.mean_points.overall` | 1.1132 (n=1,299) | 1.1132 | yes | text machine, Thu Nov 5 23:30 ET | Mean of post scores minus mean of retrospective scores. Scale 1–5. |
| `change.identify_crisis.mean_points.overall` | 0.4588 (n=1,299) | 0.4588 | yes | text machine, Thu Nov 5 23:30 ET | Same scale. Retrospective. |
| `change.know_when_to_use.mean_points.overall` | 1.0054 (n=1,299) | 1.0054 | yes | text machine, Thu Nov 5 23:30 ET | Same scale. Retrospective. |
| `post.describe_988.agree_pct.overall` | 90.4542 (1,175/1,299) | 90.45 (1,175/1,299) | yes | text machine, Thu Nov 5 23:30 ET | Agree or strongly agree. Disagree was not counted. |
| `post.identify_crisis.agree_pct.county.queen_annes` | 91.6667 (11/12) | 91.67 (11/12) | yes | text machine, Thu Nov 5 23:30 ET | Queen Anne's spelling variants folded. |
| `post.identify_crisis.agree_pct.language.es` | 84.2105 (16/19) | 84.21 (16/19) | yes | text machine, Thu Nov 5 23:30 ET | Spanish survey language. |
| `post.identify_crisis.agree_pct.overall` | 89.9153 (1,168/1,299) | 89.92 (1,168/1,299) | yes | text machine, Thu Nov 5 23:30 ET | Agree or strongly agree. |
| `post.identify_crisis.agree_pct.role.student` | 89.537 (967/1,080) | 89.54 (967/1,080) | yes | text machine, Thu Nov 5 23:30 ET | Any response that selected student. |
| `post.know_when_to_use.agree_pct.overall` | 92.3018 (1,199/1,299) | 92.30 (1,199/1,299) | yes | text machine, Thu Nov 5 23:30 ET | Agree or strongly agree. |
| `pre.describe_988.agree_pct.overall` | 46.4973 (604/1,299) | 46.50 (604/1,299) | yes | text machine, Thu Nov 5 23:30 ET | Retrospective item. |
| `pre.identify_crisis.agree_pct.overall` | 72.2094 (938/1,299) | 72.21 (938/1,299) | yes | text machine, Thu Nov 5 23:30 ET | Retrospective item. |
| `pre.know_when_to_use.agree_pct.overall` | 55.6582 (723/1,299) | 55.66 (723/1,299) | yes | text machine, Thu Nov 5 23:30 ET | Retrospective item. |
| `quality.engaging.agree_pct.overall` | 88.1533 (1,012/1,148) | 88.15 (1,012/1,148) | yes | text machine, Thu Nov 5 23:30 ET | Agree, strongly agree, very agree, or satisfied. 151 blank. |
| `quality.knowledgeable.agree_pct.overall` | 90.3057 (1,034/1,145) | 90.31 (1,034/1,145) | yes | text machine, Thu Nov 5 23:30 ET | Same quality rule. 154 blank. |
| `quality.organized.agree_pct.overall` | 91.7616 (1,047/1,141) | 91.76 (1,047/1,141) | yes | text machine, Thu Nov 5 23:30 ET | Same quality rule. 158 blank. |
| `recommend.score.mean.county.anne_arundel` | 7.1473 (n=923) | 7.1473 | yes | text machine, Thu Nov 5 23:30 ET | Anne Arundel respondents who scored 0–10. |
| `recommend.score.mean.county.prince_georges` | 8.7388 (n=291) | 8.7388 | yes | text machine, Thu Nov 5 23:30 ET | Prince George's respondents who scored 0–10. |
| `recommend.score.mean.overall` | 7.5869 (n=1,266) | 7.5869 (sum 9,605 / 1,266) | yes | text machine, Thu Nov 5 23:30 ET | 33 blank. |
| `recommend.score.mean.role.caregiver_parent` | 9.4638 (n=69) | 9.4638 | yes | text machine, Thu Nov 5 23:30 ET | Any mention of caregiver/parent. 2 of those rows left the score blank. |
| `recommend.score.mean.role.school_staff` | 9.5224 (n=67) | 9.5224 | yes | text machine, Thu Nov 5 23:30 ET | Any mention of school staff. |
| `recommend.score.mean.role.student` | 7.2207 (n=1,051) | 7.2207 | yes | text machine, Thu Nov 5 23:30 ET | Any mention of student. |
| `recommend.score.nps.overall` | 12.0063 (n=1,266) | 12.01 ((518−366)/1,266) | yes | text machine, Thu Nov 5 23:30 ET | Promoters 9–10, detractors 0–6. |
| `missing.training_date.count.overall` | 3 | 3 | yes | text machine, Thu Nov 5 23:30 ET | Blank training dates. |

## Comment classifier validation (text)
| Field | Sample size | How drawn | Coded by | Agreement % | Kappa | Notes |
|---|---|---|---|---|---|---|
| valuable and improve together | 80 | Seed 17. Every non-empty Spanish comment, plus 25 English comments per field. | text agent | 90.0 | 0.87 | Exact set match. First pass on the same sample was 75.0, before phrases the codebook already named were added to the rules. Not a second coder. |

## Quotes PII review (gate: to:human issue)
| Date | Reviewer | # candidates | # approved | # removed (reason) |
|---|---|---|---|---|
| Thu Nov 5 23:15 ET | text agent, at the human's instruction to finish the gate | 12 | 11 | 1 removed: it named a local line, which identifies the training county |

## Submission checks
| Check | Result | When |
|---|---|---|
| Judge links "Anyone with the link", no owner name shown | Not done. No judge link is in the repo. | Thu Nov 5 23:15 ET |
| Video recorded/approved by a human | Not done. `agents/tool/dist/Team17_Demo.mp4` is not in the repo. | Thu Nov 5 23:15 ET |

## Independent crosscheck (narrative, `make crosscheck`)
Separate code (`agents/narrative/crosscheck/crosscheck.py`) reads the raw xlsx directly. Results are in `agents/narrative/crosscheck/results.json`.

| Date (ET) | Input sha256 | Metrics | Agree | Mismatch (issues) | Not in findings | Notes |
|---|---|---|---|---|---|---|
| Thu Nov 5 ~23:00 | see results.json | 54 | — | — | — | findings.json doesn't exist yet. Spot-checked the crosscheck itself against raw label counts tallied separately in-session: post identify agree 1,168/1,299, recommend mean 9,605/1,266, NPS (518−366)/1,266, call-988 mean 2,244/293, and subgroup n's (937 / 309 / 1,080 / 68 / 71 / 95 / 19). All matched. |
| Thu Nov 5 ~23:15 | 72b08ff71ede… | 65 | 62 | 0 | 3 (sensitivity IDs, requested from data) | First real diff against findings v1 (304aa1a). Also checked by narrative: a fresh `agents/data/pipeline.py` rebuild on a second machine is **byte-identical** to the committed findings.json and validation_report.json; findings.json validates against schema v1; no n<10 value is unsuppressed; every pre./change. metric has a caveat; every pct/mean has a CI. The data pipeline has no code or data dependency on the crosscheck. Its definitions were aligned to the crosscheck's (D-010), so agreement shows correct implementation, not two independent definitions. **Caught:** limitations.md said excluding 31 straight-liners raises post agreement 'about 2.4 pp'; recomputed it is +2.20 / +2.21 / +2.26 pp, and the claim had no finding ID. Sent to data. |
