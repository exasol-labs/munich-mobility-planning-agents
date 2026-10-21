# munich-mobility-planning-v2: Today, residents and jobs

**Question:** how well is each district served by scheduled public transport today, counting where people work as well as where they live?

**URL once deployed:** http://127.0.0.1:5100/apps/munich-mobility-planning-v2 · tutorial chapter: [05-v2-jobs.md](../../tutorial/05-v2-jobs.md) · builds on [v1](../munich-mobility-planning-v1/README.md)

v2 is v1 plus one control, the job weight **w**. Demand becomes **activity = residents + w × jobs**. At w = 0 the map is exactly v1. At w = 1 (the default) a job counts as much as a resident.

## What it shows (top to bottom)

1. **Header:** "Munich Mobility Planning", subtitle "v2 – Today, residents and jobs". Under it, a meta line, e.g. "Today (2024 residents) · jobs weight w = 1.0 · city average 34,425 places per 1,000 activity · source: MUNICH_DATASET on Exasol, read-only".
2. **Intro card** (verbatim):
   > **How well is each district served by public transport today, counting where people work as well as where they live?**
   > Residents aren't the whole picture: offices, universities and shops bring people into a district every day. This view counts jobs too: activity = residents + w × jobs. At w = 0 it shows residents only, as in v1. At w = 1 a job counts as much as a resident. The map shows scheduled places offered per 1,000 activity, relative to the Munich average (1.0×). Red is below average, blue above.
3. **Control row** (a card): "Job weight (w)", a number input from 0 to 1.5 in steps of 0.25, default 1.0, with the hint "Activity = residents + w × jobs. w = 0: residents only."
4. **Service map** "How well served is each district? – today (w = 1.0)". This is the v1 map with these changes:
   - The ratio is places per 1,000 activity ÷ the city average **at the same w**.
   - The dense outline is the top third by **activity** per km². The legend reads "dense (top third by activity/km²)".
   - The hover shows the ratio, residents and jobs, activity per km², places and departures per 1,000 activity, residents per station, the mode note and the flag ("flag: yes/no").
5. **Caveat line:** "Scheduled service (MVV timetable, reference Wednesday 21 Oct 2026). Residents end of 2024. Jobs: the city's modelled estimate of workers at place of work (Erwerbstätigenprognose 2025, base year 2022)."
6. **"SQL executed" foldout** at the bottom, as in v1.

## Files

Same set as v1. Only `app.py`, `dash-app.json` and `queries/sql_smoke.json` differ.

| File | Role |
|---|---|
| `app.py` | Layout, the w input, the map. One callback (`refresh`) redraws on every w change; a second one (`set_w`) validates the input. |
| `queries/ranking.sql` | Unchanged from v1 (byte-identical). Called with `year = 2024`, `projects = 'none'`, `pessimistic = 0` and `w_jobs` from the input. |
| `queries/geo.sql` | District polygons and centroids, cached for an hour. |
| `queries/sql_smoke.json` | `ranking.sql` with `w_jobs = 1.0`, `year = 2024`, `projects = "none"`, `pessimistic = 0`; `geo.sql` with no parameters. |
| `sql_log.py`, `munich_ui.py`, `dash_server_exasol.py`, `requirements.txt` | As in v1. |
| `dash-app.json` | Route `/apps/munich-mobility-planning-v2`, profile `starter-kit`. |

## How it computes

**Jobs** come from `DISTRICT_EMPLOYMENT.jobs_2022`: workers at place of work in 2022, from the city's Erwerbstätigenprognose 2025 (empirica 2024, Tabelle 3). This is a modelled estimate, not a count, and no licence is stated. At `year = 2024` the job formula returns `jobs_2022`, which serves as the 2024 baseline:

