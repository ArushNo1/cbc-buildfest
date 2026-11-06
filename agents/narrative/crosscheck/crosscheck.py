#!/usr/bin/env python3
"""Independent crosscheck of the headline survey numbers.

Reads the raw workbook directly with its own small label maps and shares NO code or mappings with agents/data/,
so a pipeline bug shows up as a disagreement. Writes agents/narrative/crosscheck/results.json (aggregates only),
diffs it against outputs/findings.json, and opens one `to:data` issue per mismatched finding ID (skipping any
that are already open). Exit codes: 0 = agree or nothing to diff yet, 1 = mismatches, 2 = different input file.
Usage: crosscheck.py --data PATH [--findings outputs/findings.json] [--out results.json] [--no-issues]
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TOL = 0.05  # value tolerance: findings may round to 1 decimal. n / n_missing / numerator must match exactly.
SMALL_N = 10

# Each column is found by substrings of its normalized header, so NBSPs and small wording edits don't matter.
COLS = {
    "post_identify_crisis": ["disagree or agree with the statements", "identify mental health"],
    "post_describe_988": ["disagree or agree with the statements", "describe 988"],
    "post_know_when_to_use": ["disagree or agree with the statements", "when to use 988"],
    "pre_identify_crisis": ["think back", "identify mental health"],
    "pre_describe_988": ["think back", "describe 988"],
    "pre_know_when_to_use": ["think back", "when to use 988"],
    "quality_engaging": ["aspects of the training", "engaged"],
    "quality_knowledgeable": ["aspects of the training", "subject matter"],
    "quality_organized": ["aspects of the training", "organized"],
    "recommend": ["likely are you to recommend"],
    "call_988": ["likely are you to call 988"],
    "county": ["which county"],
    "role": ["are you a"],
    "language": ["language"],
    "training_date": ["date of your training"],
}
LIKERT = {"strongly disagree": 1, "disagree": 2, "neither agree nor disagree": 3, "neither agree or disagree": 3,
          "agree": 4, "satisfied": 4, "strongly agree": 5, "very agree": 5}
MAPPING_NOTE = ("1-5 Likert; 'Very agree'=5, 'Satisfied'=4, 'Neither agree or/nor disagree'=3; agree = score >= 4; "
                "unrecognized labels and blanks count as n_missing; 0-10 scores outside 0..10 are missing; "
                "roles are any-mention of the multi-select")
ITEMS = ["identify_crisis", "describe_988", "know_when_to_use"]


def norm(v):
    return " ".join(str(v).replace("\xa0", " ").replace("‎", "").split()).lower()


def find_cols(df):
    found, missing = {}, []
    for key, subs in COLS.items():
        hits = [c for c in df.columns if all(s in norm(c) for s in subs)]
        if len(hits) > 1:
            sys.exit(f"crosscheck: header for {key} is ambiguous: {hits}")
        if hits:
            found[key] = hits[0]
        else:
            missing.append(key)
    return found, missing


def likert(s):
    return s.map(lambda v: LIKERT.get(norm(v)) if pd.notna(v) else None).astype("float64")


def score10(s):
    x = pd.to_numeric(s, errors="coerce")
    return x.where((x >= 0) & (x <= 10))


def rec(fid, value, n, n_total, numerator, denom):
    if n < SMALL_N:
        value = None
    return {"id": fid, "value": None if value is None else round(float(value), 4), "n": int(n),
            "n_missing": int(n_total - n), "numerator": numerator, "denominator": denom}


def agree_pct(fid, scores, denom):
    v = scores.dropna()
    k = int((v >= 4).sum())
    return rec(fid, 100 * k / len(v) if len(v) else None, len(v), len(scores), k, denom)


def mean(fid, values, denom):
    v = values.dropna()
    return rec(fid, v.mean() if len(v) else None, len(v), len(values), None, denom)


def nps(fid, values, denom):
    v = values.dropna()
    val = 100 * ((v >= 9).sum() - (v <= 6).sum()) / len(v) if len(v) else None
    return rec(fid, val, len(v), len(values), None, denom)


def groups(df, c):
    """Key subgroup masks (dimension, level, mask, words)."""
    out = []
    if "county" in c:
        county = df[c["county"]].map(norm).str.replace(r" county.*$", "", regex=True)
        out += [("county", "anne_arundel", county == "anne arundel", "Anne Arundel"),
                ("county", "prince_georges", county == "prince george's", "Prince George's"),
                ("county", "montgomery", county == "montgomery", "Montgomery"),
                ("county", "queen_annes", county == "queen anne's", "Queen Anne's")]
    if "role" in c:
        roles = df[c["role"]].map(lambda v: {norm(t) for t in str(v).split(";") if norm(t)} if pd.notna(v) else set())
        for level, test, words in [("student", "student", "student"), ("school_staff", "school staff", "school staff"),
                                   ("caregiver_parent", "caregiver", "caregiver/parent"), ("other", "other", "other/community")]:
            out.append(("role", level, roles.map(lambda r, t=test: any(x.startswith(t) for x in r)), f"{words} (any mention)"))
    if "language" in c:
        lang = df[c["language"]].map(norm)
        out += [("language", "en", lang.str.contains("english"), "English-survey"),
                ("language", "es", lang.str.contains("español|espanol"), "Spanish-survey")]
    return out


def compute(df):
    c, missing_cols = find_cols(df)
    out = []
    s = {k: likert(df[c[k]]) for k in c if k.startswith(("post_", "pre_", "quality_"))}
    for item in ITEMS:
        post, pre = s.get(f"post_{item}"), s.get(f"pre_{item}")
        if post is not None:
            out += [agree_pct(f"post.{item}.agree_pct.overall", post, "respondents with a recognized answer to this post item"),
                    mean(f"post.{item}.mean.overall", post, "respondents with a recognized answer to this post item (1-5)")]
        if pre is not None:
            out += [agree_pct(f"pre.{item}.agree_pct.overall", pre, "respondents with a recognized answer to this retrospective 'before' item"),
                    mean(f"pre.{item}.mean.overall", pre, "respondents with a recognized answer to this retrospective 'before' item (1-5)")]
        if post is not None and pre is not None:
            out.append(mean(f"change.{item}.mean_points.overall", post - pre,
                            "respondents with recognized answers to both the before and after item (post minus pre, points on 1-5)"))
    for q in ["engaging", "knowledgeable", "organized"]:
        if f"quality_{q}" in s:
            out.append(agree_pct(f"quality.{q}.agree_pct.overall", s[f"quality_{q}"], "respondents with a recognized answer to this quality item"))
    if "recommend" in c:
        r = score10(df[c["recommend"]])
        out += [mean("recommend.score.mean.overall", r, "respondents who gave a 0-10 recommend score"),
                nps("recommend.score.nps.overall", r, "respondents who gave a 0-10 recommend score (9-10 minus 0-6)")]
    if "call_988" in c:
        out.append(mean("call_988.likelihood.mean.overall", score10(df[c["call_988"]]), "respondents who answered the optional call-988 question"))
    if "training_date" in c:
        d = df[c["training_date"]]
        out.append({"id": "missing.training_date.count.overall", "value": int(d.isna().sum()), "n": len(d),
                    "n_missing": int(d.isna().sum()), "numerator": None, "denominator": "all rows"})
    post_cols = [f"post_{i}" for i in ITEMS if f"post_{i}" in s]
    if post_cols:  # sensitivity: drop respondents answering "Strongly disagree" (1) on every post item
        keep = ~pd.concat([s[k] == 1 for k in post_cols], axis=1).all(axis=1)
        for k in post_cols:
            out.append(agree_pct(f"{k.replace('_', '.', 1)}.agree_pct.sensitivity.excl_straightline", s[k][keep],
                                 "respondents with a recognized answer, excluding those who chose 'Strongly disagree' on every post item"))
    for dim, level, mask, words in groups(df, c):
        for item in ITEMS:
            if f"post_{item}" in s:
                out.append(agree_pct(f"post.{item}.agree_pct.{dim}.{level}", s[f"post_{item}"][mask],
                                     f"{words} respondents with a recognized answer to this post item"))
        if "recommend" in c:
            out.append(mean(f"recommend.score.mean.{dim}.{level}", score10(df[c["recommend"]])[mask],
                            f"{words} respondents who gave a 0-10 recommend score"))
    return out, missing_cols


def diff(mine, findings):
    by_id = {f["id"]: f for f in findings.get("findings", [])}
    mismatches, not_found = [], []
    for m in mine:
        f = by_id.get(m["id"])
        if f is None:
            not_found.append(m["id"])
            continue
        probs = []
        if (f.get("value") is None) != (m["value"] is None) or (
                m["value"] is not None and abs(f["value"] - m["value"]) > TOL):
            probs.append(("value", f.get("value"), m["value"]))
        for k in ("n", "n_missing", "numerator"):
            if f.get(k) is not None and m.get(k) is not None and f[k] != m[k]:
                probs.append((k, f[k], m[k]))
        if probs:
            mismatches.append((m, f, probs))
    return mismatches, not_found


def open_issues(mismatches, sha):
    existing = set(subprocess.run(
        ["gh", "issue", "list", "--state", "open", "--label", "to:data", "--limit", "500", "--json", "title", "-q", ".[].title"],
        capture_output=True, text=True, check=True).stdout.splitlines())
    for m, f, probs in mismatches:
        title = f"[crosscheck] mismatch: {m['id']}"
        if title in existing:
            print(f"  already open: {title}")
            continue
        rows = "\n".join(f"| {k} | {a} | {b} |" for k, a, b in probs)
        body = f"""[agent:narrative]

