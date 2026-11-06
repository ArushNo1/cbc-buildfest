"""Assemble site/ (static, Vercel-ready): the current dashboard plus the unchanged
pipeline code, which re-runs in the browser via Pyodide when staff drop in a new export.
Aggregates and code only; no row-level data is copied."""
import json, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site"
APP = [
    "agents/data/pipeline.py", "agents/data/mappings/*.json",
    "agents/text/themes.py", "agents/text/validation_summary.json",
    "agents/tool/build.py", "agents/tool/web/*",
    "contracts/*.json", "scripts/site/run.py",
]

if __name__ == "__main__":
    shutil.rmtree(OUT, ignore_errors=True)
    files = sorted({p.relative_to(ROOT).as_posix() for g in APP for p in ROOT.glob(g) if p.is_file()})
    for f in files:
        (OUT / "app" / f).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / f, OUT / "app" / f)
    (OUT / "app/manifest.json").write_text(json.dumps(files, indent=1))
    shutil.copy2(ROOT / "outputs/dashboard.html", OUT / "dashboard.html")
    shutil.copy2(ROOT / "scripts/site/index.html", OUT / "index.html")
    print(f"site: {len(files)} app files -> {OUT}")
