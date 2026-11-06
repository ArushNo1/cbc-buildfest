# Requirements

## Deliverables (all in `submission/`, anonymous, filenames exact)

| # | File | Spec | Built by | Gate |
|---|---|---|---|---|
| 1 | `Team17_TechnicalArtifact.zip` (or link) | Runs without errors on the provided data, handles reasonable data updates, clear outputs, run instructions | tool (with data, text) | `make run` from clean clone; drift tests green |
| 2 | `Team17_Demo.mp4` | ≤120 s | tool | ffprobe ≤120 s; human approves |
| 3 | `Team17_Memo.pdf` | 1–2 pages, non-technical: key findings, methodology, recommendations, implementation (who, how often, what they need), limitations | narrative | ≤2 pages; check_numbers |
| 4 | `Team17_AIAppendix.pdf` | Exactly 1 page: tools, representative prompts, ≥1 AI error/limitation, how outputs were refined, what was verified/corrected manually, how findings were validated against data | narrative | 1 page; every claim traceable to `logs/ai/` or `docs/verification.md` |
| 5 | `Team17_Presentation.pptx` | .pptx only (no PDF): solution, findings, AI use, recommendations | narrative | pptx; check_numbers |

Due **Sun Nov 8, 09:00 ET**, no late submissions. Humans submit the Google Form.

## Rubric → where we earn it

| Criterion | Weight | What judges look for | Where |
|---|---|---|---|
| Business/Social Impact | 35% | Prioritized recs, feasible implementation, impact measures; flags thin findings; protects privacy | memo recs + implementation; deck; small-n flags; quotes PII review |
| Technical Soundness | 30% | Reproducible; justified methods; sample sizes; small groups; data inconsistencies; open-ended comments; retrospective-rating limits | data pipeline + validation report; themes validation; limitations.md; CIs |
| Functionality | 20% | Correct numbers; runs from instructions; handles data updates | findings.json + human recompute; RUN.md; drift tests |
| AI Process | 15% | Tools, prompts, revisions, errors documented; independent verification against data | logs/ai → appendix; docs/verification.md |

Track awards: Best Technical Tool, Most Effective Visualization, EveryMind's Choice.
