"""Unit tests for individual cleaners and helpers in agents/data/pipeline.py."""

import pytest
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[3]
PIPELINE_MOD_PATH = ROOT / "agents/data/pipeline.py"

spec = importlib.util.spec_from_file_location("pipeline", PIPELINE_MOD_PATH)
pipeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipeline)


def test_clean_county():
    _, _, county_rules, _, _ = pipeline.load_mappings()

    c, raw, lvl, flag = pipeline.clean_county("Montgomery County with NAMI MC", county_rules)
    assert c == "Montgomery"
    assert lvl == "montgomery"
    assert flag is None

    c, raw, lvl, flag = pipeline.clean_county("Fairfax county ", county_rules)
    assert c == "Fairfax (VA)"
    assert lvl == "fairfax_va"
    assert flag is None

    c, raw, lvl, flag = pipeline.clean_county("Mars County", county_rules)
    assert c is None
    assert "unknown_county:Mars County" == flag

    c, raw, lvl, flag = pipeline.clean_county(None, county_rules)
    assert c is None
    assert flag == "missing_county"


def test_clean_roles():
    _, _, _, role_rules, _ = pipeline.load_mappings()

    joined, l, flags = pipeline.clean_roles("School staff member;Caregiver/parent;", role_rules)
    assert joined == "Caregiver/parent;School staff member"
    assert flags == []

    joined, l, flags = pipeline.clean_roles("Student;", role_rules)
    assert joined == "Student"
    assert flags == []

    joined, l, flags = pipeline.clean_roles("Astronaut", role_rules)
    assert flags == ["unknown_role:Astronaut"]


def test_clean_likert():
    _, likert_map, _, _, _ = pipeline.load_mappings()

    val, flag = pipeline.clean_likert("Very agree", "test_col", likert_map)
    assert val == 5
    assert flag is None

    val, flag = pipeline.clean_likert("Satisfied", "test_col", likert_map)
    assert val == 4
    assert flag is None

    val, flag = pipeline.clean_likert("Neither agree or disagree", "test_col", likert_map)
    assert val == 3
    assert flag is None

    val, flag = pipeline.clean_likert("Bogus label", "test_col", likert_map)
    assert val is None
    assert flag == "unknown_label:test_col:bogus label"


def test_clean_score10():
    val, flag = pipeline.clean_score10("10", "rec")
    assert val == 10
    assert flag is None

    val, flag = pipeline.clean_score10(0.0, "rec")
    assert val == 0
    assert flag is None

    val, flag = pipeline.clean_score10("11", "rec")
    assert val is None
    assert flag == "out_of_range:rec:11"

    val, flag = pipeline.clean_score10("-1", "rec")
    assert val is None
    assert flag == "out_of_range:rec:-1"


def test_wilson_ci():
    low, high = pipeline.calc_wilson_ci(k=50, n=100)
    assert 39.0 < low < 41.0
    assert 59.0 < high < 61.0

    low, high = pipeline.calc_wilson_ci(k=0, n=10)
    assert low == 0.0
    assert high > 0.0

    low, high = pipeline.calc_wilson_ci(k=10, n=10)
    assert low < 100.0
    assert high == 100.0
