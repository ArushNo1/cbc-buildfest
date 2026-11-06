"""Dashboard build tests. Synthetic inputs only (CI never sees the survey data)."""
from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


build = _load("tool_build", ROOT / "agents/tool/build.py")
synth = _load("tool_synth", HERE / "synth.py")
EX = ROOT / "contracts/examples"


def _vm(html: str) -> dict:
    m = re.search(r'<script id="dash-data" type="application/json">(.*?)</script>', html, re.S)
    assert m, "embedded data block missing"
    return json.loads(m.group(1))


def _write(tmp_path, findings=None, themes=None):
    f = tmp_path / "findings.json"
    t = tmp_path / "themes.json"
    f.write_text(json.dumps(findings or synth.make_findings()), encoding="utf-8")
    t.write_text(json.dumps(themes or synth.make_themes()), encoding="utf-8")
    return f, t


def _run(tmp_path, f, t, *extra):
    out = tmp_path / "dash.html"
    code = build.main(["--findings", str(f), "--themes", str(t), "--out", str(out),
                       "--validation", str(tmp_path / "none.json"), *extra])
    return code, out


def test_examples_build_and_are_stamped_example(tmp_path):
    code, out = _run(tmp_path, EX / "findings.example.json", EX / "themes.example.json")
    assert code == 0
    html = out.read_text(encoding="utf-8")
    assert "<title>" in html and "(EXAMPLE DATA)" in html
    vm = _vm(html)
    assert vm["meta"]["synthetic"] is True


def test_deterministic(tmp_path):
    f, t = _write(tmp_path)
    _, out = _run(tmp_path, f, t)
    first = out.read_bytes()
    _, out = _run(tmp_path, f, t)
    assert out.read_bytes() == first


def test_self_contained_no_network(tmp_path):
    f, t = _write(tmp_path)
    _, out = _run(tmp_path, f, t)
    html = out.read_text(encoding="utf-8")
    assert not re.search(r"<script[^>]+src=", html, re.I)
    assert not re.search(r"<link\b", html, re.I)
    assert not re.search(r"""(src|href)\s*=\s*["']?https?:""", html, re.I)
    assert "@import" not in html and "url(http" not in html


def test_groups_dimensions_and_order(tmp_path):
    f, t = _write(tmp_path)
    _, out = _run(tmp_path, f, t)
    vm = _vm(out.read_text(encoding="utf-8"))
    m = {x["key"]: x for x in vm["metrics"]}["post.identify_crisis.agree_pct"]
    assert m["overall"]["n"] == 1299
    assert m["dim_order"] == ["county", "role", "language", "training_month"]
    county = {r["level"]: r for r in m["dims"]["county"]}
    assert county["prince_georges"]["level_label"] == "Prince George's"
    assert county["garrett"]["value"] is None and county["garrett"]["suppressed"] is True
    assert m["dims"]["county"][-1]["level"] == "other_pooled"
    months = [r["level_label"] for r in m["dims"]["training_month"]]
    assert months[0] == "Oct 2025" and "Apr 2026" in months
    dist = [x for x in vm["metrics"] if x["dist_bin"] is not None]
    assert sorted(x["dist_bin"] for x in dist) == list(range(11))


def test_new_county_and_new_dimension_render_without_code_changes(tmp_path):
    f, t = _write(tmp_path, findings=synth.make_findings(extra_groups={
        "county": {"baltimore_city": 25}, "region": {"central_md": 40}}))
    code, out = _run(tmp_path, f, t)
    assert code == 0
    vm = _vm(out.read_text(encoding="utf-8"))
    m = {x["key"]: x for x in vm["metrics"]}["post.describe_988.agree_pct"]
    assert "baltimore_city" in {r["level"] for r in m["dims"]["county"]}
    assert "region" in m["dim_order"]
    assert vm["meta"]["dimension_labels"]["region"] == "Region"
    assert {r["level"]: r for r in m["dims"]["region"]}["central_md"]["level_label"] == "Central Md"


