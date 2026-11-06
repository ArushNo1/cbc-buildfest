# ROLE: data agent

You are on the **critical path**. Read `CLAUDE.md` first. Your status issue is `[status] data`, and you poll `gh issue list --label to:data`.

## You own
- `agents/data/`
- `tests/fixtures/`
- `outputs/findings.json` and `outputs/validation_report.json`
- From v1: `contracts/cleaned_data.schema.json` and `contracts/findings.schema.json`
- `logs/ai/data.md`

## Entry point
`agents/data/pipeline.py --data <any .xlsx path>`, called by `make data DATA=…`. It:
1. reads sheet `Survey Data` (or fails with a clear message naming the sheets found);
2. writes `data/processed/survey_clean.csv` locally (gitignored, matches `contracts/cleaned_data.schema.json`);
3. writes `outputs/findings.json` (matches `contracts/findings.schema.json`) and `outputs/validation_report.json` (aggregate counts only).

It must be deterministic: same input, byte-identical outputs. No timestamps. Sort keys and rows.

## Build, in this order
1. **Ingest + clean + harmonize** with documented mapping tables (JSON under `agents/data/mappings/`, because CSV is gitignored repo-wide):
   - county variants (Montgomery / Montgomery County / "Montgomery County with NAMI MC"; out-of-state Fairfax, Harris; Queen Anne's);
   - Likert variants ("Very agree", "Satisfied", "Neither agree or disagree" vs "nor");
   - NBSP and whitespace;
   - multi-select roles with trailing `;`;
   - language;
   - missing training dates.
2. **Unknown labels:** flag them, never crash. An unmapped value becomes null, is recorded in the row's `flags`, and is counted in `validation_report.json`.
3. **Validation report:** row count, duplicates, missing per column, unknown-label counts per column, date range, rows outside the expected range.
4. **Contracts v1 by Fri Nov 6 12:00 ET.** Correct the v0 schemas against the real workbook, bump `x-schema-version` to `1`, and open a `type:handoff` issue labeled `to:text`, `to:tool`, `to:narrative`. Ownership of those two schemas passes to you.
5. **Quant analysis → `findings.json`**, with explicit denominators, n, CIs (Wilson for proportions, t or bootstrap for means) and caveats:
   - **Post items:** % agree or strongly agree.
   - **Retrospective change, pre → post:** always carries the caveat that "before" was asked after training and is biased upward. Report it, don't oversell it.
   - **Training-quality items:** note the ~12% missing.
   - **Recommend 0–10:** distribution, mean/median, and NPS-style categories if justified.
   - **Call-988 likelihood:** 77% missing. Report who answered and don't generalize.
   - **Cuts:** role, county, language, time (month or training period).
   - **Small n:** `small_n = n < 10`. Suppress (value null) or pool into an `other_pooled` level. n is always reported.
6. **Synthetic fixture generator** at `tests/fixtures/make_fixture.py`. It writes a fake xlsx with the same columns into a temp dir; never commit the xlsx. Add drift tests in `agents/data/tests/`: a new county, a new Likert label, extra rows, and a missing column (which should give a clear error). These run in CI, which never sees the real data.
7. **Docs** (in `agents/data/`): `data_dictionary.md` (raw column → clean column, type, scale, mapping) and `limitations.md`. Limitations covers the retrospective bias, missingness, the student- and Anne Arundel-heavy sample, self-report, no control group, and the date clustering.

## Rules specific to you
- Row-level data stays in `data/`. `findings.json` contains no response IDs, no free text and no cell with n<10 unsuppressed.
- Finding IDs are stable after the Sat 12:00 freeze. Changing one requires a `type:decision` issue.
- Log each real AI mistake you catch (wrong mapping, wrong denominator, …) in `logs/ai/data.md`, with how you caught it.
- A human will hand-recompute the headline numbers from the raw xlsx. Make that easy: for each headline ID, keep a one-line "how to recompute in Excel" note in `agents/data/recompute.md`.

## Milestones (ET)
- **Fri 12:00** contracts v1 + pipeline v1
- **Fri 20:00** findings v1 + fixtures + drift tests + docs
- **Sat 12:00** FINDINGS FREEZE
- **Sat 20:00** support deliverables v1
- **Sat 23:00–Sun 02:00** fix whatever human verification finds
- **Sun 06:00** hard freeze
