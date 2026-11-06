#!/usr/bin/env python3
"""Every number tagged [F:id] in drafts must match outputs/findings.json or outputs/themes.json as displayed.

Tag syntax (number right before the tag):
    78% [F:post.identify_crisis.agree_pct.overall]
    n=1,041 [F:post.identify_crisis.agree_pct.overall#n]
Fields after '#': value (default), n, numerator, n_missing, ci_low, ci_high; for themes also pct, n_mentions.
"As displayed" = within half a unit of the last shown digit. Any percentage without a tag also fails.
Usage: check_numbers.py [files...]   (default: agents/narrative/drafts/*.md, agents/tool/video/script.md)
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GLOBS = ["agents/narrative/drafts/*.md", "agents/tool/video/script.md"]
TAGGED = re.compile(r"(-?\d[\d,]*(?:\.\d+)?)\s*(?:%|points?|pts)?\s*\[F:([a-z0-9_.]+)(?:#([a-z_]+))?\]")
PCT_UNTAGGED = re.compile(r"\d[\d,]*(?:\.\d+)?\s*%(?!\s*\[F:)")


def load_index(root=ROOT):
    idx = {}
    f = root / "outputs/findings.json"
    if f.exists():
        idx.update({x["id"]: x for x in json.loads(f.read_text(encoding="utf-8"))["findings"]})
    t = root / "outputs/themes.json"
    if t.exists():
        idx.update({x["id"]: {**x, "value": x["pct"]} for x in json.loads(t.read_text(encoding="utf-8"))["counts"]})
    return idx


def check_text(text, idx, name="<text>"):
    errors = []
    line = lambda pos: text.count("\n", 0, pos) + 1
    for m in TAGGED.finditer(text):
        shown, fid, field = m.group(1), m.group(2), m.group(3) or "value"
        where = f"{name}:{line(m.start())}"
        if fid not in idx:
            errors.append(f"{where}: unknown ID {fid}")
            continue
        actual = idx[fid].get(field)
        if actual is None:
            errors.append(f"{where}: {fid}#{field} is null (suppressed/missing) but shown as {shown}")
            continue
        decimals = len(shown.split(".")[1]) if "." in shown else 0
        if abs(float(actual) - float(shown.replace(",", ""))) > 0.5 * 10 ** -decimals + 1e-9:
            errors.append(f"{where}: shows {shown} but {fid}#{field} = {actual}")
    for m in PCT_UNTAGGED.finditer(text):
        errors.append(f"{name}:{line(m.start())}: untagged percentage '{m.group(0).strip()}'")
    return errors


def main(argv):
    files = [Path(a) for a in argv] or [p for g in DEFAULT_GLOBS for p in sorted(ROOT.glob(g))]
    if not files:
        print("check_numbers: no drafts yet")
        return 0
    idx = load_index()
    errors = [e for f in files for e in check_text(f.read_text(encoding="utf-8"), idx, str(f))]
    for e in errors:
        print("FAIL", e, file=sys.stderr)
    print(f"check_numbers: {len(files)} file(s), {len(errors)} problem(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
