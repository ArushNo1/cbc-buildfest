#!/usr/bin/env bash
# Repo guards, run by CI and `make verify`:
#  1. AI attribution in commit messages/authors (hard rule 1)
#  2. raw / row-level data files tracked or staged (hard rule 2)
#  3. identity strings in text files under submission/ (hard rule 3; binary metadata is scripts/verify.py's job)
# Commit range: $RANGE, else CI's PR base / push "before", else unpushed commits (origin/main..HEAD), else all history.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"
fail=0
head=${HEAD_SHA:-HEAD}
if [ -n "${RANGE:-}" ]; then range=$RANGE
elif [ -n "${BASE:-}" ]; then range="$BASE..$head"
elif [ -n "${BEFORE:-}" ] && ! [[ $BEFORE =~ ^0+$ ]] && git cat-file -e "$BEFORE^{commit}" 2>/dev/null; then range="$BEFORE..$head"
elif [ -z "${CI:-}" ] && git rev-parse -q --verify origin/main >/dev/null; then range="origin/main..$head"
else range=$head; fi

# 1. attribution
if ! git log --format='%an <%ae>%n%cn <%ce>%n%B' "$range" | bash scripts/hooks/commit-msg /dev/stdin; then
  echo "FAIL: AI attribution in commits ($range). Do not rewrite history; open a to:human blocker." >&2; fail=1
fi

# 2. data files
bad=$(git ls-files | grep -Ei '^data/|\.(xlsx|xlsm|xls|csv|tsv|parquet|feather|sav|dta|sqlite|db)$')
if [ -n "$bad" ]; then echo "FAIL: raw/row-level data files tracked or staged:" >&2; echo "$bad" >&2; fail=1; fi

# 3. identity strings in submission/ (team git names/emails come from history, so none are hard-coded here)
if [ -d submission ]; then
  ids=$(mktemp)
  { git log --format='%an%n%ae'; git log --format='%ae' | sed -E 's/@.*//; s/^[0-9]+\+//'; } | awk 'length >= 4' | sort -u > "$ids"
  hits=$( { find submission -type f -print0 | xargs -0 -r grep -IilE '\bumd\b|terpmail'
            find submission -type f -print0 | xargs -0 -r grep -IilF -f "$ids"; } 2>/dev/null | sort -u)
  rm -f "$ids"
  if [ -n "$hits" ]; then echo "FAIL: identity strings in submission/:" >&2; echo "$hits" >&2; fail=1; fi
fi

[ $fail = 0 ] && echo "check_repo: OK ($range)"
exit $fail
