import importlib.util
import json
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads((ROOT / "contracts" / "themes.schema.json").read_text(encoding="utf-8"))
CODEBOOK = (Path(__file__).resolve().parent / "codebook.md").read_text(encoding="utf-8")


def load_themes():
    path = Path(__file__).resolve().parent / "themes.py"
    spec = importlib.util.spec_from_file_location("text_themes", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


themes = load_themes()


def test_codebook_lists_every_theme():
    for item in themes.THEMES:
        assert item["theme_id"] in CODEBOOK
    for theme_id in themes.RESIDUAL:
        assert theme_id in CODEBOOK


def test_classify_examples():
    assert themes.classify("I learned the warning signs of a crisis.", "valuable") == [
        "recognize_crisis"
    ]
    assert "what_988_is" in themes.classify("Now I know what 988 is.", "valuable")
    assert themes.classify("I know when to call 988 instead of 911.", "valuable") == [
        "what_988_is",
        "when_to_use",
    ]
    assert themes.classify("good", "valuable") == ["no_substantive"]
    assert themes.classify("asdfasdf", "valuable") == ["other_unclear"]
    assert themes.classify("", "improve") == []
    assert themes.classify("It felt rushed. We needed more time.", "improve") == ["more_time"]
    assert themes.classify("The mic cut out and the room was cold.", "improve") == ["logistics"]
    assert themes.classify("Please add Spanish materials.", "improve") == ["accessibility"]
    assert themes.classify("Aprendí las señales de una crisis.", "valuable") == ["recognize_crisis"]
    assert themes.classify("How to recognize signs of a crisis", "valuable") == ["recognize_crisis"]
    assert "what_988_is" in themes.classify("That 988 can be called or texted", "valuable")
    assert "confidence_to_help" in themes.classify("How to support a friend", "valuable")
    assert themes.classify("everything", "valuable") == ["no_substantive"]
    assert themes.classify("Make it shorter", "improve") == ["more_time"]
    assert "more_examples" in themes.classify("Add real-life examples", "improve")
    assert themes.classify("Nothing, it was great", "improve") == ["no_substantive"]
    assert themes.classify("Más actividades", "improve") == ["more_interaction"]
    assert themes.classify("Nada, todo bien", "improve") == ["no_substantive"]
    assert themes.language_level({"language": "English (United States)"}) == "en"
    assert themes.language_level({"language": "Español (México)"}) == "es"
    both = themes.classify("good examples of what to say", "valuable")
    assert "practice_scenarios" in both
    assert "confidence_to_help" in both


def test_pii_flags_and_ignores_988():
    assert themes.screen_pii("Reach me at test@example.com") == ["email"]
    assert themes.screen_pii("call 555-010-0199") == ["phone"]
    assert "phone" in themes.screen_pii("Call me at 555-0100 about my school")
    assert "school" in themes.screen_pii("Call me at 555-0100 about my school")
    assert "name" in themes.screen_pii("Thanks to trainer Jane Doe, more sessions like hers")
    assert "school" in themes.screen_pii("I go to Example High School")
    assert "name" in themes.screen_pii("Dr. Rivera explained the lifeline.")
    assert themes.screen_pii("I learned what 988 is") == []


def test_fixture_output_matches_schema_and_hides_text(tmp_path):
    rows = themes.fixture_rows()
    payload = themes.build_themes(
        rows,
        {"file_sha256": "abc", "n_rows": len(rows)},
        note="SYNTHETIC FIXTURE. Values are made up. Never cite.",
    )
    jsonschema.validate(payload, SCHEMA)
    blob = json.dumps(payload)
    for row in rows:
        assert row["comment_valuable"] not in blob
        assert row["comment_improve"] not in blob

    by_id = {item["id"]: item for item in payload["counts"]}
    crisis = by_id["themes.valuable.recognize_crisis.pct.county.anne_arundel"]
    assert crisis["n"] == 10
    assert crisis["n_mentions"] == 10
    assert crisis["pct"] == 100.0
    assert crisis["small_n"] is False

    spanish = by_id["themes.valuable.recognize_crisis.pct.language.es"]
    assert spanish["n"] == 2
    assert spanish["small_n"] is True
    assert spanish["n_mentions"] is None
    assert spanish["pct"] is None

    levels = {item["group"]["level"] for item in payload["counts"] if item["group"]["dimension"] == "county"}
    assert "Calvert" not in levels
    assert "other_pooled" in levels
    assert payload["pii_screen"]["n_flagged"] == 1
    assert payload["validation"]["agreement_pct"] is None
    assert payload["spanish"]["n_comments"] == 2


def test_fixture_cli_is_deterministic(tmp_path):
    first = tmp_path / "a.json"
    second = tmp_path / "b.json"
    assert themes.main(["--fixture", "--output", str(first)]) == 0
    assert themes.main(["--fixture", "--output", str(second)]) == 0
    assert first.read_text(encoding="utf-8") == second.read_text(encoding="utf-8")
    jsonschema.validate(json.loads(first.read_text(encoding="utf-8")), SCHEMA)


def test_missing_input_fails(tmp_path):
    try:
        themes.main(["--input", str(tmp_path / "missing.csv"), "--output", str(tmp_path / "out.json")])
    except SystemExit as exc:
        assert exc.code != 0
    else:
        raise AssertionError("expected a missing-file exit")
