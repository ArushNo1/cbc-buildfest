# AI process log: tool agent

Append-only. Record only what actually happened. This feeds the AI appendix (hard rule 4).

Entry template:

## <date> <time ET>: <short title>
- **Prompt (representative):** "..."
- **What the AI produced:**
- **Error / limitation (if any), and how it was caught:**
- **Revision:**
- **Manually verified against data:** what, how, result


## 2026-11-05 23:15 ET: dashboard builder v1 (M1 skeleton, then wired to real outputs)
- **Tool:** Claude Code (Claude Opus model), running in the Claude desktop app on this machine.
- **Prompt (representative):** "You are the tool agent. Read CLAUDE.md and agents/tool/ROLE.md, check issues labeled to:tool, and work toward your milestones: a self-contained HTML dashboard built from outputs/findings.json and outputs/themes.json, with honest axes, n everywhere, small-group flags, accessibility and plain language."
- **What the AI produced:** `agents/tool/build.py` (reads both JSON files, validates them against `contracts/*.schema.json`, groups findings by metric and group, writes one self-contained `outputs/dashboard.html`), `agents/tool/web/` (HTML template, CSS, vanilla JS renderer, no CDN), `agents/tool/tests/` (19 tests plus a synthetic findings and themes generator), and `agents/tool/RUN.md`. Design rule: the page only formats, sorts and selects numbers from the two JSON files. It never computes a statistic.
- **Errors / limitations caught, and how:**
  - **Visual review in a browser** (synthetic data, then real outputs):
    - The "Before" legend swatch had no color. The CSS rule was missing.
    - The "everyone" reference line ran through the value labels. Fixed with a label background.
    - Month labels on the time axis overlapped. Changed to collision-based thinning.
    - The long "Measure" dropdown overflowed the screen at phone width.
    - The time line joined points across months with no trainings, which implied continuity. It now breaks the line there.
    - The caveat box showed "value suppressed" boilerplate instead of the item's real caveat.
    - The group dropdown lost its intended order (county, role, language). Cause: `json.dumps(sort_keys=True)` re-sorts dict keys. Fixed with an explicit `dim_order` list.
  - **Unit test caught a real bug:** an explicitly named `--themes` file that didn't exist was silently skipped, because a `try/except` swallowed the error. It now fails with a message.
  - **First integration with the real `outputs/themes.json`:**
    - Its `group.level` values are display names ("Prince George's") while its IDs use slugs. The first ID parser would have mis-grouped them. The level slug is now taken from the ID.
    - Its `source.file_sha256` fingerprints the cleaned CSV, not the xlsx. A naive equality check would have shown a false "different export" warning. A hash difference now counts as "unconfirmed" and only differing row counts count as a mismatch.
  - **Summary wording:**
    - The auto-generated "most common suggestion" picked catch-all buckets ("Question, not a suggestion", "No substantive comment"). Those are now excluded from that sentence and sorted last.
    - The "highest group" summary named Queen Anne's on n = 12 without its wide range. Summaries now show n and the 95% range.
    - I had written a static claim ("most respondents are students in two counties") that no finding backs. It was replaced with generic wording.
  - **Palette validator:** run on after-blue and before-grey. Grey fails only the chroma floor, as expected for a deliberate de-emphasis color. CVD and normal-vision separation and contrast pass in light and dark.
- **Revision:** all of the above fixed. `make test`: 37 passed.
- **Manually verified against data:**
  - `make run DATA=data/raw/BuildFest_EveryMind_Survey_Data_FULL.xlsx` ran end to end, exit 0.
  - The rebuilt `outputs/findings.json` was byte-identical to the committed file.
  - The rebuilt `outputs/themes.json` differed only in its `validation` block, which was nulled because the hand labels exist only on the text machine. I restored the committed file and reported it to text.
  - Spot-checked tiles against `outputs/findings.json`: post identify-crisis 89.9 of 1,299; recommend mean 7.59 of 1,266; NPS +12.0; call-988 mean 7.66 of 293, with 1,006 missing.
  - No numbers were hand-recomputed from the xlsx. That is the human check in issue 29.

## 2026-11-05 23:40 ET: artifact packaging and walkthrough notebook
- **Prompt (representative):** "Keep going on the tool milestones: package the technical artifact zip (code, contracts, outputs, RUN.md, fixture generator; no data, no identity strings) and write the walkthrough notebook that loads only outputs/*.json."
- **What the AI produced:**
  - `agents/tool/package.py`:
    - builds the zip from an allow-list of git-tracked files;
    - runs the identity scan from `scripts/verify.py` before writing;
    - writes a reproducible zip (fixed timestamps, sorted entries);
    - with `--smoke`, unzips into an empty, non-git folder and runs `make run` and `make test` there.
  - `agents/tool/walkthrough.ipynb`, committed with outputs cleared, plus a test that executes every code cell.
- **Errors / limitations caught, and how:**
  - **Narrative's `verify.py` would reject the zip.** Reading it before packaging showed that its data-file pattern `(^|/)data/` also matches `agents/data/`, which holds the pipeline code. Reported to narrative in #42. `package.py` blocks only a top-level `data/`.
  - **`make setup` fails without git.** Its `git config` step fails in an unzipped folder, which is how judges will run it. Also in #42. RUN.md now gives the pip fallback.
  - **CLAUDE.md is left out of the zip.** Its rules text contains "umd", which the identity scan flags.
