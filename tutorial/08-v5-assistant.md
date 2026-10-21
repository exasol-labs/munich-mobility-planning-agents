# 8. v5: An assistant that drives the view

About 20 minutes, plus a few cents to a dollar of OpenAI usage. You need v4 from [07-v4-scenarios.md](07-v4-scenarios.md) and an OpenAI API key with credits.

## What you'll build

v4 with an **Ask** box. You type a question such as "Show 2045 with the funded projects" or "What if the S-Bahn ran every 10 minutes?". An assistant answers from SQL on your database, from the dashboard's own model, from the research in this repo and from the web. It can also **change the view for you**: the year, the scenario and what-ifs. When it does, the map, the chart and the controls follow. Every answer shows how it got there.

**URL:** http://127.0.0.1:5100/apps/munich-mobility-planning-v5

## The idea: let the user ask, and keep every number traceable

The dashboards so far answer the questions they were built for. v5 lets someone ask the next question without a new build. It does so without turning into a black box:
- **The model is OpenAI `gpt-6-astra`** at reasoning effort medium, called through the Responses API. It is **stateless** (`store=False`): the app carries the conversation itself.
- **It has five tools:**
  - `run_sql`: read-only, guarded, at most 200 rows.
  - `dashboard_scenario`: runs v4's model for any year, w and scenario.
  - `what_if`: turns a frequency change or a new line into extra places per district.
  - `set_view`: the assistant changes the view, and the controls follow it.
  - web search with citations.
- **Its context** is `research/v5-context.md`, about 44k tokens, sent with every request and cached by OpenAI. It contains the data model, the dashboard's model, the reference numbers, the findings and the research on plans and projects. Read it; it's the same Markdown you can browse in `research/`.
- **Every answer** carries badges (Data, Plans, Web, Assumption) and a "How I got this" fold-out with each SQL statement, model run, what-if and web source, plus the tokens and an estimated cost.

## Before you start: the OpenAI key

1. Create a key at platform.openai.com and make sure the account has credits.
2. Put the key in `secrets/openai_api_key`, on one line with nothing else. The folder is gitignored, and `secrets/openai_api_key.example` shows the format. **Never paste a key into a chat**, including this one with Claude.
3. Link it to the place where the dashboard reads it:

```bash
python3 install.py
```

`install.py` sets the file to mode 600 and links `~/.exasol-starter-kit/credentials/openai_api_key` to it. Its readiness table should show "OpenAI key in secrets/openai_api_key" as OK. The dashboard reads the key on every question, so replacing it later needs only a page reload.

**What is sent to OpenAI:** your questions, the context pack, the current view, and the results of the tools the model calls (SQL rows, at most 200 per query; model and what-if results). Database credentials are never sent: the SQL runs on your machine.

**What it costs:** measured at about **US$0.05–0.60 per question**. A one-sentence question cost $0.05, a web search question $0.23, and "Show me 2045 with the funded projects" $0.56. The estimate under each answer leaves out OpenAI's cache-write premium and web-search fees, so the bill is slightly higher.

## Build it with Claude (the main path)

```text
Use the urban-planning agent. Build the Dash Server app munich-mobility-planning-v5 following the spec in
dashboards/munich-mobility-planning-v5/README.md. Start from your v4 app (munich-mobility-planning-v4) and add
what the spec adds: the {extra} what-if input in ranking.sql, the view-store that drives map, chart and
controls, the Ask panel and Answers section, the two-group "SQL executed" foldout, and assistant.py with the
key lookup, SQL guard, tools and cost estimate. Use research/v5-context.md as context.md. Don't read, print or
ask me for the OpenAI key: it is already linked at ~/.exasol-starter-kit/credentials/openai_api_key.
Rules: Dash Server only, through the dash-server MCP tools (no artifact, HTML file or inline chart). All SQL
read-only through the exasol MCP. Show me each SQL statement before you run it and before you interpret its
result. Check the reference checks in the spec that need no model call first (default view, parity with v4,
guard), then deploy, run the healthcheck and give me the URL. I'll ask the first question myself.
```

## Shortcut: deploy the finished version

```text
Deploy the app in dashboards/munich-mobility-planning-v5 to Dash Server as munich-mobility-planning-v5 (app_create_exasol_dashboard, copy all files, app_deploy_draft, app_run_healthcheck) and give me the URL.
```

## Look at it

