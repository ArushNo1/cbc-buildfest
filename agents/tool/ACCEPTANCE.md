# Tool acceptance checks

Automated by `agents/tool/acceptance.py` on outputs built from input fingerprint `72b08ff71ede` (1,299 rows). Re-run: `python3 agents/tool/acceptance.py --report agents/tool/ACCEPTANCE.md`.

| Check | Result | Detail |
|---|---|---|
| offline: light 1200px loads with no network, no script errors, no broken sections | PASS | errors=[] requests=[] broken=0 |
| numbers: all 695 rows in 'All numbers' match findings/themes (value, 95% range, n) | PASS | mismatches=[] missing=[] extra=[] |
| numbers: all 9 headline tiles match findings | PASS | [] |
| numbers: hidden small groups show no value on any chart | PASS | rows=0 |
| a11y: page language set | PASS | en |
| a11y: one h1 and no skipped heading levels | PASS | jumps=[] |
| a11y: every control has a label | PASS | unlabelled=0 |
| a11y: every chart has an accessible name | PASS | unnamed=0 |
| a11y: every chart has a table view next to it | PASS | charts without table=0 |
| a11y: first Tab reaches 'Skip to content' | PASS | Skip to content |
| a11y: keyboard focus on a bar shows its numbers; Escape hides them | PASS | Can identify mental health challenges an |
| a11y: text contrast >= 4.5:1 (light) | PASS |  |
| a11y: chart marks contrast >= 3:1 against the background (light) | PASS |  |
| offline: dark 1200px loads with no network, no script errors, no broken sections | PASS | errors=[] requests=[] broken=0 |
| a11y: text contrast >= 4.5:1 (dark) | PASS |  |
| a11y: chart marks contrast >= 3:1 against the background (dark) | PASS |  |
| offline: light 375px loads with no network, no script errors, no broken sections | PASS | errors=[] requests=[] broken=0 |
| layout: no horizontal scroll at 375 px | PASS | scrollWidth=375 |
| video: length <= 120 s | PASS | 95.72999999999999 s |
| video: no identity strings in metadata | PASS |  |
| video: every narrated number matches outputs (check_numbers) | PASS |  |
| video: captions file present | PASS |  |
| identity: zip contains no data files | PASS |  |
| identity: no team identity strings in 58 files | PASS | {} |

## Other checks run on Fri Nov 6, 00:00–01:00 ET (tool agent, not human)

| Check | Result |
|---|---|
| Clean clone from GitHub → `make setup` → `make run DATA=<export>` → `make test` | Pass: 58 tests. `findings.json` byte-identical. `themes.json` differs only by one sentence in `validation.procedure` saying the agreement stats come from the committed summary; the agreement figures themselves (90.0%, kappa 0.87, n = 80) are unchanged. |
| `make run` on all 6 synthetic drift fixtures (base, new county, new Likert label, extra rows, missing column, shifted dates) | Pass: exit 0 and no traceback for each. New labels and counties are counted in Data checks; the missing call-988 column is reported and those numbers skipped. Every dashboard opened offline with no script errors. |
| `agents/tool/recompute_check.py`: third independent recompute of all findings from the raw export | Pass: 222/222 match (value within 0.005, n and numerator exact). It caught 3 of 3 errors deliberately injected into a copy of `findings.json`. |
| Artifact zip: unzip into a non-git folder → `make setup` → `make run` → `make test` (`package.py --smoke`) | Pass |
| Zip reproducibility | Pass: built on two machines, byte-identical. |
| `make verify` | Pass except the mp4 checks, which need `ffprobe` (not installed on this machine). Length and metadata are covered above with ffmpeg. |
| Form run instructions (`agents/tool/dist/FORM_run_instructions.txt`) followed literally in a fresh unzip: view the dashboard with no install, `pip install`, the three-command no-`make` path, `make run`, `make test`, `recompute_check.py` | Pass: every step works. 58 tests pass; the recompute matches 222/222; acceptance inside the zip passes 18/18 (video and identity checks are skipped there by design). |
