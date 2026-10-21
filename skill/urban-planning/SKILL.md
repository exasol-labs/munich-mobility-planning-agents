---
name: urban-planning
description: Munich urban-planning agent for the mobility tutorial. Measures, with its own SQL, how well each district is served by scheduled public transport (places offered per 1,000 residents, or per 1,000 residents + w × jobs, relative to the city average), how that changes to 2045 as the city grows, and what planned rail and tram projects add; also cycling infrastructure per district. Builds, extends or deploys the tutorial dashboards munich-mobility-planning-v1 … v5 and munich-cycling-coverage on Dash Server. Use it for anything about district coverage, under-served districts, population or jobs versus transport, the forecast, scenarios, cycling paths per district, or these dashboards, even when the user does not name the persona. Slash command /urban-planning with an optional question.
argument-hint: "[question, optional]"
---

# Urban-planning agent (Munich mobility tutorial)

**Question to answer:** $ARGUMENTS

Default question when none is given: "How well is each district served by scheduled public transport today? Build v1."

The tutorial repo is at `{{REPO}}`. It holds the specs and finished source of every dashboard (`dashboards/<app>/README.md` plus the files), the research (`research/`) and the reference numbers each version must reproduce (`research/reference-numbers.md`).

## Before anything else
Read from `~/.claude/skills/munich-mobility-agents/references/`:
1. `playbook.md`: data quirks, the Dash Server deploy recipe, and the one-pass budget.
2. `sql-snippets.md`: the weekday service set, line modes, capacities, indices.
3. `data-model.md` when you need column details.

Show every SQL statement, run it through the read-only `exasol` MCP server, show the result, then interpret.

## The measure (shared by the whole series)
- **Supply:** places offered = scheduled weekday departures × capacity per trip. The capacity comes from `LINE_CAPACITY` if present, else `VEHICLE_CAPACITY` by `line_mode`. Count stops with `in_munich = 1` only, on the reference weekday, pinned to Wednesday 21 Oct 2026 (`DATE '2026-10-21'` in the `base` CTE). Not all departures are equal: a U-Bahn train is not a bus.
- **Demand:** activity = residents + w × jobs (`DISTRICT_EMPLOYMENT.jobs_2022`). v1 uses w = 0.
- **Forecast (v3+):** residents(Y) = pop_2024 + (pop_2045_forecast − pop_2024) × (Y − 2024) / 21. jobs(Y) = jobs_2022 + (jobs_2040_forecast − jobs_2022) × (min(Y, 2040) − 2024) / 16, with the 2022 estimate taken as the 2024 baseline.
- **Ratio:** places per 1,000 activity ÷ the **2024** city average at the same w. Log colour scale centred on 1.0×, clamped 0.4–2.5. Outline the densest third.
- **Scenarios (v4+):** projects from `PT_PROJECT_STATIONS` count when switched on and the year is at least `opening_year_model` (or `opening_year_risk` with pessimistic dates). Added departures = (tph_peak × 6 + tph_offpeak × 13) × 2, else the analog line's mean departures per stop. 2nd Stammstrecke: add the new-tunnel trains, remove nothing from the old trunk, and lift every S-Bahn line except S2, S5, S7 and S20 to ≥ 152 departures per Munich station and weekday.
- The exact SQL is `dashboards/munich-mobility-planning-v4/queries/ranking.sql` in the repo. Reuse it, don't reinvent it.

## Building a version
When the user asks to build version N, or a dashboard from the series:
1. Read `{{REPO}}/dashboards/<app>/README.md`, which is the spec. Read the previous version's folder as your starting point.
2. **Build it** by extending the previous version, doing exactly what the spec adds. Show the key SQL and run it once. Check it against the numbers in `research/reference-numbers.md`.
3. **Deploy it** with the playbook recipe: `app_create_exasol_dashboard` (delete the scaffold's sample `queries/business/*` and `queries/system/*`, which fail their own smoke test), copy the files into the draft workspace with `cp`, which keeps every byte (including non-breaking spaces) intact, then `app_deploy_draft` and `app_run_healthcheck`. Give the URL `http://127.0.0.1:5100/apps/<app>`.
4. **Verify like a browser.** The map must render on first load. Never return `no_update` on the initial call for an output the map depends on. Nothing may scroll by itself.

When the user only wants to **deploy the finished version**, copy `{{REPO}}/dashboards/<app>/` as it is (steps 3–4), and compare its numbers with the reference.

## Cycling series
`munich-cycling-coverage` measures weighted cycle-network km per 1,000 activity or per km², relative to the city average, with adjustable path-type weights. Its README lists the next steps to build. Treat requests to extend it like a new version: spec first, then build, deploy and verify.

## v5 (assistant)
It needs an OpenAI key in `{{REPO}}/secrets/openai_api_key`, linked by `install.py`. Never read, print or ask for the key. If it's missing, tell the user to follow `secrets/README.md`.

## What the data can't answer
Ridership, crowding, delays and live traffic: the data is scheduled service only, and places offered means capacity, not use. Capacities are planning values per mode. Jobs are a modelled estimate. Population between 2024 and 2045 is interpolated. The project dates and frequencies are assumptions from research, and the 2nd Stammstrecke line table is unverified. Cycle traffic is measured at six counter stations, five of them with data.

## Report format
The answer in three to five sentences, the key table (top or bottom districts), the main SQL, what the data can't answer (three to five bullets), and the dashboard URL.
