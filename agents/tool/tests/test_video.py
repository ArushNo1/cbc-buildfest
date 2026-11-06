"""Video pipeline tests that need no browser, ffmpeg or TTS."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("make_video", ROOT / "agents/tool/video/make_video.py")
mv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mv)

SAMPLE = """# title
intro text is ignored
## One
shot: top
> First line with 92% [F:post.know_when_to_use.agree_pct.overall] agreeing.
> Second line.
## Two
shot: compare metric=recommend.score.mean dim=role
> Students 7.2 [F:recommend.score.mean.role.student].
## Empty
shot: #notes
"""


def test_parse_strips_tags_and_skips_empty_scenes():
    scenes = mv.parse_script(SAMPLE)
    assert [s["title"] for s in scenes] == ["One", "Two"]
    assert scenes[0]["text"] == "First line with 92% agreeing. Second line."
    assert "[F:" in scenes[0]["tagged"] and "[F:" not in scenes[1]["text"]


def test_shots():
    assert mv.parse_shot("top") == ["scroll", "top", 0, None, None]
    assert mv.parse_shot("#notes+520") == ["scroll", "#notes", 520, None, None]
    assert mv.parse_shot("compare metric=a.b.c dim=role") == ["compare", "#compare", 0, "a.b.c", "role"]


def test_captions_are_short_and_cover_all_words():
    text = mv.parse_script((ROOT / "agents/tool/video/script.md").read_text(encoding="utf-8"))[2]["text"]
    chunks = mv.caption_chunks(text)
    assert all(len(c) <= 100 for c in chunks)
    assert " ".join(chunks).split() == text.split()


def test_speech_text_spells_988():
    assert mv.speech_text("call 988 now, 1988 stays") == "call nine eight eight now, 1988 stays"


def test_plan_and_srt_without_tts(tmp_path):
    scenes = mv.parse_script(SAMPLE)
    mv.synthesize(scenes, tmp_path, "x", 180, tts=False)
    total = mv.plan(scenes)
    assert scenes[0]["start_s"] == mv.LEAD_IN_S
    assert scenes[1]["start_s"] > scenes[0]["start_s"] + scenes[0]["speech_s"]
    assert total < mv.LIMIT_S
    out = mv.srt(scenes)
    assert out.startswith("1\n00:00:00,800 --> ") and "Students 7.2." in out


def test_committed_script_numbers_match_and_fit_the_limit(tmp_path):
    text = (ROOT / "agents/tool/video/script.md").read_text(encoding="utf-8")
    if (ROOT / "outputs/findings.json").exists():
        mv.check_numbers(text, "script.md")  # raises on any mismatch
    scenes = mv.parse_script(text)
    mv.synthesize(scenes, tmp_path, "x", 180, tts=False)
    assert mv.plan(scenes) <= mv.TARGET_MAX_S