- **Revision:** none needed after the smoke test.
- **Manually verified against data:** `python3 agents/tool/package.py --smoke DATA=data/raw/BuildFest_EveryMind_Survey_Data_FULL.xlsx`:
  - built 44 files (153 KB);
  - `make run` and `make test` (48 passed) succeeded in the unzipped folder;
  - the rebuilt `outputs/findings.json` was identical to the committed file;
  - `outputs/dashboard.html` differed only because the clean rebuild nulls the comment-coder validation stats. That is the same cause as in #41.

## 2026-11-05 23:55 ET: narration script and video pipeline (capture not yet run)
- **Prompt (representative):** "Install ffmpeg and a headless browser, then build the demo video proof of concept: headless capture of the dashboard, captions, narration, ffmpeg."
- **What the AI produced:**
  - `agents/tool/video/script.md`: 6 scenes, each number tagged `[F:…]`. `check_numbers` reports 0 problems.
  - `agents/tool/video/make_video.py`, which:
    - parses the scenes and runs the number check (a mismatch stops the build);
    - generates speech with macOS `say`;
    - plans the timeline and caption cards and refuses anything over 117 s;
    - records the dashboard in headless Chromium, with captions drawn into the page so ffmpeg needs no subtitle filter;
    - muxes the audio at each scene's measured start time and strips metadata.
  - `agents/tool/tests/test_video.py` (6 tests; no browser or ffmpeg needed).
- **Errors / limitations caught, and how:**
  - **Installs failed.** Homebrew's ffmpeg install and Playwright's Chromium download both failed. The first error ("Failed to create dir") looked like a sandbox restriction. Reading the full log showed "No space left on device": the disk had about 450 MB free. I stopped the install and removed only Homebrew's temp unpack folder from my own run. No user files were touched. Capture and encoding are blocked until space is freed.
  - **Speech text.** I spotted a likely misreading of "988" ("nine hundred eighty-eight"), so the spoken text now says "nine eight eight" while captions keep "988". Covered by a unit test.
  - **Rebuild issue fixed by text.** Text's fix for #41 (`raw_file_sha256`) let the dashboard confirm both files come from the same export. The dashboard was rebuilt.
- **Manually verified against data:**
  - `make_video.py --dry-run`: the number check passed against `outputs/`.
  - Speech timing with the Samantha voice at 182 wpm comes to 84.1 s planned (limit 120 s).
  - Before writing the "students vs. staff" line, I checked in `outputs/findings.json` that the ranges don't overlap: student recommend mean 7.22 (7.08–7.36, n = 1,051) vs. school staff 9.52 (9.34–9.71, n = 67).

## 2026-11-06 00:50 ET: video PoC rendered; dashboard picks up findings v1.1 (time cuts, distributions, sensitivity, sample mix)
- **Prompt (representative):** "Space freed, retry" (install ffmpeg and Chromium, then render the video proof of concept).
- **What the AI produced:**
  - Rendered `agents/tool/dist/Team17_Demo.mp4`:
    - 83.1 s, 1280x720, H.264/AAC, 6.1 MB, metadata stripped;
    - `.srt` captions alongside;
    - 7 scenes, narration from macOS `say`.
  - Dashboard changes for data's new findings (they answered #40):
    - training-month line chart, broken at months with no trainings;
    - season periods in date order;
    - 0–10 histograms for the recommend and call-988 scores;
    - a "Who answered" composition chart;
    - the sensitivity check (excluding straight-line "Strongly disagree" responders) shown as a note in the learning section, kept out of the group picker.
- **Errors / limitations caught, and how:**
  - **Install problems:**
    - Homebrew's ffmpeg install failed twice inside the command sandbox at `ca-certificates` (`undefined method '[]' for nil` in `load_tab`).
    - A retry with the sandbox disabled was refused by the permission system. I did not work around it.
    - Switched to `imageio-ffmpeg` (pip; static ffmpeg with libx264 and aac). It has no ffprobe, so `make_video.py` now reads the duration from ffmpeg's own output.
    - Five ffmpeg dependencies Homebrew had poured stay in `/opt/homebrew/Cellar`. They are harmless and `brew autoremove` clears them.
  - **The Playwright browser cache vanished between two runs.** `~/Library/Caches/ms-playwright` was gone, likely cleared under low disk space. Reinstalled with `--only-shell` (headless shell only, about 200 MB instead of about 570 MB).
  - **Bugs found by reviewing frames pulled from the rendered video:**
    - The legend's "95% range" swatch shared the `.ci` class with the absolutely positioned whiskers, so it floated to the top of the page as stray "⊢" marks. It had looked like a missing swatch in the first review.
    - The 0–10 axis showed "-0" (`Math.ceil(-1e-9) * 2.5`) and steps of 2.5. Fixed to 0, 2, 4, …
    - The narration about improvement comments played over the "most valuable" chart. The scene was split, with a new anchor on the "improve" chart.
    - The closing line about IDs showed the caveats list. It now shows the "All numbers" table.
    - Caption cards broke mid-phrase. They now split one card per sentence, into even halves when a sentence is long.
  - **New-findings integration:**
    - Season levels (`fall_2026`, `spring_2026`, `other_periods`) sorted alphabetically, putting fall before spring. Added chronological ordering.
    - The "months with no trainings break the line" rule also hid the spring-to-fall line. It is now limited to monthly data.
  - **Wording:** I had written "The conclusions don't change." under the sensitivity numbers. That interpretation isn't backed by a finding, so I removed it.
  - **My own test was wrong:** it expected `spring_2026` before `2026_04`. Spring maps to April, so they tie and the tie breaks by name. The test was corrected, not the code.
- **Manually verified against data:**
  - Scene start times in the render were within 50 ms of plan.
  - The narration number check passed on the final script.
  - Frames at each scene matched the narration.
  - Headless screenshots at 1200 px and 375 px showed no console errors and no horizontal scroll.
