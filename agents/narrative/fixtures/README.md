# Synthetic fixtures (for the data agent)

`make_fixtures.py` writes synthetic workbooks in the **raw export format**: sheet `Survey Data`, the same 20 headers (including their non-breaking spaces), the same column types and the same messy label vocabulary as the real file. Every row and comment is generated; nothing is copied from real responses. Use these for drift tests and in CI, which never has the real data.

```bash
make fixtures                     # -> tests/fixtures/fixture_<variant>.xlsx  (gitignored; regenerate on any machine)
python3 agents/narrative/fixtures/make_fixtures.py --out /tmp/fx --n 300 --seed 17
```

## Variants

All variants are built from the same base rows (n=300 by default, seed 17, so output is deterministic).

| File | What changed | What your pipeline should do |
|---|---|---|
| `fixture_base.xlsx` | nothing; faithful mess included (county variants, "Very agree", "Satisfied", "Neither agree or disagree", NBSP, trailing `;` roles, U+200E on Language, ~1.5% Spanish, ≥1 missing training date, ~12% missing quality block, ~77% missing call-988, whitespace-only comments) | run clean |
| `fixture_new_county.xlsx` | every 20th row's county is `Garrett County`, and one row is `Baltimore City ` | flag them as unknown and keep the rows; don't crash; small-n handling applies |
| `fixture_new_likert_label.xlsx` | `Somewhat agree` on every 25th post "identify" answer; `Totally agree` on some "engaged" answers | map to null + flag + count in validation_report; don't crash |
| `fixture_extra_rows.xlsx` | base rows + 2n new rows (Ids continue) | all counts scale; no hard-coded totals |
| `fixture_missing_column.xlsx` | the likelihood-to-call-988 column is removed | skip those findings with a clear message, or fail with an error naming the column. Never a traceback. |
| `fixture_shifted_dates.xlsx` | every date +365 days (outside Oct 2025–Oct 2026) | time cuts aren't hard-coded to the original months |

The "improve" comments include **deliberate fake PII** ("Thanks to trainer Jane Doe…", "Call me at 555-0100…") so the text agent's PII screen has something to catch.

## Using it in your tests (`agents/data/tests/`)

```python
import importlib.util, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("make_fixtures", ROOT / "agents/narrative/fixtures/make_fixtures.py")
fx = importlib.util.module_from_spec(spec); spec.loader.exec_module(fx)

def test_new_county_is_flagged(tmp_path):
    paths = fx.write_all(tmp_path, n=120, seed=5)   # {"base": Path, "new_county": Path, ...}
    ...  # run agents/data/pipeline.py --data paths["new_county"], then assert on validation_report.json
```

Also exported: `fx.HEADERS` (the exact raw headers), `fx.COUNTY`, `fx.POST`, `fx.PRE`, `fx.QUALITY`, `fx.RECOMMEND`, `fx.CALL988`, `fx.VALUABLE`, `fx.IMPROVE`, `fx.generate(n, seed)` → DataFrame.

Faithfulness check: `agents/narrative/tests/test_crosscheck_fixtures.py::test_base_fixture_is_faithful_to_real_export` compares headers, dtypes and label sets with the real file when it is present locally (skipped in CI). If the real export changes, tell narrative (`to:narrative`) and the generator will be updated.
