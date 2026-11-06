#!/usr/bin/env python3
"""Make the demo video (agents/tool/dist/Team17_Demo.mp4, <= 120 s) from the dashboard and the narration script.

Pipeline:
  1. Parse agents/tool/video/script.md into scenes (shot + narration) and check every tagged number
     against outputs/findings.json / themes.json (scripts/check_numbers.py). A mismatch stops the build.
  2. Text-to-speech per scene with macOS `say` (or --no-tts: silent, timed by word count).
  3. Plan the timeline and captions; refuse if the total exceeds the limit.
  4. Drive outputs/dashboard.html in headless Chromium (Playwright), record 1280x720, scroll/select per
     scene, and draw the captions into the page (so ffmpeg needs no subtitle support).
  5. ffmpeg: trim the page-load lead-in, lay each scene's audio at the scene's real start time, encode
     H.264/AAC, strip metadata. Also writes a .srt caption file next to the mp4.

Usage:
  python3 agents/tool/video/make_video.py                 # full build
  python3 agents/tool/video/make_video.py --dry-run       # steps 1-3 only (no browser, no ffmpeg)
Needs: Playwright + Chromium (`python3 -m pip install playwright && python3 -m playwright install chromium`)
and ffmpeg on PATH (or `python3 -m pip install imageio-ffmpeg`).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "script.md"
DASHBOARD = ROOT / "outputs" / "dashboard.html"
DIST = ROOT / "agents" / "tool" / "dist"
OUT = DIST / "Team17_Demo.mp4"
LIMIT_S = 120.0
TARGET_MAX_S = 117.0          # keep a margin under the hard limit
LEAD_IN_S = 0.8               # silence before the first line
GAP_S = 0.45                  # pause after each scene's narration
WORDS_PER_S = 2.6             # timing estimate when there is no TTS
VIEW = {"width": 1280, "height": 720}
TAG = re.compile(r"\s*\[F:[^\]]+\]")
# Spoken form only; captions keep the written form.
SPEECH = [(re.compile(r"\b988\b"), "nine eight eight")]


def speech_text(text: str) -> str:
    for pat, rep in SPEECH:
        text = pat.sub(rep, text)
    return text


class VideoError(Exception):
    pass


# ----------------------------------------------------------------------------- script

def parse_script(text: str) -> list[dict]:
    scenes, cur = [], None
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith("## "):
            cur = {"title": line[3:].strip(), "shot": "top", "tagged": []}
            scenes.append(cur)
        elif cur is not None and line.lower().startswith("shot:"):
            cur["shot"] = line.split(":", 1)[1].strip()
        elif cur is not None and line.startswith(">"):
            cur["tagged"].append(line[1:].strip())
    out = []
    for s in scenes:
        tagged = " ".join(x for x in s["tagged"] if x)
        if not tagged:
            continue
        spoken = re.sub(r"\s+", " ", TAG.sub("", tagged)).strip()
        out.append({"title": s["title"], "shot": s["shot"], "tagged": tagged, "text": spoken})
    if not out:
        raise VideoError("no scenes with narration found in the script")
    return out


def check_numbers(script_text: str, name: str) -> None:
    spec = importlib.util.spec_from_file_location("check_numbers", ROOT / "scripts" / "check_numbers.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    errors = mod.check_text(script_text, mod.load_index(), name)
    if errors:
        raise VideoError("narration numbers don't match findings/themes:\n  " + "\n  ".join(errors))


def caption_chunks(text: str, max_chars: int = 88) -> list[str]:
    """Split narration into caption cards: one card per sentence; a long sentence is cut into
    near-equal parts on word boundaries (no tiny leftovers)."""
    sentences = [x for x in re.split(r"(?<=[.!?])\s+", text.strip()) if x]
    chunks: list[str] = []
    for sent in sentences:
        if len(sent) <= max_chars:
            chunks.append(sent)
            continue
        parts = -(-len(sent) // max_chars)
        target = len(sent) / parts
        line = ""
        for w in sent.split():
            if line and len(line) >= target * 0.92 and len(chunks) < 10_000:
                chunks.append(line)
                line = w
            else:
                line = f"{line} {w}".strip()
        if line:
            chunks.append(line)
    return chunks


# ----------------------------------------------------------------------------- audio

def audio_duration(path: Path) -> float:
    if shutil.which("afinfo"):
        out = subprocess.run(["afinfo", str(path)], capture_output=True, text=True).stdout
        m = re.search(r"estimated duration:\s*([\d.]+)", out)
        if m:
            return float(m.group(1))
    ffprobe = shutil.which("ffprobe")
    if ffprobe:
        out = subprocess.run([ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                             capture_output=True, text=True).stdout.strip()
        if out:
            return float(out)
    raise VideoError(f"can't read the duration of {path} (needs afinfo or ffprobe)")


def synthesize(scenes: list[dict], work: Path, voice: str, rate: int, tts: bool) -> None:
    if tts and not shutil.which("say"):
        raise VideoError("`say` (macOS text-to-speech) not found; rerun with --no-tts for a captions-only video")
    for i, s in enumerate(scenes):
        if tts:
            wav = work / f"scene_{i:02d}.aiff"
            subprocess.run(["say", "-v", voice, "-r", str(rate), "-o", str(wav), speech_text(s["text"])], check=True)
            s["audio"] = str(wav)
            s["speech_s"] = audio_duration(wav)
        else:
            s["audio"] = None
            s["speech_s"] = round(len(s["text"].split()) / WORDS_PER_S, 2)


def plan(scenes: list[dict]) -> float:
    t = LEAD_IN_S
    for s in scenes:
        s["start_s"] = round(t, 3)
        s["dur_s"] = round(s["speech_s"] + GAP_S, 3)
        chunks = caption_chunks(s["text"])
        total_chars = sum(len(c) for c in chunks) or 1
        at, caps = 0.0, []
        for c in chunks:
            d = s["speech_s"] * len(c) / total_chars
            caps.append({"text": c, "at_s": round(at, 3), "dur_s": round(d, 3)})
            at += d
        s["captions"] = caps
        t += s["dur_s"]
    return round(t + 0.6, 3)


def srt(scenes: list[dict]) -> str:
    def ts(x: float) -> str:
        ms = int(round(x * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    lines, k = [], 1
    for s in scenes:
        for c in s["captions"]:
            a = s["start_s"] + c["at_s"]
            lines += [str(k), f"{ts(a)} --> {ts(a + c['dur_s'])}", c["text"], ""]
            k += 1
    return "\n".join(lines)


# ----------------------------------------------------------------------------- capture

OVERLAY_JS = """
() => {
  const s = document.createElement('style');
  s.textContent = `#demo-cap{position:fixed;left:50%;bottom:28px;transform:translateX(-50%);max-width:1080px;width:max-content;
    background:rgba(11,11,11,.84);color:#fff;font:600 25px/1.35 system-ui,-apple-system,"Segoe UI",sans-serif;
    padding:12px 20px;border-radius:12px;text-align:center;z-index:9999;box-shadow:0 6px 24px rgba(0,0,0,.25)}
    #demo-cap:empty{display:none} #tip{display:none!important} html{scroll-behavior:auto}`;
  document.head.appendChild(s);
  const d = document.createElement('div'); d.id = 'demo-cap'; d.setAttribute('aria-hidden','true');
  document.body.appendChild(d);
}
"""
SHOT_JS = """
([kind, target, offset, metric, dim]) => {
  const tip = document.getElementById('tip'); if (tip) tip.hidden = true;
  if (kind === 'compare') {
    const m = document.getElementById('cmp-metric'), d = document.getElementById('cmp-dim');
    if (!m || ![...m.options].some(o => o.value === metric)) return 'missing metric ' + metric;
    m.value = metric; m.dispatchEvent(new Event('change'));
    if (dim) { if (![...d.options].some(o => o.value === dim)) return 'missing dim ' + dim; d.value = dim; d.dispatchEvent(new Event('change')); }
    target = '#compare';
  }
  let y = 0;
  if (target && target !== 'top') {
    const el = document.querySelector(target);
    if (!el) return 'missing ' + target;
    y = el.getBoundingClientRect().top + window.scrollY - 12 + (offset || 0);
  }
  window.scrollTo({ top: y, behavior: 'smooth' });
  return 'ok';
}
"""


def parse_shot(shot: str) -> list:
    shot = shot.strip()
    if shot.startswith("compare"):
        kv = dict(x.split("=", 1) for x in shot.split()[1:] if "=" in x)
        return ["compare", "#compare", 0, kv.get("metric"), kv.get("dim")]
    m = re.fullmatch(r"(#[\w-]+)(?:\+(\d+))?", shot)
    if m:
        return ["scroll", m.group(1), int(m.group(2) or 0), None, None]
    return ["scroll", "top", 0, None, None]


def capture(scenes: list[dict], dashboard: Path, work: Path) -> tuple[Path, float]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise VideoError("Playwright is not installed: python3 -m pip install playwright && python3 -m playwright install chromium") from None
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception as e:  # noqa: BLE001 - surface the install hint
            raise VideoError(f"can't start headless Chromium ({e.__class__.__name__}). Run: python3 -m playwright install chromium") from None
        ctx = browser.new_context(viewport=VIEW, device_scale_factor=1, color_scheme="light", reduced_motion="no-preference",
                                  record_video_dir=str(work), record_video_size=VIEW)
        t0 = time.monotonic()
        page = ctx.new_page()
        page.goto(dashboard.resolve().as_uri())
        page.wait_for_load_state("load")
        page.evaluate(OVERLAY_JS)
        page.wait_for_timeout(300)
        lead = time.monotonic() - t0
        for s in scenes:
            # wait until this scene's planned start, then record when it really started
            target = lead + s["start_s"]
            now = time.monotonic() - t0
            if target > now:
                page.wait_for_timeout(int((target - now) * 1000))
            s["real_start_s"] = round(time.monotonic() - t0 - lead, 3)
            res = page.evaluate(SHOT_JS, parse_shot(s["shot"]))
            if res != "ok":
                ctx.close(); browser.close()
                raise VideoError(f"scene '{s['title']}': shot `{s['shot']}` failed ({res})")
            for c in s["captions"]:
                due = lead + s["real_start_s"] + c["at_s"]
                now = time.monotonic() - t0
                if due > now:
                    page.wait_for_timeout(int((due - now) * 1000))
                page.evaluate("(t) => { document.getElementById('demo-cap').textContent = t; }", c["text"])
            end = lead + s["real_start_s"] + s["dur_s"]
            now = time.monotonic() - t0
            if end > now:
                page.wait_for_timeout(int((end - now) * 1000))
            page.evaluate("() => { document.getElementById('demo-cap').textContent = ''; }")
        page.wait_for_timeout(700)
        video = Path(page.video.path())
        ctx.close()
        browser.close()
    return video, lead


# ----------------------------------------------------------------------------- encode

def ffmpeg_exe() -> str:
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        raise VideoError("ffmpeg not found: `brew install ffmpeg` or `python3 -m pip install imageio-ffmpeg`") from None


def encode(video: Path, lead: float, scenes: list[dict], total: float, out: Path) -> None:
    ff = ffmpeg_exe()
    cmd = [ff, "-y", "-v", "error", "-ss", f"{lead:.3f}", "-i", str(video)]
    voiced = [s for s in scenes if s.get("audio")]
    for s in voiced:
        cmd += ["-i", s["audio"]]
    if voiced:
        parts = []
        for k, s in enumerate(voiced, start=1):
            d = int(round(s.get("real_start_s", s["start_s"]) * 1000))
            parts.append(f"[{k}:a]aresample=48000,adelay={d}|{d}[a{k}]")
        mix = "".join(f"[a{k}]" for k in range(1, len(voiced) + 1))
        parts.append(f"{mix}amix=inputs={len(voiced)}:normalize=0,apad[aout]")
        cmd += ["-filter_complex", ";".join(parts), "-map", "0:v", "-map", "[aout]", "-c:a", "aac", "-b:a", "160k"]
    else:
        cmd += ["-map", "0:v", "-an"]
    cmd += ["-t", f"{total:.3f}", "-r", "30", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
            "-preset", "medium", "-map_metadata", "-1", "-metadata", "title=", "-metadata", "encoder=",
            "-fflags", "+bitexact", "-flags:v", "+bitexact", "-movflags", "+faststart", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise VideoError("ffmpeg failed:\n" + r.stderr[-2000:])


def probe_duration(path: Path) -> float | None:
    ff = shutil.which("ffprobe")
    if ff:
        out = subprocess.run([ff, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                             capture_output=True, text=True).stdout.strip()
        if out:
            return float(out)
    # No ffprobe (e.g. imageio-ffmpeg): ffmpeg prints "Duration: HH:MM:SS.ss" when given only an input.
    err = subprocess.run([ffmpeg_exe(), "-hide_banner", "-i", str(path)], capture_output=True, text=True).stderr
    m = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", err)
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)) if m else None


# ----------------------------------------------------------------------------- main

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Build the demo video from the dashboard and the narration script")
    ap.add_argument("--script", type=Path, default=SCRIPT)
    ap.add_argument("--dashboard", type=Path, default=DASHBOARD)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--voice", default="Samantha")
    ap.add_argument("--rate", type=int, default=182, help="words per minute for `say`")
    ap.add_argument("--no-tts", action="store_true", help="captions only, no narration audio")
    ap.add_argument("--dry-run", action="store_true", help="check numbers, time the narration, write captions; no capture")
    ap.add_argument("--allow-example", action="store_true", help="allow a dashboard stamped EXAMPLE DATA (never for the final video)")
    ap.add_argument("--keep", action="store_true", help="keep the work folder (raw webm, audio) for inspection")
    args = ap.parse_args(argv)

    work = Path(tempfile.mkdtemp(prefix="t17_video_"))
    try:
        text = args.script.read_text(encoding="utf-8")
        check_numbers(text, str(args.script))
        scenes = parse_script(text)
        synthesize(scenes, work, args.voice, args.rate, not args.no_tts)
        total = plan(scenes)
        for s in scenes:
            print(f"video: {s['start_s']:6.1f}s  {s['dur_s']:5.1f}s  {s['title']}  [{s['shot']}]")
        print(f"video: planned length {total:.1f}s (limit {LIMIT_S:.0f}s)")
        if total > TARGET_MAX_S:
            raise VideoError(f"narration runs {total:.1f}s; cut words until it is under {TARGET_MAX_S:.0f}s")
        args.out.parent.mkdir(parents=True, exist_ok=True)
        srt_path = args.out.with_suffix(".srt")
        srt_path.write_text(srt(scenes), encoding="utf-8")
        if args.dry_run:
            print(f"video: dry run OK; captions -> {srt_path}")
            return 0
        html = args.dashboard.read_text(encoding="utf-8")
        if "(EXAMPLE DATA)</title>" in html and not args.allow_example:
            raise VideoError("the dashboard is stamped EXAMPLE DATA; build it from real outputs first (make run)")
        raw, lead = capture(scenes, args.dashboard, work)
        encode(raw, lead, scenes, total, args.out)
        srt_path.write_text(srt([{**s, "start_s": s.get("real_start_s", s["start_s"])} for s in scenes]), encoding="utf-8")
        dur = probe_duration(args.out)
        if dur is not None and dur > LIMIT_S:
            raise VideoError(f"{args.out.name} is {dur:.1f}s, over the {LIMIT_S:.0f}s limit")
        (work / "timeline.json").write_text(json.dumps(scenes, indent=1), encoding="utf-8")
        size = args.out.stat().st_size / 1e6
        print(f"video: {args.out} ({size:.1f} MB{f', {dur:.1f}s' if dur else ''}); captions -> {srt_path}")
        return 0
    except VideoError as e:
        print(f"video: ERROR {e}", file=sys.stderr)
        return 1
    finally:
        if args.keep:
            print(f"video: work files kept in {work}")
        else:
            shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
