# 3 · Install the planning agent

**Goal:** Claude Code knows the data, the method and the dashboard look, and always builds dashboards on Dash Server.
**Time:** about 5 minutes.

## 3.1 Run the installer
```bash
python3 install.py
```
It installs into your Claude Code configuration (`~/.claude/`):
- **Agent `urban-planning`** (`agents/urban-planning.md`): the analyst you'll work with in chapters 4–9.
- **Skills:**
  - `urban-planning`: the method and the dashboard series.
  - `munich-mobility-agents`: the data model, SQL building blocks, the deploy recipe and the shared dashboard look `munich_ui.py`.
- **A Dash Server rule** in `~/.claude/CLAUDE.md`, plus any other AI clients it finds (Codex, Cursor, Gemini CLI, OpenCode, Continue). It says every dashboard, chart or view is built on Dash Server, never as a chat artifact or an image. A small hook enforces it in Claude Code.
- **The key link for v5:** `secrets/openai_api_key` → `~/.exasol-starter-kit/credentials/openai_api_key`. The key is optional until [chapter 8](08-v5-assistant.md).

At the end it prints a readiness check:
```
  OK    exakit on PATH
  OK    database running
  OK    dash-server running
  OK    skill munich-mobility-agents
  OK    skill urban-planning
  OK    agent urban-planning
  WARN  OpenAI key in secrets/openai_api_key  ->  only needed for v5
```
**Quit Claude Code and start it again** (`claude`), so it loads the new agent and skills.

`python3 install.py --uninstall` removes everything it installed. It leaves your key file alone.

## 3.2 Your first question
In Claude Code:
```
Use the urban-planning agent: how many scheduled weekday departures does each district get, and how many places do they offer? Show the SQL, no dashboard yet.
```
Watch how it works: **ask → inspect (show the SQL) → run → validate → answer**. It weights each departure by the vehicle's capacity (a U-Bahn train is not a bus), counts only stops inside Munich, and says what the data can't answer.

Then try the second guardrail:
```
Which district has the worst traffic right now?
```
There's no live traffic, delay or passenger data, so it says so and offers the scheduled-service view instead.

## Check
- The readiness check has no FAIL.
- The answer to 3.2 shows its SQL and mentions the reference weekday, Wednesday 21 Oct 2026, pinned inside the GTFS window (1 Sep–30 Nov 2026).

Next: [4 · v1 – how well is each district served today?](04-v1-residents.md)
