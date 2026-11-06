import importlib.util
import json
import pathlib
import subprocess

import pandas as pd
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[3]
RAW = ROOT / "data/raw/BuildFest_EveryMind_Survey_Data_FULL.xlsx"


def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


fx = load("make_fixtures", "agents/narrative/fixtures/make_fixtures.py")
xc = load("crosscheck", "agents/narrative/crosscheck/crosscheck.py")


def read(p):
    return pd.read_excel(p, sheet_name=fx.SHEET)


@pytest.fixture(scope="module")
def paths(tmp_path_factory):
    return fx.write_all(tmp_path_factory.mktemp("fx"), n=120, seed=5)


# ---- crosscheck
def test_crosscheck_known_values():
    df = fx.generate(n=14, seed=3)
    df[fx.POST[0]] = ["Strongly agree", "Agree" + fx.NB, "Disagree", None, "Bogus"] + ["Neither agree nor disagree"] * 9
    df[fx.RECOMMEND] = [10, 9, 0, 6, 7, None, 11] + [8.0] * 7  # 11 is out of range -> missing
    r = {m["id"]: m for m in xc.compute(df)[0]}
    a = r["post.identify_crisis.agree_pct.overall"]
    assert (a["n"], a["n_missing"], a["numerator"]) == (12, 2, 2)
    assert a["value"] == pytest.approx(100 * 2 / 12, abs=1e-3)
    assert (r["recommend.score.nps.overall"]["n"], r["recommend.score.nps.overall"]["value"]) == (12, 0.0)
    assert r["recommend.score.mean.overall"]["value"] == pytest.approx(88 / 12, abs=1e-3)


def test_diff_flags_value_and_denominator_mismatches():
    mine = [{"id": "a.x", "value": 50.0, "n": 100, "n_missing": 0, "numerator": 50},
            {"id": "a.y", "value": 7.5, "n": 90, "n_missing": 10, "numerator": None},
            {"id": "a.z", "value": 1.0, "n": 20, "n_missing": 0, "numerator": None},
            {"id": "a.w", "value": 3.0, "n": 20, "n_missing": 0, "numerator": None}]
    findings = {"findings": [{"id": "a.x", "value": 50.04, "n": 100, "n_missing": 0, "numerator": 50},
                             {"id": "a.y", "value": 7.5, "n": 92, "n_missing": 8},
                             {"id": "a.z", "value": 1.2, "n": 20}]}
    mism, not_found = xc.diff(mine, findings)
    assert [m["id"] for m, _, _ in mism] == ["a.y", "a.z"] and not_found == ["a.w"]
    assert ("n", 92, 90) in mism[0][2]


def test_open_issues_has_both_values_and_skips_open_ones(monkeypatch):
    calls = []

    def fake_run(cmd, **kw):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout="[crosscheck] mismatch: a.old\n")

    monkeypatch.setattr(xc.subprocess, "run", fake_run)
    m = {"id": "a.new", "value": 1.0, "n": 20, "n_missing": 0, "numerator": None, "denominator": "mine"}
    xc.open_issues([({**m, "id": "a.old"}, {"value": 2}, [("value", 2, 1.0)]),
                    (m, {"value": 2, "denominator": "theirs"}, [("value", 2, 1.0)])], "ab" * 32)
    creates = [c for c in calls if c[:3] == ["gh", "issue", "create"]]
    assert len(creates) == 1 and "[crosscheck] mismatch: a.new" in creates[0]
    body = creates[0][creates[0].index("--body") + 1]
    assert "| value | 2 | 1.0 |" in body and '"theirs"' in body and '"mine"' in body


# ---- fixtures
def test_variants_have_their_drift(paths):
    base = read(paths["base"])
    assert list(base.columns) == fx.HEADERS and len(base) == 120 and base[fx.HEADERS[5]].isna().sum() >= 1
    assert "Garrett County" in set(read(paths["new_county"])[fx.COUNTY])
    nl = read(paths["new_likert_label"])
    assert "Somewhat agree" in set(nl[fx.POST[0]]) and "Totally agree" in set(nl[fx.QUALITY[0]])
    er = read(paths["extra_rows"])
    assert len(er) == 360 and er["Id"].is_unique
    assert fx.CALL988 not in read(paths["missing_column"]).columns
    assert pd.to_datetime(read(paths["shifted_dates"])[fx.HEADERS[5]]).max() > pd.Timestamp("2026-10-31")


def test_crosscheck_runs_on_every_variant(paths, tmp_path):
    for name, p in paths.items():
        args = ["--data", str(p), "--out", str(tmp_path / f"{name}.json"), "--findings", str(tmp_path / "none.json")]
        assert xc.main(args) == 0, name
    dropped = json.loads((tmp_path / "missing_column.json").read_text())["metrics"]
    assert not any(m["id"].startswith("call_988") for m in dropped)
    nl = {m["id"]: m for m in json.loads((tmp_path / "new_likert_label.json").read_text())["metrics"]}
    assert nl["post.identify_crisis.agree_pct.overall"]["n_missing"] == 5  # rows 0, 25, 50, 75, 100


@pytest.mark.skipif(not RAW.exists(), reason="raw data is local-only (never in CI)")
def test_base_fixture_is_faithful_to_real_export(paths):
    raw, base = read(RAW), read(paths["base"])
    assert list(raw.columns) == list(base.columns)
    assert [str(t) for t in raw.dtypes] == [str(t) for t in base.dtypes]
    for col in [fx.HEADERS[3], fx.HEADERS[4], fx.COUNTY, *fx.POST, *fx.PRE, *fx.QUALITY]:
        assert set(base[col].dropna()) <= set(raw[col].dropna()), col
