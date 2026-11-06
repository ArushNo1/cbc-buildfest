#!/usr/bin/env python3
"""Offline, deterministic theme coding for the two survey comment fields.

No network and no API key. Same input, same themes.json.
Row-level comments stay in memory or in gitignored data/processed/.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = ROOT / "data" / "processed" / "survey_clean.csv"
DEFAULT_OUTPUT = ROOT / "outputs" / "themes.json"
SMALL_N = 10

THEMES = [
    {
        "theme_id": "recognize_crisis",
        "field": "valuable",
        "label": "Recognizing a crisis",
        "description": "Learning to notice warning signs or tell that someone is in crisis.",
        "patterns": [
            r"warning sign",
            r"signs of (a |the )?(crisis|suicide)",
            r"signos? de alerta",
            r"senales de (una )?crisis",
            r"spot(ting)? (a |the )?crisis",
            r"identif\w* (a |the |una )?crisis",
            r"recogniz\w* (a |the )?crisis",
            r"recogniz\w* signs",
            r"how to tell (if |when )?someone",
        ],
    },
    {
        "theme_id": "what_988_is",
        "field": "valuable",
        "label": "What 988 is",
        "description": "What the 988 lifeline is or how a contact works.",
        "patterns": [
            r"\b988\b",
            r"lifeline",
            r"linea de crisis",
            r"que es el 988",
            r"how (a )?(call|text) works",
        ],
    },
    {
        "theme_id": "when_to_use",
        "field": "valuable",
        "label": "When to use 988",
        "description": "When to contact 988, including versus 911.",
        "patterns": [
            r"when to (call|text|use|contact)",
            r"cuando (llamar|usar|contactar)",
            r"puedo llamar",
            r"anyone can call",
            r"\b911\b",
            r"instead of (calling )?911",
        ],
    },
    {
        "theme_id": "confidence_to_help",
        "field": "valuable",
        "label": "Confidence to help",
        "description": "Feeling more prepared to help, or knowing what to say or do.",
        "patterns": [
            r"\bconfident\b",
            r"\bconfianza\b",
            r"prepared to help",
            r"what to (say|do)",
            r"que decir",
            r"how to help",
            r"como ayudar",
            r"support a friend",
            r"ayudar a un amigo",
        ],
    },
    {
        "theme_id": "practice_scenarios",
        "field": "valuable",
        "label": "Practice and scenarios",
        "description": "Role play, scenarios, examples, or practice during the training.",
        "patterns": [
            r"role[\s-]?play",
            r"scenario",
            r"\bexamples?\b",
            r"\bejemplos?\b",
            r"\bpractice\b",
            r"\bpractica\b",
            r"\bdinamica\b",
        ],
    },
    {
        "theme_id": "resources_shared",
        "field": "valuable",
        "label": "Materials and resources",
        "description": "Handouts, cards, links, or resource lists shared in the training.",
        "patterns": [
            r"handout",
            r"pamphlet",
            r"\bfolleto\b",
            r"\brecursos\b",
            r"resource list",
            r"\bwallet card\b",
            r"the (link|website|card)\b",
        ],
    },
    {
        "theme_id": "presenter_quality",
        "field": "valuable",
        "label": "Presenter",
        "description": "The presenter, trainer, or speaker was clear, engaging, or knowledgeable.",
        "patterns": [
            r"\bpresenter\b",
            r"\btrainer\b",
            r"\bspeaker\b",
            r"\bfacilitator\b",
        ],
    },
    {
        "theme_id": "more_time",
        "field": "improve",
        "label": "Session length or pace",
        "description": "The session felt rushed, too long, or too short, or the person wanted more time.",
        "patterns": [
            r"more time",
            r"mas tiempo",
            r"too (fast|short|long|rushed)",
            r"\brushed\b",
            r"\bslower\b",
            r"\bshorter\b",
            r"muy rapido",
            r"not enough time",
            r"\blonger\b",
            r"more sessions",
        ],
    },
    {
        "theme_id": "more_interaction",
        "field": "improve",
        "label": "More interaction",
        "description": "More discussion or activities, or less lecture.",
        "patterns": [
            r"more (interaction|interactive|discussion|activities)",
            r"less lecture",
            r"mas interaccion",
            r"mas actividades",
            r"\binteractive\b",
            r"\bactivities\b",
        ],
    },
    {
        "theme_id": "more_examples",
        "field": "improve",
        "label": "More examples",
        "description": "A request for more examples, cases, stories, or videos.",
        "patterns": [
            r"more (examples|scenarios|cases|stories|videos)",
            r"mas ejemplos",
            r"real-life",
            r"\bexamples\b",
            r"\bvideos\b",
            r"case stud",
        ],
    },
    {
        "theme_id": "practical_scripts",
        "field": "improve",
        "label": "Practical scripts",
        "description": "A request for wording, steps, or a script.",
        "patterns": [
            r"what to say",
            r"que decir",
            r"step by step",
            r"\bscript\b",
            r"exact words",
        ],
    },
    {
        "theme_id": "local_followup",
        "field": "improve",
        "label": "Local follow-up",
        "description": "County or school resources, or a request for follow-up after the training.",
        "patterns": [
            r"local resource",
            r"recursos locales",
            r"follow[\s-]?up",
            r"our (county|school|area)",
            r"in our county",
        ],
    },
    {
        "theme_id": "accessibility",
        "field": "improve",
        "label": "Access and language",
        "description": "Language access, captions, hybrid delivery, or disability access.",
        "patterns": [
            r"\bspanish\b",
            r"\bespanol\b",
            r"\bidio?ma\b",
            r"\bcaptions?\b",
            r"\bsubtitulos\b",
            r"\bhybrid\b",
            r"online option",
            r"wheelchair",
            r"\baccessib\w*",
        ],
    },
    {
        "theme_id": "logistics",
        "field": "improve",
        "label": "Logistics",
        "description": "Room, audio, slides, schedule, or parking.",
        "patterns": [
            r"\b(room|audio|microphone|mic|slides|parking|schedule)\b",
            r"\b(sonido|microfono)\b",
            r"too (cold|hot|loud|quiet)",
        ],
    },
    {
        "theme_id": "content_depth",
        "field": "improve",
        "label": "Depth and populations",
        "description": "Too basic, too advanced, or more on a specific population.",
        "patterns": [
            r"too (basic|advanced|simple)",
            r"more depth",
            r"mas profundo",
            r"\b(youth|lgbtq|veterans?)\b",
            r"\bjovenes\b",
        ],
    },
]

RESIDUAL = ("other_unclear", "no_substantive")
RESIDUAL_META = {
    "other_unclear": (
        "Other or unclear",
        "A non-empty comment that is not filler and matches no theme.",
    ),
    "no_substantive": (
        "No substantive comment",
        "The whole comment is filler such as n/a, nothing, good, or thanks.",
    ),
}

FILLER = re.compile(
    r"^(?:"
    r"n/?a|none|nothing|no|nope|idk|i don'?t know|not sure|unsure|"
    r"good|great|ok|okay|yes|fine|all good|no comment|no comments|"
    r"nothing to improve|no improvements?|it was (good|great|fine)|"
    r"nothing, it was (good|great|fine)|everything|all of it|"
    r"nada|ninguno|ninguna|no se|gracias|thank you|thanks|todo bien|perfecto|"
    r"nada, todo bien|"
    r"[\W_]+"
    r")$"
)

EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE = re.compile(
    r"(?<!\d)(?:(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}|\d{3}[\s.-]\d{4})(?!\d)"
)
SCHOOL = re.compile(r"\b(?:high school|middle school|elementary school|escuela|my school)\b")
HONORIFIC = re.compile(r"\b(?:[Mm]r|[Mm]rs|[Mm]s|[Dd]r|[Pp]rof)\.?\s+[A-Z][a-z]{2,}\b")
ROLE_NAME = re.compile(
    r"\b(?:trainer|presenter|speaker|facilitator)\s+[A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})?\b"
)
MY_NAME = re.compile(r"\b[Mm]y name is\s+[A-Z][a-z]{2,}\b")

PERIODS = (
    ("2025-10", "2026-03", "2025-10_to_2026-03"),
    ("2026-04", "2026-05", "2026-04_to_2026-05"),
    ("2026-06", "2026-08", "2026-06_to_2026-08"),
    ("2026-09", "2026-10", "2026-09_to_2026-10"),
)

COMPILED = {
    (item["field"], item["theme_id"]): [re.compile(p) for p in item["patterns"]]
    for item in THEMES
}


def fold(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text).replace("\u00a0", " "))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", text).strip().lower()


def comment_text(row: dict, field: str) -> str:
    key = "comment_valuable" if field == "valuable" else "comment_improve"
    value = row.get(key)
    if value is None:
        return ""
    return str(value).replace("\u00a0", " ").strip()


def is_filler(text: str) -> bool:
    folded = fold(text)
    return folded == "" or len(folded) <= 2 or FILLER.match(folded) is not None


def classify(text: str, field: str) -> list[str]:
    """Theme ids for one comment. Filler is exclusive. Otherwise multi-label."""
    if text.strip() == "":
        return []
    if is_filler(text):
        return ["no_substantive"]
    folded = fold(text)
    hits = [
        theme_id
        for (rule_field, theme_id), patterns in COMPILED.items()
        if rule_field == field and any(p.search(folded) for p in patterns)
    ]
    if not hits:
        return ["other_unclear"]
    return sorted(set(hits))


def screen_pii(text: str) -> list[str]:
    if text.strip() == "":
        return []
    flags = []
    if EMAIL.search(text):
        flags.append("email")
    if PHONE.search(text):
        flags.append("phone")
    if SCHOOL.search(fold(text)):
        flags.append("school")
    if HONORIFIC.search(text) or MY_NAME.search(text) or ROLE_NAME.search(text):
        flags.append("name")
    return flags


def primary_role(roles: str) -> str:
    parts = [part.strip().lower() for part in str(roles or "").split(";") if part.strip()]
    if not parts:
        return "unspecified"
    if any("student" in part for part in parts):
        return "student"
    if len(parts) == 1:
        return parts[0]
    return "multiple"


def training_period(row: dict) -> str:
    raw = str(row.get("training_month") or "")
    if not re.fullmatch(r"\d{4}-\d{2}", raw):
        date = str(row.get("training_date") or "")
        raw = date[:7]
    if not re.fullmatch(r"\d{4}-\d{2}", raw):
        return "unknown"
    for start, end, label in PERIODS:
        if start <= raw <= end:
            return label
    return "other"


def language_level(row: dict) -> str:
    lang = fold(row.get("language") or "")
    if lang in {"en", "english"} or lang.startswith("english"):
        return "en"
    if lang in {"es", "spanish", "espanol"} or lang.startswith("espanol") or lang.startswith("spanish"):
        return "es"
    return lang or "unknown"


def slug(level: str) -> str:
    text = fold(level).replace("'", "")
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text or "unknown"


def metric_id(field: str, theme_id: str, dimension: str, level: str) -> str:
    if dimension == "overall":
        return f"themes.{field}.{theme_id}.pct.overall"
    return f"themes.{field}.{theme_id}.pct.{dimension}.{slug(level)}"


def theme_catalog() -> list[dict]:
    rows = [
        {
            "theme_id": item["theme_id"],
            "field": item["field"],
            "label": item["label"],
            "description": item["description"],
        }
        for item in THEMES
    ]
    for field in ("valuable", "improve"):
        for theme_id in RESIDUAL:
            label, description = RESIDUAL_META[theme_id]
            rows.append(
                {
                    "theme_id": theme_id,
                    "field": field,
                    "label": label,
                    "description": description,
                }
            )
    return sorted(rows, key=lambda row: (row["field"], row["theme_id"]))


def _pct(mentions: int, n: int) -> float:
    return round(100.0 * mentions / n, 1)


def _dimensions(rows: list[dict], columns: set[str]) -> list[tuple[str, callable, set[str]]]:
    dims: list[tuple[str, callable, set[str]]] = [
        ("overall", lambda _row: "all", {"all"}),
    ]
    if "language" in columns:
        dims.append(("language", language_level, {"en", "es"}))
    if "county" in columns:
        dims.append(("county", lambda row: str(row.get("county") or "unknown"), set()))
    if "roles" in columns:
        dims.append(("role", lambda row: primary_role(row.get("roles") or ""), set()))
    if "training_month" in columns or "training_date" in columns:
        dims.append(("training_period", training_period, set()))
    return dims


def _grouped(rows: list[dict], field: str, level_fn, always_keep: set[str]) -> dict[str, list[dict]]:
    nonempty = [row for row in rows if comment_text(row, field)]
    counts = Counter(level_fn(row) for row in nonempty)
    small = {level for level, n in counts.items() if n < SMALL_N and level not in always_keep}

    def mapped(row: dict) -> str:
        level = level_fn(row)
        return "other_pooled" if level in small else level

    groups: dict[str, list[dict]] = defaultdict(list)
    for row in nonempty:
        groups[mapped(row)].append(row)
    return groups


def build_themes(rows: list[dict], source: dict, note: str | None = None) -> dict:
    columns = set()
    for row in rows:
        columns.update(row.keys())
    required = {"comment_valuable", "comment_improve"}
    missing = sorted(required - columns)
    if rows and missing:
        raise SystemExit(
            "themes.py: input is missing "
            + ", ".join(missing)
            + ". Found columns: "
            + ", ".join(sorted(columns))
        )

    catalog = theme_catalog()
    by_field: dict[str, list[str]] = defaultdict(list)
    for item in catalog:
        by_field[item["field"]].append(item["theme_id"])

    counts = []
    for field in ("valuable", "improve"):
        for dimension, level_fn, always_keep in _dimensions(rows, columns):
            for level, group_rows in sorted(_grouped(rows, field, level_fn, always_keep).items()):
                n = len(group_rows)
                suppressed = n < SMALL_N
                coded = [classify(comment_text(row, field), field) for row in group_rows]
                for theme_id in by_field[field]:
                    mentions = sum(theme_id in labels for labels in coded)
                    counts.append(
                        {
                            "id": metric_id(field, theme_id, dimension, level),
                            "theme_id": theme_id,
                            "field": field,
                            "group": {"dimension": dimension, "level": level},
                            "n_mentions": None if suppressed else mentions,
                            "n": n,
                            "pct": None if suppressed else _pct(mentions, n),
                            "small_n": suppressed,
                            "suppressed": suppressed,
                        }
                    )

    flagged = 0
    for row in rows:
        for field in ("valuable", "improve"):
            text = comment_text(row, field)
            if text and screen_pii(text):
                flagged += 1

    spanish_rows = [
        row
        for row in rows
        if language_level(row) == "es"
        and (comment_text(row, "valuable") or comment_text(row, "improve"))
    ]
    payload = {
        "schema_version": "0",
        "method": (
            "Keyword and regex rules in agents/text/themes.py, documented in "
            "agents/text/codebook.md. Multi-label. Filler comments are coded only as "
            "no_substantive. A non-match is other_unclear. No network and no API key. "
            "Percents use non-empty comments as the denominator and are rounded "
            "half-to-even to 1 decimal. Groups with n < 10 are suppressed. County, role, "
            "and training-period levels with n < 10 are pooled into other_pooled. "
            "English and Spanish stay separate."
        ),
        "taxonomy": catalog,
        "counts": sorted(counts, key=lambda item: item["id"]),
        "validation": {
            "sample_size": 0,
            "agreement_pct": None,
            "cohen_kappa": None,
            "procedure": (
                "Not run. Planned for themes v1: stratified random sample, seed 17, "
                "hand-coded blind to this classifier, labels stored only in data/processed/. "
                "No agreement rate is claimed."
            ),
        },
        "spanish": {
            "n_comments": len(spanish_rows),
            "handling": (
                "Spanish phrases are in the same offline rules. Rows with language es "
                "and a non-empty comment are counted here and reported as their own "
                "language group. If that group has n < 10, its counts are suppressed."
                if "language" in columns
                else "No language column on this input. Spanish phrases in the rules still match the text, but rows are not split into an es group."
            ),
        },
        "pii_screen": {
            "method": (
                "Regex on each non-empty comment for an email, a separated phone number "
                "(10-digit or 7-digit), a school phrase including 'my school', an honorific "
                "plus a capitalized name, 'my name is', or a role word such as trainer plus "
                "a capitalized name. 988 is not treated as a phone number. Names with no "
                "honorific and no role word are missed. "
                "n_flagged counts comment fields, not rows. Quotes still require human review."
            ),
            "n_flagged": flagged,
        },
        "source": source,
    }
    if note:
        payload["note"] = note
    return payload


def fixture_rows() -> list[dict]:
    """Synthetic comments for the skeleton. Not survey data."""
    rows = []
    for _ in range(10):
        rows.append(
            {
                "language": "en",
                "roles": "student;",
                "county": "Anne Arundel",
                "training_month": "2026-04",
                "comment_valuable": "I can spot the warning signs of a crisis.",
                "comment_improve": "It was rushed and I wanted more time.",
            }
        )
    rows[0]["comment_valuable"] += " Reach me at test@example.com."
    for _ in range(10):
        rows.append(
            {
                "language": "en",
                "roles": "student;",
                "county": "Prince George's",
                "training_month": "2026-09",
                "comment_valuable": "The presenter explained what 988 is.",
                "comment_improve": "Add more examples and a script of what to say.",
            }
        )
    rows.append(
        {
            "language": "es",
            "roles": "teacher;",
            "county": "Calvert",
            "training_month": "2026-04",
            "comment_valuable": "Aprendí las señales de una crisis.",
            "comment_improve": "Necesitamos más tiempo.",
        }
    )
    rows.append(
        {
            "language": "es",
            "roles": "teacher;",
            "county": "Calvert",
            "training_month": "2026-04",
            "comment_valuable": "Ahora sé qué es el 988.",
            "comment_improve": "Nada",
        }
    )
    return rows


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def dumps(payload: dict) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Code survey comments into themes.json")
    parser.add_argument("--input", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--fixture", action="store_true", help="Use the synthetic fixture")
    args = parser.parse_args(argv)

    if args.fixture:
        rows = fixture_rows()
        encoded = json.dumps(rows, sort_keys=True, ensure_ascii=False).encode("utf-8")
        source = {"file_sha256": hashlib.sha256(encoded).hexdigest(), "n_rows": len(rows)}
        note = "SYNTHETIC FIXTURE. Values are made up. Never cite."
    else:
        path = args.input or DEFAULT_INPUT
        if not path.exists():
            raise SystemExit(
                f"themes.py: {path} does not exist. Run make data first, or pass --fixture."
            )
        rows = read_csv(path)
        source = {"file_sha256": file_sha256(path), "n_rows": len(rows)}
        note = None

    payload = build_themes(rows, source, note)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(dumps(payload), encoding="utf-8")
    print(f"themes.py: wrote {args.output} ({source['n_rows']} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
