---
name: munich-mobility-agents
description: Route every dashboard, chart or Munich mobility question in the tutorial to Dash Server and to the urban-planning agent. Use whenever a request mentions a dashboard, chart, graph, plot, view, visualisation or KPI page (even a bare "create a dashboard"), the MUNICH_DATASET schema (districts, MVV stops and routes, population, jobs, projects, cycling infrastructure, bike counters, roadworks), or the munich-mobility-planning-v1 … v5 and munich-cycling-coverage dashboards. Triggers — "create a dashboard", "build a dashboard", "make a chart", "visualise this", "Munich", "MUNICH_DATASET", "MVV", "district", "v1", "v5", "cycling coverage".
---

# munich-mobility-agents

Two jobs, in this order.

## 1. Dashboards go to Dash Server. No exceptions.
Read `references/dashboard-routing.md`. In short:
- "Dashboard", "chart", "graph", "plot", "view", "visualise", "KPI page" → a **Dash Server** app built through the `dash-server` MCP control plane, using the deploy recipe in `references/playbook.md` section 4. Hand back the URL (default `http://127.0.0.1:5100/apps/<app>`).
- Never an Artifact, an HTML or React page, `show_widget`, an inline SVG, an image, a Streamlit app, or a Markdown table labelled "dashboard". A `PreToolUse` hook (`assets/block_artifacts.py`) blocks the Artifact and widget tools. If you hit it, that's the rule working.
- `dash-server` tools missing → `exakit marketplace dash-server`, `exakit mcp-setup`, `exakit start`, `exakit status`, then tell the user to restart Claude.
- A bare "create a dashboard" → ask one question (which question or which version), then build on Dash Server.
- "It already exists, refresh it" → update the existing app; don't create a second one.

## 2. Questions go to the urban-planning agent
Everything in this tutorial (district coverage, population and jobs versus transport, the forecast, scenarios, cycling infrastructure, and building or deploying the series) goes to the `urban-planning` subagent (`~/.claude/agents/urban-planning.md`), with the user's request passed on verbatim. If subagents are unavailable, load the `urban-planning` skill and follow it yourself. Relay the answer, the SQL, the gaps and the URL.

| App | What it is |
|---|---|
| `munich-mobility-planning-v1` … `-v5` | the planning series (per resident → + jobs → forecast → scenarios → assistant) |
| `munich-cycling-coverage` | the start of the cycling series |

## Working rules for any query on MUNICH_DATASET
- Start with `references/playbook.md` (data quirks, deploy recipe, orders of magnitude) and `references/sql-snippets.md` (building blocks), then `references/data-model.md`. Column names are lowercase and must be double-quoted (`"district_no"`).
- Show the SQL, run it through the read-only `exasol` MCP server, show the result, then interpret. Every number in an answer comes from a query that was shown.
- Say what the data cannot answer: MVV GTFS is scheduled service, with no passengers, delays, crowding or live traffic. Nothing here is synthetic.
- Write requests (delete, update, create table) are refused: the MCP login is read-only and the database enforces it.
- Example prompts: `references/demo-prompts.md`.
