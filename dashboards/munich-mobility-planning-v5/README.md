# munich-mobility-planning-v5: Ask the assistant

**Question:** the same as v4, but you can ask about it in plain language. The assistant answers from SQL, from the dashboard's own model, from the research in its context and from the web. It can change the view for you and compute what-ifs.

**URL once deployed:** http://127.0.0.1:5100/apps/munich-mobility-planning-v5 · tutorial chapter: [08-v5-assistant.md](../../tutorial/08-v5-assistant.md) · builds on [v4](../munich-mobility-planning-v4/README.md)

The model is OpenAI `gpt-6-astra` at reasoning effort `medium`, called through the Responses API. It needs an OpenAI API key with credits. Without a key, the page still works as v4, but without the Ask box.

## What it shows (top to bottom)

1. **Header:** "Munich Mobility Planning", subtitle "v5 – Ask the assistant", then "Ask about how well each district is served by scheduled public transport, now and to 2045, the planned projects, or a what-if. Set the year and scenario yourself, or let the assistant set them. Scheduled service only, not passengers."
   - Under it, the **view line**: the current state as text, e.g. "Showing 2026 (now) · w = 1.0 · Scenario: None (today's timetable) · 0 project(s) active · +0 places/day net · source: MUNICH_DATASET on Exasol, read-only".
2. **Year slider:** 2024–2045, marks 2024, 2025, 2030, 2035, 2040 and 2045, plus "<current year> (now)". Its default is the current calendar year, clamped to 2024–2045.
3. **Scenarios foldout:** as in v4. The presets also include a disabled "Custom", which is selected when the ticked projects match no preset.
4. **Ask panel:**
   - Three example chips: "Show 2045 with the funded projects", "What if the S-Bahn ran every 10 minutes?" and "Which district is worst served today, counting jobs?". A chip only fills the input; nothing is sent until you click **Ask**.
   - A text area, the **Ask** and **New conversation** buttons, and the line "Answers by OpenAI gpt-6-astra. Questions, the context pack and the SQL results it asks for are sent to OpenAI."
   - A status line while a question runs: "Thinking…", "Running SQL…", "Running the dashboard model…", "Computing what-if…", "Updating the map…", "Searching the web…" or "Writing the answer…".
   - Without a key, the input is hidden and a setup line explains where the key goes.
5. **What-if banner** (only while a what-if is on the map): "What-if: <name>, a hypothetical, not a real plan".
6. **Map and change chart** side by side, as in v4. The titles carry "(now)" for the current year, the scenario and the what-if name. The chart subtitle ends "with the active projects and any what-if".
7. **Answers** (hidden until the first answer or error arrives). Your questions and the answers come newest last. Each answer has:
   - source badges: **Data** (SQL, the model or a view change), **Plans** (projects named), **Web**, **Assumption** (a what-if);
   - a **"How I got this"** fold-out: every SQL statement, model run, what-if, view change, web search and cited web source, and a footer with the model, the number of requests, input/cached/output tokens, the estimated cost in US$ and the time.
8. **"SQL executed" foldout** at the very bottom, in two groups:
   - "Dashboard queries for the current view": `ranking.sql`, `projects.sql` and `geo.sql`.
   - "Assistant queries in this conversation": every statement the assistant's tools ran. Each is labelled with the tool and the question it served. Rejected attempts are listed too, marked "rejected by guard: <reason>", with the SQL shown as "SQL (not sent)". New conversation clears this group.

The page never scrolls by itself.

## Files