- **The default view is now.** The page opens on the current year, 2026, marked "(now)". Munich overall is already −1.66 % against 2024, from growth alone.
- **Click a chip,** e.g. "Show 2045 with the funded projects". It only fills the input; click **Ask** to send. Watch the status line: "Thinking…", "Updating the map…", "Writing the answer…". The map switches to 2045 and Funded only, and the Scenarios controls follow, before the answer is finished.
- **Follow up:** "Now use pessimistic dates." The assistant remembers the conversation and changes one setting.
- **Ask a what-if:** "What if the S-Bahn ran every 10 minutes?". The assistant states its assumptions (lines, trains per hour, hours, capacity), computes extra places per district and can put the what-if on the map. A yellow banner then says it's a hypothetical, not a real plan.
- **Ask about the plans:** "What is the current planned opening date of the U5 extension to Pasing? Cite your source." It searches the web, and the sources appear under "How I got this".
- **Try the guardrails.** Ask it to delete or change data: `run_sql` rejects anything but one `SELECT`, and the database user is read-only anyway. Ask about passengers or delays: it says the data has none.
- **Use the controls yourself.** The slider and Scenarios still work, and the assistant gets the current view with your next question.
- **Open "SQL executed".** It has two groups: the dashboard's queries for the current view, and every statement the assistant ran in this conversation, labelled with the tool and your question. A rejected attempt is shown as "rejected by guard".
- **New conversation** clears the answers, the what-ifs and the assistant's SQL, and resets the view to now.

> **Check**
> - First load: **2026 (now)**, w = 1.0, no projects; Munich overall **−1.66 %** (33,853 vs 34,425)
> - "Show 2045 with the funded projects": the view line reads "Showing 2045 · w = 1.0 · Scenario: Funded only · 6 project(s) active · +7.3 M places/day net", and Munich overall is **−6.84 %**
> - Set by hand, the controls give the v4 numbers: 2045 None −13.37 %, Everything −2.42 %, 2nd Stammstrecke only **−8.65 %**
> - A what-if "S4 at least 4 trains/h for 19 h" adds +729,600 places, the same as v4's 15-minute rule for S4
>
> ```bash
> python3 scripts/check_dashboard.py munich-mobility-planning-v5
> python3 scripts/verify_numbers.py --case R6
> ```

## What the data can't tell you

- A what-if is capacity arithmetic, not a plan. Demand shifts, crowding, travel time, cost and feasibility are not modelled, and the assistant is told to say so.
- Web answers are only as good as their sources. Open the cited links.
- The assistant can be wrong. That's why every number is backed by a tool call you can inspect, and why the reference numbers are in its context.
- Still scheduled service only: no passengers, delays or live traffic.

## How it works

**One store drives the page.** A `view-store` (year, w, projects, pessimistic dates, what-if) is the only input of the map and chart. The controls write it, and so does the assistant's `set_view`. A second callback copies it back into the controls.

**The what-if enters the SQL as one string.** `assistant.py` turns a what-if into `'district_no:places;district_no:places'`, and `ranking.sql` splits it:

```sql
    SELECT REGEXP_SUBSTR({extra!s}, '[^;]+', 1, LEVEL) AS item FROM DUAL CONNECT BY LEVEL <= 100
```
```sql
           COALESCE(dep.places, 0) + COALESCE(sel.add_places, 0) + COALESCE(ex.add_places, 0) AS places, COALESCE(dep.places, 0) AS places_today,
```

With an empty string the result is identical to v4.

**A frequency what-if** reuses the 15-minute rule with the frequency as a parameter:

```python
            target = float(tph) * float(hours) * 2
```
```python
                extra_dep = max(dep, target) - dep
```

**The guard** in front of `run_sql` allows one statement only and refuses comments, modifying keywords and system tables. Every table must be written `MUNICH_DATASET.TABLE`:

```python
FORBIDDEN = re.compile(
    r"\b(insert|update|delete|merge|drop|create|alter|truncate|grant|revoke|"
    r"commit|rollback|call|execute|import|export)\b", re.I)
```

Behind it, the database user is read-only: a `CREATE TABLE` that got past the guard would fail with "insufficient privileges".

**The request** sends the context pack as `instructions`, with `store=False`, effort medium and web search enabled. There are at most 12 tool rounds per question. The full spec, including the tool schemas and the key lookup, is in [dashboards/munich-mobility-planning-v5/README.md](../dashboards/munich-mobility-planning-v5/README.md).

Next: [09-cycling-series.md](09-cycling-series.md), a new series on cycling.
