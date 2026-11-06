#!/usr/bin/env bash
# One-time GitHub board setup: labels, milestones, status issues, per-agent milestone issues, human gates, "infra ready".
# Usage: bash scripts/bootstrap_github.sh      (DRY_RUN=1 prints the gh calls instead)
# Safe to re-run: labels are upserted, existing milestones/issues (same title) are skipped.
set -euo pipefail

if [ "${DRY_RUN:-}" = 1 ]; then
  gh() {
    { printf 'gh'; printf ' %q' "$@"; echo; } >&2
    case "$1 $2" in
      "repo view") echo "OWNER/REPO" ;;
      "issue create") echo "https://github.com/OWNER/REPO/issues/0" ;;
    esac
  }
fi

REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)

# ---- labels
label() { gh label create "$1" --color "$2" --description "$3" --force -R "$REPO" >/dev/null; }
for a in data text tool narrative; do label "to:$a" 1d76db "Addressed to the $a agent"; done
label to:human       d93f0b "Needs a human teammate"
label needs-human    d93f0b "Blocked until a human acts"
label type:request   0e8a16 "Change request to an owner"
label type:blocker   b60205 "Someone cannot proceed"
label type:handoff   5319e7 "Something is ready for a consumer"
label type:decision  fbca04 "Decision; also logged in docs/decisions.md"
label type:status    c5def5 "Per-agent status issue"
for d in artifact video memo appendix deck; do label "deliverable:$d" bfdadc "Deliverable: $d"; done

# ---- milestones (due_on in UTC; ET = UTC-5 after Nov 1)
M1="M1 contracts + pipeline v1 (Fri Nov 6 12:00 ET)"
M2="M2 findings, themes, dashboard v1 (Fri Nov 6 20:00 ET)"
M3="M3 FINDINGS FREEZE (Sat Nov 7 12:00 ET)"
M4="M4 five deliverables v1 in submission/ (Sat Nov 7 20:00 ET)"
M5="M5 human verification + final video (Sat 23:00-Sun 02:00 ET)"
M6="M6 HARD FREEZE (Sun Nov 8 06:00 ET; humans submit by 08:00)"
existing_ms=$(gh api "repos/$REPO/milestones?state=all&per_page=100" -q '.[].title' || true)
ms() {
  if grep -qxF -- "$1" <<<"$existing_ms"; then echo "skip milestone (exists): $1" >&2; return 0; fi
  gh api "repos/$REPO/milestones" -f title="$1" -f due_on="$2" >/dev/null
}
ms "$M1" 2026-11-06T17:00:00Z
ms "$M2" 2026-11-07T01:00:00Z
ms "$M3" 2026-11-07T17:00:00Z
ms "$M4" 2026-11-08T01:00:00Z
ms "$M5" 2026-11-08T07:00:00Z
ms "$M6" 2026-11-08T11:00:00Z

# ---- issues
existing=$(gh issue list -R "$REPO" --state all --limit 500 --json title -q '.[].title' || true)
URL=""
issue() { # title milestone labels body  -> sets $URL ("" if skipped)
  URL=""
  if grep -qxF -- "$1" <<<"$existing"; then echo "skip issue (exists): $1" >&2; return 0; fi
  local args=(-R "$REPO" --title "$1" --label "$3" --body "[agent:narrative]"$'\n\n'"$4")
  if [ -n "$2" ]; then args+=(--milestone "$2"); fi
  URL=$(gh issue create "${args[@]}")
  echo "$URL"
}

for a in data text tool narrative; do
  issue "[status] $a" "" "type:status" "Status for the **$a** agent. The $a agent edits this body at every milestone: done / next / blocked / ETA. Start: \`git pull --rebase\`, read CLAUDE.md and agents/$a/ROLE.md."
  if [ -n "$URL" ] && [ "$a" != narrative ]; then gh issue pin "${URL##*/}" -R "$REPO"; fi
done

t() { issue "$1 · $2: $3" "$4" "to:$2,$5" "$6"$'\n\nClose when done; update `[status] '"$2"'`.'; }
A=deliverable:artifact

