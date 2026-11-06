import json
import pathlib
import subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
HOOK = ROOT / "scripts/hooks/commit-msg"


def hook_rc(tmp_path, msg):
    f = tmp_path / "msg"
    f.write_text(msg, encoding="utf-8")
    return subprocess.run(["bash", str(HOOK), str(f)], capture_output=True).returncode


def test_commit_msg_hook(tmp_path):
    assert hook_rc(tmp_path, "Update CLAUDE.md and .claude/settings.json\n") == 0
    assert hook_rc(tmp_path, "Add findings v1\n# Co-Authored-By in a git comment line is ignored\n") == 0
    for bad in [
        "Fix\n\nCo-Authored-By: Someone <noreply@anthropic.com>\n",
        "Fix\n\n\U0001F916 Generated with Claude Code\n",
        "Use claude to draft memo\n",
    ]:
        assert hook_rc(tmp_path, bad) == 1, bad


@pytest.mark.parametrize("name", ["cleaned_data", "findings", "themes"])
def test_contracts_and_examples(name):
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads((ROOT / f"contracts/{name}.schema.json").read_text())
    jsonschema.Draft202012Validator.check_schema(schema)
    example = ROOT / f"contracts/examples/{name}.example.json"
    if example.exists():
        jsonschema.validate(json.loads(example.read_text()), schema)
