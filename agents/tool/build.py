#!/usr/bin/env python3
"""Build outputs/dashboard.html from outputs/findings.json and outputs/themes.json.

- One self-contained HTML file: inline CSS and JS, no network at view time.
- Aggregates only. Every number shown comes from findings.json / themes.json; this
  script and the page never compute new statistics (they only format, sort and select).
- Deterministic: the same inputs give a byte-identical file (no timestamps).
- Generic over finding IDs: new counties, roles, months, labels or metrics appear
  without code changes. Small groups (n < small_n_threshold) never show a value.

Usage:
    python3 agents/tool/build.py                       # outputs/*.json -> outputs/dashboard.html
    python3 agents/tool/build.py --strict              # fail if outputs/*.json are missing
    python3 agents/tool/build.py --findings F --themes T --out O
If outputs/*.json don't exist yet (and --strict is off), the synthetic files in
contracts/examples/ are used and the page is stamped EXAMPLE.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
WEB = HERE / "web"
CONTRACTS = ROOT / "contracts"
EXAMPLES = CONTRACTS / "examples"
OUTPUTS = ROOT / "outputs"

DEFAULTS = {
    "findings": OUTPUTS / "findings.json",
    "themes": OUTPUTS / "themes.json",
    "validation": OUTPUTS / "validation_report.json",
    "out": OUTPUTS / "dashboard.html",
}
EXAMPLE_FILES = {
    "findings": EXAMPLES / "findings.example.json",
    "themes": EXAMPLES / "themes.example.json",
}

# Only these finding fields are embedded in the page (never anything row-level).
RECORD_KEYS = (
    "id", "label", "value", "unit", "n", "numerator", "n_missing", "denominator",
    "ci_low", "ci_high", "ci_method", "small_n", "suppressed", "caveat",
)

# Plain-language names. Labels only: no numbers live here.
MEASURE_LABELS = {
    "post": "After training",
    "pre": "Before training (recalled after)",
    "change": "Self-rated change",
    "quality": "Training quality",
    "recommend": "Would recommend",
    "call_988": "Would call 988",
    "missing": "Data completeness",
    "sample": "Who took the survey",
    "themes": "Comments",
}
ITEM_LABELS = {
    "identify_crisis": "Can identify mental health challenges and crises",
    "describe_988": "Can describe 988 and how it works",
    "know_when_to_use": "Knows when to use 988",
    "engaging": "Presenters engaged the participants",
    "knowledgeable": "Presenters knew the subject well",
    "organized": "Training was well organized",
    "score": "Would recommend the training (0–10)",
    "likelihood": "Likely to call 988 in a crisis (0–10)",
    "training_date": "Training date",
    "respondents": "Respondents",
}
STAT_LABELS = {
    "agree_pct": "% agree or strongly agree",
    "mean": "average",
    "median": "median",
    "mean_points": "average change (points)",
    "nps": "Net Promoter Score",
    "count": "count",
    "pct": "% of comments",
}
DIMENSION_LABELS = {
    "overall": "Everyone",
    "county": "County",
    "role": "Role",
    "language": "Survey language",
    "training_month": "Training month",
    "training_period": "Training period",
    "sensitivity": "Sensitivity check",
}
SAMPLE_STAT_LABELS = {"pct": "% of all respondents", "count": "number of respondents"}
SEASON_MONTH = {"winter": 1, "spring": 4, "summer": 7, "fall": 9, "autumn": 9}
DIMENSION_ORDER = ["county", "role", "language", "training_period", "training_month"]
TIME_DIMENSIONS = {"training_month", "training_period", "month", "period", "quarter"}
LEVEL_LABELS = {
    "all": "All respondents",
    "other_pooled": "Other (small groups pooled)",
    "unknown": "Not recorded",
    "en": "English",
    "es": "Spanish",
    "prince_georges": "Prince George's",
    "queen_annes": "Queen Anne's",
    "st_marys": "St. Mary's",
    "caregiver_parent": "Caregiver / parent",
    "caregiver": "Caregiver / parent",
    "multiple": "More than one role",
    "school_staff": "School staff",
    "other": "Other (e.g., community member)",
    "other_periods": "Other months",
    "excl_straightline": "Excluding same-answer-throughout responses",
}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
FIELD_LABELS = {"valuable": "Most valuable thing learned", "improve": "How to improve the training"}
DIST_STAT = re.compile(r"^dist_(\d+)$")


class BuildError(Exception):
    """A problem the person running the build can fix; printed without a traceback."""


# --------------------------------------------------------------------------- inputs

def load_json(path: Path, what: str) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise BuildError(f"{what} at {path} is not valid JSON: {e}") from None


def validate(doc: dict, schema_name: str, what: str) -> None:
    schema_path = CONTRACTS / schema_name
    try:
        import jsonschema
    except ImportError:  # pragma: no cover - requirements.txt installs it
        print(f"build: jsonschema not installed; skipping contract check for {what}", file=sys.stderr)
        return
    schema = load_json(schema_path, f"schema {schema_name}")
    errors = sorted(jsonschema.Draft202012Validator(schema).iter_errors(doc), key=lambda e: list(e.path))
    if errors:
        lines = [f"  - at {'/'.join(map(str, e.path)) or '(root)'}: {e.message}" for e in errors[:10]]
        more = f"\n  ... and {len(errors) - 10} more" if len(errors) > 10 else ""
        raise BuildError(f"{what} does not match contracts/{schema_name}:\n" + "\n".join(lines) + more)


def is_synthetic(doc: dict, path: Path) -> bool:
    note = str(doc.get("note") or "").upper()
    sha = str((doc.get("source") or {}).get("file_sha256") or "")
    try:
        in_examples = path.resolve().parent == EXAMPLES.resolve()
    except OSError:
        in_examples = False
    return in_examples or "SYNTHETIC" in note or "EXAMPLE" in note or (bool(sha) and set(sha) == {"0"})


def resolve_input(kind: str, given: Path | None, strict: bool) -> tuple[Path | None, bool]:
    """Return (path, fell_back_to_example)."""
    path = given or DEFAULTS[kind]
    if path.exists():
        return path, False
    if given is not None or strict:
        raise BuildError(
            f"{kind}: {path} does not exist. Run `make data` (findings) / `make themes` (themes) "
            f"first, or drop --strict to build on the synthetic examples."
        )
    fallback = EXAMPLE_FILES.get(kind)
    if fallback and fallback.exists():
        print(f"build: WARNING {path.relative_to(ROOT)} not found; using synthetic {fallback.relative_to(ROOT)} "
              f"(page stamped EXAMPLE)", file=sys.stderr)
        return fallback, True
    return None, False


# --------------------------------------------------------------------------- shaping

def split_id(fid: str, dimension: str, level: str) -> tuple[str, str]:
    """(metric key, level slug). post.identify_crisis.agree_pct.county.anne_arundel -> (post.identify_crisis.agree_pct, anne_arundel).

    Works whether group.level is the slug ("anne_arundel") or a display name ("Anne Arundel").
    """
    parts = fid.split(".")
    if dimension == "overall":
        if fid.endswith(".overall") and len(parts) > 1:
            return fid[: -len(".overall")], "all"
        return (".".join(parts[:3]) if len(parts) > 3 else fid), "all"
    suffix = f".{dimension}.{level}"
    if fid.endswith(suffix) and len(fid) > len(suffix):
        return fid[: -len(suffix)], level
    if len(parts) >= 4 and parts[-2] == dimension:
        return ".".join(parts[:-2]), parts[-1]
    return (".".join(parts[:3]) if len(parts) > 3 else fid), level


def metric_key(fid: str, dimension: str, level: str) -> str:
    return split_id(fid, dimension, level)[0]


def pretty(slug: str) -> str:
    words = slug.replace("_", " ").split()
    return " ".join(w if w.isupper() else w[:1].upper() + w[1:] for w in words) or slug


def _month(y: str, m: str) -> str | None:
    return f"{MONTHS[int(m) - 1]} {y}" if 1 <= int(m) <= 12 else None


def level_label(dimension: str, level: str, group: dict, raw_level: str | None = None) -> str:
    for k in ("label", "level_label"):
        if isinstance(group.get(k), str) and group[k].strip():
            return group[k].strip()
    if level in LEVEL_LABELS:
        return LEVEL_LABELS[level]
    if raw_level and raw_level != level and not re.fullmatch(r"[a-z0-9_]+", raw_level):
        return raw_level.strip()  # group.level already is a display name, e.g. "Prince George's"
    m = re.fullmatch(r"(\d{4})[_-](\d{1,2})", level)
    if m and _month(m.group(1), m.group(2)):
        return _month(m.group(1), m.group(2))
    m = re.fullmatch(r"(\d{4})[_-](\d{1,2})_to_(\d{4})[_-](\d{1,2})", level)
    if m and _month(m.group(1), m.group(2)) and _month(m.group(3), m.group(4)):
        a, z = _month(m.group(1), m.group(2)), _month(m.group(3), m.group(4))
        return a if a == z else f"{a} – {z}"
    return pretty(level)


def time_key(level: str) -> int:
    """Months since year 0 for YYYY_MM, YYYY-MM_to_YYYY-MM and season_YYYY levels; unparseable levels sort last."""
    m = re.match(r"(\d{4})[_-](\d{1,2})(?:_to_|$)", level)
    if m:
        return int(m.group(1)) * 12 + int(m.group(2)) - 1
    m = re.fullmatch(r"(winter|spring|summer|fall|autumn)[_-](\d{4})", level)
    if m:
        return int(m.group(2)) * 12 + SEASON_MONTH[m.group(1)] - 1
    return 10**9


def dimension_label(dim: str) -> str:
    return DIMENSION_LABELS.get(dim, pretty(dim))


def metric_parts(key: str) -> dict:
    parts = key.split(".")
    if parts[0] == "themes" and len(parts) >= 4:
        return {"measure": "themes", "field": parts[1], "item": parts[2], "stat": parts[3]}
    measure = parts[0]
    item = parts[1] if len(parts) > 1 else ""
    stat = parts[2] if len(parts) > 2 else ""
    return {"measure": measure, "field": None, "item": item, "stat": stat}


def scale_for(measure: str, unit: str, stat: str) -> dict:
    """Axis domain + mark for a metric. Bars always start at zero; means/points/NPS use dots."""
    if unit == "pct":
        return {"lo": 0, "hi": 100, "mark": "bar", "fixed": True}
    if unit == "count":
        return {"lo": 0, "hi": None, "mark": "bar", "fixed": False}
    if unit == "nps":
        return {"lo": -100, "hi": 100, "mark": "dot", "fixed": True}
    if unit in ("mean", "median"):
        if measure in ("post", "pre", "quality"):
            return {"lo": 1, "hi": 5, "mark": "dot", "fixed": True}
        if measure in ("recommend", "call_988"):
            return {"lo": 0, "hi": 10, "mark": "dot", "fixed": True}
        return {"lo": 0, "hi": None, "mark": "dot", "fixed": False}
    if unit == "points":
        return {"lo": None, "hi": None, "mark": "dot", "fixed": False, "zero": True}
    return {"lo": 0, "hi": None, "mark": "dot", "fixed": False}


def record(f: dict, threshold: int, warnings: list[str]) -> dict:
    r = {k: f.get(k) for k in RECORD_KEYS}
    g = f.get("group") or {}
    r["dimension"] = str(g.get("dimension", "overall"))
    raw_level = str(g.get("level", "all"))
    r["metric"], r["level"] = split_id(str(r["id"]), r["dimension"], raw_level)
    r["level_label"] = level_label(r["dimension"], r["level"], g, raw_level)
    r["hidden_by_dashboard"] = False
    n = r.get("n")
    # Privacy backstop: a value from fewer than `threshold` people is never put in the page.
    if r.get("value") is not None and isinstance(n, int) and n < threshold:
        warnings.append(f"{r['id']}: n={n} < {threshold} but value not suppressed; hidden in dashboard")
        r["hidden_by_dashboard"] = True
    if r.get("value") is None or r["hidden_by_dashboard"]:
        r["suppressed"] = True
        for k in ("value", "ci_low", "ci_high", "numerator"):
            r[k] = None
    if isinstance(n, int) and n < threshold:
        r["small_n"] = True
    return r


def theme_record(c: dict, taxonomy: dict, threshold: int, warnings: list[str]) -> dict:
    field = c.get("field", "")
    tax = taxonomy.get((field, c.get("theme_id"))) or {}
    as_finding = {
        "id": c["id"],
        "label": tax.get("label") or pretty(str(c.get("theme_id", ""))),
        "value": c.get("pct"),
        "unit": "pct",
        "n": c.get("n"),
        "numerator": c.get("n_mentions"),
        "n_missing": None,
        "denominator": f"people in this group who wrote a comment on “{FIELD_LABELS.get(field, pretty(field)).lower()}”",
        "ci_low": c.get("ci_low"),
        "ci_high": c.get("ci_high"),
        "ci_method": c.get("ci_method"),
        "small_n": c.get("small_n"),
        "suppressed": c.get("suppressed"),
        "caveat": c.get("caveat") or "A comment can mention several themes, so shares don't add up to 100%.",
        "group": c.get("group") or {},
    }
    return record(as_finding, threshold, warnings)


def group_metrics(records: list[dict], titles: dict) -> list[dict]:
    metrics: dict[str, dict] = {}
    for r in records:
        key = r.pop("metric")
        m = metrics.get(key)
        if m is None:
            parts = metric_parts(key)
            sc = scale_for(parts["measure"], r.get("unit") or "", parts["stat"])
            dist = DIST_STAT.match(parts["stat"])
            m = metrics[key] = {
                "key": key, **parts, "unit": r.get("unit"), "scale": sc,
                "dist_bin": int(dist.group(1)) if dist else None,
                "measure_label": MEASURE_LABELS.get(parts["measure"], pretty(parts["measure"])),
                "item_label": titles.get(key) or ITEM_LABELS.get(parts["item"]) or pretty(parts["item"]),
                "stat_label": (SAMPLE_STAT_LABELS if parts["measure"] == "sample" else STAT_LABELS).get(
                    parts["stat"], pretty(parts["stat"])),
                "overall": None, "dims": {},
            }
        if r["dimension"] == "overall":
            m["overall"] = r
        else:
            m["dims"].setdefault(r["dimension"], []).append(r)
    out = []
    for key in sorted(metrics):
        m = metrics[key]
        dims = {}
        for d in sorted(m["dims"], key=lambda d: (DIMENSION_ORDER.index(d) if d in DIMENSION_ORDER else 99, d)):
            if d in TIME_DIMENSIONS:
                rows = sorted(m["dims"][d], key=lambda r: (time_key(r["level"]), r["level"]))
            else:
                rows = sorted(m["dims"][d], key=lambda r: (r["level"] == "other_pooled", r["level"]))
            dims[d] = rows
        m["dims"] = dims
        m["dim_order"] = list(dims)  # JSON objects are emitted with sorted keys; this keeps the intended order
        out.append(m)
    return out


def flatten(obj, prefix="", out=None, limit=300):
    """Scalar leaves of an aggregate report as [path, value] pairs (for the data-checks table)."""
    out = [] if out is None else out
    if len(out) >= limit:
        return out
    if isinstance(obj, dict):
        for k in sorted(obj):
            flatten(obj[k], f"{prefix} › {k}" if prefix else str(k), out, limit)
    elif isinstance(obj, list):
        if all(not isinstance(x, (dict, list)) for x in obj):
            out.append([prefix, ", ".join(str(x) for x in obj[:20]) + (" …" if len(obj) > 20 else "")])
        else:
            for i, x in enumerate(obj[:50]):
                flatten(x, f"{prefix} › {i + 1}", out, limit)
    elif isinstance(obj, (str, int, float, bool)) or obj is None:
        out.append([prefix, obj])
    return out


def build_view_model(findings: dict, themes: dict | None, validation: dict | None,
                     findings_synthetic: bool, themes_synthetic: bool) -> tuple[dict, list[str]]:
    warnings: list[str] = []
    threshold = int(findings.get("small_n_threshold") or 10)
    ids = [f["id"] for f in findings["findings"]]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        raise BuildError(f"findings.json has duplicate IDs (IDs must be unique and stable): {', '.join(dupes[:10])}")

    records = [record(f, threshold, warnings) for f in findings["findings"]]
    metrics = group_metrics(records, {})

    theme_block = None
    if themes is not None:
        taxonomy = {(t["field"], t["theme_id"]): t for t in themes.get("taxonomy", [])}
        trecs = [theme_record(c, taxonomy, threshold, warnings) for c in themes.get("counts", [])]
        tids = [r["id"] for r in trecs]
        tdupes = sorted({i for i in tids if tids.count(i) > 1})
        if tdupes:
            raise BuildError(f"themes.json has duplicate count IDs: {', '.join(tdupes[:10])}")
        tmetrics = group_metrics(trecs, {})
        for m in tmetrics:
            tax = taxonomy.get((m["field"], m["item"])) or {}
            m["item_label"] = tax.get("label") or pretty(m["item"])
            m["description"] = tax.get("description", "")
            m["measure_label"] = f"Comments: {FIELD_LABELS.get(m['field'], pretty(m['field'] or ''))}"
        metrics += tmetrics
        theme_block = {
            "method": themes.get("method", ""),
            "validation": themes.get("validation"),
            "spanish": themes.get("spanish"),
            "pii_screen": themes.get("pii_screen"),
            "fields": {f: FIELD_LABELS.get(f, pretty(f)) for f in {t["field"] for t in themes.get("taxonomy", [])}},
            "field_order": sorted({t["field"] for t in themes.get("taxonomy", [])},
                                  key=lambda f: (list(FIELD_LABELS).index(f) if f in FIELD_LABELS else 9, f)),
            "source": themes.get("source"),
            "schema_version": themes.get("schema_version"),
            "synthetic": themes_synthetic,
        }

    src = findings.get("source") or {}
    tsrc = (themes or {}).get("source") or {}
    # Same export? A matching fingerprint confirms it. themes.py may fingerprint the cleaned file
    # rather than the xlsx, so a different fingerprint alone is "unconfirmed"; different row counts is a mismatch.
    t_sha = tsrc.get("raw_file_sha256") or tsrc.get("file_sha256")
    if t_sha and t_sha == src.get("file_sha256"):
        sources_match = "yes"
    elif tsrc.get("n_rows") is not None and src.get("n_rows") is not None and tsrc["n_rows"] != src["n_rows"]:
        sources_match = "no"
        warnings.append(f"themes.json covers {tsrc['n_rows']} rows but findings.json covers {src['n_rows']}: "
                        "they were built from different exports")
    elif themes is None:
        sources_match = "n/a"
    else:
        sources_match = "unconfirmed"

    caveats = sorted({r["caveat"] for r in records if r.get("caveat")})
    vm = {
        "meta": {
            "title": "Understanding 988 training: post-training survey dashboard",
            "synthetic": findings_synthetic or themes_synthetic,
            "findings_synthetic": findings_synthetic,
            "themes_synthetic": themes_synthetic,
            "source": {"file_sha256": src.get("file_sha256"), "sheet": src.get("sheet"), "n_rows": src.get("n_rows")},
            "themes_source": tsrc or None,
            "sources_match": sources_match,
            "findings_schema_version": findings.get("schema_version"),
            "small_n_threshold": threshold,
            "n_findings": len(records),
            "n_hidden": sum(1 for r in records if r["suppressed"]),
            "dimension_labels": {**DIMENSION_LABELS},
            "time_dimensions": sorted(TIME_DIMENSIONS),
            "warnings": warnings,
        },
        "metrics": metrics,
        "caveats": caveats,
        "themes": theme_block,
        "validation_report": flatten(validation) if validation is not None else None,
    }
    for m in metrics:  # dimension labels for anything new
        for d in m["dims"]:
            vm["meta"]["dimension_labels"].setdefault(d, dimension_label(d))
    return vm, warnings


# --------------------------------------------------------------------------- render

def embed_json(obj) -> str:
    s = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    # Safe inside <script type="application/json">: no tag can be closed from the data.
    return s.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def render(vm: dict) -> str:
    template = (WEB / "template.html").read_text(encoding="utf-8")
    css = (WEB / "dashboard.css").read_text(encoding="utf-8")
    js = (WEB / "dashboard.js").read_text(encoding="utf-8")
    title = vm["meta"]["title"] + (" (EXAMPLE DATA)" if vm["meta"]["synthetic"] else "")
    html = (template
            .replace("__TITLE__", title.replace("&", "&amp;").replace("<", "&lt;"))
            .replace("/*__CSS__*/", css)
            .replace("__DATA__", embed_json(vm))
            .replace("/*__JS__*/", js))
    return html


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Build the self-contained survey dashboard (outputs/dashboard.html)")
    p.add_argument("--findings", type=Path, default=None, help="default: outputs/findings.json")
    p.add_argument("--themes", type=Path, default=None, help="default: outputs/themes.json")
    p.add_argument("--validation", type=Path, default=None, help="default: outputs/validation_report.json (optional)")
    p.add_argument("--out", type=Path, default=DEFAULTS["out"])
    p.add_argument("--strict", action="store_true", help="fail instead of falling back to contracts/examples")
    args = p.parse_args(argv)

    try:
        fpath, f_fb = resolve_input("findings", args.findings, args.strict)
        findings = load_json(fpath, "findings")
        validate(findings, "findings.schema.json", f"findings ({fpath})")

        themes, t_syn = None, False
        tpath, t_fb = resolve_input("themes", args.themes, args.strict)  # raises if named/strict and missing
        if tpath is not None:
            themes = load_json(tpath, "themes")
            validate(themes, "themes.schema.json", f"themes ({tpath})")
            t_syn = t_fb or is_synthetic(themes, tpath)

        vpath = args.validation or DEFAULTS["validation"]
        validation = load_json(vpath, "validation report") if vpath.exists() else None

        vm, warnings = build_view_model(findings, themes, validation,
                                        f_fb or is_synthetic(findings, fpath), t_syn)
        html = render(vm)
    except BuildError as e:
        print(f"build: ERROR {e}", file=sys.stderr)
        return 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(html, encoding="utf-8")
    for w in warnings:
        print(f"build: WARNING {w}", file=sys.stderr)
    meta = vm["meta"]
    tag = " [EXAMPLE DATA]" if meta["synthetic"] else ""
    try:
        shown = args.out.resolve().relative_to(ROOT)
    except ValueError:
        shown = args.out
    print(f"build: {len(vm['metrics'])} metrics from {meta['n_findings']} findings"
          f"{' + themes' if vm['themes'] else ''}; {meta['n_hidden']} suppressed/hidden -> {shown}{tag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
