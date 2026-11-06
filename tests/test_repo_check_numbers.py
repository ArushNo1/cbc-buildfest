import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("check_numbers", ROOT / "scripts/check_numbers.py")
cn = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cn)

IDX = {"a.b": {"value": 78.46, "n": 1041}, "a.s": {"value": None, "n": 4}}


def test_numbers_match_as_displayed():
    assert cn.check_text("78% [F:a.b], 78.5% [F:a.b] of n=1,041 [F:a.b#n]", IDX) == []


def test_mismatch_suppressed_unknown_untagged():
    errs = cn.check_text("79% [F:a.b]\n5% [F:a.s]\n3 [F:nope]\nabout 40% said", IDX)
    assert len(errs) == 4, errs
    assert any("shows 79" in e for e in errs)
    assert any("null" in e for e in errs)
    assert any("unknown ID nope" in e for e in errs)
    assert any("untagged percentage '40%'" in e for e in errs)
