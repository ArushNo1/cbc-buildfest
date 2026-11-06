#!/usr/bin/env python3
"""Package the technical artifact: agents/tool/dist/Team17_TechnicalArtifact.zip

- Only git-tracked files, from an allow-list (code, contracts, outputs, run docs, fixture generator, tests).
- Never data/, never row-level files, never .git/, never agent ROLE files or local notes.
- Every text file is scanned with the same identity patterns as scripts/verify.py before the zip is written.
- Reproducible: sorted entries, fixed timestamps and permissions, so the same commit gives the same bytes.

Usage:
    python3 agents/tool/package.py                       # build the zip
    python3 agents/tool/package.py --smoke DATA=path.xlsx  # also unzip to a temp dir and run make run + make test there
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "agents" / "tool" / "dist" / "Team17_TechnicalArtifact.zip"
TOP = "Team17_TechnicalArtifact"
FIXED_TIME = (2026, 11, 8, 0, 0, 0)

INCLUDE = (
    "Makefile", "requirements.txt", ".gitignore",
    "agents/data/", "agents/text/", "agents/tool/",
    "agents/narrative/crosscheck/", "agents/narrative/fixtures/", "agents/narrative/tests/",
    "contracts/", "outputs/",
    "scripts/hooks/", "scripts/check_numbers.py",
    "tests/test_repo_",
)
EXCLUDE = re.compile(
    r"(^|/)ROLE\.md$|^agents/tool/dist/|(^|/)__pycache__/|\.pyc$|^tests/fixtures/|(^|/)\.DS_Store$"
    r"|\.(xlsx|xlsm|xls|csv|tsv|parquet|feather|sav|dta|sqlite|db)$|identity_strings"
)
# Top-level data/ or any .git/ — but NOT agents/data/ (that is pipeline code).
DATA_MEMBER = re.compile(r"^data/|(^|/)\.git/")


def tracked_files() -> list[str]:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True).stdout
    return sorted(p for p in out.decode("utf-8").split("\0") if p)


def select(files: list[str]) -> list[str]:
    keep = [f for f in files if f.startswith(INCLUDE) and not EXCLUDE.search(f) and not DATA_MEMBER.search(f)]
    return [f for f in keep if (ROOT / f).is_file()]


def identity_patterns():
    spec = importlib.util.spec_from_file_location("verify", ROOT / "scripts" / "verify.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.identity_patterns(), mod.identity_hits


def readme_text() -> str:
    run = (ROOT / "agents" / "tool" / "RUN.md").read_text(encoding="utf-8")
    head = ("# Team 17 technical artifact\n\n"
            "Turns the EveryMind post-training survey export into checked numbers (`outputs/findings.json`), "
            "coded comment themes (`outputs/themes.json`) and a self-contained dashboard (`outputs/dashboard.html`). "
            "Open `outputs/dashboard.html` in any browser to see the results without running anything. "
            "The survey data itself is not included; put the export in `data/raw/` to rebuild.\n\n"
            "Code map: `agents/data/` cleaning and statistics · `agents/text/` comment themes · "
            "`agents/tool/` dashboard · `agents/narrative/crosscheck/` independent recompute · "
            "`agents/narrative/fixtures/` synthetic test workbooks · `contracts/` file formats.\n\n")
    return head + run.split("\n", 1)[1].lstrip()


def build(out: Path) -> list[str]:
    files = select(tracked_files())
    pats, hits_fn = identity_patterns()
    problems = []
    blobs: dict[str, bytes] = {}
    for f in files:
        data = (ROOT / f).read_bytes()
        blobs[f] = data
        for h in hits_fn(data.decode("utf-8", "ignore"), pats):
            problems.append(f"identity string {h!r} in {f}")
    readme = readme_text().encode("utf-8")
    for h in hits_fn(readme.decode("utf-8"), pats):
        problems.append(f"identity string {h!r} in README.md")
    if problems:
        raise SystemExit("package: refusing to write the zip:\n  " + "\n  ".join(problems))
    missing = [p for p in ("agents/data/pipeline.py", "agents/text/themes.py", "agents/tool/build.py",
                           "outputs/findings.json", "outputs/themes.json", "outputs/dashboard.html") if p not in blobs]
    if missing:
        raise SystemExit("package: required files are not tracked in git: " + ", ".join(missing))

    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".zip.tmp")
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        entries = [("README.md", readme)] + [(f, blobs[f]) for f in files]
        for name, data in sorted(entries):
            info = zipfile.ZipInfo(f"{TOP}/{name}", date_time=FIXED_TIME)
            executable = name.startswith("scripts/hooks/") or name.endswith(".sh")
            info.external_attr = (0o755 if executable else 0o644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data)
    tmp.replace(out)
    return ["README.md"] + files


def smoke(zip_path: Path, data: Path) -> int:
    """Unzip into an empty folder (no git), then run the documented commands there."""
    with tempfile.TemporaryDirectory(prefix="t17_artifact_") as d:
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(d)
        top = Path(d) / TOP
        raw = top / "data" / "raw"
        raw.mkdir(parents=True)
        shutil.copy2(data, raw / data.name)
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        steps = [["make", "run", f"DATA=data/raw/{data.name}"], ["make", "test"]]
        for cmd in steps:
            print(f"package: smoke: {' '.join(cmd)}", flush=True)
            r = subprocess.run(cmd, cwd=top, env=env, capture_output=True, text=True)
            tail = "\n".join((r.stdout + r.stderr).strip().splitlines()[-6:])
            print("  " + tail.replace("\n", "\n  "))
            if r.returncode != 0:
                print(f"package: smoke FAILED at `{' '.join(cmd)}` (exit {r.returncode})", file=sys.stderr)
                return 1
        for rel in ("outputs/findings.json", "outputs/dashboard.html"):
            a, b = (top / rel).read_bytes(), (ROOT / rel).read_bytes()
            same = "identical to" if a == b else "DIFFERENT from"
            print(f"package: smoke: rebuilt {rel} is {same} the committed file")
    print("package: smoke OK")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--out", type=Path, default=OUT)
    p.add_argument("--smoke", metavar="DATA=path.xlsx", default=None,
                   help="after building, unzip to a temp dir and run `make run` + `make test` there")
    args = p.parse_args(argv)
    names = build(args.out)
    size = args.out.stat().st_size
    rel = args.out.relative_to(ROOT) if args.out.is_relative_to(ROOT) else args.out
    print(f"package: {len(names)} files, {size / 1024:.0f} KB -> {rel}")
    if args.smoke:
        data = Path(args.smoke.split("=", 1)[-1]).expanduser()
        if not data.exists():
            print(f"package: --smoke data file not found: {data}", file=sys.stderr)
            return 1
        return smoke(args.out, data.resolve())
    return 0


if __name__ == "__main__":
    sys.exit(main())
