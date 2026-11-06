# Contracts

| File | Describes | Owner (v1+) |
|---|---|---|
| `cleaned_data.schema.json` | one row of local `data/processed/survey_clean.csv` (never committed) | data |
| `findings.schema.json` | `outputs/findings.json` | data |
| `themes.schema.json` | `outputs/themes.json` | text |
| `examples/*.example.json` | tiny **synthetic** examples of each output shape, to build against before real outputs exist. Never cite. | owner of the schema |

Versioning: bump `x-schema-version` in the schema and `schema_version` in the output together. Breaking changes (renamed or removed fields or IDs) need a `type:handoff` issue to every consumer (`to:text`, `to:tool`, `to:narrative`) before you push. `tests/test_repo_guards.py` checks that each schema is valid and that each example validates against it.

v0 was written by narrative from the case's column list, without opening the data. The data agent should correct it against the real workbook for v1 (due Fri Nov 6 12:00 ET).
