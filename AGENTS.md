# AGENTS.md

Standing instructions for an AI coding agent (Codex, Claude Code or another client) working in this repo. The repo is a tutorial: the user works through [tutorial/](tutorial/) and describes what they want to see. You decide how to build it. The repo contains no dashboard code; every dashboard is written by you, in the user's session.

- **Codex** and **Claude Code** read this file automatically when started in the repo folder.

## Ground rules

- **Dashboards run on Dash Server only.** Build them with the `dash-server` MCP tools. Don't produce a chat artifact, an HTML file, an image, an inline chart, a Streamlit or Flask app, or a Markdown table presented as a dashboard. If the dash-server tools are missing, follow [MCP servers missing](tutorial/10-troubleshooting.md#mcp-servers-missing) and ask the user to restart the session.
- **SQL is read-only.** Run analysis SQL through the `exasol` MCP server, whose login can only read. You never write to the database. Loading data is the user's step (chapter 2).
- **Show your work.** Show each SQL statement before you interpret its result. Explain modeling choices in plain words, and say which ones are assumptions.
- **No secrets.** Don't read, print, copy or ask for the OpenAI key or the database password, and don't put them in files or on a command line. The key lives in `secrets/openai_api_key` (gitignored); you may only check that the file exists. If the user offers to paste a key into the chat, point them to [secrets/README.md](secrets/README.md).
- **Metric units:** area in km², density in residents per km², lengths in m (km for city totals), durations in minutes. Never hectares, miles or feet.
- **State the limits of the data** whenever a question touches them: the MVV data is the scheduled timetable, with no passengers, crowding, delays or live traffic. Jobs are a modeled estimate. Population between 2024 and 2045 is interpolated.
- **Each version builds on the previous one.** When the user asks for the next version, start from the app you built before and keep what works.

## The data

Schema `MUNICH_DATASET`, 20 tables. [data/README.md](data/README.md) describes the tables and sources; [data/data-model.md](data/data-model.md) documents every column. Read the data model before the first query.

**Where things are:**
- Districts, their area, polygons and centroids: `DISTRICTS`. Population counts and the official 2045 forecast: `DISTRICT_POPULATION`. Jobs (2022 estimate and 2040 forecast): `DISTRICT_EMPLOYMENT`.
- The scheduled timetable: the `MVV_*` GTFS tables. Capacity of one scheduled trip: `VEHICLE_CAPACITY` per mode, with per-line overrides in `LINE_CAPACITY`.
- Planned rail and tram projects: `PT_PROJECT_STATIONS`, one row per station and line, with the research behind it in [research/pt-projects-notes.md](research/pt-projects-notes.md).
- Cycling: `CYCLING_INFRASTRUCTURE`, `BIKE_COUNT_STATIONS`, `BIKE_COUNTS_DAILY`, `BIKE_COUNTS_15MIN`. Roadworks: `ROADWORKS`.

**SQL quirks:**
- Column names are lowercase and must be double-quoted (`"district_no"`). Schema and table names are upper case and unquoted.
- Don't use reserved words such as `year`, `hour`, `day`, `value`, `count`, `type` or `name` as aliases.
- The exasol MCP tool rejects a top-level `UNION ALL`; put it inside a CTE. For regular expressions use `REGEXP_INSTR(x, 'pattern') > 0`.
- Every point table has `district_no` (1–25), so district rollups are equality joins.
- For anything per district, use stops with `in_munich = 1`. `COALESCE("parent_station", "stop_id")` groups platforms into a station.
- Use `MVV_ROUTES."line_mode"` (S-Bahn, U-Bahn, Regional rail, Tram, Bus), not `route_mode`.

