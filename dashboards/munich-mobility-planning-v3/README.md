# munich-mobility-planning-v3: Forecast to 2045, if service stays as today

**Question:** as Munich grows to 2045, how does each district's scheduled public transport supply per resident and job change if nothing is added?

**URL once deployed:** http://127.0.0.1:5100/apps/munich-mobility-planning-v3 · tutorial chapter: [06-v3-forecast.md](../../tutorial/06-v3-forecast.md) · builds on [v2](../munich-mobility-planning-v2/README.md)

v3 adds a **year slider** (2024–2045) and a **"Change since 2024" chart**. Residents and jobs follow the city's forecasts; the timetable stays exactly as it is today. The colours compare every year with the **2024** city average, so the map gets more orange as the city grows.

## What it shows (top to bottom)

1. **Header:** "Munich Mobility Planning", subtitle "v3 – Forecast to 2045, if service stays as today". Meta line, e.g. "Year 2045 · jobs weight w = 1 · today's timetable, no projects · source: MUNICH_DATASET on Exasol, read-only".
2. **Intro card** (verbatim):
   > **How does this change as Munich grows, if nothing is added?**
   > Munich is forecast to grow from 1.60 M residents (2024) to 1.83 M (2045), mostly at the edges of the city. Move the year slider: residents follow the city's official forecast, and jobs follow the 2040 forecast. The timetable stays exactly as it is today. The map compares each district with today's Munich average, and the chart on the right shows how much each district's places per 1,000 activity change since 2024.
3. **Control card** with two parts side by side:
   - "Year": a slider from 2024 to 2045, step 1, default 2024, marks at 2024, 2025, 2030, 2035, 2040 and 2045.
   - "Job weight (w)": the v2 input (0 to 1.5, step 0.25, default 1.0), with the hint "Activity = residents + w × jobs; w = 0 means residents only. 0 to 1.5 in steps of 0.25."
4. **Two cards side by side** (they wrap on narrow screens; flex 3 : 2):
   - **Service map** "How well served is each district? – <year> (if service stays as it is today)". This is the v2 map, but the colour is the district's value in the selected year ÷ the **2024** city average at the same w. The colour bar is titled "× city average (2024)". The hover adds the ratio against the selected year's own city average, the 2024 ratio, the change in percentage points, and the % change in places per 1,000 activity.
   - **"Change since 2024 – <year>"** (690 px high): a horizontal bar per district showing the % change in places per 1,000 activity between 2024 and the selected year. A dark **"Munich overall"** bar sits on top with its value as text, then a spacer row and a separator line, then the 25 districts sorted from highest to lowest. Bars below −0.05 % are orange, bars above +0.05 % blue, the rest grey.
5. **Caveat line** under the map: "Scheduled service as of today, held constant. Residents between 2024 and 2045 interpolated to the official 2045 forecast (Demografiebericht Teil 2). Jobs: 2022 estimate as the 2024 baseline, to the 2040 forecast, held after."
6. **"SQL executed" foldout** at the bottom.

## Files

Same set as v2. Only `app.py`, `dash-app.json` and `queries/sql_smoke.json` differ.

| File | Role |
|---|---|
| `app.py` | Layout, slider, w input, the map (`service_map(rows, geo, year)`) and the bar chart (`change_bars(rows, year, city_pct)`). One `refresh` callback takes `w-store` and `year` as inputs and returns both figures. |
| `queries/ranking.sql` | Unchanged from v1 (byte-identical). Called with `year` from the slider, `w_jobs` from the input, `projects = 'none'`, `pessimistic = 0`. |
| `queries/geo.sql` | As in v1. |
| `queries/sql_smoke.json` | `ranking.sql` with `w_jobs = 1.0`, `year = 2045`, `projects = "none"`, `pessimistic = 0`. |
| `sql_log.py`, `munich_ui.py`, `dash_server_exasol.py`, `requirements.txt` | As in v1. |

## How it computes

**Residents in year Y** are interpolated linearly from the 2024 count to the official 2045 forecast (`DISTRICT_POPULATION.pop_2045_forecast`, Demografiebericht München Teil 2). Only 2045 is published per district, so every year in between is an interpolation. **Jobs in year Y** start from the 2022 estimate as the 2024 baseline, rise linearly to the 2040 forecast and are held after 2040:

