"""Drift tests for the data agent pipeline.

Uses Narrative's synthetic fixture generator (agents/narrative/fixtures/make_fixtures.py)
to test pipeline robustness against:
- Baseline synthetic mess
- New/unrecognized counties (Garrett County, Baltimore City)
- New/unrecognized Likert labels (Somewhat agree, Totally agree)
- Scaled rows
- Missing columns (call_988 removed)
- Shifted dates (+365 days)

These tests run in CI, which never has access to the real survey data.
"""

import importlib.util
import json
import pathlib
import jsonschema
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[3]
PIPELINE_MOD_PATH = ROOT / "agents/data/pipeline.py"
FIXTURES_MOD_PATH = ROOT / "agents/narrative/fixtures/make_fixtures.py"


def load_module(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


fx = load_module("make_fixtures", FIXTURES_MOD_PATH)
pipeline = load_module("data_pipeline", PIPELINE_MOD_PATH)


@pytest.fixture(scope="module")
def fixture_paths(tmp_path_factory):
    out_dir = tmp_path_factory.mktemp("drift_fx")
    return fx.write_all(out_dir, n=120, seed=5)


@pytest.fixture(scope="module")
def findings_schema():
    schema_path = ROOT / "contracts/findings.schema.json"
    return json.loads(schema_path.read_text(encoding="utf-8"))


def test_fixture_base(fixture_paths, tmp_path, findings_schema):
    """Base fixture with faithful mess should run cleanly and produce valid outputs."""
    csv_out = tmp_path / "survey_clean.csv"
    findings_out = tmp_path / "findings.json"
    val_out = tmp_path / "val_report.json"

    rc = pipeline.run_pipeline(
        data_path=fixture_paths["base"],
        output_csv=csv_out,
        output_findings=findings_out,
        output_validation=val_out
    )
    assert rc == 0
    assert csv_out.exists()
    assert findings_out.exists()
    assert val_out.exists()

    findings_data = json.loads(findings_out.read_text(encoding="utf-8"))
    jsonschema.validate(findings_data, findings_schema)

    val_data = json.loads(val_out.read_text(encoding="utf-8"))["validation"]
    assert val_data["row_count"] == 120
    assert val_data["duplicate_response_ids"] == 0
    assert val_data["unknown_label_counts"] == {}


def test_fixture_new_county(fixture_paths, tmp_path, findings_schema):
    """Unknown counties (Garrett, Baltimore City) should be flagged, not crash."""
    csv_out = tmp_path / "survey_clean.csv"
    findings_out = tmp_path / "findings.json"
    val_out = tmp_path / "val_report.json"

    rc = pipeline.run_pipeline(
        data_path=fixture_paths["new_county"],
        output_csv=csv_out,
        output_findings=findings_out,
        output_validation=val_out
    )
    assert rc == 0

    val_data = json.loads(val_out.read_text(encoding="utf-8"))["validation"]
    assert "unknown_county" in val_data["flags_summary"]
    assert val_data["flags_summary"]["unknown_county"] > 0

    findings_data = json.loads(findings_out.read_text(encoding="utf-8"))
    jsonschema.validate(findings_data, findings_schema)


def test_fixture_new_likert_label(fixture_paths, tmp_path, findings_schema):
    """Unknown Likert labels ('Somewhat agree', 'Totally agree') become null and are counted."""
    csv_out = tmp_path / "survey_clean.csv"
    findings_out = tmp_path / "findings.json"
    val_out = tmp_path / "val_report.json"

    rc = pipeline.run_pipeline(
        data_path=fixture_paths["new_likert_label"],
        output_csv=csv_out,
        output_findings=findings_out,
        output_validation=val_out
    )
    assert rc == 0

    val_data = json.loads(val_out.read_text(encoding="utf-8"))["validation"]
    assert len(val_data["unknown_label_counts"]) > 0
    assert "unknown_label" in val_data["flags_summary"]

    findings_data = json.loads(findings_out.read_text(encoding="utf-8"))
    jsonschema.validate(findings_data, findings_schema)


def test_fixture_extra_rows(fixture_paths, tmp_path, findings_schema):
    """Pipeline scales with additional rows without hardcoded count assumptions."""
    csv_out = tmp_path / "survey_clean.csv"
    findings_out = tmp_path / "findings.json"
    val_out = tmp_path / "val_report.json"

    rc = pipeline.run_pipeline(
        data_path=fixture_paths["extra_rows"],
        output_csv=csv_out,
        output_findings=findings_out,
        output_validation=val_out
    )
    assert rc == 0

    val_data = json.loads(val_out.read_text(encoding="utf-8"))["validation"]
    assert val_data["row_count"] == 360  # base 120 + 2*120

    findings_data = json.loads(findings_out.read_text(encoding="utf-8"))
    jsonschema.validate(findings_data, findings_schema)


def test_fixture_missing_column(fixture_paths, tmp_path, findings_schema):
    """When an optional column (e.g. call-988) is missing, pipeline skips gracefully."""
    csv_out = tmp_path / "survey_clean.csv"
    findings_out = tmp_path / "findings.json"
    val_out = tmp_path / "val_report.json"

    rc = pipeline.run_pipeline(
        data_path=fixture_paths["missing_column"],
        output_csv=csv_out,
        output_findings=findings_out,
        output_validation=val_out
    )
    assert rc == 0

    val_data = json.loads(val_out.read_text(encoding="utf-8"))["validation"]
    assert "call_988_likelihood" in val_data["missing_columns_in_source"]

    findings_data = json.loads(findings_out.read_text(encoding="utf-8"))
    jsonschema.validate(findings_data, findings_schema)

    finding_ids = {f["id"] for f in findings_data["findings"]}
    assert "call_988.likelihood.mean.overall" not in finding_ids


def test_fixture_shifted_dates(fixture_paths, tmp_path, findings_schema):
    """Dates shifted by +365 days are handled without date range failure."""
    csv_out = tmp_path / "survey_clean.csv"
    findings_out = tmp_path / "findings.json"
    val_out = tmp_path / "val_report.json"

    rc = pipeline.run_pipeline(
        data_path=fixture_paths["shifted_dates"],
        output_csv=csv_out,
        output_findings=findings_out,
        output_validation=val_out
    )
    assert rc == 0

    val_data = json.loads(val_out.read_text(encoding="utf-8"))["validation"]
    assert val_data["date_range"]["min_date"] is not None
    assert val_data["date_range"]["min_date"] > "2026-10-01"
