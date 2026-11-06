#!/usr/bin/env python3
"""Synthetic, schema-faithful copy of the EveryMind survey export, plus drift variants.

Same sheet name, the same 20 headers (including their non-breaking spaces) and the same messy label vocabulary
as the real export. Every row and comment is generated: nothing is copied from real responses.
Usage:  python3 agents/narrative/fixtures/make_fixtures.py [--out tests/fixtures] [--n 300] [--seed 17]
Python: write_all(out_dir, n, seed) -> {variant: path};  generate(n, seed) -> DataFrame
"""
import argparse
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

SHEET = "Survey Data"
NB = "\xa0"
LRM = "‎"  # the real Language values end with a left-to-right mark
_STMT = "Please tell us how much you disagree or agree with the statements.."
_BACK = "Now think back to before you took part in the Understanding 988 training." + NB + NB + "."
_ASPECT = "How much do you agree or disagree with the following aspects of the training?."
HEADERS = [
    "Id", "Start time", "Completion time", "Language", "Are you a....?",
    "Please enter the date of your training.",
    "Which county is this training affiliated with?" + NB,
    _STMT + "I can identify mental health challenges and crises.",
    _STMT + "I can describe 988 and how it works.",
    _STMT + "I know when to use 988.",
    _BACK + "I could" + NB + "identify mental health challenges and crises.",
    _BACK + "I could describe 988 and how it works.",
    _BACK + "I knew when to use 988.",
    _ASPECT + "The presenter(s) engaged the participants.",
    _ASPECT + "The presenter(s) knew the subject matter well." + NB,
    _ASPECT + "The training was well organized.",
    "How likely are you to recommend the Understanding 988 training to a friend or colleague?",
    "How likely are you to call 988 if you or someone else is experiencing a mental health challenge or crisis?",
    "What was the most valuable thing you learned during the training?" + NB,
    "How can we improve this training in the future?",
]
COUNTY, POST, PRE, QUALITY = HEADERS[6], HEADERS[7:10], HEADERS[10:13], HEADERS[13:16]
RECOMMEND, CALL988, VALUABLE, IMPROVE = HEADERS[16], HEADERS[17], HEADERS[18], HEADERS[19]

AGREE = ["Strongly disagree", "Disagree", "Neither agree nor disagree", "Agree", "Strongly agree"]  # scores 1..5
# Quality items use a messier vocabulary in the real export: (label, weight) per score.
QUALITY_LABELS = {
    1: [("Strongly disagree", 1)], 2: [("Disagree", 1)], 3: [("Neither agree or disagree", 1)],
    4: [("Agree", 0.97), ("Satisfied", 0.03)], 5: [("Strongly agree" + NB, 0.975), ("Very agree", 0.025)],
}
ROLES = [("Student", .83), ("Other (e.g., community member)", .045), ("Other (e.g., community member);", .023),
         ("School staff member;", .032), ("School staff member", .017), ("Caregiver/parent", .028),
         ("Caregiver/parent;", .016), ("Caregiver/parent;Student", .004),
         ("School staff member;Caregiver/parent;", .003), ("Student;", .002)]
COUNTIES = [("Anne Arundel", .72), ("Prince George's", .238), ("Montgomery" + NB, .021),
            ("Queen Anne's County ", .009), ("Fairfax", .002), ("Fairfax county ", .002),
            ("Montgomery County", .002), ("Montgomery County with NAMI MC", .002), ("Harris", .002),
            ("Queen Anne's County", .002)]
LANGS = [("English (United States)" + LRM, .985), ("Español (México)" + LRM, .015)]
# Synthetic comments. "Jane Doe" and 555-0100 are deliberate fake PII so the PII screen has something to catch.
VALUABLE_EN = ["How to recognize signs of a crisis", "That 988 can be called or texted",
               "When to call 988 instead of 911", "That anyone can call 988", "How to support a friend",
               "The warning signs of suicide", "That 988 is free and confidential", "everything", "idk"]
IMPROVE_EN = ["More interactive activities", "Make it shorter", "More time for questions",
              "Add real-life examples", "Nothing, it was great", "More videos", "n/a",
              "Thanks to trainer Jane Doe, more sessions like hers", "Call me at 555-0100 about my school"]
VALUABLE_ES, IMPROVE_ES = ["Que puedo llamar al 988", "Cómo ayudar a un amigo"], ["Más actividades", "Nada, todo bien"]


def _pick(rng, pairs, size):
    labels, w = zip(*pairs)
    return rng.choice(labels, size=size, p=np.array(w) / sum(w))


def _session_dates(rng):
    """~40 synthetic session dates clustered like the real export (Apr-May and Sep-Oct 2026, sparse before)."""
    spans = [((2025, 10, 20), (2026, 3, 31), 8), ((2026, 4, 8), (2026, 5, 14), 14),
             ((2026, 6, 1), (2026, 8, 28), 4), ((2026, 9, 1), (2026, 10, 21), 14)]
    out = []
    for lo, hi, k in spans:
        days = (date(*hi) - date(*lo)).days
        out += [date(*lo) + timedelta(days=int(d)) for d in rng.choice(days, size=k, replace=False)]
    return sorted(out)