```sql
           p."pop_2024" + (p."pop_2045_forecast" - p."pop_2024") * ({year!d} - 2024) / 21.0 AS pop_y,
           e."jobs_2022" + (e."jobs_2040_forecast" - e."jobs_2022") * (LEAST({year!d}, 2040) - 2024) / 16.0 AS jobs_y,
```

**Supply stays at today's timetable** in every year, because `projects = 'none'`. Only the denominator grows.

**The fixed 2024 baseline.** `ranking.sql` computes each district's value in year Y and in 2024, and the city average for both:

```sql
           1000.0 * (COALESCE(dep.places, 0) + COALESCE(sel.add_places, 0)) / (dem.pop_y + {w_jobs!f} * dem.jobs_y) AS places_per_1k_act,
           1000.0 * COALESCE(dep.places, 0) / (dem.pop_24 + {w_jobs!f} * dem.jobs_24) AS places_per_1k_act_24,
```
```sql
           1000.0 * SUM(places) OVER () / SUM(activity) OVER () AS city_places_per_1k_act,
           1000.0 * SUM(places_today) OVER () / SUM(activity_24) OVER () AS city_places_per_1k_act_24,
```

The output columns the map and chart use:

```sql
       ROUND(places_per_1k_act / city_places_per_1k_act_24, 3) AS service_ratio,
       ROUND(places_per_1k_act / city_places_per_1k_act, 3) AS ratio_own_year,
       ROUND(places_per_1k_act_24 / city_places_per_1k_act_24, 3) AS ratio_2024,
       ROUND(100 * (places_per_1k_act - places_per_1k_act_24) / city_places_per_1k_act_24, 1) AS ratio_change_pp,
       ROUND(100 * (places_per_1k_act / places_per_1k_act_24 - 1), 1) AS pct_change_places,
```

- The map colours `service_ratio`: the value in year Y against the **2024** city average.
- The district bars show `pct_change_places`: the district's own change since 2024.
- The "Munich overall" bar is computed in `app.py` from the two rounded city values of the first row:

```python
def pct(a, b):
    return (b / a - 1) * 100 if a else 0.0
```
```python
        city_pct = pct(ui.num(r0.get("city_places_per_1k_act_2024")), ui.num(r0.get("city_places_per_1k_act")))
```

The w input behaves as in v2 (snaps to 0.25, invalid input keeps the last valid value). `ranking.sql` runs on every change; `geo.sql` is cached for an hour.

## Controls

| Control | Range | Effect |
|---|---|---|
| Year | 2024–2045, step 1, default 2024 | Re-runs `ranking.sql` with `year`; both titles, the map, the bars and the meta line follow. |
| Job weight (w) | 0 to 1.5, step 0.25, default 1.0 | As in v2. The 2024 baseline uses the same w. |

## Reference checks

From `research/reference-numbers.md`:

| Check | Expected |
|---|---|
| 2024, w = 1 (R2) | "Munich overall" +0.0 %, city 34,425 per 1,000 activity; map as v2 |
| 2045, w = 1 (R3) | "Munich overall" −13.37 % (29,822 vs 34,425) |
| 2045, w = 1: largest declines | Aubing-Lochhausen-Langwied −40.5 % (Freiham), Feldmoching-Hasenbergl −26.9 %, Trudering-Riem −25.2 %, Schwabing-Freimann −22.0 %, Bogenhausen −19.8 % |
| 2045, w = 1: smallest | Untergiesing-Harlaching +0.5 %, Hadern −2.4 %, Obergiesing-Fasangarten −3.1 % |
| 2026, w = 1 | "Munich overall" −1.66 % (33,853 vs 34,425), population and job growth alone |
| 2045, w = 0 | runs without errors |
| Chart | 26 bars (25 districts + Munich overall); map 25 polygons |
| Healthcheck | healthy |

## Deploy

```text
Deploy the app in dashboards/munich-mobility-planning-v3 to Dash Server as munich-mobility-planning-v3 (app_create_exasol_dashboard, copy all files, app_deploy_draft, app_run_healthcheck) and give me the URL.
```

The steps are as in [v1](../munich-mobility-planning-v1/README.md#deploy).

**Verify:** `python3 scripts/check_dashboard.py munich-mobility-planning-v3` (run from the repo root after deploying).

## What it can't tell you

The years between 2024 and 2045 are a straight line between two points, not a forecast for each year. The jobs forecast stops at 2040. The timetable is held at autumn 2026, while the real one will change: the timetable 2027 alone cuts and adds service (see `research/plans-facts.md`). Scheduled service only: no passengers, crowding or delays.
