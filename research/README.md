# Research

The background behind the forecast (v3), the scenarios (v4) and the assistant (v5). The research was done in German and English across official sources: the City of Munich, MVG, MVV, DB, the Bavarian state parliament and the city council. Each file marks what was verified on the source page and what was seen only in search results.

| File | What's in it | Used by |
|---|---|---|
| [urban-planning.md](urban-planning.md) | The planning agent's findings for every dashboard version: method, SQL, results and caveats | v1–v5 |
| [district-growth.md](district-growth.md) | Population per district: counts 2015/2024/2025, the official 2045 forecast, the big development areas (Freiham, Neufreimann, Nordost …) | v3, v4 |
| [plans-facts.md](plans-facts.md) | Munich's current mobility projects and proposals, as facts with sources: transit, cycling, roadworks, politics and budget | v4, v5 |
| [plans-research.md](plans-research.md) | The same research as an assessed summary: what is funded, what is stalled, what it means per district | v4, v5 |
| [pt-projects-notes.md](pt-projects-notes.md) | Per project: stations, opening years, frequencies and the 2nd Stammstrecke operating concept, behind `data/source/pt_projects.csv` | v4 |
| [cycling-coverage.md](cycling-coverage.md) | Findings of the cycling dashboard | cycling |
| [reference-numbers.md](reference-numbers.md) | The numbers each dashboard must reproduce, used as checks in the tutorial | all |
| [v5-context.md](v5-context.md) | The context pack the v5 assistant reads with every question: role and rules, data model, the dashboard's model and full SQL, reference numbers and findings. About 44k tokens | v5 |

The v5 dashboard ships its own copy as `dashboards/munich-mobility-planning-v5/context.md`. Edit both together, or regenerate it, when you change the research.
