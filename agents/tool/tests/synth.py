"""Synthetic findings.json / themes.json for testing the dashboard.

Every value is made up (seeded random). Never cite. The `note` says SYNTHETIC, so
build.py stamps the page EXAMPLE. Shapes follow contracts/*.schema.json and the IDs
narrative asked data to use (issue: crosscheck IDs), plus the dashboard extras:
recommend/call_988 score distributions (`<m>.<item>.dist_<k>.overall`) and
training_month levels (`YYYY_MM`).
"""
from __future__ import annotations

import math
import random

NOTE = "SYNTHETIC TEST DATA for the dashboard. Values are made up. Never cite."

ITEMS = {
    "identify_crisis": "identify mental health challenges and crises",
    "describe_988": "describe 988 and how it works",
    "know_when_to_use": "know when to use 988",
}
QUALITY = {"engaging": "the presenter(s) engaged the participants",
           "knowledgeable": "the presenter(s) knew the subject matter well",
           "organized": "the training was well organized"}
GROUPS = {
    "county": {"anne_arundel": 900, "prince_georges": 300, "montgomery": 27, "queen_annes": 14,
               "garrett": 6, "other_pooled": 11},
    "role": {"student": 1050, "school_staff": 60, "caregiver_parent": 55, "other": 80},
    "language": {"en": 1280, "es": 19},
    "training_month": {"2025_10": 40, "2026_03": 7, "2026_04": 380, "2026_05": 420, "2026_09": 210, "2026_10": 230},
}


def _wilson(k: int, n: int) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    z, p = 1.96, k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    hw = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(100 * (c - hw), 2), round(100 * (c + hw), 2))


def _f(fid, label, value, unit, n, dim, level, *, numerator=None, n_missing=0, denom="respondents who answered",
       ci=(None, None), ci_method=None, caveat="", cols=None, threshold=10):
    small = n < threshold
    supp = small
    return {
        "id": fid, "label": label, "value": None if supp else value, "unit": unit, "n": n,
        "numerator": None if supp else numerator, "n_missing": n_missing, "denominator": denom,
        "ci_low": None if supp else ci[0], "ci_high": None if supp else ci[1],
        "ci_method": None if supp else ci_method,
        "group": {"dimension": dim, "level": level}, "small_n": small, "suppressed": supp,
        "caveat": ("Fewer than 10 respondents; value suppressed." if supp else caveat),
        "source_columns": cols or [],
    }