t M1 data "contracts v1 + pipeline v1" "$M1" "$A" "CRITICAL PATH.
- [ ] Correct contracts/cleaned_data + findings schemas against the real workbook; bump to v1
- [ ] \`make data DATA=<any xlsx>\` writes data/processed/survey_clean.csv (local) + outputs/findings.json + outputs/validation_report.json
- [ ] Mapping tables (JSON) for county / Likert / roles / language; unknown labels flagged, never crash
- [ ] type:handoff issue to:text,to:tool,to:narrative announcing v1"
t M1 text "codebook draft + classifier skeleton" "$M1" "$A" "- [ ] agents/text/codebook.md draft for both comment fields
- [ ] agents/text/themes.py skeleton (offline, deterministic) writing outputs/themes.json on the fixture/example
- [ ] Propose themes schema v1 (or confirm v0)
- [ ] PII screen design"
t M1 tool "dashboard skeleton + make run wired" "$M1" "$A" "- [ ] agents/tool/build.py renders outputs/dashboard.html from contracts/examples (marked EXAMPLE)
- [ ] \`make run DATA=path\` chain works once data/text entry points exist
- [ ] Chart conventions: zero-based bars, n on every chart, small-n flags"
t M1 narrative "verify + check_numbers + submit scaffolding" "$M1" "deliverable:memo,deliverable:appendix,deliverable:deck" "- [ ] scripts/verify.py (filenames, page counts, mp4 length, pptx, metadata, identity strings)
- [ ] scripts/check_numbers.py ([F:id] tags vs findings/themes)
- [ ] scripts/submit.py
- [ ] Outlines: memo, appendix, deck"

t M2 data "findings v1 + fixtures + drift tests + docs" "$M2" "$A" "- [ ] All analyses in ROLE.md with n, denominator, CI, small-n, caveats (retrospective!)
- [ ] tests/fixtures/make_fixture.py + drift tests (new county, new label, extra rows, missing column)
- [ ] agents/data/data_dictionary.md, limitations.md, recompute.md"
t M2 text "themes v1 with validation" "$M2" "$A" "- [ ] outputs/themes.json v1: taxonomy, counts by group with n + small-n
- [ ] Hand-checked sample: size + agreement (+ kappa) reported truthfully
- [ ] Spanish handling, PII screen counts"
t M2 tool "dashboard v1 + RUN.md + notebook + video PoC" "$M2" "$A,deliverable:video" "- [ ] Dashboard v1 on real outputs, accessible, plain language
- [ ] agents/tool/RUN.md, walkthrough notebook (aggregates only)
- [ ] Video pipeline proof of concept (headless capture + captions + ffmpeg)"
t M2 narrative "memo, appendix, deck v0" "$M2" "deliverable:memo,deliverable:appendix,deliverable:deck" "- [ ] drafts in agents/narrative/drafts/, every number tagged [F:id], check_numbers green
- [ ] appendix v0 only from logs/ai + docs/verification.md"

t M3 data "FINDINGS FREEZE" "$M3" "$A" "- [ ] IDs + values frozen; after this, changes need a type:decision issue
- [ ] Headline IDs listed in docs/verification.md for human recompute (request to:narrative)"
t M3 text "themes freeze + candidate quotes to human" "$M3" "$A" "- [ ] themes.json frozen
- [ ] Candidate quotes → the human PII review issue (no raw text in issues without human OK)"
t M3 tool "dashboard complete + narration script" "$M3" "$A,deliverable:video" "- [ ] Dashboard feature-complete on frozen findings
- [ ] agents/tool/video/script.md with [F:id] tags → to:narrative for review"
t M3 narrative "drafts locked to frozen IDs" "$M3" "deliverable:memo,deliverable:deck" "- [ ] Memo/deck findings sections use only frozen IDs
- [ ] Review the narration script; chase human-gate issues"

t M4 data "support deliverables v1" "$M4" "$A" "- [ ] Answer recompute questions; data-refresh notes for RUN.md (to:tool)"
t M4 text "quotes_reviewed.json + final codebook" "$M4" "$A" "- [ ] outputs/quotes_reviewed.json only after human approval
- [ ] Final codebook + validation write-up"
t M4 tool "artifact zip + demo mp4 v1" "$M4" "$A,deliverable:video" "- [ ] agents/tool/dist/Team17_TechnicalArtifact.zip (no data/, no identity strings), tested from a clean clone
- [ ] agents/tool/dist/Team17_Demo.mp4 ≤120 s"
t M4 narrative "all five deliverables v1 in submission/" "$M4" "deliverable:memo,deliverable:appendix,deliverable:deck" "- [ ] Team17_Memo.pdf (≤2 pages), Team17_AIAppendix.pdf (1 page), Team17_Presentation.pptx
- [ ] \`make submit\` + \`make verify\` green"

t M5 data "fix human-verification findings" "$M5" "$A" "- [ ] Any recompute mismatch fixed or explained (type:decision)"
t M5 text "fix human-verification findings" "$M5" "$A" "- [ ] Any quote/PII or theme issue raised by humans fixed"
t M5 tool "final demo video" "$M5" "$A,deliverable:video" "- [ ] Final mp4 (or hand off to human re-record) ≤120 s, numbers match frozen IDs"
t M5 narrative "fold verification into appendix + docs" "$M5" "deliverable:appendix,deliverable:memo" "- [ ] docs/verification.md complete and true; appendix reflects it"

t M6 data "hard freeze" "$M6" "$A" "- [ ] No pushes after 06:00 ET except human-approved fixes"
t M6 text "hard freeze" "$M6" "$A" "- [ ] No pushes after 06:00 ET except human-approved fixes"
t M6 tool "hard freeze" "$M6" "$A,deliverable:video" "- [ ] No pushes after 06:00 ET except human-approved fixes"
t M6 narrative "final make submit + hand to humans" "$M6" "deliverable:memo,deliverable:appendix,deliverable:deck,deliverable:video,$A" "- [ ] Final \`make submit\`; \`make verify\` green; post the checklist on the form-submission issue"

h() { issue "HUMAN: $1" "$2" "to:human,needs-human${3:+,$3}" "$4"; }
h "hand-recompute headline numbers from the raw xlsx" "$M5" "deliverable:memo,deliverable:deck" "Recompute each headline finding in docs/verification.md directly from the raw xlsx (Excel filters/COUNTIFS), following agents/data/recompute.md, independently of the pipeline. Record value + n per ID in docs/verification.md (or comment here). Any mismatch → type:blocker to:data."
h "screen candidate quotes for PII" "$M3" "deliverable:memo,deliverable:deck,deliverable:video" "Text agent posts candidate quotes (or response IDs to read locally). Remove anything with names (including trainers), schools, contact info, or identifying detail. Comment approved/removed; text then writes outputs/quotes_reviewed.json."
h "verify judge links are 'Anyone with the link' and show no owner name" "$M6" "deliverable:artifact,deliverable:video" "Open every judge-facing link in a private window, logged out. Confirm it opens and that no owner name, email or handle is visible."
h "record or approve the demo video" "$M5" "deliverable:video" "Watch agents/tool/dist/Team17_Demo.mp4 (≤120 s). Approve, or re-record using agents/tool/video/script.md. Numbers must match frozen IDs."
h "submit the Google Form and list each member's contributions" "$M6" "" "Agents never submit. Upload the five files from submission/ after \`make verify\` is green, by 08:00 ET Sun Nov 8 (form closes 09:00). List each member's contributions as the form asks."

issue "infra ready" "" "type:handoff,to:data,to:text,to:tool" "Bootstrap is pushed to main. Start now:
1. \`git pull --rebase\`, then \`make setup\` (enables the commit-msg hook), then confirm \`git config user.name/email\` is your human's.
2. Read CLAUDE.md (hard rules, ownership, work loop) and agents/<you>/ROLE.md.
3. Your milestone issues: \`gh issue list --label to:<you>\`. Your status issue: \`[status] <you>\`.
4. Contracts v0 are in contracts/ (from the case's column list; data file not opened). Data owns the v1 correction, due Fri 12:00 ET.
5. Log AI use in logs/ai/<you>.md as you go."
echo "done: $REPO" >&2