The independent crosscheck (`agents/narrative/crosscheck/crosscheck.py`: separate code, reads data/raw directly) disagrees with `outputs/findings.json` for **`{m['id']}`** (input sha256 `{sha[:12]}`).

| field | findings.json | crosscheck |
|---|---|---|
{rows}

- **findings.json:** value {f.get('value')}, n {f.get('n')}, n_missing {f.get('n_missing')}, numerator {f.get('numerator')}. Denominator: "{f.get('denominator')}"
- **crosscheck:** value {m['value']}, n {m['n']}, n_missing {m['n_missing']}, numerator {m['numerator']}. Denominator: "{m['denominator']}"
- **crosscheck mapping:** {MAPPING_NOTE}. Value tolerance ±{TOL}.

Please fix it, or explain the definitional difference in a comment and label this `type:decision`. Re-check with `make crosscheck`.
"""
        subprocess.run(["gh", "issue", "create", "--title", title, "--label", "to:data,type:request,deliverable:artifact",
                        "--body", body], check=True)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--findings", default=str(ROOT / "outputs/findings.json"))
    ap.add_argument("--out", default=str(HERE / "results.json"))
    ap.add_argument("--no-issues", action="store_true")
    a = ap.parse_args(argv)

    sha = hashlib.sha256(Path(a.data).read_bytes()).hexdigest()
    df = pd.read_excel(a.data, sheet_name="Survey Data")
    mine, missing_cols = compute(df)
    if missing_cols:
        print(f"crosscheck: columns not found, metrics skipped: {missing_cols}")
    Path(a.out).write_text(json.dumps({"source": {"file_sha256": sha, "n_rows": len(df)}, "tolerance": TOL,
                                       "mapping": MAPPING_NOTE, "metrics": mine}, indent=2, ensure_ascii=False) + "\n")
    print(f"crosscheck: {len(mine)} metrics from {len(df)} rows -> {a.out}")

    if not Path(a.findings).exists():
        print(f"crosscheck: {a.findings} not found; nothing to diff yet")
        return 0
    findings = json.loads(Path(a.findings).read_text(encoding="utf-8"))
    theirs = findings.get("source", {}).get("file_sha256")
    if theirs and theirs != sha:
        print(f"crosscheck: findings.json was built from a different file ({theirs[:12]} vs {sha[:12]}); not diffing")
        return 2
    mismatches, not_found = diff(mine, findings)
    print(f"crosscheck: {len(mine) - len(not_found) - len(mismatches)} agree, {len(mismatches)} mismatch, "
          f"{len(not_found)} not in findings.json")
    for m, f, probs in mismatches:
        print(f"  MISMATCH {m['id']}: " + "; ".join(f"{k} findings={x} crosscheck={y}" for k, x, y in probs))
    if not_found:
        print("  not in findings.json (check ID names): " + ", ".join(not_found))
    if mismatches and not a.no_issues:
        open_issues(mismatches, sha)
    return 1 if mismatches else 0


if __name__ == "__main__":
    sys.exit(main())
