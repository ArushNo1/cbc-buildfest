"""The presentation builds from agents/narrative/drafts/deck.md into a clean, finished deck."""
import importlib.util
import re
import zipfile
from pathlib import Path

from pptx import Presentation

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("deck_build", ROOT / "scripts/deck_build.py")
deck_build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deck_build)


def test_deck_builds_finished_slides(tmp_path):
    md = (ROOT / "agents/narrative/drafts/deck.md").read_text(encoding="utf-8")
    out = tmp_path / "deck.pptx"
    deck_build.build(md, out)
    prs = Presentation(str(out))
    assert len(prs.slides) == len(re.findall(r"^## ", md, re.M))
    for i, slide in enumerate(prs.slides, start=1):
        text = " ".join(sh.text_frame.text for sh in slide.shapes if sh.has_text_frame)
        assert "[F:" not in text, f"slide {i}: citation tag left in slide text"
        assert not re.search(r"#\d{2}\b|\bTODO\b|lorem", text, re.I), f"slide {i}: internal note or placeholder"
        assert slide.shapes.title.text_frame.text.strip(), f"slide {i}: no title"
        for sh in slide.shapes:
            if sh.shape_type == 13:  # picture
                assert sh._element.nvPicPr.cNvPr.get("descr"), f"slide {i}: picture without alt text"
    core = zipfile.ZipFile(out).read("docProps/core.xml").decode()
    assert "<dc:creator></dc:creator>" in core or "<dc:creator/>" in core
