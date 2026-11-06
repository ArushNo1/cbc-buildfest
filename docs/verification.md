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
