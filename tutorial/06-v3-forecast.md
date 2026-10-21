# 6. v3: The forecast to 2045, if nothing is added

About 15 minutes. You need v2 from [05-v2-jobs.md](05-v2-jobs.md).

## What you'll build

v2 plus a **year slider** from 2024 to 2045 and a second chart, **"Change since 2024"**. Residents and jobs follow the city's forecasts, while the timetable stays exactly as it is today. The map compares every year with the **2024** city average, so it turns more orange as the city grows.

**URL:** http://127.0.0.1:5100/apps/munich-mobility-planning-v3

## The idea: growth without new service

Munich is forecast to grow from 1.60 M residents (2024) to 1.83 M (2045), mostly at the edges of the city. If the timetable stays the same, every new resident and job shares the existing places. v3 shows where that hurts most. It is the "do nothing" baseline that v4's projects are measured against.

Three modelling choices:
- **Residents** are interpolated in a straight line from the 2024 count to the official 2045 forecast (`DISTRICT_POPULATION`, Demografiebericht München Teil 2). Only 2045 is published per district.
- **Jobs** start from the 2022 estimate as the 2024 baseline, rise in a straight line to the 2040 forecast, and are held after 2040.
- **The timetable stays as it is today**, and the colours compare with the 2024 city average. That fixed baseline makes years comparable.

## Build it with Claude (the main path)

```text
Use the urban-planning agent. Build the Dash Server app munich-mobility-planning-v3 following the spec in
dashboards/munich-mobility-planning-v3/README.md. Start from your v2 app (munich-mobility-planning-v2) and add
only what the spec adds: the year slider, residents and jobs for the selected year, colours against the fixed
2024 city average, and the "Change since 2024" chart with the Munich overall bar.
Rules: Dash Server only, through the dash-server MCP tools (no artifact, HTML file or inline chart). All SQL
read-only through the exasol MCP. Show me each SQL statement before you run it and before you interpret its
result. Check 2024 and 2045 at w = 1 against the "Reference checks" in the spec, then deploy, run the
healthcheck and give me the URL.
```

## Shortcut: deploy the finished version

```text
Deploy the app in dashboards/munich-mobility-planning-v3 to Dash Server as munich-mobility-planning-v3 (app_create_exasol_dashboard, copy all files, app_deploy_draft, app_run_healthcheck) and give me the URL.
```

## Look at it

- **Move the slider to 2045.** The edges of the city darken. Aubing-Lochhausen-Langwied, where Freiham is being built, falls furthest.
- **Read the chart.** "Munich overall" sits on top, then the 25 districts from best to worst. Orange bars lose, blue bars gain.
- **Hover a district on the map.** You see two ratios: against the 2024 average (the colour) and against the selected year's own average. You also see the 2024 ratio and the change in percentage points and in %.
- **Try 2026.** Two years of growth alone cost the city about 1.7 %.
- **Set w = 0** to see the forecast per resident only.
- **"SQL executed":** the `ranking.sql` entry now shows the year you chose. Unfold the SQL and find `LEAST(2045, 2040)` in the jobs formula.

> **Check** (w = 1)
> - 2024: Munich overall **+0.0 %**, city 34,425 (same as v2)
> - 2045: Munich overall **−13.37 %** (29,822 vs 34,425 places per 1,000 activity)
> - 2045, largest declines: **Aubing-Lochhausen-Langwied −40.5 %**, **Feldmoching-Hasenbergl −26.9 %**, **Trudering-Riem −25.2 %**, then Schwabing-Freimann −22.0 % and Bogenhausen −19.8 %
> - 2045, smallest: Untergiesing-Harlaching +0.5 %, Hadern −2.4 %, Obergiesing-Fasangarten −3.1 %
> - 2026: Munich overall −1.66 %
> - 26 bars in the chart (25 districts plus Munich overall)
>
> ```bash
> python3 scripts/check_dashboard.py munich-mobility-planning-v3
> python3 scripts/verify_numbers.py --case R3
> ```

## What the data can't tell you

- The years in between are a straight line between two points, not a forecast for each year. The jobs forecast ends in 2040.
- Holding today's timetable is a thought experiment. The real timetable changes every year. For example, the 2027 timetable takes effect on 13 Dec 2026 (see `research/plans-facts.md`).
- Fewer places per person doesn't mean fuller trains. There are no passenger or crowding data.

## How it works

The interpolation is in the `dem` CTE of `ranking.sql`:

```sql
           p."pop_2024" + (p."pop_2045_forecast" - p."pop_2024") * ({year!d} - 2024) / 21.0 AS pop_y,
           e."jobs_2022" + (e."jobs_2040_forecast" - e."jobs_2022") * (LEAST({year!d}, 2040) - 2024) / 16.0 AS jobs_y,
```

- 21 years from 2024 to 2045 for residents.
- 16 years from 2024 to 2040 for jobs. `LEAST` holds them after 2040.

The fixed baseline: each district's value in year Y is divided by the **2024** city average. The bars use each district's own change since 2024:

```sql
       ROUND(places_per_1k_act / city_places_per_1k_act_24, 3) AS service_ratio,
```
```sql
       ROUND(100 * (places_per_1k_act / places_per_1k_act_24 - 1), 1) AS pct_change_places,
```

The "Munich overall" bar is computed in `app.py` from the two city values, (city in Y ÷ city in 2024 − 1) × 100.

`ranking.sql` is still byte-identical to v1; only `app.py` changed. The full spec is in [dashboards/munich-mobility-planning-v3/README.md](../dashboards/munich-mobility-planning-v3/README.md).

Next: [07-v4-scenarios.md](07-v4-scenarios.md), what the planned rail and tram projects add.
