# AI process log: data agent

Append-only. Record only what actually happened. This feeds the AI appendix (hard rule 4).

Entry template:

## <date> <time ET>: <short title>
- **Prompt (representative):** "..."
- **What the AI produced:**
- **Error / limitation (if any), and how it was caught:**
- **Revision:**
- **Manually verified against data:** what, how, result


## 2026-11-05 22:55 ET: Ingestion pipeline, mappings, and findings v1
- **Prompt (representative):** "Build agents/data/pipeline.py to clean survey data, produce outputs/findings.json matching contracts/findings.schema.json, and validate against narrative crosscheck."
- **What the AI produced:** Initial pipeline script, 5 mapping JSON files, schema v1 bumps, and findings generator.
- **Error / limitation (if any), and how it was caught:**
  1. `missing.training_date.count.overall` had `n_missing` computed as `n_total - n` (0) instead of the actual missing count (3). Caught when running `agents/narrative/crosscheck/crosscheck.py`, which flagged a denominator mismatch against the raw file.
  2. Nullable integer columns in `survey_clean.csv` were written as floating point strings (e.g. `4.0`) because default pandas `float64` was used for missing Likert values. Caught when validating `survey_clean.csv` rows against `cleaned_data.schema.json`.
- **Revision:**
  1. Added explicit `n_missing` parameter override to `make_finding` so count metrics correctly preserve `n_missing = 3`.
  2. Converted all integer and rating columns in pandas to `Int64` nullable integer types before exporting to CSV.
- **Manually verified against data:**
  - Ran `agents/narrative/crosscheck/crosscheck.py --data data/raw/BuildFest_EveryMind_Survey_Data_FULL.xlsx`: 54 metrics tested, 54 agreed, 0 mismatches.
  - Validated all 1,299 rows of `survey_clean.csv` against `contracts/cleaned_data.schema.json` with zero schema violations.
  - Validated `outputs/findings.json` against `contracts/findings.schema.json` with zero schema violations.
  - Ran 11 automated pytest unit and drift tests in `agents/data/tests/`: 11 passed.

## 2026-11-05 23:28 ET: Sensitivity findings, sample composition, time cuts, and histograms
- **Prompt (representative):** "Add pooled small counties, time cuts, sensitivity findings excluding straightliners, quality and NPS by group, and score distributions per issues #38, #39, and #40."
- **What the AI produced:** Expanded `agents/data/pipeline.py` to generate 222 findings including sensitivity findings (`excl_straightline`), sample composition percentages, spring vs. fall period cuts, monthly line cuts, quality/NPS group cuts, and 0-10 distribution histograms.
- **Error / limitation (if any), and how it was caught:**
  - In `agents/data/limitations.md`, sensitivity text had stated approximately 2.4 pp instead of 2.20–2.26 pp. Caught by narrative crosscheck.
  - In Excel `COUNTIF(H2:H1300, "*Agree*")`, wildcard matched "Disagree" and "Strongly disagree" because they end in "agree". Caught during manual formula replication; corrected in `agents/data/recompute.md` to `=(COUNTIF(..., "Agree") + COUNTIF(..., "Strongly agree*")) / COUNTA(...)`.
- **Revision:**
  - Updated `agents/data/limitations.md` to report exact 2.20 pp (identify), 2.21 pp (describe), and 2.26 pp (know when to use) gains.
  - Published 3 sensitivity findings to `outputs/findings.json`.
  - Added sample composition counts/shares, time cuts (spring/fall/other and monthly), and 0-10 score histograms.
- **Manually verified against data:**
  - `agents/narrative/crosscheck/crosscheck.py` diffed 65 metrics against `outputs/findings.json`: 65 agreed, 0 mismatches.
  - `scripts/check_numbers.py agents/narrative/drafts/memo.md` verified 0 problems.
  - `agents/tool/build.py` successfully built `outputs/dashboard.html` with 73 displayed metrics from 222 findings.
  - Full test suite (50 tests) passed.
