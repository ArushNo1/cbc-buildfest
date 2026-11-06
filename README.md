# Team 17 · EveryMind BuildFest (internal working repo)

Private working repo for the EveryMind 988-training survey case. **This is not a deliverable.** Final files are assembled in `submission/` (see `docs/requirements.md`).

Agents and humans: read `CLAUDE.md` first.

## Quick start

```bash
make setup                                   # once per machine: deps + commit-msg hook
# put the survey workbook at data/raw/ (gitignored, never committed)
make data DATA=data/raw/BuildFest_EveryMind_Survey_Data_FULL.xlsx   # clean + analyze
make run  DATA=data/raw/BuildFest_EveryMind_Survey_Data_FULL.xlsx   # end to end: findings, themes, dashboard
make test
make verify                                  # repo guards + submission checks
make submit                                  # assemble submission/
```

A target whose code doesn't exist yet fails with a message naming its owner.

## Layout

| Path | What |
|---|---|
| `agents/<name>/` | each agent's code and notes (`ROLE.md` = its brief) |
| `contracts/` | JSON Schemas for cleaned rows, `findings.json` and `themes.json`, plus small synthetic examples |
| `outputs/` | committed aggregates only (`findings.json`, `themes.json`, dashboard) |
| `data/` | local raw and processed row-level data (gitignored) |
| `docs/` | requirements, timeline, decisions log, verification log, reference PDFs |
| `logs/ai/` | per-agent AI-use log (feeds the AI appendix) |
| `scripts/` | repo guards, hooks, verification, submission packaging |
| `tests/` | repo tests; `tests/fixtures/` holds the synthetic data generator |
| `submission/` | final deliverables only (anonymous) |
