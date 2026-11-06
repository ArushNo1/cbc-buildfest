#!/usr/bin/env python3
"""Assemble submission/ from built files, then run verify. Agents never submit the form (hard rule 5).
Rendering drafts -> agents/narrative/build/*.pdf|pptx is a separate step (narrative, M2)."""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "Team17_Memo.pdf": "agents/narrative/build/Team17_Memo.pdf",
    "Team17_AIAppendix.pdf": "agents/narrative/build/Team17_AIAppendix.pdf",
    "Team17_Presentation.pptx": "agents/narrative/build/Team17_Presentation.pptx",
    "Team17_Demo.mp4": "agents/tool/dist/Team17_Demo.mp4",
    "Team17_TechnicalArtifact.zip": "agents/tool/dist/Team17_TechnicalArtifact.zip",
    "Team17_TechnicalArtifact.txt": "agents/tool/dist/Team17_TechnicalArtifact.txt",
}

(ROOT / "submission").mkdir(exist_ok=True)
for dst, src in SOURCES.items():
    if (ROOT / src).exists():
        shutil.copyfile(ROOT / src, ROOT / "submission" / dst)  # copyfile: no source metadata carried over
        print(f"copied {src} -> submission/{dst}")
    else:
        print(f"not built yet: {src}")
sys.exit(subprocess.run([sys.executable, str(ROOT / "scripts/verify.py")]).returncode)
