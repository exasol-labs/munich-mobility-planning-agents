# Dashboard routing: Dash Server, never an artifact

## Why this file exists
Without it, an agent asked to "create a dashboard" takes the fastest path it knows: an HTML artifact, a React page, an inline chart or a Markdown table. On this demo every visual result must live on **Dash Server** so the audience sees a hosted, re-openable dashboard built from inspectable SQL on the local Exasol database.

## The rule
Any request whose output is visual — dashboard, chart, graph, plot, view, visualisation, KPI page, executive view, report page, "show me" — is built as a Dash Server app. Three layers enforce it on an installed machine:

1. `~/.claude/CLAUDE.md` carries the rule block (between `munich-mobility-agents:start/end` markers).
2. This skill's description triggers on the same words.
3. A `PreToolUse` hook in `~/.claude/settings.json` runs `assets/block_artifacts.py`, which denies the `Artifact` tool (publishing a page) and any `show_widget` tool with a message that points back here. `MUNICH_ALLOW_ARTIFACTS=1` in the environment disables the hook for one session.

## The build path for the tutorial dashboards
Every app in the series has a spec and its finished source in the tutorial repo: `dashboards/<app>/README.md` plus `app.py`, `munich_ui.py`, `sql_log.py`, `queries/*.sql`, `queries/sql_smoke.json` and `requirements.txt`.
- **Build:** extend the previous version per the spec. Show and run the key SQL once, and check it against `research/reference-numbers.md`.
- **Deploy:** follow `references/playbook.md` section 4:
  1. `app_create_exasol_dashboard`, which writes `dash_server_exasol.py`.
  2. Delete the scaffold's sample `queries/business/*` and `queries/system/*`, which fail their own smoke test.
  3. Copy the files into the draft workspace with `cp`.
  4. `app_deploy_draft{name, deployment_target: "live", auto_rollback_on_health_failure: true}`, then `app_run_healthcheck{name}`.
  5. Windows: `app_build` → `app_run_healthcheck` → `app_promote_revision`.

Design rules: let Exasol compute and Dash render; never query at import time; use `{x}` / `{x!d}` placeholders, never `:name`; check `has_error(rows)` before iterating; use the read-only profile only. **Never return `no_update` on the initial call for anything the map depends on, or the page renders blank in a real browser.** No code may scroll the page.

## App names
`munich-mobility-planning-v1` … `munich-mobility-planning-v5` and `munich-cycling-coverage`. Reuse them: "refresh" means updating the existing app.

## What to do if dash-server is missing or down
Work down this list; stop at the first step that fixes it, and never substitute another renderer.

1. `exakit status` — is dash-server `running`, `stopped`, or `not installed`?
2. Not installed → `exakit marketplace dash-server` (installs the add-on; non-interactive form: `EXAKIT_MARKETPLACE_ADDONS=dash-server exakit marketplace`).
3. `exakit mcp-setup` — registers the control plane as the `dash-server` MCP server in Claude Code.
4. `exakit start` — starts the database and every add-on, dash-server included.
5. Tell the user: "dash-server is installed and running; restart Claude so its tools load, then ask again." The tools of a server registered during a session appear only in the next session.
6. Stopped but installed → step 4 only. Page blank or 500 while the control plane answers → `exakit stop && exakit start`.
