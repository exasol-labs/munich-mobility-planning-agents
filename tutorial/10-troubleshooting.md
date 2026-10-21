# 10. Troubleshooting

These are the problems we actually hit while building this tutorial, and what fixed them. Start with the quick check:

```bash
exakit status
python3 install.py      # ends with a readiness table: what is ready and what is not
python3 scripts/check_all.py
```

## Running everything with an agent

[AGENTS.md](../AGENTS.md) has a runbook for an agent (for example Claude Code) that runs the whole tutorial end to end: the ground rules, how to deploy a finished dashboard with the Dash Server MCP tools, how to build one yourself, and what to report back.

## The database hangs, or `exakit status` says "conflict"

**Symptom:** queries hang or fail with "SSL: UNEXPECTED_EOF_WHILE_READING" or "Connection reset by peer". The dashboards show an error panel, and `exakit status` reports the runtime as `conflict` or not running, although something still holds port 8563.

**Fix:** restart the kit.

```bash
exakit stop && exakit start
exakit status
```

## Too many connections

**Symptom:** queries fail after you have deployed several dashboards. The local database allows 20 connections, and Dash Server keeps idle sessions for each deployed app.

**Fix:** wait a few seconds and retry once. If that doesn't help, restart the kit (`exakit stop && exakit start`). It's worth restarting after a long build session anyway.

## MCP servers missing

**Symptom:** Claude Code has no `dash-server` tools (`app_create_exasol_dashboard`, `app_deploy_draft`, …), or the `exasol` MCP server is not connected, so Claude can't run SQL.

**Fix:**

```bash
exakit mcp-doctor        # what is wrong with the MCP setup
exakit mcp-setup         # register (or repair) the exasol and dash-server servers for your AI clients
```

Then **restart Claude Code**, so the tools load. If the dash-server add-on isn't installed at all, install and start it first:

```bash
exakit marketplace dash-server
exakit mcp-setup
exakit start
exakit status
```

If the `exasol` server is registered but times out, the database is usually down: see [the conflict section above](#the-database-hangs-or-exakit-status-says-conflict).

## Reloading a table

**Don't run `exakit data-load` again over existing tables.** It appends into existing tables by column position, so a second load doubles rows or puts values into the wrong columns. Either drop the table first, or use:

```bash
python3 scripts/load_data.py --replace
python3 scripts/verify_data.py
```

`--replace` reloads only the tables whose row counts differ from the expected ones. `verify_data.py` then checks the counts.

## Claude builds an artifact or HTML page instead of a dashboard

Every dashboard in this tutorial runs on Dash Server. `python3 install.py` installs a rule (and a hook that blocks chat artifacts, unless you used `--no-hook`). If Claude still offers an artifact, say "Build it on Dash Server through the dash-server MCP tools", and check that the dash-server tools are loaded (see [MCP servers missing](#mcp-servers-missing)).

## SQL fails with "object … not found"

Column names in `MUNICH_DATASET` are lowercase and must be double-quoted: `SELECT "district_no" FROM MUNICH_DATASET.DISTRICTS`. Unquoted `district_no` fails with "object DISTRICT_NO not found". Table and schema names need no quotes.

## Blank page after a deploy

The browser still holds the old revision's page. **Hard-reload** it (Cmd+Shift+R on macOS, Ctrl+Shift+R on Windows and Linux). If it stays blank, ask Claude to run `app_run_healthcheck` and `app_tail_logs` for the app.

Then run the first-render smoke test:

```bash
python3 scripts/check_dashboard.py munich-mobility-planning-v4
```

## A deployed file is subtly broken

`app_put_files` once dropped a non-breaking space in `munich_ui.py` while we built the series. When you deploy a finished dashboard, have Claude copy the files byte for byte (a plain file copy into the draft workspace) instead of retyping them. Also remove the sample queries that `app_create_exasol_dashboard` creates, so the healthcheck's SQL smoke test runs only the app's own files.

## My numbers differ slightly from the Check boxes

The reference weekday is pinned to Wednesday 21 Oct 2026 in every query, so the numbers don't depend on the date you run the tutorial. If yours differ, the data load is the likely cause (see [Reloading a table](#reloading-a-table)). To compare against the expected values:

```bash
python3 scripts/verify_numbers.py --case all
```

v5's default year is the current calendar year, so after 2026 its first view (and the "now" mark) moves too. The cycling dashboard's "now" is fixed at 2026.

## v5: the Ask box is missing, or the assistant fails

| Message | Fix |
|---|---|
| "The assistant needs an OpenAI API key …" (instead of the input) | Put the key in `secrets/openai_api_key`, run `python3 install.py`, reload the page. |
| "… is readable by other users. Run: chmod 600 …" | `chmod 600 secrets/openai_api_key` (`install.py` does this too). |
| "OpenAI rejected the API key." | The key is wrong or revoked. Replace it in `secrets/openai_api_key` and reload. |
| "The OpenAI account has no credits. Add credits at platform.openai.com → Billing." | Add credits to the account that owns the key. No restart needed: the key and account are checked on every question. |
| "OpenAI rate limit reached. Try again in a minute." | Wait, then ask again. |
| "The answer was cut off …" | Ask a narrower question. |
| An answer ends with a database error | The database is down: see [the conflict section](#the-database-hangs-or-exakit-status-says-conflict). |

Never paste the key into a chat to "help" Claude fix it. The key only belongs in `secrets/openai_api_key`.

## Headless browser tests show no map

If you test the dashboards with a headless browser (Playwright, headless Chrome), the maps need WebGL. Without a GPU, start Chrome with software WebGL (SwiftShader), or the map stays empty while everything else renders. Use a separate browser profile for tests, not the tab you are working in.

## Still stuck

Ask Claude with the facts: "`exakit status` says …, the dashboard shows …, here is the healthcheck output." The urban-planning agent can read the app's logs (`app_tail_logs`) and run the healthcheck, and it changes nothing in the database.
