# 10 · Troubleshooting

Start with:
```bash
exakit status
```
Then describe the problem to your agent with the facts: "`exakit status` says …, the dashboard shows …". It can run the healthcheck and read the app's logs on Dash Server, and it changes nothing in the database.

## The database hangs, or `exakit status` says "conflict"

**Symptom:** queries hang or fail with "SSL: UNEXPECTED_EOF_WHILE_READING" or "Connection reset by peer". Dashboards show an error, and `exakit status` reports the runtime as `conflict` or not running.

**Fix:** restart the kit.
```bash
exakit stop && exakit start
exakit status
```

## Too many connections

**Symptom:** queries fail with "license limit of 20 parallel connections" after several deploys. Dash Server keeps idle sessions for each deployed app.

**Fix:** wait a few seconds and retry. If that doesn't help, restart the kit (`exakit stop && exakit start`).

## MCP servers missing

**Symptom:** your agent has no `dash-server` tools, or no `exasol` server, so it can't build dashboards or run SQL. Check with `/mcp` in Codex or Claude Code.

**Fix:**
```bash
exakit mcp-doctor        # what is wrong with the MCP setup
exakit mcp-setup         # register or repair the exasol and dash-server servers for your AI clients
```
Then quit your agent and start it again (`codex` or `claude`) so the tools load. If the dash-server add-on isn't installed:
```bash
exakit marketplace dash-server
exakit mcp-setup
exakit start
```
If the `exasol` server is registered but times out, the database is usually down: see [the section above](#the-database-hangs-or-exakit-status-says-conflict).

**Codex** may ask for approval before it calls an MCP tool. Approve the `exasol` and `dash-server` tools for the session.

## The agent builds an artifact or an HTML page instead of a dashboard

Every dashboard in this tutorial runs on Dash Server. Say "Build it on Dash Server with the dash-server tools", and check that the tools are loaded (see [MCP servers missing](#mcp-servers-missing)).

## Reloading a table

`exakit data-load` skips tables that are already loaded. To reload one table, for example after a load was interrupted, drop it first and load its file again. The `starter-kit` profile of `exapump` has write rights; the agent's MCP login doesn't, so you run this yourself:
```bash
exapump sql -p starter-kit "DROP TABLE MUNICH_DATASET.DISTRICTS"
exakit data-load "$PWD/data/munich-dataset/districts.csv"
```
When `exakit data-load` asks for the table, enter `MUNICH_DATASET.DISTRICTS`. Don't load a file on top of an existing table: rows are appended by column position, which can duplicate rows or put values in the wrong columns.

## SQL fails with "object … not found"

Column names in `MUNICH_DATASET` are lowercase and must be double-quoted: `SELECT "district_no" FROM MUNICH_DATASET.DISTRICTS`. Unquoted `district_no` fails with "object DISTRICT_NO not found". AGENTS.md tells the agent this; if it happens anyway, point it there.

## Blank page after a deploy

**Hard-reload** the page (Cmd+Shift+R on macOS, Ctrl+Shift+R on Windows and Linux). If it stays blank, ask your agent to run the healthcheck and read the app's logs. A common cause is a callback that returns no value on the first load.

## v5: the assistant fails

| On the page | Fix |
|---|---|
| A setup line instead of the input | Put the key in `secrets/openai_api_key` and create the link (see [chapter 8](08-v5-assistant.md#before-you-start-the-openai-key)), then reload. |
| The key is rejected | The key is wrong or revoked. Replace it in `secrets/openai_api_key` and reload. |
| No credits | Add credits to the account that owns the key, at platform.openai.com → Billing. |
| Rate limit | Wait a minute, then ask again. |
| An answer ends with a database error | The database is down: see [the first section](#the-database-hangs-or-exakit-status-says-conflict). |

Don't paste the key into a chat to help the agent fix it. The key only belongs in `secrets/openai_api_key`.

## Maps stay empty in a headless browser

If you or your agent test dashboards in a headless browser, the maps need WebGL. Without a GPU, start Chrome with software WebGL (SwiftShader). Use a separate browser profile for tests.
