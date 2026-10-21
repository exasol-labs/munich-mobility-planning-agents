# Munich Mobility: a hands-on tutorial for AI-assisted analytics on Exasol Personal

You load real open data from the City of Munich into a local Exasol database on your laptop. Then you use Claude Code to build a series of live dashboards that answer one planning question, step by step:

> **How well is each Munich district served by public transport, now and as the city grows to 2045, and what do the planned rail and tram projects change?**

Every answer is SQL you can read, and every dashboard is a Dash Server app you can open, re-run and change. The only prerequisite is the **[Exasol Personal Local Starter Kit](https://github.com/exasol-labs/exasol-personal-local-starterkit)**. Everything else (agent, dashboards, research, scripts) is in this repo. The dataset is an 18 MB zip on this repo's Releases page, which `scripts/load_data.py` downloads for you.

## What you'll build

| # | Dashboard | What it adds | Chapter |
|---|---|---|---|
| v1 | `munich-mobility-planning-v1` | Today: scheduled places offered per resident, district by district, on a map | [04](tutorial/04-v1-residents.md) |
| v2 | `munich-mobility-planning-v2` | Residents **plus jobs**: districts people travel *to* | [05](tutorial/05-v2-jobs.md) |
| v3 | `munich-mobility-planning-v3` | A **forecast to 2045** if nothing is added: year slider, change since 2024 | [06](tutorial/06-v3-forecast.md) |
| v4 | `munich-mobility-planning-v4` | **Rail and tram projects** as switchable scenarios (U5, Tram-Westtangente, 2nd Stammstrecke …) | [07](tutorial/07-v4-scenarios.md) |
| v5 | `munich-mobility-planning-v5` | An **AI assistant** that answers questions, runs what-ifs ("what if the S-Bahn ran every 10 minutes?") and drives the map | [08](tutorial/08-v5-assistant.md) |
| ➜ | `munich-cycling-coverage` | The **cycling** network per person and per km²: the start of a new series for you to continue | [09](tutorial/09-cycling-series.md) |

Each dashboard has an **"SQL executed"** foldout at the bottom that shows every statement it ran.

## The path

1. [Set up the Exasol Personal Local Starter Kit](tutorial/01-setup-starter-kit.md): database, Dash Server, Claude Code connected over MCP
2. [Load the Munich data](tutorial/02-load-data.md): 20 tables, one command (`python3 scripts/load_data.py`)
3. [Install the planning agent](tutorial/03-install-agent.md): `python3 install.py`, then your first question
4. [v1 – today, per resident](tutorial/04-v1-residents.md)
5. [v2 – residents and jobs](tutorial/05-v2-jobs.md)
6. [v3 – forecast to 2045](tutorial/06-v3-forecast.md)
7. [v4 – rail and tram scenarios](tutorial/07-v4-scenarios.md)
8. [v5 – ask the assistant](tutorial/08-v5-assistant.md) (needs an OpenAI API key)
9. [The cycling series: your turn](tutorial/09-cycling-series.md)
10. [Troubleshooting](tutorial/10-troubleshooting.md)

Plan about two to three hours for chapters 1–8.

For each dashboard you can either **build it with Claude** from the spec in `dashboards/<app>/README.md` (the point of the tutorial), or **deploy the finished version** from the same folder, if you only want to see it.

### Or let an agent do all of it
The repo is agent-ready. Once the starter kit is installed (chapter 1.1, the one step that needs you), open the repo in Claude Code and say:
```
Run this tutorial end to end per AGENTS.md: load the data, install the agent, deploy all six dashboards, and verify each step.
```
The agent follows [AGENTS.md](AGENTS.md). It's a runbook with a check after every step (`scripts/verify_data.py`, `scripts/verify_numbers.py`, `scripts/check_dashboard.py`, `scripts/check_all.py`). It stops where only you can act: installing the kit, restarting the session to load new tools, and putting your OpenAI key in `secrets/`.

## Repo map

| Path | What it is |
|---|---|
| [tutorial/](tutorial/) | The chapters above |
| [data/](data/README.md) | The table reference, sources and licences, `dataset.json` (where the data zip is published, with its checksum), and the curated rail and tram project list |
| [dashboards/](dashboards/) | The finished source of all six dashboards, each with a README that is also its build spec |
| [research/](research/README.md) | The research behind the forecast and scenarios (population growth, jobs, city plans, project details) and the context the v5 assistant reads |
| [agents/](agents/), [skill/](skill/) | What `install.py` puts into Claude Code: the agent, its skills, the data model, SQL building blocks and the dashboard look |
| [install.py](install.py) | Installs the agent and skills, adds the Dash Server rule, links your key, checks readiness |
| [secrets/](secrets/README.md) | Where **your** OpenAI key goes (gitignored, never committed) |
| [scripts/](scripts/) | `load_data.py` (load and verify the data), `verify_data.py`, `verify_numbers.py` (the model's reference numbers), `check_dashboard.py` (first-render check of a deployed app), `check_all.py`, and the optional `prepare_dataset.py` (rebuild the CSVs from the portal download) |
| [tests/expected.json](tests/expected.json) | The expected row counts and reference numbers the checks compare against |
| [AGENTS.md](AGENTS.md) · [CLAUDE.md](CLAUDE.md) | The runbook for an AI agent driving the whole tutorial |

## Honest about the data
The MVV data is the **scheduled** timetable. It has no passenger counts, delays or crowding, so "well served" means *capacity offered*, not use. Jobs per district are a modelled city estimate, and the population between 2024 and 2045 is interpolated to the official forecast. Every dashboard says so on the page, and the agent says so when a question drifts there.

## Sources and links
- **Data:** the Munich open data portal ([opendata.muenchen.de](https://opendata.muenchen.de)), the MVV GTFS timetable, the City of Munich's Demografiebericht and Erwerbstätigenprognose. Details and licences are in [data/README.md](data/README.md).
- **Tools:** [Exasol Personal](https://www.exasol.com/personal/) · [Starter Kit](https://github.com/exasol-labs/exasol-personal-local-starterkit) · [Dash Server](https://github.com/exasol-labs/dash-server) · [Exasol MCP server](https://github.com/exasol/mcp-server)