def generate(n=300, seed=17, id_start=1):
    rng = np.random.default_rng(seed)
    sessions = _session_dates(rng)
    w = 1 / np.arange(1, len(sessions) + 1) ** 0.7  # a few big sessions, many small
    tdate = np.array(sessions, dtype=object)[rng.permutation(len(sessions))][rng.choice(len(sessions), n, p=w / w.sum())]
    start = [datetime.combine(d, datetime.min.time()) + timedelta(seconds=int(s))
             for d, s in zip(tdate, rng.integers(9 * 3600, 15 * 3600, n))]
    end = [s + timedelta(seconds=int(x)) for s, x in zip(start, rng.integers(60, 600, n))]

    df = pd.DataFrame({
        "Id": np.arange(id_start, id_start + n),
        "Start time": [s.strftime("%Y-%m-%d %H:%M:%S") for s in start],
        "Completion time": [e.strftime("%Y-%m-%d %H:%M:%S") for e in end],
        "Language": _pick(rng, LANGS, n),
        "Are you a....?": _pick(rng, ROLES, n),
        HEADERS[5]: [d.isoformat() for d in tdate],
        COUNTY: _pick(rng, COUNTIES, n),
    })
    df.loc[rng.choice(n, max(1, round(n * 0.0025)), replace=False), HEADERS[5]] = np.nan  # real: 3 of 1,299

    straight = rng.random(n) < 0.03  # real export has a block of all-"Strongly disagree" answers
    for pre_col, post_col in zip(PRE, POST):
        pre = rng.choice(np.arange(1, 6), n, p=[.07, .12, .22, .42, .17])
        post = np.minimum(5, pre + rng.choice([0, 1, 2], n, p=[.45, .40, .15]))
        pre[straight], post[straight] = 1, 1
        df[post_col] = [AGREE[s - 1] for s in post]
        df[pre_col] = [AGREE[s - 1] for s in pre]

    q_missing = rng.random(n) < 0.115  # whole quality block skipped together, as in the real export
    for col in QUALITY:
        score = rng.choice(np.arange(1, 6), n, p=[.02, .01, .07, .33, .57])
        df[col] = [_pick(rng, QUALITY_LABELS[s], 1)[0] for s in score]
        df.loc[q_missing | (rng.random(n) < 0.003), col] = np.nan

    rec = rng.choice(np.arange(11), n, p=np.array([13, 7, 11, 18, 32, 120, 88, 115, 186, 139, 271]) / 1000).astype(float)
    rec[rng.random(n) < 0.025] = np.nan
    call = rng.choice(np.arange(11), n, p=np.array([1, 1, 2, 3, 4, 10, 6, 11, 15, 17, 30]) / 100).astype(float)
    call[rng.random(n) < 0.775] = np.nan
    df[RECOMMEND], df[CALL988] = rec, call

    es = df["Language"].str.startswith("Español")
    df[VALUABLE] = np.where(es, rng.choice(VALUABLE_ES, n), rng.choice(VALUABLE_EN, n))
    df[IMPROVE] = np.where(es, rng.choice(IMPROVE_ES, n), rng.choice(IMPROVE_EN, n))
    df.loc[rng.random(n) < 0.18, VALUABLE] = np.nan
    r = rng.random(n)
    df.loc[r < 0.50, IMPROVE] = np.nan
    df.loc[(r >= 0.50) & (r < 0.505), IMPROVE] = " "  # whitespace-only answers exist in the real export
    return df[HEADERS]


def _shift_days(s, days, fmt):
    return pd.to_datetime(s).add(pd.Timedelta(days=days)).dt.strftime(fmt).where(s.notna())


VARIANTS = {
    "base": lambda df, n, seed: df,
    # A county no mapping table has seen yet, plus one more spelling.
    "new_county": lambda df, n, seed: df.assign(**{COUNTY: [
        "Garrett County" if i % 20 == 0 else "Baltimore City " if i == 7 else v for i, v in enumerate(df[COUNTY])]}),
    # Unseen Likert labels on one knowledge item and one quality item.
    "new_likert_label": lambda df, n, seed: df.assign(**{
        POST[0]: ["Somewhat agree" if i % 25 == 0 else v for i, v in enumerate(df[POST[0]])],
        QUALITY[0]: ["Totally agree" if i % 30 == 1 else v for i, v in enumerate(df[QUALITY[0]])]}),
    # Next export: the same rows plus 2n new ones (new Ids, same distributions).
    "extra_rows": lambda df, n, seed: pd.concat([df, generate(2 * n, seed + 1, id_start=n + 1)], ignore_index=True),
    # The likelihood-to-call-988 question removed from the form.
    "missing_column": lambda df, n, seed: df.drop(columns=[CALL988]),
    # Every date one year later (outside the original Oct 2025 - Oct 2026 range).
    "shifted_dates": lambda df, n, seed: df.assign(**{
        HEADERS[5]: _shift_days(df[HEADERS[5]], 365, "%Y-%m-%d"),
        "Start time": _shift_days(df["Start time"], 365, "%Y-%m-%d %H:%M:%S"),
        "Completion time": _shift_days(df["Completion time"], 365, "%Y-%m-%d %H:%M:%S")}),
}


def write_all(out_dir="tests/fixtures", n=300, seed=17):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    base, paths = generate(n, seed), {}
    for name, make in VARIANTS.items():
        paths[name] = out / f"fixture_{name}.xlsx"
        make(base.copy(), n, seed).to_excel(paths[name], sheet_name=SHEET, index=False)
    return paths


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default="tests/fixtures")
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--seed", type=int, default=17)
    a = ap.parse_args()
    for name, p in write_all(a.out, a.n, a.seed).items():
        print(f"{name:17s} {p}")
