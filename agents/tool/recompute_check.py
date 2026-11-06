#!/usr/bin/env python3
"""Independent recompute of every finding in outputs/findings.json from the raw survey export.

A third implementation (tool agent): shares no code with agents/data/ (the pipeline) or
agents/narrative/crosscheck/. Written from the definitions in docs/decisions.md (D-010) and
agents/data/data_dictionary.md. Reads the export locally and prints aggregate comparisons only.

  python3 agents/tool/recompute_check.py [data/raw/<export>.xlsx] [outputs/findings.json]

Compares value (within 0.005), n and numerator (exact) for every finding; exit 1 on any mismatch.
"""
import json
import math
import re
import sys
from collections import defaultdict

import pandas as pd

ROOT = __import__("pathlib").Path(__file__).resolve().parents[2]
RAW = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "data/raw/BuildFest_EveryMind_Survey_Data_FULL.xlsx")
FINDINGS = sys.argv[2] if len(sys.argv) > 2 else str(ROOT / "outputs/findings.json")
df = pd.read_excel(RAW, sheet_name="Survey Data", dtype=object)


def norm(x):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return ""
    return re.sub(r"\s+", " ", str(x).replace("\xa0", " ").replace("‎", "")).strip()


def col(*needles):
    hits = [c for c in df.columns if all(n.lower() in norm(c).lower() for n in needles)]
    assert len(hits) == 1, (needles, hits)
    return hits[0]


C = {
    "lang": col("language"), "role": col("are you a"), "date": col("date of your training"), "county": col("which county"),
    "post.identify_crisis": col("disagree or agree with the statements", "can identify"),
    "post.describe_988": col("disagree or agree with the statements", "can describe"),
    "post.know_when_to_use": col("disagree or agree with the statements", "know when"),
    "pre.identify_crisis": col("think back", "identify"), "pre.describe_988": col("think back", "describe"),
    "pre.know_when_to_use": col("think back", "knew when"),
    "quality.engaging": col("aspects of the training", "engaged"), "quality.knowledgeable": col("aspects of the training", "knew the subject"),
    "quality.organized": col("aspects of the training", "well organized"),
    "recommend": col("recommend the understanding"), "call": col("likely are you to call 988"),
}
LIKERT = {"strongly disagree": 1, "disagree": 2, "neither agree nor disagree": 3, "neither agree or disagree": 3,
          "agree": 4, "satisfied": 4, "strongly agree": 5, "very agree": 5}


def likert(v):
    return LIKERT.get(norm(v).lower())


def score10(v):
    s = norm(v)
    try:
        f = float(s)
    except ValueError:
        return None
    return int(f) if f.is_integer() and 0 <= f <= 10 else None


def county(v):
    s = norm(v).lower()
    if "anne arundel" in s:
        return "anne_arundel"
    if "prince george" in s:
        return "prince_georges"
    if s.startswith("montgomery"):
        return "montgomery"
    if "queen anne" in s:
        return "queen_annes"
    return "other_pooled"


def roles(v):
    out = set()
    for part in norm(v).split(";"):
        p = part.strip().lower()
        if not p:
            continue
        if p.startswith("student"):
            out.add("student")
        elif p.startswith("school staff"):
            out.add("school_staff")
        elif p.startswith("caregiver"):
            out.add("caregiver_parent")
        elif p.startswith("other"):
            out.add("other")
    return out


rows = []
for _, r in df.iterrows():
    d = pd.to_datetime(norm(r[C["date"]]) or None, errors="coerce")
    month = None if pd.isna(d) else f"{d.year}_{d.month:02d}"
    period = None
    if month:
        period = "spring_2026" if month in ("2026_04", "2026_05") else "fall_2026" if month in ("2026_09", "2026_10") else "other_periods"
    rec = {
        "groups": {"overall": {"all"}, "county": {county(r[C["county"]])}, "role": roles(r[C["role"]]),
                   "language": {"es" if norm(r[C["lang"]]).lower().startswith(("espa", "spanish")) else "en"},
                   "training_month": {month} if month else set(), "training_period": {period} if period else set()},
        "recommend": score10(r[C["recommend"]]), "call": score10(r[C["call"]]),
    }
    for k in [k for k in C if "." in k]:
        rec[k] = likert(r[C[k]])
    rec["straight"] = all(rec[f"post.{i}"] == 1 for i in ("identify_crisis", "describe_988", "know_when_to_use"))
    rows.append(rec)
N = len(rows)


def members(dim, level):
    if dim == "sensitivity":
        return [r for r in rows if not r["straight"]]
    return [r for r in rows if level in r["groups"].get(dim, set())]


def compute(measure, item, stat, dim, level):
    grp = members(dim, level)
    if measure == "sample":
        k = len(grp)
        return {"value": k if stat == "count" else 100 * k / N, "n": N, "numerator": k}
    if measure in ("post", "pre", "quality"):
        vals = [r[f"{measure}.{item}"] for r in grp if r[f"{measure}.{item}"] is not None]
        if stat == "agree_pct":
            k = sum(v >= 4 for v in vals)
            return {"value": 100 * k / len(vals) if vals else None, "n": len(vals), "numerator": k}
        if stat == "mean":
            return {"value": sum(vals) / len(vals) if vals else None, "n": len(vals)}
    if measure == "change":
        pairs = [(r[f"post.{item}"], r[f"pre.{item}"]) for r in grp if r[f"post.{item}"] is not None and r[f"pre.{item}"] is not None]
        return {"value": sum(a - b for a, b in pairs) / len(pairs), "n": len(pairs)}
    if measure in ("recommend", "call_988"):
        key = "recommend" if measure == "recommend" else "call"
        vals = [r[key] for r in grp if r[key] is not None]
        m = re.fullmatch(r"dist_(\d+)", stat)
        if m:
            k = sum(v == int(m.group(1)) for v in vals)
            return {"value": 100 * k / len(vals), "n": len(vals), "numerator": k}
        if stat == "mean":
            return {"value": sum(vals) / len(vals) if vals else None, "n": len(vals)}
        if stat == "nps":
            return {"value": 100 * (sum(v >= 9 for v in vals) - sum(v <= 6 for v in vals)) / len(vals) if vals else None, "n": len(vals)}
    if measure == "missing" and item == "training_date":
        k = sum(1 for r in rows if not r["groups"]["training_month"])
        return {"value": k, "n": N, "numerator": k}
    return None


findings = json.load(open(FINDINGS))["findings"]
compared, bad, skipped = 0, [], []
for f in findings:
    parts = f["id"].split(".")
    dim, level = f["group"]["dimension"], f["group"]["level"]
    measure, item, stat = parts[0], parts[1], parts[2]
    got = compute(measure, item, stat, dim, level)
    if got is None:
        skipped.append(f["id"])
        continue
    compared += 1
    probs = []
    if got["n"] != f["n"]:
        probs.append(f"n {got['n']} vs {f['n']}")
    if f.get("numerator") is not None and got.get("numerator") is not None and got["numerator"] != f["numerator"]:
        probs.append(f"numerator {got['numerator']} vs {f['numerator']}")
    if f["value"] is not None:
        if got["value"] is None or abs(got["value"] - f["value"]) > 0.005:
            probs.append(f"value {got['value']} vs {f['value']}")
    if probs:
        bad.append(f"{f['id']}: " + "; ".join(probs))
print(f"recompute: {compared} findings compared independently, {len(bad)} mismatches, {len(skipped)} not covered")
for b in bad:
    print("  MISMATCH", b)
for s in skipped:
    print("  not covered:", s)
sys.exit(1 if bad else 0)