```sql
dem AS (
    -- residents: linear interpolation 2024 -> 2045 forecast, jobs: 2022 estimate as the 2024 baseline -> 2040 forecast, held after 2040
    SELECT d."district_no" AS district_no, d."district_name" AS district, d."area_km2" AS area_km2,
           p."pop_2024" + (p."pop_2045_forecast" - p."pop_2024") * ({year!d} - 2024) / 21.0 AS pop_y,
           e."jobs_2022" + (e."jobs_2040_forecast" - e."jobs_2022") * (LEAST({year!d}, 2040) - 2024) / 16.0 AS jobs_y,
           p."pop_2024" AS pop_24,
           e."jobs_2022" AS jobs_24
    FROM MUNICH_DATASET.DISTRICTS d
    JOIN MUNICH_DATASET.DISTRICT_POPULATION p ON p."district_no" = d."district_no"
    JOIN MUNICH_DATASET.DISTRICT_EMPLOYMENT e ON e."district_no" = d."district_no"
),
```

**Activity and the per-1,000 measure:**

```sql
           dem.pop_y + {w_jobs!f} * dem.jobs_y AS activity,
```
```sql
           1000.0 * (COALESCE(dep.places, 0) + COALESCE(sel.add_places, 0)) / (dem.pop_y + {w_jobs!f} * dem.jobs_y) AS places_per_1k_act,
```

Supply (places offered = weekday departures × capacity per trip, stops with `in_munich = 1`) is computed exactly as in v1. The map colours `service_ratio` = `places_per_1k_act / city_places_per_1k_act_24`, where the city average uses the same w.

**The flag** (shown in the hover): a district is flagged when it is in the top third by activity per km² and the bottom third by places per 1,000 activity.

```sql
       CASE WHEN act_t = 1 AND places_t = 3 THEN 1 ELSE 0 END AS flagged,
```

**The w input,** in `app.py`. The number input is the single source of truth, and a `dcc.Store` (`w-store`, default 1.0) keeps the last valid value. A valid value snaps to 0.25. An empty, invalid or out-of-range entry falls back to the last valid value:

```python
        last = 1.0 if last_w is None else float(last_w)
        try:
            v = float(input_w)
        except (TypeError, ValueError):
            return no_update, last
        if not (0 <= v <= 1.5):
            return no_update, last
        v = round(v * 4) / 4
        return (no_update if v == last else v), v
```

`set_w` uses `prevent_initial_call=True`. On first load, `refresh` draws from the store's default (w = 1.0). `ranking.sql` is not cached, because w changes; `geo.sql` is cached for an hour.

## Controls

| Control | Range | Effect |
|---|---|---|
| Job weight (w) | 0 to 1.5, step 0.25, default 1.0 | Re-runs `ranking.sql` with the new `w_jobs`. The map title, colours, labels, hover and meta line follow. |

## Reference checks

From `research/reference-numbers.md`:

| Check | Expected |
|---|---|
| w = 1 (R2): city average | 34,425 places per 1,000 activity |
| w = 1: lowest | Sendling-Westpark 0.496×, then Allach-Untermenzing 0.589×, Milbertshofen-Am Hart 0.688× |
| w = 1: highest | Ludwigsvorstadt-Isarvorstadt 1.882×, Altstadt-Lehel 1.814×, Au-Haidhausen 1.736× |
| w = 1: flagged | none |
| w = 0 (R1) | identical to v1: city 60,325 per 1,000 residents, Sendling-Westpark 0.40×, Altstadt-Lehel 6.18× |
| Input | 0.6 snaps to 0.5; "abc" keeps the last value |
| Healthcheck | healthy |

## Deploy

```text
Deploy the app in dashboards/munich-mobility-planning-v2 to Dash Server as munich-mobility-planning-v2 (app_create_exasol_dashboard, copy all files, app_deploy_draft, app_run_healthcheck) and give me the URL.
```

The steps are the same as for [v1](../munich-mobility-planning-v1/README.md#deploy): create with profile `starter-kit`, copy the files byte for byte, remove the scaffold's sample queries, deploy the draft, run the healthcheck.

**Verify:** `python3 scripts/check_dashboard.py munich-mobility-planning-v2` (run from the repo root after deploying).

## What it can't tell you

Jobs are a modelled estimate of workers at place of work, not a count, and w is a judgement, not a measurement. Nothing here says how many residents or workers actually use public transport. The service data is still the scheduled timetable: no passengers, crowding or delays.
