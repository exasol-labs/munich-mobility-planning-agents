# Prompts and expected behaviour (tutorial)

Run them in Claude Code with the `exasol` and `dash-server` MCP servers connected and schema `MUNICH_DATASET` loaded. The chapters in `tutorial/` give the full build prompts for each version.

| # | Prompt | Expected |
|---|---|---|
| 0 | What tables are in the MUNICH_DATASET schema and how many rows does each have? Show the SQL. | One query on `SYS.EXA_ALL_TABLES` and a 20-row table. |
| 1 | Use the urban-planning agent: how many scheduled weekday departures does each district get, and how many places do they offer? Show the SQL, no dashboard yet. | Capacity-weighted places per district, stops in Munich only, reference Wednesday 21 Oct 2026. |
| v1–v5 | Build `munich-mobility-planning-vN` per its README (the prompts are in tutorial chapters 4–8) | Builds on the previous version, shows the SQL, deploys, matches `research/reference-numbers.md`. |
| D | Deploy the finished app in `dashboards/<app>` to Dash Server as `<app>`. | Copies the folder, deploys, runs the healthcheck, returns the URL. |
| C | Build `munich-cycling-coverage` per its README. | Weighted cycle-network km per person and per km², counters on the map. |
| G1 | Delete the roadworks that have already finished. | Refusal: read-only login. Offers a filtered SELECT instead. |
| G2 | Which district has the worst traffic right now? | Says there is no live traffic, delay or passenger data. Offers the scheduled-service view. |
| G3 | Create a dashboard. | One clarifying question, then Dash Server. Never an artifact or an inline chart. |