**Facts to respect:**
- **The reference weekday is Wednesday 21 Oct 2026.** The GTFS feed covers 1 Sep–30 Nov 2026. Use the services that run on that date (`MVV_CALENDAR` with `wednesday = 1` and the date in range, plus the additions and minus the removals in `MVV_CALENDAR_DATES`), so the numbers don't depend on the day the tutorial is run.
- **A departure is weighted by capacity.** One scheduled trip offers the capacity of its line (`LINE_CAPACITY`) or, without an override, of its mode (`VEHICLE_CAPACITY`). These are planning values, not passengers.
- **Population and jobs:** residents are counted for 2015, 2024 and 2025 and forecast for 2045; jobs are estimated for 2022 and forecast for 2040. The model starts from the 2024 count (jobs: the 2022 estimate as the 2024 baseline) and interpolates linearly to 2045 (jobs to 2040), so the 2025 count is not used. Jobs after 2040 stay at the 2040 value.
- **Projects** have an opening year (`opening_year_model`, 2040 where none is published), sometimes a later risk year, a status and a funding flag. Service comes from a published frequency (trains per hour, peak and off-peak, per direction) or, without one, from an existing analog line. Rows with `station_name = 'unknown'` have no published stations.

## Building on Dash Server

1. `apps_list`. If the app doesn't exist: `app_create_exasol_dashboard` with profile `starter-kit`. Never create a second app for the same version.
2. Delete the scaffold's sample queries (`queries/business/*`, `queries/system/*`) with `app_delete_file`; one of them fails its own smoke test.
3. Write the files with `app_put_files`. Put queries in `queries/*.sql` with pyexasol placeholders (`{year!d}`, `{w!f}`, `{ids!s}`) and sample values in `queries/sql_smoke.json` for the healthcheck. Run them with the helper the scaffold writes (`dash_server_exasol.py`); never write a connection, DSN or password into the app. Use plain ASCII spaces in code: `app_put_files` can drop non-breaking spaces.
4. To start from the previous version, read its files with `app_list_files` and `app_read_file`.
5. `app_deploy_draft{name, deployment_target: "live", auto_rollback_on_health_failure: true}`, then `app_run_healthcheck`. On Windows: `app_build` → `app_run_healthcheck` → `app_promote_revision`.
6. If something fails, read `app_tail_logs` or `app_inspect_traceback`, fix and deploy again. On "license limit of 20 parallel connections" or a git conflict, wait a few seconds and retry once.
7. Give the user the URL, `http://127.0.0.1:5100/apps/<app>` (the port is in `exakit status --json`).

**Dash pitfalls:**
- On the initial callback, give every output the first view depends on a concrete value. `no_update` there leaves the page blank.
- Break loops between a store and the controls with `ctx.triggered_id`.
- Don't scroll the page from a callback.
- To test a page in a headless browser, start Chrome with software WebGL (SwiftShader), or maps stay empty. Use a separate browser profile, never the user's open tabs.

**Every dashboard in the tutorial:**
- uses the same look as the ones before it, so the series reads as one product;
- ends with an "SQL executed" foldout that lists each statement the page ran, with its parameters, rows and duration, and the SQL text as sent;
- carries a short caveat line on what the data can't say.

## Checking results

[research/reference-numbers.md](research/reference-numbers.md) has the numbers from one worked implementation of the tutorial. Your modeling choices may differ, so treat them as a reference: compare, and when you are far off, explain which choice causes the difference and let the user decide.

## Running the whole tutorial

When the user asks you to run the tutorial end to end, work through the chapters in order. Use each chapter's prompts as the user's requests and its **Look at it** section to check your result. Stop where only the user can act: installing the kit (chapter 1), restarting the session after `exakit mcp-setup`, downloading and loading the data (chapter 2), and putting the OpenAI key in place (chapter 8). Without a key, build v5 anyway and show a setup line where the assistant would be. After each chapter, report one line: what you built and the URL. At the end, list all URLs and anything skipped, with the reason.

## Guardrails

| The user asks | Expected behavior |
|---|---|
| "Delete the roadworks that have already finished." | Refuse: the login is read-only. Offer a filtered `SELECT` instead. |
| "Which district has the worst traffic right now?" | Explain that there is no live traffic, delay or passenger data. Offer the scheduled-service view. |
| "Create a dashboard." (nothing else) | Ask one clarifying question, then build it on Dash Server. |
