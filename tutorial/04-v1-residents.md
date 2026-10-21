# 4. v1: How well is each district served today, per resident?

About 15 minutes. You need chapters [01](01-setup-starter-kit.md) to [03](03-install-agent.md) done: Exasol and Dash Server running, `MUNICH_DATASET` loaded, and the urban-planning agent installed.

## What you'll build

A single map of Munich's 25 districts. Each one is coloured by the scheduled public transport capacity it gets on a typical weekday per 1,000 residents, relative to the Munich average. 1.0× is the average; orange is below, blue above. The densest third of districts is outlined. There are no controls yet. This is the baseline that every later version builds on.

**URL:** http://127.0.0.1:5100/apps/munich-mobility-planning-v1

## The idea: count places, not departures

The obvious measure is "departures per stop". But a bus carries about 90 people and an S-Bahn train about 1,200. So the dashboard counts **places offered**:

> places offered = weekday departures × capacity per trip

The capacity per trip comes from `LINE_CAPACITY` where a line has its own value (U4/U7 580, tram 20 257, MetroBus 100, …). Otherwise it comes from `VEHICLE_CAPACITY` by `line_mode`: S-Bahn 1,200, U-Bahn 900, regional rail 500, tram 205, bus 90. Only stops inside Munich count (`in_munich = 1`). The 24,218 stops outside the city are excluded.

The typical weekday is one Wednesday from the MVV timetable, **pinned to Wednesday 21 Oct 2026** (the feed runs 1 Sep–30 Nov 2026). Every reader gets the same numbers, whenever they run the tutorial.

Then divide by residents and compare with the city:

> ratio = (district places per 1,000 residents) ÷ (Munich places per 1,000 residents)

## Build it with Claude (the main path)

Paste this into Claude Code, started in the repo folder:

```text
Use the urban-planning agent. Build the Dash Server app munich-mobility-planning-v1 following the spec in
dashboards/munich-mobility-planning-v1/README.md. This is the first version, so start a new app. You may reuse
munich_ui.py, dash_server_exasol.py and sql_log.py from that folder for the shared look and the "SQL executed"
foldout, but write the SQL and app.py yourself from the spec.
Rules: build it on Dash Server only, through the dash-server MCP tools (no artifact, HTML file or inline chart).
Run all SQL read-only through the exasol MCP. Show me each SQL statement before you run it and before you
interpret its result. Before deploying, check your numbers against the "Reference checks" in the spec; if they
differ, compare with queries/ranking.sql in that folder. Then deploy, run the healthcheck and give me the URL.
```

Claude shows you the SQL for the reference weekday, the places per district and the ratio, runs it and compares with the checks below. Then it builds the app.

## Shortcut: deploy the finished version

If you want to see the result first, paste:

```text
Deploy the app in dashboards/munich-mobility-planning-v1 to Dash Server as munich-mobility-planning-v1 (app_create_exasol_dashboard, copy all files, app_deploy_draft, app_run_healthcheck) and give me the URL.
```

## Look at it

- **Hover a district.** You see its ratio, residents, residents per km², places and departures per 1,000 residents, residents per station, and a mode note: "mostly bus" or "mostly rail".
- **Find the outliers.** Altstadt-Lehel's label reads 6.18×, but its colour stops at the 2.5× end of the scale. The scale is logarithmic and clamped at 0.4–2.5, so 0.5× and 2× are equally far from grey.
- **Look at the outlines.** The densest third (by residents per km²) is drawn thick. Which of them are orange?
- **Open "SQL executed"** at the bottom. You see `ranking.sql` and `geo.sql`, the parameters (`w_jobs = 0.0, year = 2024, projects = 'none', pessimistic = 0`), rows and time. Unfold an entry to see the full SQL exactly as it was sent to Exasol.

> **Check**
> - City average: **60,325** places per 1,000 residents
> - Lowest: **Sendling-Westpark 0.40×** (24,110 places per 1,000 residents), then Untergiesing-Harlaching 0.573× and Feldmoching-Hasenbergl 0.592×
> - Highest: **Altstadt-Lehel 6.18×**, drawn at the 2.5× colour clamp; then Ludwigsvorstadt-Isarvorstadt 2.858× and Schwanthalerhöhe 2.178×
> - 25 districts drawn, the densest third outlined
>
> ```bash
> python3 scripts/check_dashboard.py munich-mobility-planning-v1
> python3 scripts/verify_numbers.py --case R1
> ```
>
> If you run this on a different date, the query picks another Wednesday in the feed, and your numbers can differ slightly.

## What the data can't tell you

- This is the **scheduled** timetable. There are no passengers, crowding, delays or live traffic in this dataset. Try asking Claude "Which district has the worst traffic right now?": it should tell you that there is no live data, and offer the scheduled-service view instead.
- Capacities are planning values per mode or line, not measured loads.
- A ratio per district says nothing about walking distance. Altstadt-Lehel scores high partly because rail lines run through it.
- The database login is read-only. Ask "Delete the roadworks that have already finished" and Claude refuses, offering a filtered query instead.

## How it works

The whole model is one query, `queries/ranking.sql`. The spec in [dashboards/munich-mobility-planning-v1/README.md](../dashboards/munich-mobility-planning-v1/README.md) walks through it. The heart of it is three CTEs.

The capacity per trip, with the line override first:

```sql
lines AS (
    SELECT r."route_id", r."route_short_name" AS line, COALESCE(lc."capacity_per_trip", v."capacity_per_trip") AS capacity
    FROM MUNICH_DATASET.MVV_ROUTES r
    JOIN MUNICH_DATASET.VEHICLE_CAPACITY v ON v."line_mode" = r."line_mode"
    LEFT JOIN MUNICH_DATASET.LINE_CAPACITY lc ON lc."line" = r."route_short_name" AND lc."line_mode" = r."line_mode"
),
```

Places per district: every stop event on the reference Wednesday adds its trip's capacity to the district of its stop.

```sql
dep AS (
    SELECT s."district_no" AS dno, COUNT(*) AS departures, SUM(wt.capacity) AS places, COUNT(DISTINCT wt.line) AS n_lines
    FROM MUNICH_DATASET.MVV_STOP_TIMES st
    JOIN wt ON wt."trip_id" = st."trip_id"
    JOIN MUNICH_DATASET.MVV_STOPS s ON s."stop_id" = st."stop_id"
    WHERE s."in_munich" = 1
    GROUP BY s."district_no"
),
```

And the ratio. The city average is total places ÷ total residents, not an average of district ratios:

```sql
           1000.0 * SUM(places_today) OVER () / SUM(activity_24) OVER () AS city_places_per_1k_act_24,
```
```sql
       ROUND(places_per_1k_act / city_places_per_1k_act_24, 3) AS service_ratio,
```

The query is already written for later versions: it takes a year, a job weight and projects. v1 calls it with `w_jobs = 0`, `year = 2024` and `projects = 'none'`, so "activity" is just residents.

Next: [05-v2-jobs.md](05-v2-jobs.md), counting jobs too.
