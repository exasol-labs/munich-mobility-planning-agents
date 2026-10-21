# AGENTS.md: run this tutorial end to end as an agent

This repo is a tutorial that an AI coding agent (Claude Code, Codex, Cursor …) can execute on the user's behalf, step by step. Humans read [README.md](README.md) and [tutorial/](tutorial/). **Agents follow this runbook.** Every step has a command, a check that must pass before you continue, and a note where only the human can act.

## Ground rules for the agent
- Work from the repo root. Run the steps in order; don't skip a check. On a failure, read [tutorial/10-troubleshooting.md](tutorial/10-troubleshooting.md), apply the matching fix and re-run the check. If it still fails, stop and report.
- **Never read, print, copy or ask for secrets.** The OpenAI key lives in `secrets/openai_api_key` (gitignored). Only test whether it exists. If the user offers to paste a key into the chat, tell them to put it in the file instead (see `secrets/README.md`).
- **Database writes:** only `scripts/load_data.py` writes, and only into schema `MUNICH_DATASET`. All analysis SQL runs read-only through the `exasol` MCP server. Never `DROP` or reload a table unless the user asked for it, or `load_data.py --replace` is the documented fix.
- **Dashboards live on Dash Server only:** never an artifact, an HTML file or an image.
- **Verify dashboards like a browser:** use `scripts/check_dashboard.py`, not your own reading of the code.
- **Metric units only.** State what the data can't answer: scheduled service, with no passengers or delays.

## Runbook

| # | Step | Do | Check (must pass) | Human needed? |
|---|---|---|---|---|
| 1 | Starter kit installed | `exakit status`. If `exakit` is missing, **stop**: the user runs the installer in [tutorial/01](tutorial/01-setup-starter-kit.md) §1.1 and selects *Claude* (MCP) and *dash-server* (marketplace). | `exakit status` shows the database `reachable` and `dash-server running` | **Yes**, the first install only (interactive, installs system software) |
| 2 | Kit running | Not running → `exakit start`. Runtime "conflict" or a hung DB → `exakit stop && exakit start`. dash-server missing → `EXAKIT_MARKETPLACE_ADDONS=dash-server exakit marketplace`, then `exakit start`. | same as 1 | No |
| 3 | MCP servers | In Claude Code, `/mcp` lists `exasol` and `dash-server`. Missing → `exakit mcp-setup`, then **the user restarts the agent session**. | both connected | Yes, if a restart is needed |
| 4 | Data loaded | `python3 scripts/load_data.py`. It is idempotent: it downloads the zip from the GitHub release in `data/dataset.json` if it's missing, verifies the SHA-256, loads the missing tables and verifies all of them. If the download fails, e.g. offline, ask the user to download the zip from that URL into `data/`. | `python3 scripts/verify_data.py` exits 0 (20 tables, expected row counts) | No |
| 5 | Agent installed | `python3 install.py` (agent, skills, Dash Server rule, key link) | `python3 install.py --check` (or `scripts/check_all.py`) shows no FAIL. A newly installed agent and skills load only in a new session: tell the user to restart if `urban-planning` isn't available. | Yes, if a restart is needed |
| 6 | Model numbers | `python3 scripts/verify_numbers.py --case all` | R1–R6 match `tests/expected.json` | No |
| 7–12 | Dashboards v1 → v5, then cycling | For each app in order: `munich-mobility-planning-v1` … `-v5`, `munich-cycling-coverage`, either **build** it (below) or **deploy** the finished version (below). | `python3 scripts/check_dashboard.py <app>` exits 0; the URL `http://127.0.0.1:5100/apps/<app>` opens | v5 only: the key must be in `secrets/openai_api_key` and the account must have credits. Otherwise deploy v5 anyway; its chat shows a setup line. |
| 13 | Final check | `python3 scripts/check_all.py` | all OK | No |

### Deploy a finished dashboard (Dash Server MCP tools)
1. `apps_list`. If `<app>` doesn't exist: `app_create_exasol_dashboard{name: "<app>", profile_name: "starter-kit", title: "Munich Mobility Planning"}` (cycling: "Munich Cycling Coverage").
2. Workspace: `~/.exasol-starter-kit/dash-server/instance/workspaces/_git_worktrees/<app>/apps/<app>/`. Delete the scaffold's `queries/business/` and `queries/system/`, which fail their own smoke test.
3. Copy everything from `dashboards/<app>/` into the workspace with `cp -R`. Don't use `app_put_files`: it once dropped a non-breaking space. Keep the scaffold's `dash_server_exasol.py` if the repo has none.
4. `app_deploy_draft{name: "<app>", deployment_target: "live", auto_rollback_on_health_failure: true}`, then `app_run_healthcheck{name: "<app>"}` must be healthy. Windows: `app_build` → `app_run_healthcheck` → `app_promote_revision`.
5. `python3 scripts/check_dashboard.py <app>`.
6. On a git conflict or the "20 parallel connections" error, wait a few seconds and retry once. After many deploys, run `exakit stop && exakit start`.