def test_privacy_backstop_hides_unsuppressed_small_cells(tmp_path, capsys):
    doc = synth.make_findings()
    leak = dict(doc["findings"][0])
    leak.update(id="post.identify_crisis.agree_pct.county.tiny_county", value=87.6543, numerator=4, n=5,
                small_n=False, suppressed=False, ci_low=40.1234, ci_high=97.4321,
                group={"dimension": "county", "level": "tiny_county"})
    doc["findings"].append(leak)
    f, t = _write(tmp_path, findings=doc)
    code, out = _run(tmp_path, f, t)
    assert code == 0
    html = out.read_text(encoding="utf-8")
    for v in ("87.6543", "40.1234", "97.4321"):
        assert v not in html
    rec = {r["level"]: r for r in {x["key"]: x for x in _vm(html)["metrics"]}["post.identify_crisis.agree_pct"]["dims"]["county"]}["tiny_county"]
    assert rec["value"] is None and rec["hidden_by_dashboard"] is True and rec["small_n"] is True
    assert "tiny_county" in capsys.readouterr().err


def test_labels_cannot_break_out_of_the_data_block(tmp_path):
    doc = synth.make_findings()
    doc["findings"][0]["label"] = "</script><script>alert(1)</script>"
    doc["findings"][0]["caveat"] = "<img src=x onerror=alert(1)>"
    f, t = _write(tmp_path, findings=doc)
    _, out = _run(tmp_path, f, t)
    html = out.read_text(encoding="utf-8")
    assert "<script>alert(1)" not in html and "<img src=x" not in html
    assert html.count("</script>") == 2  # the data block and the app script, nothing injected
    assert _vm(html)["metrics"]  # still parses


def test_contract_violation_fails_with_a_message(tmp_path, capsys):
    bad = synth.make_findings()
    bad["findings"][0]["unit"] = "percent"  # not in the schema enum
    f, t = _write(tmp_path, findings=bad)
    code, _ = _run(tmp_path, f, t)
    assert code == 1
    assert "does not match contracts/findings.schema.json" in capsys.readouterr().err


def test_duplicate_ids_fail(tmp_path, capsys):
    doc = synth.make_findings()
    doc["findings"].append(dict(doc["findings"][0]))
    f, t = _write(tmp_path, findings=doc)
    code, _ = _run(tmp_path, f, t)
    assert code == 1
    assert "duplicate IDs" in capsys.readouterr().err


def test_strict_requires_real_outputs(tmp_path, capsys):
    code = build.main(["--findings", str(tmp_path / "missing.json"), "--out", str(tmp_path / "x.html"), "--strict"])
    assert code == 1
    assert "does not exist" in capsys.readouterr().err


def test_missing_named_themes_file_fails(tmp_path):
    f, _ = _write(tmp_path)
    code = build.main(["--findings", str(f), "--themes", str(tmp_path / "nope.json"), "--out", str(tmp_path / "d.html")])
    assert code == 1  # a file you name explicitly must exist; only the defaults fall back to examples


def test_embeds_only_whitelisted_fields(tmp_path):
    doc = synth.make_findings()
    f, t = _write(tmp_path, findings=doc)
    _, out = _run(tmp_path, f, t)
    vm = _vm(out.read_text(encoding="utf-8"))
    allowed = set(build.RECORD_KEYS) | {"dimension", "level", "level_label", "hidden_by_dashboard"}
    for m in vm["metrics"]:
        recs = ([m["overall"]] if m["overall"] else []) + [r for rows in m["dims"].values() for r in rows]
        for r in recs:
            assert set(r) <= allowed


@pytest.mark.parametrize("fid,dim,lvl,key", [
    ("post.identify_crisis.agree_pct.overall", "overall", "all", "post.identify_crisis.agree_pct"),
    ("post.identify_crisis.agree_pct.county.anne_arundel", "county", "anne_arundel", "post.identify_crisis.agree_pct"),
    ("themes.improve.more_time.pct.language.es", "language", "es", "themes.improve.more_time.pct"),
    ("recommend.score.dist_7.overall", "overall", "all", "recommend.score.dist_7"),
    ("odd.metric.stat.extra.thing", "county", "Not A Slug", "odd.metric.stat"),
])
def test_metric_key(fid, dim, lvl, key):
    assert build.metric_key(fid, dim, lvl) == key


def test_level_labels():
    assert build.level_label("training_month", "2026_04", {}) == "Apr 2026"
    assert build.level_label("county", "queen_annes", {}) == "Queen Anne's"
    assert build.level_label("county", "x", {"label": "Custom Name"}) == "Custom Name"
    assert build.level_label("county", "garrett", {}) == "Garrett"


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_dashboard_js_parses():
    r = subprocess.run(["node", "--check", str(ROOT / "agents/tool/web/dashboard.js")], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