def make_findings(seed: int = 7, extra_groups: dict | None = None) -> dict:
    rng = random.Random(seed)
    groups = {k: dict(v) for k, v in GROUPS.items()}
    for dim, levels in (extra_groups or {}).items():
        groups.setdefault(dim, {}).update(levels)
    out = []
    retro = "'Before' ratings were asked after the training (retrospective), which tends to overstate change."

    def cuts():
        yield "overall", "all", 1299
        for dim, levels in groups.items():
            for lvl, n in levels.items():
                yield dim, lvl, n

    def suffix(dim, lvl):
        return "overall" if dim == "overall" else f"{dim}.{lvl}"

    for item, text in ITEMS.items():
        for dim, lvl, n in cuts():
            p_post = rng.uniform(0.78, 0.95)
            k = round(p_post * n)
            out.append(_f(f"post.{item}.agree_pct.{suffix(dim, lvl)}", f"Agree they can {text} (after)",
                          round(100 * k / n, 2), "pct", n, dim, lvl, numerator=k, ci=_wilson(k, n), ci_method="wilson95"))
            if dim == "overall":
                kp = round(rng.uniform(0.4, 0.75) * n)
                out.append(_f(f"pre.{item}.agree_pct.overall", f"Agree they could {text} (before, recalled)",
                              round(100 * kp / n, 2), "pct", n, dim, lvl, numerator=kp, ci=_wilson(kp, n),
                              ci_method="wilson95", caveat=retro))
                ch = round(rng.uniform(0.3, 1.1), 3)
                out.append(_f(f"change.{item}.mean_points.overall", f"Average self-rated change: {text}", ch, "points",
                              n, dim, lvl, ci=(round(ch - 0.05, 3), round(ch + 0.05, 3)), ci_method="t95",
                              denom="respondents who answered both the before and after item", caveat=retro))
    for item, text in QUALITY.items():
        for dim, lvl, n in cuts():
            nn = max(0, round(n * 0.88))
            k = round(rng.uniform(0.85, 0.97) * nn)
            out.append(_f(f"quality.{item}.agree_pct.{suffix(dim, lvl)}", f"Agree {text}",
                          round(100 * k / nn, 2) if nn else None, "pct", nn, dim, lvl, numerator=k,
                          n_missing=n - nn, ci=_wilson(k, nn), ci_method="wilson95",
                          caveat="About 12% skipped the training-quality questions."))
    for dim, lvl, n in cuts():
        m = round(rng.uniform(7.2, 8.9), 3)
        out.append(_f(f"recommend.score.mean.{suffix(dim, lvl)}", "Average likelihood to recommend (0-10)", m, "mean", n,
                      dim, lvl, ci=(round(m - 0.15, 3), round(m + 0.15, 3)), ci_method="t95"))
        nps = round(rng.uniform(10, 45), 1)
        out.append(_f(f"recommend.score.nps.{suffix(dim, lvl)}", "Net Promoter Score", nps, "nps", n, dim, lvl,
                      ci=(round(nps - 6, 1), round(nps + 6, 1)), ci_method="bootstrap95"))
    weights = [rng.uniform(0.2, 1) * (1 + i / 3) for i in range(11)]
    tot = sum(weights)
    counts = [round(1299 * w / tot) for w in weights]
    nn = sum(counts)
    for k, c in enumerate(counts):
        out.append(_f(f"recommend.score.dist_{k}.overall", f"Share who scored {k} on recommend", round(100 * c / nn, 2),
                      "pct", nn, "overall", "all", numerator=c, ci=_wilson(c, nn), ci_method="wilson95"))
    out.append(_f("call_988.likelihood.mean.overall", "Average likelihood to call 988 (0-10)", 8.1, "mean", 299,
                  "overall", "all", n_missing=1000, ci=(7.8, 8.4), ci_method="t95",
                  caveat="77% did not answer this question; it describes only those who did."))
    out.append(_f("missing.training_date.count.overall", "Responses with no training date", 3, "count", 1299,
                  "overall", "all", numerator=3, denom="all survey responses"))
    return {
        "schema_version": "0", "note": NOTE,
        "source": {"file_sha256": "f" * 64, "sheet": "Survey Data", "n_rows": 1299},
        "small_n_threshold": 10, "findings": out,
    }


THEMES = {
    "valuable": [("recognize_crisis", "Recognizing a crisis"), ("what_988_is", "What 988 is"),
                 ("when_to_use", "When to use 988"), ("helping_others", "How to help someone"),
                 ("everything", "Everything / general praise")],
    "improve": [("more_interactive", "More interactive activities"), ("shorter", "Shorter session"),
                ("more_examples", "More real-life examples"), ("nothing", "Nothing to change")],
}


def make_themes(seed: int = 11) -> dict:
    rng = random.Random(seed)
    taxonomy, counts = [], []
    base = {"valuable": 1060, "improve": 650}
    groups = {"county": {"anne_arundel": 0.7, "prince_georges": 0.25, "other_pooled": 0.04},
              "language": {"en": 0.985, "es": 0.006}}
    for field, themes in THEMES.items():
        for tid, label in themes:
            taxonomy.append({"theme_id": tid, "field": field, "label": label, "description": f"Synthetic theme: {label}."})
            cells = [("overall", "all", base[field])] + [
                (d, lvl, round(base[field] * share)) for d, lv in groups.items() for lvl, share in lv.items()]
            for dim, lvl, n in cells:
                small = n < 10
                k = round(rng.uniform(0.05, 0.45) * n)
                sfx = "overall" if dim == "overall" else f"{dim}.{lvl}"
                counts.append({
                    "id": f"themes.{field}.{tid}.pct.{sfx}", "theme_id": tid, "field": field,
                    "group": {"dimension": dim, "level": lvl},
                    "n_mentions": None if small else k, "n": n,
                    "pct": None if small else round(100 * k / n, 2), "small_n": small, "suppressed": small,
                })
    return {
        "schema_version": "0", "note": NOTE.replace("dashboard", "dashboard (themes)"),
        "source": {"file_sha256": "f" * 64, "n_rows": 1299},
        "method": "Synthetic: keyword rules (offline).",
        "taxonomy": taxonomy, "counts": counts,
        "validation": {"sample_size": 100, "agreement_pct": None, "cohen_kappa": None, "procedure": "SYNTHETIC."},
        "spanish": {"n_comments": 6, "handling": "Synthetic."},
        "pii_screen": {"method": "Synthetic.", "n_flagged": 2},
    }