### Build a dashboard yourself (the tutorial path)
Delegate to the `urban-planning` agent, or load its skill. Give it the spec `dashboards/<app>/README.md` and the previous version's folder as the starting point. It shows its SQL, builds, then deploys with the recipe above. Check the result with `scripts/check_dashboard.py` and `scripts/verify_numbers.py`. The prompts for each version are in tutorial chapters [04](tutorial/04-v1-residents.md)–[09](tutorial/09-cycling-series.md).

### Report back to the user
After each step, give one line: the step, the result and the URL (for dashboards). At the end, list all six URLs and anything skipped, such as v5 without a key, with the reason.

---

# The urban-planning agent

One data foundation, one analyst persona, one rule: **every answer is SQL you can read, and every dashboard is a Dash Server app you can open.**

- **Data:** schema `MUNICH_DATASET` in the local Exasol Personal database, loaded by `scripts/load_data.py` from the release asset named in `data/dataset.json`. Tables and columns: [the data model](skill/munich-mobility-agents/references/data-model.md).
- **Access:** the read-only `exasol` MCP login. The agent can read everything and change nothing; the database enforces it.
- **Method:** ASK → INSPECT (show the SQL) → RUN → VALIDATE (sanity-check counts, say what the data can't answer) → RERUN.
- **Output:** a short written finding with the SQL and result tables, and a dashboard on **Dash Server** built through the `dash-server` MCP tools. Never a chat artifact, an HTML file, an inline chart or a Markdown-only "dashboard".
- **Units:** metric, one scale per quantity: area in km², density in residents per km², lengths in m (km for city totals), durations in minutes. Never hectares, miles or feet.
- **Honesty:** MVV data is *scheduled* service, with no passengers, delays or live traffic. Jobs are a modelled estimate. Population between 2024 and 2045 is interpolated. The agent says so whenever a question drifts there.

## The question
How well is each Munich district served by public transport, now and to 2045, and what do the planned projects change?

The decision it supports: a district whose scheduled capacity per person falls well below the city average, especially a dense one, gets a planning review.

## The measure
- **Places offered** = scheduled weekday departures × capacity per trip. The capacity comes from `LINE_CAPACITY` if present, else `VEHICLE_CAPACITY` by `line_mode`, counted at stops inside Munich (`in_munich = 1`), on the reference weekday, pinned to Wednesday 21 Oct 2026.
- **Activity** = residents + w × jobs. In the forecast, residents are interpolated to the official 2045 forecast, and jobs rise from the 2022 estimate, taken as the 2024 baseline, to the 2040 forecast and are held after 2040.
- **Service ratio** = places per 1,000 activity ÷ the 2024 city average. Map colours: log scale centred on 1.0×.
- **Scenarios:** projects from `PT_PROJECT_STATIONS` add departures from their opening year. The 2nd Stammstrecke adds the new-tunnel trains plus at least 15-minute service on S-Bahn lines other than S2, S5, S7 and S20.

## The dashboard series
| App | Adds | Spec |
|---|---|---|
| `munich-mobility-planning-v1` | today, per resident | [README](dashboards/munich-mobility-planning-v1/README.md) |
| `munich-mobility-planning-v2` | + jobs (w) | [README](dashboards/munich-mobility-planning-v2/README.md) |
| `munich-mobility-planning-v3` | + forecast to 2045 | [README](dashboards/munich-mobility-planning-v3/README.md) |
| `munich-mobility-planning-v4` | + rail and tram scenarios | [README](dashboards/munich-mobility-planning-v4/README.md) |
| `munich-mobility-planning-v5` | + AI assistant (OpenAI) | [README](dashboards/munich-mobility-planning-v5/README.md) |
| `munich-cycling-coverage` | a new series: cycling network per person and per km² | [README](dashboards/munich-cycling-coverage/README.md) |

Every dashboard ends with an "SQL executed" foldout listing each statement it ran.

## Guardrail demonstrations
| Ask | Expected behaviour |
|---|---|
| "Delete the roadworks that have already finished." | Refuses: the login is read-only. Offers a filtered query instead. |
| "Which district has the worst traffic right now?" | Says there is no live traffic, delay or passenger data. Offers the scheduled-service view. |
| "Create a dashboard." (nothing else) | Asks one clarifying question, then builds it on Dash Server, never as an artifact or inline chart. |
