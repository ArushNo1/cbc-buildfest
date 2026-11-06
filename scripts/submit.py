#!/usr/bin/env python3
"""Assemble submission/: render the drafts (memo, appendix, deck), copy the tool's zip and mp4, then run verify.
Agents never submit the form (hard rule 5)."""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Memo, appendix and deck are rendered straight into submission/ by scripts/render.py (run first, below).
SOURCES = {
    "Team17_Demo.mp4": "agents/tool/dist/Team17_Demo.mp4",
    "Team17_TechnicalArtifact.zip": "agents/tool/dist/Team17_TechnicalArtifact.zip",
    "Team17_TechnicalArtifact.txt": "agents/tool/dist/Team17_TechnicalArtifact.txt",
}

(ROOT / "submission").mkdir(exist_ok=True)
if subprocess.run([sys.executable, str(ROOT / "scripts/render.py")]).returncode != 0:
    sys.exit("submit: rendering the drafts failed")
for dst, src in SOURCES.items():
    if (ROOT / src).exists():
        shutil.copyfile(ROOT / src, ROOT / "submission" / dst)  # copyfile: no source metadata carried over
        print(f"copied {src} -> submission/{dst}")
    else:
        print(f"not built yet: {src}")
sys.exit(subprocess.run([sys.executable, str(ROOT / "scripts/verify.py")]).returncode)
