"""Runs the unchanged pipeline -> themes -> dashboard inside Pyodide (files mounted at /app)."""
import runpy, sys


def step(path, *args):
    sys.argv = [path, *args]
    try:
        runpy.run_path(path, run_name="__main__")
    except SystemExit as e:
        if e.code not in (0, None):
            raise RuntimeError(f"{path.rsplit('/', 1)[-1]} stopped: {e.code}")


def run(xlsx):
    step("/app/agents/data/pipeline.py", "--data", xlsx)
    step("/app/agents/text/themes.py")
    step("/app/agents/tool/build.py")
    return open("/app/outputs/dashboard.html", encoding="utf-8").read()
