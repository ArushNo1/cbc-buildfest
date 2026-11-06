#!/usr/bin/env python3
"""Data pipeline for EveryMind BuildFest post-training survey data.

Deterministic ingestion, cleaning, harmonization, and statistical analysis.
Follows contracts/cleaned_data.schema.json and contracts/findings.schema.json.

Outputs:
  - data/processed/survey_clean.csv (local, gitignored)
  - outputs/findings.json (aggregates only, single source of truth)
  - outputs/validation_report.json (aggregates only)

Usage:
  python agents/data/pipeline.py --data data/raw/BuildFest_EveryMind_Survey_Data_FULL.xlsx
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MAPPINGS_DIR = HERE / "mappings"

SMALL_N_THRESHOLD = 10
Z_95 = 1.959963984540054

# Student-t critical values (alpha=0.05 two-sided) for df = 1..30, and large df
T_TABLE_95 = {
    1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571,
    6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
    11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131,
    16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086,
    21: 2.080, 22: 2.074, 23: 2.069, 24: 2.064, 25: 2.060,
    26: 2.056, 27: 2.052, 28: 2.048, 29: 2.045, 30: 2.042,
    40: 2.021, 60: 2.000, 80: 1.990, 100: 1.984, 120: 1.980,
}


def get_t_crit(df: int) -> float:
    if df < 1:
        return Z_95
    if df in T_TABLE_95:
        return T_TABLE_95[df]
    if df > 120:
        return Z_95
    # Linear interpolation for values between keys
    keys = sorted(T_TABLE_95.keys())
    for i in range(len(keys) - 1):
        if keys[i] <= df <= keys[i + 1]:
            k1, k2 = keys[i], keys[i + 1]
            t1, t2 = T_TABLE_95[k1], T_TABLE_95[k2]
            return t1 + (t2 - t1) * (df - k1) / (k2 - k1)
    return Z_95


def norm_str(val: Any) -> str:
    """Normalize whitespace, NBSP, and control characters."""
    if val is None or pd.isna(val):
        return ""
    s = str(val).replace("\xa0", " ").replace("\u200e", "").replace("‎", "")
    return " ".join(s.split()).strip()


def load_mappings() -> Tuple[Dict, Dict, List[Dict], List[Dict], List[Dict]]:
    with open(MAPPINGS_DIR / "column_map.json", "r", encoding="utf-8") as f:
        col_map = json.load(f)
    with open(MAPPINGS_DIR / "likert_map.json", "r", encoding="utf-8") as f:
        likert_map = json.load(f)
    with open(MAPPINGS_DIR / "county_map.json", "r", encoding="utf-8") as f:
        county_rules = json.load(f)["rules"]
    with open(MAPPINGS_DIR / "role_map.json", "r", encoding="utf-8") as f:
        role_rules = json.load(f)["rules"]
    with open(MAPPINGS_DIR / "language_map.json", "r", encoding="utf-8") as f:
        lang_rules = json.load(f)["rules"]
    return col_map, likert_map, county_rules, role_rules, lang_rules


def map_columns(df_cols: List[str], col_map: Dict) -> Tuple[Dict[str, str], List[str]]:
    """Match clean column names to raw column headers."""
    found = {}
    missing = []
    norm_headers = {c: norm_str(c).lower() for c in df_cols}

    for clean_name, rule in col_map.items():
        rule_type = rule.get("type", "contains")
        matched = []
        if rule_type == "exact":
            names = [n.lower() for n in rule.get("names", [])]
            for orig, nh in norm_headers.items():
                if nh in names:
                    matched.append(orig)
        elif rule_type == "contains":
            subs = [s.lower() for s in rule.get("substrings", [])]
            for orig, nh in norm_headers.items():
                if any(sub in nh for sub in subs):
                    matched.append(orig)
        elif rule_type == "contains_all":
            subs = [s.lower() for s in rule.get("substrings", [])]
            for orig, nh in norm_headers.items():
                if all(sub in nh for sub in subs):
                    matched.append(orig)

        if len(matched) == 1:
            found[clean_name] = matched[0]
        elif len(matched) > 1:
            # Disambiguate if possible (prefer exact match or shortest header)
            exact_hits = [m for m in matched if norm_headers[m] == clean_name.lower()]
            if len(exact_hits) == 1:
                found[clean_name] = exact_hits[0]
            else:
                sys.exit(f"Data pipeline error: Ambiguous column match for '{clean_name}': {matched}")
        else:
            missing.append(clean_name)

    return found, missing


def clean_county(val: Any, county_rules: List[Dict]) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """Returns (canonical_name, raw_normalized, level_id, flag)."""
    if val is None or pd.isna(val):
        return None, None, None, "missing_county"
    raw_norm = norm_str(val)
    if not raw_norm:
        return None, None, None, "missing_county"

    low = raw_norm.lower()
    for rule in county_rules:
        if re.search(rule["pattern"], low):
            return rule["canonical"], raw_norm, rule["level_id"], None

    return None, raw_norm, None, f"unknown_county:{raw_norm}"


def clean_roles(val: Any, role_rules: List[Dict]) -> Tuple[str, List[str], List[str]]:
    """Clean multi-select roles with trailing semicolons. Returns (joined_canonical, canonical_list, flags)."""
    if val is None or pd.isna(val):
        return "", [], []
    raw_str = norm_str(val)
    if not raw_str:
        return "", [], []

    tokens = [norm_str(t) for t in raw_str.split(";") if norm_str(t)]
    canonical_set: Set[str] = set()
    flags: List[str] = []

    for t in tokens:
        low = t.lower()
        matched = False
        for rule in role_rules:
            if re.search(rule["pattern"], low):
                canonical_set.add(rule["canonical"])
                matched = True
                break
        if not matched:
            flags.append(f"unknown_role:{t}")

    sorted_canonical = sorted(canonical_set)
    return ";".join(sorted_canonical), sorted_canonical, flags


def clean_language(val: Any, lang_rules: List[Dict]) -> Tuple[Optional[str], Optional[str]]:
    """Returns (canonical_code, flag)."""
    if val is None or pd.isna(val):
        return None, "missing_language"
    raw_norm = norm_str(val)
    low = raw_norm.lower()
    for rule in lang_rules:
        if re.search(rule["pattern"], low):
            return rule["canonical"], None
    return low if low else None, f"unknown_language:{raw_norm}"


def clean_likert(val: Any, col_name: str, likert_map: Dict[str, int]) -> Tuple[Optional[int], Optional[str]]:
    """Maps Likert text to 1-5 integer scale. Unrecognized becomes None with a flag."""
    if val is None or pd.isna(val):
        return None, None
    raw_norm = norm_str(val).lower()
    if not raw_norm:
        return None, None
    if raw_norm in likert_map:
        return int(likert_map[raw_norm]), None
    return None, f"unknown_label:{col_name}:{raw_norm}"


def clean_score10(val: Any, col_name: str) -> Tuple[Optional[int], Optional[str]]:
    """Parses 0-10 score. Out-of-range or non-numeric becomes None with flag."""
    if val is None or pd.isna(val):
        return None, None
    s = norm_str(val)
    if not s:
        return None, None
    try:
        f = float(s)
        i = int(round(f))
        if 0 <= i <= 10 and abs(f - i) < 1e-4:
            return i, None
        return None, f"out_of_range:{col_name}:{s}"
    except (ValueError, TypeError):
        return None, f"unknown_score:{col_name}:{s}"


def clean_dataset(df_raw: pd.DataFrame, col_map: Dict, likert_map: Dict,
                  county_rules: List[Dict], role_rules: List[Dict],
                  lang_rules: List[Dict]) -> Tuple[pd.DataFrame, Dict]:
    """Clean all rows deterministically and compile validation report stats."""
    found_cols, missing_cols = map_columns(list(df_raw.columns), col_map)

    rows = []
    unknown_label_counts: Dict[str, Dict[str, int]] = {}
    flag_counts: Dict[str, int] = {}
    missing_per_col: Dict[str, int] = {c: 0 for c in col_map.keys()}

    for _, raw_row in df_raw.iterrows():
        row_flags: List[str] = []

        # 1. response_id
        raw_id = raw_row[found_cols["response_id"]] if "response_id" in found_cols else None
        if pd.isna(raw_id):
            resp_id = None
            row_flags.append("missing_response_id")
        else:
            try:
                resp_id = int(raw_id)
            except (ValueError, TypeError):
                resp_id = norm_str(raw_id)

        # 2. timestamps
        start_t = norm_str(raw_row[found_cols["start_time"]]) if "start_time" in found_cols and pd.notna(raw_row[found_cols["start_time"]]) else None
        comp_t = norm_str(raw_row[found_cols["completion_time"]]) if "completion_time" in found_cols and pd.notna(raw_row[found_cols["completion_time"]]) else None

        # 3. language
        raw_lang = raw_row[found_cols["language"]] if "language" in found_cols else None
        lang, lang_flag = clean_language(raw_lang, lang_rules)
        if lang_flag:
            row_flags.append(lang_flag)

        # 4. roles
        raw_roles = raw_row[found_cols["roles"]] if "roles" in found_cols else None
        roles_str, _, role_flags = clean_roles(raw_roles, role_rules)
        row_flags.extend(role_flags)

        # 5. dates
        raw_date = raw_row[found_cols["training_date"]] if "training_date" in found_cols else None
        tr_date_str = None
        tr_month_str = None
        if pd.isna(raw_date) or not norm_str(raw_date):
            row_flags.append("missing_training_date")
        else:
            try:
                dt = pd.to_datetime(raw_date)
                tr_date_str = dt.strftime("%Y-%m-%d")
                tr_month_str = dt.strftime("%Y-%m")
            except Exception:
                row_flags.append(f"invalid_date:{raw_date}")

        # 6. county
        raw_county = raw_row[found_cols["county"]] if "county" in found_cols else None
        county, county_raw, _, c_flag = clean_county(raw_county, county_rules)
        if c_flag:
            row_flags.append(c_flag)

        clean_row = {
            "response_id": resp_id,
            "start_time": start_t,
            "completion_time": comp_t,
            "language": lang,
            "roles": roles_str,
            "training_date": tr_date_str,
            "training_month": tr_month_str,
            "county": county,
            "county_raw": county_raw,
        }

        # 7. Likert items (post, pre, quality)
        likert_items = [
            "post_identify_crisis", "post_describe_988", "post_know_when_to_use",
            "pre_identify_crisis", "pre_describe_988", "pre_know_when_to_use",
            "quality_engaging", "quality_knowledgeable", "quality_organized"
        ]
        for item in likert_items:
            if item in found_cols:
                val, flag = clean_likert(raw_row[found_cols[item]], item, likert_map)
                clean_row[item] = val
                if flag:
                    row_flags.append(flag)
                    lbl = flag.split(":")[-1]
                    unknown_label_counts.setdefault(item, {})
                    unknown_label_counts[item][lbl] = unknown_label_counts[item].get(lbl, 0) + 1
            else:
                clean_row[item] = None

        # 8. Recommend & call_988
        if "recommend" in found_cols:
            rec_val, flag = clean_score10(raw_row[found_cols["recommend"]], "recommend")
            clean_row["recommend"] = rec_val
            if flag:
                row_flags.append(flag)
        else:
            clean_row["recommend"] = None

        if "call_988_likelihood" in found_cols:
            c988_val, flag = clean_score10(raw_row[found_cols["call_988_likelihood"]], "call_988")
            clean_row["call_988_likelihood"] = c988_val
            if flag:
                row_flags.append(flag)
        else:
            clean_row["call_988_likelihood"] = None

        # 9. Free-text comments
        for c_col in ["comment_valuable", "comment_improve"]:
            if c_col in found_cols:
                cm = norm_str(raw_row[found_cols[c_col]])
                clean_row[c_col] = cm if cm else None
            else:
                clean_row[c_col] = None

        # Data quality flags: straightlining
        post_vals = [clean_row["post_identify_crisis"], clean_row["post_describe_988"], clean_row["post_know_when_to_use"]]
        pre_vals = [clean_row["pre_identify_crisis"], clean_row["pre_describe_988"], clean_row["pre_know_when_to_use"]]
        if all(v == 1 for v in post_vals):
            row_flags.append("straightline_post_strongly_disagree")
            if all(v == 1 for v in pre_vals):
                row_flags.append("straightline_all_strongly_disagree")

        clean_row["flags"] = ";".join(row_flags)

        for fl in row_flags:
            base_fl = fl.split(":")[0]
            flag_counts[base_fl] = flag_counts.get(base_fl, 0) + 1

        for col, val in clean_row.items():
            if val is None or val == "":
                missing_per_col[col] = missing_per_col.get(col, 0) + 1

        rows.append(clean_row)

    df_clean = pd.DataFrame(rows)
    # Convert integer columns with potential missing values to nullable Int64
    int_cols = [
        "post_identify_crisis", "post_describe_988", "post_know_when_to_use",
        "pre_identify_crisis", "pre_describe_988", "pre_know_when_to_use",
        "quality_engaging", "quality_knowledgeable", "quality_organized",
        "recommend", "call_988_likelihood"
    ]
    for ic in int_cols:
        if ic in df_clean.columns:
            df_clean[ic] = df_clean[ic].astype("Int64")

    # Sort deterministically
    if "response_id" in df_clean.columns:
        df_clean = df_clean.sort_values(by="response_id").reset_index(drop=True)

    # Validation summary
    dates = df_clean["training_date"].dropna()
    validation_summary = {
        "row_count": len(df_clean),
        "missing_columns_in_source": missing_cols,
        "duplicate_response_ids": int(df_clean["response_id"].duplicated().sum()),
        "missing_per_column": missing_per_col,
        "unknown_label_counts": unknown_label_counts,
        "date_range": {
            "min_date": str(dates.min()) if not dates.empty else None,
            "max_date": str(dates.max()) if not dates.empty else None,
            "missing_dates": int(df_clean["training_date"].isna().sum())
        },
        "flags_summary": dict(sorted(flag_counts.items()))
    }

    return df_clean, validation_summary


def calc_wilson_ci(k: int, n: int) -> Tuple[Optional[float], Optional[float]]:
    """Calculates Wilson 95% score interval for a proportion, returned on 0-100 scale."""
    if n <= 0:
        return None, None
    p = k / n
    denom = 1.0 + (Z_95 ** 2) / n
    center = (p + (Z_95 ** 2) / (2 * n)) / denom
    margin = (Z_95 / denom) * math.sqrt((p * (1.0 - p) / n) + ((Z_95 ** 2) / (4 * (n ** 2))))
    low = max(0.0, round(100.0 * (center - margin), 2))
    high = min(100.0, round(100.0 * (center + margin), 2))
    return low, high


def calc_t_ci(series: pd.Series) -> Tuple[Optional[float], Optional[float]]:
    """Calculates Student-t 95% CI for a mean."""
    s = series.dropna()
    n = len(s)
    if n < 2:
        return None, None
    mean_val = s.mean()
    std_val = s.std(ddof=1)
    if math.isnan(std_val) or std_val == 0.0:
        return round(float(mean_val), 2), round(float(mean_val), 2)
    t_crit = get_t_crit(n - 1)
    margin = t_crit * (std_val / math.sqrt(n))
    return round(float(mean_val - margin), 2), round(float(mean_val + margin), 2)


def make_finding(fid: str, label: str, value: Optional[float], unit: str,
                 n: int, n_total: int, numerator: Optional[int], denominator_desc: str,
                 group_dim: str, group_level: str, source_cols: List[str],
                 caveat: str = "", ci_low: Optional[float] = None,
                 ci_high: Optional[float] = None,
                 ci_method: Optional[str] = None,
                 n_missing: Optional[int] = None) -> Dict:
    """Format single finding following contracts/findings.schema.json."""
    small_n = n < SMALL_N_THRESHOLD
    suppressed = small_n
    final_val = None if suppressed else (None if value is None else round(float(value), 4))
    final_num = None if suppressed else numerator

    if suppressed:
        ci_low, ci_high, ci_method = None, None, None
        supp_caveat = f"Fewer than {SMALL_N_THRESHOLD} respondents (n={n}); value suppressed for statistical reliability."
        caveat = f"{caveat} {supp_caveat}".strip()

    missing_count = int(n_total - n) if n_missing is None else int(n_missing)

    return {
        "id": fid,
        "label": label,
        "value": final_val,
        "unit": unit,
        "n": int(n),
        "numerator": final_num,
        "n_missing": missing_count,
        "denominator": denominator_desc,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "ci_method": ci_method,
        "group": {
            "dimension": group_dim,
            "level": group_level
        },
        "small_n": small_n,
        "suppressed": suppressed,
        "caveat": caveat,
        "source_columns": source_cols
    }


def compute_all_findings(df: pd.DataFrame, source_sha: str, n_raw: int,
                         missing_cols: Optional[List[str]] = None) -> List[Dict]:
    """Computes all headline, cut, and subgroup findings with exact crosscheck matching."""
    findings = []
    missing_set = set(missing_cols or [])
    items = ["identify_crisis", "describe_988", "know_when_to_use"]
    item_labels = {
        "identify_crisis": "identify mental health challenges and crises",
        "describe_988": "describe 988 and how it works",
        "know_when_to_use": "know when to use 988"
    }

    # Helper masks for subgroups
    county_clean = df["county"].fillna("")
    county_masks = {
        "anne_arundel": (county_clean == "Anne Arundel", "Anne Arundel"),
        "prince_georges": (county_clean == "Prince George's", "Prince George's"),
        "montgomery": (county_clean == "Montgomery", "Montgomery"),
        "queen_annes": (county_clean == "Queen Anne's", "Queen Anne's"),
        "other_pooled": (~county_clean.isin(["Anne Arundel", "Prince George's", "Montgomery", "Queen Anne's"]), "Other counties (pooled)")
    }

    # Roles: any-mention of each canonical role
    role_sets = df["roles"].map(lambda v: set(str(v).split(";")) if pd.notna(v) and str(v) else set())
    role_masks = {
        "student": (role_sets.map(lambda r: "Student" in r), "student (any mention)"),
        "school_staff": (role_sets.map(lambda r: "School staff member" in r), "school staff (any mention)"),
        "caregiver_parent": (role_sets.map(lambda r: "Caregiver/parent" in r), "caregiver/parent (any mention)"),
        "other": (role_sets.map(lambda r: "Other (e.g., community member)" in r), "other/community (any mention)")
    }

    lang_clean = df["language"].fillna("")
    lang_masks = {
        "en": (lang_clean == "en", "English-survey"),
        "es": (lang_clean == "es", "Spanish-survey")
    }

    # 1. Knowledge items: post, pre, change
    for item in items:
        lbl = item_labels[item]
        post_col = f"post_{item}"
        pre_col = f"pre_{item}"

        # Post item overall
        if post_col in df:
            s_post = df[post_col].dropna()
            n_post = len(s_post)
            k_post = int((s_post >= 4).sum())
            val_pct = (100.0 * k_post / n_post) if n_post > 0 else None
            ci_low, ci_high = calc_wilson_ci(k_post, n_post)
            findings.append(make_finding(
                fid=f"post.{item}.agree_pct.overall",
                label=f"Agree or strongly agree they can {lbl} (after training)",
                value=val_pct,
                unit="pct",
                n=n_post,
                n_total=len(df),
                numerator=k_post,
                denominator_desc="respondents with a recognized answer to this post item",
                group_dim="overall",
                group_level="all",
                source_cols=[post_col],
                caveat="",
                ci_low=ci_low,
                ci_high=ci_high,
                ci_method="wilson95"
            ))

            val_mean = float(s_post.mean()) if n_post > 0 else None
            ci_m_low, ci_m_high = calc_t_ci(s_post)
            findings.append(make_finding(
                fid=f"post.{item}.mean.overall",
                label=f"Average rating: I can {lbl} (after training, 1-5)",
                value=val_mean,
                unit="mean",
                n=n_post,
                n_total=len(df),
                numerator=None,
                denominator_desc="respondents with a recognized answer to this post item (1-5)",
                group_dim="overall",
                group_level="all",
                source_cols=[post_col],
                caveat="",
                ci_low=ci_m_low,
                ci_high=ci_m_high,
                ci_method="t95"
            ))

        # Pre item overall
        if pre_col in df:
            s_pre = df[pre_col].dropna()
            n_pre = len(s_pre)
            k_pre = int((s_pre >= 4).sum())
            val_pre_pct = (100.0 * k_pre / n_pre) if n_pre > 0 else None
            ci_low, ci_high = calc_wilson_ci(k_pre, n_pre)
            retro_caveat = "'Before' ratings were asked after the training (retrospective), which tends to overstate perceived change."
            findings.append(make_finding(
                fid=f"pre.{item}.agree_pct.overall",
                label=f"Agree or strongly agree they could {lbl} (retrospective 'before')",
                value=val_pre_pct,
                unit="pct",
                n=n_pre,
                n_total=len(df),
                numerator=k_pre,
                denominator_desc="respondents with a recognized answer to this retrospective 'before' item",
                group_dim="overall",
                group_level="all",
                source_cols=[pre_col],
                caveat=retro_caveat,
                ci_low=ci_low,
                ci_high=ci_high,
                ci_method="wilson95"
            ))

            val_pre_mean = float(s_pre.mean()) if n_pre > 0 else None
            ci_m_low, ci_m_high = calc_t_ci(s_pre)
            findings.append(make_finding(
                fid=f"pre.{item}.mean.overall",
                label=f"Average rating: I could {lbl} (retrospective 'before', 1-5)",
                value=val_pre_mean,
                unit="mean",
                n=n_pre,
                n_total=len(df),
                numerator=None,
                denominator_desc="respondents with a recognized answer to this retrospective 'before' item (1-5)",
                group_dim="overall",
                group_level="all",
                source_cols=[pre_col],
                caveat=retro_caveat,
                ci_low=ci_m_low,
                ci_high=ci_m_high,
                ci_method="t95"
            ))

        # Change (post minus pre)
        if post_col in df and pre_col in df:
            both = df[[post_col, pre_col]].dropna()
            diff_series = both[post_col] - both[pre_col]
            n_both = len(diff_series)
            val_diff = float(diff_series.mean()) if n_both > 0 else None
            ci_d_low, ci_d_high = calc_t_ci(diff_series)
            findings.append(make_finding(
                fid=f"change.{item}.mean_points.overall",
                label=f"Average self-rated change in ability to {lbl} (post minus pre, points 1-5)",
                value=val_diff,
                unit="points",
                n=n_both,
                n_total=len(df),
                numerator=None,
                denominator_desc="respondents with recognized answers to both the before and after item (post minus pre, points on 1-5)",
                group_dim="overall",
                group_level="all",
                source_cols=[post_col, pre_col],
                caveat="'Before' ratings were asked after the training (retrospective), which tends to overstate change.",
                ci_low=ci_d_low,
                ci_high=ci_d_high,
                ci_method="t95"
            ))

    # 2. Quality items
    qualities = [
        ("engaging", "quality_engaging", "presenter(s) engaged the participants"),
        ("knowledgeable", "quality_knowledgeable", "presenter(s) knew the subject matter well"),
        ("organized", "quality_organized", "training was well organized")
    ]
    for q_id, q_col, q_desc in qualities:
        if q_col in df:
            s_q = df[q_col].dropna()
            n_q = len(s_q)
            k_q = int((s_q >= 4).sum())
            val_q_pct = (100.0 * k_q / n_q) if n_q > 0 else None
            ci_low, ci_high = calc_wilson_ci(k_q, n_q)
            findings.append(make_finding(
                fid=f"quality.{q_id}.agree_pct.overall",
                label=f"Agree or strongly agree: {q_desc}",
                value=val_q_pct,
                unit="pct",
                n=n_q,
                n_total=len(df),
                numerator=k_q,
                denominator_desc="respondents with a recognized answer to this quality item",
                group_dim="overall",
                group_level="all",
                source_cols=[q_col],
                caveat="~12% non-response on training quality items (optional section).",
                ci_low=ci_low,
                ci_high=ci_high,
                ci_method="wilson95"
            ))

    # 3. Recommend 0-10 & NPS
    if "recommend" in df:
        s_rec = df["recommend"].dropna()
        n_rec = len(s_rec)
        val_rec_mean = float(s_rec.mean()) if n_rec > 0 else None
        ci_r_low, ci_r_high = calc_t_ci(s_rec)
        findings.append(make_finding(
            fid="recommend.score.mean.overall",
            label="Average likelihood to recommend the training (0-10)",
            value=val_rec_mean,
            unit="mean",
            n=n_rec,
            n_total=len(df),
            numerator=None,
            denominator_desc="respondents who gave a 0-10 recommend score",
            group_dim="overall",
            group_level="all",
            source_cols=["recommend"],
            caveat="",
            ci_low=ci_r_low,
            ci_high=ci_r_high,
            ci_method="t95"
        ))

        # NPS = %Promoters (9-10) - %Detractors (0-6)
        nps_val = (100.0 * ((s_rec >= 9).sum() - (s_rec <= 6).sum()) / n_rec) if n_rec > 0 else None
        findings.append(make_finding(
            fid="recommend.score.nps.overall",
            label="Net Promoter Score (% rating 9-10 minus % rating 0-6)",
            value=nps_val,
            unit="nps",
            n=n_rec,
            n_total=len(df),
            numerator=None,
            denominator_desc="respondents who gave a 0-10 recommend score (9-10 minus 0-6)",
            group_dim="overall",
            group_level="all",
            source_cols=["recommend"],
            caveat="Standard NPS calculation: % promoters (9-10) minus % detractors (0-6).",
            ci_low=None,
            ci_high=None,
            ci_method=None
        ))

    # 4. Call 988 likelihood
    if "call_988_likelihood" in df and "call_988_likelihood" not in missing_set:
        s_c988 = df["call_988_likelihood"].dropna()
        n_c988 = len(s_c988)
        val_c988_mean = float(s_c988.mean()) if n_c988 > 0 else None
        ci_c_low, ci_c_high = calc_t_ci(s_c988)
        findings.append(make_finding(
            fid="call_988.likelihood.mean.overall",
            label="Average likelihood to call 988 in a crisis (0-10)",
            value=val_c988_mean,
            unit="mean",
            n=n_c988,
            n_total=len(df),
            numerator=None,
            denominator_desc="respondents who answered the optional call-988 question",
            group_dim="overall",
            group_level="all",
            source_cols=["call_988_likelihood"],
            caveat="High non-response rate (~77% missing); represents only respondents who answered this optional question.",
            ci_low=ci_c_low,
            ci_high=ci_c_high,
            ci_method="t95"
        ))
    elif "call_988_likelihood" in missing_set:
        print("data pipeline: Column 'call_988_likelihood' missing from source; skipped related finding.")

    # 5. Missing training date count
    missing_dates = int(df["training_date"].isna().sum()) if "training_date" in df else len(df)
    findings.append(make_finding(
        fid="missing.training_date.count.overall",
        label="Count of responses missing training date",
        value=missing_dates,
        unit="count",
        n=len(df),
        n_total=len(df),
        numerator=None,
        denominator_desc="all rows",
        group_dim="overall",
        group_level="all",
        source_cols=["training_date"],
        caveat="",
        ci_low=None,
        ci_high=None,
        ci_method=None,
        n_missing=missing_dates
    ))

    # 6. Subgroup cuts (County, Role, Language)
    subgroups = [
        ("county", county_masks),
        ("role", role_masks),
        ("language", lang_masks)
    ]

    for dim, masks in subgroups:
        for level, (mask, words) in masks.items():
            sub_df = df[mask]
            sub_total = len(sub_df)

            # Post items for subgroup
            for item in items:
                post_col = f"post_{item}"
                if post_col in df:
                    s_sub = sub_df[post_col].dropna()
                    n_sub = len(s_sub)
                    k_sub = int((s_sub >= 4).sum())
                    val_sub_pct = (100.0 * k_sub / n_sub) if n_sub > 0 else None
                    ci_low, ci_high = calc_wilson_ci(k_sub, n_sub)
                    findings.append(make_finding(
                        fid=f"post.{item}.agree_pct.{dim}.{level}",
                        label=f"Agree or strongly agree they can {item_labels[item]} — {words}",
                        value=val_sub_pct,
                        unit="pct",
                        n=n_sub,
                        n_total=sub_total,
                        numerator=k_sub,
                        denominator_desc=f"{words} respondents with a recognized answer to this post item",
                        group_dim=dim,
                        group_level=level,
                        source_cols=[post_col, dim],
                        caveat="",
                        ci_low=ci_low,
                        ci_high=ci_high,
                        ci_method="wilson95"
                    ))

            # Recommend score mean for subgroup
            if "recommend" in df:
                s_rec_sub = sub_df["recommend"].dropna()
                n_rec_sub = len(s_rec_sub)
                val_rec_sub_mean = float(s_rec_sub.mean()) if n_rec_sub > 0 else None
                ci_r_low, ci_r_high = calc_t_ci(s_rec_sub)
                findings.append(make_finding(
                    fid=f"recommend.score.mean.{dim}.{level}",
                    label=f"Average recommend score (0-10) — {words}",
                    value=val_rec_sub_mean,
                    unit="mean",
                    n=n_rec_sub,
                    n_total=sub_total,
                    numerator=None,
                    denominator_desc=f"{words} respondents who gave a 0-10 recommend score",
                    group_dim=dim,
                    group_level=level,
                    source_cols=["recommend", dim],
                    caveat="",
                    ci_low=ci_r_low,
                    ci_high=ci_r_high,
                    ci_method="t95"
                ))

                # Recommend NPS for subgroup
                nps_sub = (100.0 * ((s_rec_sub >= 9).sum() - (s_rec_sub <= 6).sum()) / n_rec_sub) if n_rec_sub > 0 else None
                findings.append(make_finding(
                    fid=f"recommend.score.nps.{dim}.{level}",
                    label=f"Net Promoter Score (NPS) — {words}",
                    value=nps_sub,
                    unit="nps",
                    n=n_rec_sub,
                    n_total=sub_total,
                    numerator=None,
                    denominator_desc=f"{words} respondents who gave a 0-10 recommend score (9-10 minus 0-6)",
                    group_dim=dim,
                    group_level=level,
                    source_cols=["recommend", dim],
                    caveat="Standard NPS calculation: % promoters (9-10) minus % detractors (0-6)."
                ))

            # Quality items for subgroup
            for q_id, q_col, q_desc in qualities:
                if q_col in df:
                    s_q_sub = sub_df[q_col].dropna()
                    n_q_sub = len(s_q_sub)
                    k_q_sub = int((s_q_sub >= 4).sum())
                    val_q_sub = (100.0 * k_q_sub / n_q_sub) if n_q_sub > 0 else None
                    ci_q_l, ci_q_h = calc_wilson_ci(k_q_sub, n_q_sub)
                    findings.append(make_finding(
                        fid=f"quality.{q_id}.agree_pct.{dim}.{level}",
                        label=f"Agree or strongly agree: {q_desc} — {words}",
                        value=val_q_sub,
                        unit="pct",
                        n=n_q_sub,
                        n_total=sub_total,
                        numerator=k_q_sub,
                        denominator_desc=f"{words} respondents with a recognized answer to this quality item",
                        group_dim=dim,
                        group_level=level,
                        source_cols=[q_col, dim],
                        caveat="~12% non-response on quality items.",
                        ci_low=ci_q_l,
                        ci_high=ci_q_h,
                        ci_method="wilson95"
                    ))

    # 7. Sensitivity findings: exclude respondents who chose "Strongly disagree" (1) on all 3 post items
    post_cols_present = [f"post_{item}" for item in items if f"post_{item}" in df]
    if len(post_cols_present) == 3:
        is_straightline = (df["post_identify_crisis"] == 1) & (df["post_describe_988"] == 1) & (df["post_know_when_to_use"] == 1)
        df_sens = df[~is_straightline]
        for item in items:
            lbl = item_labels[item]
            p_col = f"post_{item}"
            s_sens = df_sens[p_col].dropna()
            n_sens = len(s_sens)
            k_sens = int((s_sens >= 4).sum())
            val_sens = (100.0 * k_sens / n_sens) if n_sens > 0 else None
            ci_l, ci_h = calc_wilson_ci(k_sens, n_sens)
            findings.append(make_finding(
                fid=f"post.{item}.agree_pct.sensitivity.excl_straightline",
                label=f"Agree or strongly agree they can {lbl} (sensitivity: excluding 31 all-strongly-disagree respondents)",
                value=val_sens,
                unit="pct",
                n=n_sens,
                n_total=len(df_sens),
                numerator=k_sens,
                denominator_desc="respondents with a recognized answer, excluding those who chose 'Strongly disagree' on every post item",
                group_dim="sensitivity",
                group_level="excl_straightline",
                source_cols=[p_col],
                caveat="Excludes 31 respondents who marked Strongly Disagree on all three post items (potential disengagement or scale misread).",
                ci_low=ci_l,
                ci_high=ci_h,
                ci_method="wilson95"
            ))

    # 8. Sample composition: total, role, county, language
    findings.append(make_finding(
        fid="sample.respondents.count.overall",
        label="Total survey respondents in dataset",
        value=len(df),
        unit="count",
        n=len(df),
        n_total=len(df),
        numerator=len(df),
        denominator_desc="total survey respondents",
        group_dim="overall",
        group_level="all",
        source_cols=["response_id"]
    ))

    for dim, masks in subgroups:
        for level, (mask, words) in masks.items():
            k_comp = int(mask.sum())
            pct_comp = (100.0 * k_comp / len(df)) if len(df) > 0 else None
            ci_l, ci_h = calc_wilson_ci(k_comp, len(df))
            findings.append(make_finding(
                fid=f"sample.respondents.count.{dim}.{level}",
                label=f"Respondent count — {words}",
                value=k_comp,
                unit="count",
                n=len(df),
                n_total=len(df),
                numerator=k_comp,
                denominator_desc="total survey respondents",
                group_dim=dim,
                group_level=level,
                source_cols=[dim]
            ))
            findings.append(make_finding(
                fid=f"sample.respondents.pct.{dim}.{level}",
                label=f"Share of total respondents — {words} (%)",
                value=pct_comp,
                unit="pct",
                n=len(df),
                n_total=len(df),
                numerator=k_comp,
                denominator_desc="total survey respondents",
                group_dim=dim,
                group_level=level,
                source_cols=[dim],
                ci_low=ci_l,
                ci_high=ci_h,
                ci_method="wilson95"
            ))

    # 9. Time cuts: Training Periods & Training Months
    if "training_month" in df:
        month_series = df["training_month"].fillna("")
        period_masks = {
            "spring_2026": (month_series.isin(["2026-04", "2026-05"]), "Spring 2026 (Apr–May)"),
            "fall_2026": (month_series.isin(["2026-09", "2026-10"]), "Fall 2026 (Sep–Oct)"),
            "other_periods": ((month_series != "") & ~month_series.isin(["2026-04", "2026-05", "2026-09", "2026-10"]), "Other months")
        }
        for p_level, (p_mask, p_words) in period_masks.items():
            p_sub = df[p_mask]
            p_total = len(p_sub)
            for item in items:
                p_col = f"post_{item}"
                if p_col in df:
                    s_p = p_sub[p_col].dropna()
                    n_p = len(s_p)
                    k_p = int((s_p >= 4).sum())
                    val_p = (100.0 * k_p / n_p) if n_p > 0 else None
                    ci_l, ci_h = calc_wilson_ci(k_p, n_p)
                    findings.append(make_finding(
                        fid=f"post.{item}.agree_pct.training_period.{p_level}",
                        label=f"Agree or strongly agree they can {item_labels[item]} — {p_words}",
                        value=val_p,
                        unit="pct",
                        n=n_p,
                        n_total=p_total,
                        numerator=k_p,
                        denominator_desc=f"{p_words} respondents with a recognized answer to this post item",
                        group_dim="training_period",
                        group_level=p_level,
                        source_cols=[p_col, "training_date"],
                        ci_low=ci_l,
                        ci_high=ci_h,
                        ci_method="wilson95"
                    ))
            if "recommend" in df:
                s_r_p = p_sub["recommend"].dropna()
                n_r_p = len(s_r_p)
                val_r_p = float(s_r_p.mean()) if n_r_p > 0 else None
                ci_l, ci_h = calc_t_ci(s_r_p)
                findings.append(make_finding(
                    fid=f"recommend.score.mean.training_period.{p_level}",
                    label=f"Average recommend score (0-10) — {p_words}",
                    value=val_r_p,
                    unit="mean",
                    n=n_r_p,
                    n_total=p_total,
                    numerator=None,
                    denominator_desc=f"{p_words} respondents who gave a 0-10 recommend score",
                    group_dim="training_period",
                    group_level=p_level,
                    source_cols=["recommend", "training_date"],
                    ci_low=ci_l,
                    ci_high=ci_h,
                    ci_method="t95"
                ))

        # Monthly line cuts
        unique_months = sorted([m for m in month_series.unique() if m])
        for ym in unique_months:
            m_level = ym.replace("-", "_")
            m_mask = month_series == ym
            m_sub = df[m_mask]
            m_total = len(m_sub)
            for item in items:
                p_col = f"post_{item}"
                if p_col in df:
                    s_m = m_sub[p_col].dropna()
                    n_m = len(s_m)
                    k_m = int((s_m >= 4).sum())
                    val_m = (100.0 * k_m / n_m) if n_m > 0 else None
                    ci_l, ci_h = calc_wilson_ci(k_m, n_m)
                    findings.append(make_finding(
                        fid=f"post.{item}.agree_pct.training_month.{m_level}",
                        label=f"Agree or strongly agree they can {item_labels[item]} — {ym}",
                        value=val_m,
                        unit="pct",
                        n=n_m,
                        n_total=m_total,
                        numerator=k_m,
                        denominator_desc=f"{ym} respondents with a recognized answer to this post item",
                        group_dim="training_month",
                        group_level=m_level,
                        source_cols=[p_col, "training_date"],
                        ci_low=ci_l,
                        ci_high=ci_h,
                        ci_method="wilson95"
                    ))
            if "recommend" in df:
                s_r_m = m_sub["recommend"].dropna()
                n_r_m = len(s_r_m)
                val_r_m = float(s_r_m.mean()) if n_r_m > 0 else None
                ci_l, ci_h = calc_t_ci(s_r_m)
                findings.append(make_finding(
                    fid=f"recommend.score.mean.training_month.{m_level}",
                    label=f"Average recommend score (0-10) — {ym}",
                    value=val_r_m,
                    unit="mean",
                    n=n_r_m,
                    n_total=m_total,
                    numerator=None,
                    denominator_desc=f"{ym} respondents who gave a 0-10 recommend score",
                    group_dim="training_month",
                    group_level=m_level,
                    source_cols=["recommend", "training_date"],
                    ci_low=ci_l,
                    ci_high=ci_h,
                    ci_method="t95"
                ))

    # 10. Score distributions: Recommend 0-10
    if "recommend" in df:
        s_rec = df["recommend"].dropna()
        n_rec = len(s_rec)
        for k in range(11):
            k_count = int((s_rec == k).sum())
            k_pct = (100.0 * k_count / n_rec) if n_rec > 0 else None
            ci_l, ci_h = calc_wilson_ci(k_count, n_rec)
            findings.append(make_finding(
                fid=f"recommend.score.dist_{k}.overall",
                label=f"Recommend score: {k} out of 10 (% of respondents)",
                value=k_pct,
                unit="pct",
                n=n_rec,
                n_total=len(df),
                numerator=k_count,
                denominator_desc="respondents who gave a 0-10 recommend score",
                group_dim="overall",
                group_level="all",
                source_cols=["recommend"],
                ci_low=ci_l,
                ci_high=ci_h,
                ci_method="wilson95"
            ))

    # 11. Score distributions: Call 988 0-10
    if "call_988_likelihood" in df and "call_988_likelihood" not in missing_set:
        s_c988 = df["call_988_likelihood"].dropna()
        n_c988 = len(s_c988)
        for k in range(11):
            k_count = int((s_c988 == k).sum())
            k_pct = (100.0 * k_count / n_c988) if n_c988 > 0 else None
            ci_l, ci_h = calc_wilson_ci(k_count, n_c988)
            findings.append(make_finding(
                fid=f"call_988.likelihood.dist_{k}.overall",
                label=f"Likelihood to call 988: {k} out of 10 (% of respondents)",
                value=k_pct,
                unit="pct",
                n=n_c988,
                n_total=len(df),
                numerator=k_count,
                denominator_desc="respondents who answered the optional call-988 question",
                group_dim="overall",
                group_level="all",
                source_cols=["call_988_likelihood"],
                caveat="High non-response rate (~77% missing); represents only respondents who answered this optional question.",
                ci_low=ci_l,
                ci_high=ci_h,
                ci_method="wilson95"
            ))

    return findings


def run_pipeline(data_path: Path, output_csv: Path, output_findings: Path,
                 output_validation: Path) -> int:
    """Execute end-to-end data pipeline."""
    if not data_path.exists():
        sys.exit(f"Data pipeline error: Data file not found: {data_path}")

    # 1. Read sheet 'Survey Data' or fail naming available sheets
    try:
        xl = pd.ExcelFile(data_path)
    except Exception as e:
        sys.exit(f"Data pipeline error: Failed to read Excel workbook at {data_path}: {e}")

    if "Survey Data" not in xl.sheet_names:
        sys.exit(f"Data pipeline error: Sheet 'Survey Data' not found in {data_path}. Found sheets: {xl.sheet_names}")

    df_raw = xl.parse("Survey Data")
    file_bytes = data_path.read_bytes()
    file_sha256 = hashlib.sha256(file_bytes).hexdigest()

    # 2. Load mappings & clean dataset
    col_map, likert_map, county_rules, role_rules, lang_rules = load_mappings()
    df_clean, val_summary = clean_dataset(df_raw, col_map, likert_map, county_rules, role_rules, lang_rules)

    # 3. Write data/processed/survey_clean.csv (local only)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df_clean.to_csv(output_csv, index=False, encoding="utf-8")
    print(f"data pipeline: Cleaned {len(df_clean)} rows -> {output_csv}")

    # 4. Write outputs/validation_report.json
    val_report = {
        "source": {
            "file_sha256": file_sha256,
            "sheet": "Survey Data",
            "n_rows": len(df_raw)
        },
        "validation": val_summary
    }
    output_validation.parent.mkdir(parents=True, exist_ok=True)
    with open(output_validation, "w", encoding="utf-8") as f:
        json.dump(val_report, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"data pipeline: Validation report -> {output_validation}")

    # 5. Compute findings and write outputs/findings.json
    findings_list = compute_all_findings(
        df=df_clean,
        source_sha=file_sha256,
        n_raw=len(df_raw),
        missing_cols=val_summary.get("missing_columns_in_source")
    )
    findings_obj = {
        "schema_version": "1",
        "note": "Single source of truth for quantitative numbers. Aggregates only.",
        "source": {
            "file_sha256": file_sha256,
            "sheet": "Survey Data",
            "n_rows": len(df_raw)
        },
        "small_n_threshold": SMALL_N_THRESHOLD,
        "findings": findings_list
    }
    output_findings.parent.mkdir(parents=True, exist_ok=True)
    with open(output_findings, "w", encoding="utf-8") as f:
        json.dump(findings_obj, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"data pipeline: {len(findings_list)} findings -> {output_findings}")

    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Clean raw survey data and produce findings.")
    parser.add_argument("--data", default=str(ROOT / "data/raw/BuildFest_EveryMind_Survey_Data_FULL.xlsx"),
                        help="Path to raw survey Excel file")
    parser.add_argument("--output-csv", default=str(ROOT / "data/processed/survey_clean.csv"),
                        help="Path for cleaned CSV output")
    parser.add_argument("--output-findings", default=str(ROOT / "outputs/findings.json"),
                        help="Path for findings JSON output")
    parser.add_argument("--output-validation", default=str(ROOT / "outputs/validation_report.json"),
                        help="Path for validation report JSON output")
    args = parser.parse_args(argv)

    return run_pipeline(
        data_path=Path(args.data),
        output_csv=Path(args.output_csv),
        output_findings=Path(args.output_findings),
        output_validation=Path(args.output_validation)
    )


if __name__ == "__main__":
    sys.exit(main())
