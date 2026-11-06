#!/usr/bin/env python3
"""Submission checks: exact filenames, memo <=2 pages, appendix exactly 1 page, mp4 <=120 s, pptx (not pdf),
metadata scrubbed, no identity strings, no data in the artifact zip, check_numbers. Prints every problem; exit 1 if any.

Identity strings = team git names/emails from history + umd/terpmail + the optional gitignored file
.identity_strings (one real name per line; never commit it). Needs pypdf and ffprobe.
SUBMISSION_DIR overrides submission/ (for testing).
"""
import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUB = Path(os.environ.get("SUBMISSION_DIR", ROOT / "submission"))
REQUIRED = {"Team17_Memo.pdf", "Team17_AIAppendix.pdf", "Team17_Presentation.pptx", "Team17_Demo.mp4"}
ARTIFACT = {"Team17_TechnicalArtifact.zip", "Team17_TechnicalArtifact.txt"}  # .txt holds the link
DATA_MEMBER = re.compile(r"^(?:[^/]+/)?data/|(^|/)\.git/|\.(xlsx|xlsm|xls|csv|tsv|parquet|feather|sav|dta|sqlite|db)$|identity_strings", re.I)
SERVICE_IDS = {"github", "noreply@github.com", "noreply", "web-flow"}
TEAM_OK = re.compile(r"^\s*(team\s*17)?\s*$", re.I)  # empty or "Team 17" is fine in author fields


def identity_patterns():
    log = subprocess.run(["git", "log", "--format=%an%n%ae"], cwd=ROOT, capture_output=True, text=True).stdout
    ids = set()
    for s in (x.strip() for x in log.splitlines()):
        ids.add(s)
        if "@" in s:
            ids.add(re.sub(r"^\d+\+", "", s.split("@")[0]))
    extra = ROOT / ".identity_strings"
    if extra.exists():
        ids.update(x.strip() for x in extra.read_text(encoding="utf-8").splitlines())
    ids = {i for i in ids if len(i) >= 4 and not i.startswith("#") and i.lower() not in SERVICE_IDS}
    return [re.compile(re.escape(i), re.I) for i in sorted(ids)] + [re.compile(r"\bumd\b|terpmail", re.I)]


def identity_hits(text, pats):
    return sorted({m.group(0) for p in pats for m in p.finditer(text)})


def check_pdf(path, pages_ok, rule, pats, problems):
    from pypdf import PdfReader
    r = PdfReader(path)
    if not pages_ok(len(r.pages)):
        problems.append(f"{path.name}: {len(r.pages)} pages, must be {rule}")
    meta = r.metadata or {}
    if not TEAM_OK.match(str(meta.get("/Author") or "")):
        problems.append(f"{path.name}: PDF Author metadata = {meta.get('/Author')!r}; clear it")
    blob = " ".join(str(v) for v in meta.values())
    xmp = r.trailer["/Root"].get("/Metadata")
    if xmp is not None:
        blob += xmp.get_object().get_data().decode("utf-8", "ignore")
    blob += "\n".join(p.extract_text() or "" for p in r.pages)
    problems += [f"{path.name}: identity string {h!r} (text or metadata)" for h in identity_hits(blob, pats)]


def check_pptx(path, pats, problems):
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        core = z.read("docProps/core.xml").decode("utf-8", "ignore") if "docProps/core.xml" in names else ""
        for tag in ("dc:creator", "cp:lastModifiedBy"):
            m = re.search(fr"<{tag}>(.*?)</{tag}>", core, re.S)
            if m and not TEAM_OK.match(m.group(1)):
                problems.append(f"{path.name}: {tag} = {m.group(1)!r}; clear it")
        if any("commentAuthors" in n for n in names):
            problems.append(f"{path.name}: has comment authors; remove comments")
        blob = " ".join(z.read(n).decode("utf-8", "ignore") for n in names if n.endswith((".xml", ".rels")))
    problems += [f"{path.name}: identity string {h!r}" for h in identity_hits(blob, pats)]


def check_mp4(path, pats, problems):
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration:format_tags", "-of", "json", str(path)]
    try:
        fmt = json.loads(subprocess.run(cmd, capture_output=True, text=True, check=True).stdout)["format"]
    except (OSError, subprocess.CalledProcessError, ValueError, KeyError) as e:
        problems.append(f"{path.name}: ffprobe failed ({e})")
        return
    if float(fmt.get("duration", 0)) > 120:
        problems.append(f"{path.name}: {float(fmt['duration']):.1f} s, max 120 s")
    tags = fmt.get("tags", {})
    for k in ("artist", "author", "composer", "album_artist", "copyright"):
        if not TEAM_OK.match(str(tags.get(k, ""))):
            problems.append(f"{path.name}: metadata {k} = {tags[k]!r}; clear it")
    problems += [f"{path.name}: identity string {h!r} in metadata" for h in identity_hits(json.dumps(tags), pats)]


def check_zip(path, pats, problems):
    with zipfile.ZipFile(path) as z:
        for info in z.infolist():
            if DATA_MEMBER.search(info.filename):
                problems.append(f"{path.name}: must not contain {info.filename}")
            elif not info.is_dir() and info.file_size < 5_000_000:
                for h in identity_hits(z.read(info).decode("utf-8", "ignore"), pats):
                    problems.append(f"{path.name}: identity string {h!r} in {info.filename}")


def main():
    problems = []
    pats = identity_patterns()
    files = {p.name: p for p in SUB.iterdir() if p.is_file() and p.name != ".gitkeep"} if SUB.exists() else {}
    for n in sorted(set(files) - REQUIRED - ARTIFACT):
        problems.append(f"unexpected file in submission/: {n} (exact names only; deck is .pptx only)")
    problems += [f"missing: {n}" for n in sorted(REQUIRED - set(files))]
    if not set(files) & ARTIFACT:
        problems.append("missing: Team17_TechnicalArtifact.zip (or .txt with the link)")
    checks = {
        "Team17_Memo.pdf": lambda p: check_pdf(p, lambda n: 1 <= n <= 2, "1-2", pats, problems),
        "Team17_AIAppendix.pdf": lambda p: check_pdf(p, lambda n: n == 1, "exactly 1", pats, problems),
        "Team17_Presentation.pptx": lambda p: check_pptx(p, pats, problems),
        "Team17_Demo.mp4": lambda p: check_mp4(p, pats, problems),
        "Team17_TechnicalArtifact.zip": lambda p: check_zip(p, pats, problems),
        "Team17_TechnicalArtifact.txt": lambda p: problems.extend(
            f"{p.name}: identity string {h!r}" for h in identity_hits(p.read_text(encoding="utf-8"), pats)),
    }
    for name, fn in checks.items():
        if name in files:
            try:
                fn(files[name])
            except Exception as e:  # a corrupt file is a finding, not a crash
                problems.append(f"{name}: could not be read ({type(e).__name__}: {e})")
    if subprocess.run([sys.executable, str(ROOT / "scripts/check_numbers.py")]).returncode:
        problems.append("check_numbers failed (see above)")
    for p in problems:
        print("FAIL", p, file=sys.stderr)
    print(f"verify: {len(problems)} problem(s) in {SUB}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