| File | Role |
|---|---|
| `app.py` | The page. One `dcc.Store` (`view-store`: year, w, projects, pessimistic, what-if) is the only source for the map and chart. Callbacks: `refresh` (view → map, chart, titles, view line, banner, SQL group 1); `view_to_controls` (view → slider, preset, w, checklists); `controls_to_view` (controls → view, `prevent_initial_call=True`, writes only on a real change); `chat` (boot, Ask, New conversation and a 1-second poll while a job runs); a clientside callback for the chips. Also the `Backend` class: the only things `assistant.py` may use from the dashboard. |
| `assistant.py` | The OpenAI tool loop: key lookup, SQL guard, tool schemas, sessions, background jobs, what-if arithmetic, cost estimate. |
| `context.md` | The fixed context pack sent as `instructions` with every request, 140,862 bytes (about 44k tokens; 44,066 counted by OpenAI's token count endpoint before the last small edits). It contains role and rules, the data model, the dashboard's model, the reference numbers, the findings and the research on plans and projects, and `ranking.sql` in full. It is the same file as `research/v5-context.md`. |
| `queries/ranking.sql` | v4's model plus a what-if input `{extra!s}` (below). |
| `queries/projects.sql` | Unchanged from v4. |
| `queries/geo.sql` | As in v1. |
| `queries/whatif_line_stations.sql` | Today's departures per line and station inside Munich on the reference Wednesday, for a frequency what-if. |
| `queries/stops.sql` | Munich stop names per district with a mean position, for placing new-line stations. |
| `queries/capacity.sql` | `VEHICLE_CAPACITY` by mode, for a new line. |
| `queries/sql_smoke.json` | Smoke parameters for all six query files (`ranking.sql` with `"extra": ""`, `whatif_line_stations.sql` with `"lines": "S1,S4"`). |
| `munich_ui.py`, `dash_server_exasol.py` | As in v1. v5 has no `sql_log.py`; the foldout code is in `app.py`. |
| `requirements.txt` | v1's three packages plus `openai==3.35.1`. |
| `dash-app.json` | Route `/apps/munich-mobility-planning-v5`, profile `starter-kit`. |

## How it computes

**The map and chart** are v4's. The one SQL change is the what-if input in `ranking.sql`:

```sql
ex_raw AS (
    -- v5 what-if: extra places per weekday per district, passed as one string 'district_no:places;district_no:places'
    -- ('' = NULL = nothing added). Built by assistant.py from what_if(); counted in every year >= 2024.
    SELECT REGEXP_SUBSTR({extra!s}, '[^;]+', 1, LEVEL) AS item FROM DUAL CONNECT BY LEVEL <= 100
),
ex AS (
    SELECT CAST(SUBSTR(item, 1, INSTR(item, ':') - 1) AS DECIMAL(4, 0)) AS district_no,
           SUM(CAST(SUBSTR(item, INSTR(item, ':') + 1) AS DOUBLE)) AS add_places
    FROM ex_raw WHERE item IS NOT NULL AND {year!d} >= 2024
    GROUP BY CAST(SUBSTR(item, 1, INSTR(item, ':') - 1) AS DECIMAL(4, 0))
),
```
```sql
           COALESCE(dep.places, 0) + COALESCE(sel.add_places, 0) + COALESCE(ex.add_places, 0) AS places, COALESCE(dep.places, 0) AS places_today,
```

With `extra = ''` the output is identical to v4. The app checks the string before it is used (`norm_view`: `(\d{1,2}:\d+)(;\d{1,2}:\d+)*`); anything else is dropped.

**The default view** is the current calendar year, w = 1.0, no projects and no what-if (`assistant.default_view()`). It is used on first load, after New conversation and when there is no key. On the first call the chat callback always returns a concrete view, never `no_update`, because `refresh` waits on that output when the page loads.

**The key** is read on every question, never cached, logged or sent to the page:
1. `OPENAI_API_KEY` in the process environment, else
2. `~/.exasol-starter-kit/credentials/openai_api_key`, which must not be readable by group or others (mode 600).

In this repo you put the key in `secrets/openai_api_key` (gitignored). `python3 install.py` sets it to mode 600 and links the kit path to it.

**The request** (`_request` in `assistant.py`):

```python
    kw = dict(model=MODEL, instructions=_context(), input=items, tools=TOOLS, store=False,
              reasoning={"effort": REASONING_EFFORT}, max_output_tokens=MAX_OUTPUT_TOKENS,
              include=["web_search_call.action.sources"], stream=True)
```

- `store=False`: OpenAI keeps no conversation. The app carries the earlier turns of this browser session itself, dropping the oldest whole turns above an estimated 150,000 tokens (`HISTORY_TOKEN_CAP`).
- Each question goes with a line describing the current view, e.g. "[Current view on the page] year 2045 · w = 1.0 · scenario: Funded only · …".
- At most 12 tool rounds per question (`MAX_TOOL_ROUNDS`); the last round runs with `tool_choice = "none"`. A job times out after 600 s. Each question runs in a background thread and the page polls it once a second.

**The tools** (strict JSON schemas in `TOOLS`):

| Tool | What it does |
|---|---|
| `run_sql` | One read-only `SELECT` or `WITH` on `MUNICH_DATASET`, through the app's own Exasol profile (the read-only MCP user). At most 200 rows come back; 30 s timeout. |
| `dashboard_scenario` | Runs `ranking.sql` for a year, w, projects or preset, pessimistic dates and optionally a stored what-if. Returns the city figure, the % change since 2024 and all 25 districts. Doesn't change the view. |
| `what_if` | Turns a hypothetical into extra places per weekday per district and stores it under a name. Doesn't change the view. |
| `set_view` | Changes this viewer's map, chart and view line. The controls follow. Everything is validated first; on any error the view stays as it was. |
| `web_search` | OpenAI's built-in web search. Cited URLs show under "How I got this". |

**The SQL guard** runs before `run_sql` sends anything. It allows one statement only, with no comments (`--`, `/* */`). It must start with `SELECT` or `WITH` and contain no modifying keyword. System objects are refused, and every table must be named `MUNICH_DATASET.TABLE` (CTE names and `DUAL` are allowed):

```python
FORBIDDEN = re.compile(
    r"\b(insert|update|delete|merge|drop|create|alter|truncate|grant|revoke|"
    r"commit|rollback|call|execute|import|export)\b", re.I)
SYSTEM_OBJECTS = re.compile(r'\b(?:"?SYS"?\s*\.|EXA_[A-Z_]+)', re.I)
```

Behind the guard, the database user itself is read-only: a `CREATE TABLE` sent past the guard fails with "insufficient privileges".

**What-if arithmetic** (`what_if` in `assistant.py`):
- **`frequency`:** for each listed line and Munich station, the extra places are (GREATEST(departures today, trains per hour × hours × 2) − departures today) × capacity per trip. Hours default to 19. This is the 15-minute rule of v4 with the frequency as a parameter. Today's departures come from `whatif_line_stations.sql`.
- **`new_line`:** per station, (peak × 6 + off-peak × 13) × 2 departures × the mode's capacity per trip (`capacity.sql`). A station is either an existing Munich stop name, matched against `stops.sql`, or a new point given by lat/lon and placed in its district by point-in-polygon.
- The result is the string `'district_no:places;…'`. It adds to supply in every year shown; departures and the 2024 baseline don't change.

```python
            target = float(tph) * float(hours) * 2
```
```python
                dep = float(r["dep_today"])
                extra_dep = max(dep, target) - dep
```
```python
            dep = (float(peak) * 6 + float(off) * 13) * 2
```

**Cost estimate** (shown per answer), at US$ per 1M tokens:

```python
PRICES = {"input": 10.00, "cached": 1.00, "output": 50.00}  # US$ per 1M tokens, gpt-6-astra standard (v5-prep)
```

The estimate leaves out the cache-write premium and web-search fees, so the bill is slightly higher.

**Errors are shown in plain words.** For example: "The OpenAI account has no credits. Add credits at platform.openai.com → Billing.", "OpenAI rejected the API key.", "OpenAI rate limit reached." or a database message. A job never dies silently: any failure ends the turn with a visible error line.

## Controls

| Control | Effect |
|---|---|
| Year slider, Scenarios (preset, w, pessimistic dates, checklists) | As in v4, but they write `view-store`. An active what-if is kept. |
| Example chips | Fill the input; nothing is sent. |
| Ask | Starts a question (disabled while one runs). |
| New conversation | Clears the answers, stored what-ifs and SQL group 2, and resets the view to the default (current year). |

## Reference checks

| Check | Expected |
|---|---|
| First load | 2026 (now), w = 1.0, no projects; Munich overall **−1.66 %** (33,853 vs 34,425), 0 places added; 25 polygons, 26 bars; Answers hidden |
| No key | setup line shown, input hidden; map and chart still work |
| Parity with v4 (set the controls) | 2045 None −13.37 %, Funded −6.84 % (+7.3 M), Everything −2.42 % (+12.2 M), 2. Stammstrecke only −8.65 % |
| Ask "Show 2045 with the funded projects" | the assistant calls `set_view`; the view line reads "Showing 2045 · w = 1.0 · Scenario: Funded only · 6 project(s) active · +7.3 M places/day net"; Munich overall −6.84 %; the answer quotes 32,069 places per 1,000 activity |
| What-if "S4 at least 4 trains/h for 19 h" | +729,600 places per weekday, equal to v4's 15-minute rule for S4 |
| Guard | DELETE, two statements, unqualified tables, comments and system tables are rejected |
| Healthcheck | healthy (SQL smoke on all six query files) |

Measured cost on 21 Oct 2026, from the app's estimate:

| Question | Requests | Time | Cost |
|---|---|---|---|
| "In one sentence: what does the colour of a district on the map show?" | 1 | 4.6 s | US$0.05 |
| "Now use pessimistic dates." (follow-up) | 2 | 5.4 s | US$0.11 |
| "What is the current planned opening date of the U5 extension to Pasing? Cite your source." (3 web searches) | 1 | 17.5 s | US$0.23 |
| "Show me 2045 with the funded projects." | 2 | 8.8 s | US$0.56 |

## Deploy

1. Put your OpenAI key in `secrets/openai_api_key` (one line, nothing else) and run `python3 install.py`. Never paste the key into a chat.
2. Ask Claude Code:

```text
Deploy the app in dashboards/munich-mobility-planning-v5 to Dash Server as munich-mobility-planning-v5 (app_create_exasol_dashboard, copy all files, app_deploy_draft, app_run_healthcheck) and give me the URL.
```

The steps are as in [v1](../munich-mobility-planning-v1/README.md#deploy). Copy `context.md` too: `assistant.py` reads it from the app folder. The key is read on every question, so after adding or replacing it you only reload the page.

**Verify:** `python3 scripts/check_dashboard.py munich-mobility-planning-v5` (run from the repo root after deploying).

## What gets sent to OpenAI, and what the data can't tell you

- **Sent to OpenAI:** your questions, the context pack (`context.md`, every request), the current view, and the results of the tools the model calls: SQL rows (at most 200 per query), model and what-if results. Web searches run at OpenAI. Database credentials are never sent: SQL runs on your machine through the dashboard's profile.
- **Not stored at OpenAI** as a conversation (`store=False`). The conversation lives in the app's memory for this browser session and is dropped after 4 idle hours.
- **Limits:** scheduled service only, no passengers or delays. A what-if is capacity arithmetic, not a plan: demand shifts, crowding, travel time, cost and feasibility are not modelled. Web answers are only as good as their cited sources; check them.
