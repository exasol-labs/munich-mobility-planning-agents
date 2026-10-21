# 9. A new series: cycling coverage

About 20 minutes for the dashboard, then as long as you like for the exercises.

## What you'll build

`munich-cycling-coverage` asks the planning question for bikes: how much cycle network does each district have, weighted by path quality, compared with the city average? You can look at it **per person** (per 1,000 residents + w × jobs, with the year slider to 2045) or **per km²**. The bicycle counters sit on the map as measured demand. The look, the map, the demand model and the "SQL executed" foldout are the ones you know from v1–v4.

**URL:** http://127.0.0.1:5100/apps/munich-cycling-coverage

Think of it as v1 of a new series. The exercises at the end are v2, v3 and onward, and you build them.

## The idea: weight the network by quality

`CYCLING_INFRASTRUCTURE` has about 21,000 segments with a length and a path type. A painted lane isn't worth as much as a separated cycle track, so each type gets a weight. The weights are adjustable assumptions:

| Path type | Weight |
|---|---|
| Radweg (cycle track), Fahrradstraße (cycle street) | 1.0 |
| Getrennter Rad- und Gehweg (separated cycle and footpath) | 0.8 |
| Radfahr-/Schutzstreifen (painted lane) | 0.6 |
| Gemeinsamer Geh- und Radweg (shared footpath) | 0.5 |
| Gehweg Radverkehr frei (footway, cycling allowed) | 0.3 |

Two-way paths count ×2. Crossings and links (`Übergang`, `Anschlussabschnitt`) and `Dummy` segments are excluded. That leaves **1,049 km** of usable path, or **875 weighted km**.

Then the same comparison as for transit: weighted km per 1,000 activity (or per km²) ÷ the city average. Per person compares each year with the 2024 average, so growth without new paths darkens the map. Per km² doesn't change with the year.

## Build it with Claude (the main path)

```text
Use the urban-planning agent. Build the Dash Server app munich-cycling-coverage following the spec in
dashboards/munich-cycling-coverage/README.md. Reuse the look, the map, the demand CTE and the "SQL executed"
foldout from munich-mobility-planning-v4, and write cycling.sql, pathmix.sql and counters.sql from the spec.
Pass the path weights as numeric placeholders and validate them to 0-1.
Rules: Dash Server only, through the dash-server MCP tools (no artifact, HTML file or inline chart). All SQL
read-only through the exasol MCP. Show me each SQL statement before you run it and before you interpret its
result. Check the numbers against the "Reference checks" in the spec, then deploy, run the healthcheck and give
me the URL.
```

## Shortcut: deploy the finished version

```text
Deploy the app in dashboards/munich-cycling-coverage to Dash Server as munich-cycling-coverage (app_create_exasol_dashboard, copy all files, app_deploy_draft, app_run_healthcheck) and give me the URL.
```

## Look at it

- **Per person, the dense centre is thin.** Altstadt-Lehel and Maxvorstadt have the least network per person.
- **Switch the lens to per km².** The same centre is 1.5–2.2× the city average by area, and the outer districts look thin instead. Both are true. Which one matters depends on the question.
- **Move the year to 2045** in the per-person lens. Aubing-Lochhausen-Langwied falls from 1.20× (2024) to 0.72×, because Freiham grows and no paths are added.
- **Open "Path weights"** and set the two shared-footpath types to 0. Watch which outer districts drop. **Reset weights** brings back the defaults.
- **Hover a green dot.** Each one is a counter, with its bikes per day, the rain penalty (days with more than 1 mm of rain vs dry days) and its data period. The ring is Margaretenstraße, which has no data.
- **The path-quality mix** below the map sorts the districts by the map's ratio and shows what their network is made of.
- **"SQL executed"** shows `cycling.sql` with your year, w and all six weights substituted.

> **Check** (2026, w = 1, default weights)
> - Network: **1,049 km** usable, **875 weighted km**. The meta line shows 1,044.5 km, the part inside the 25 districts; 13 segments (4.9 km) have no district.
> - Lowest per person: **Altstadt-Lehel 0.34×**, **Maxvorstadt 0.45×**. The same districts are **1.5–2.2×** per km².
> - Lowest per km²: **Aubing-Lochhausen-Langwied 0.34×**
> - Counters: **5** with data; **Erhardtstraße 4,765** bikes per day, rain penalty **37 %**
> - City average: 0.311 weighted km per 1,000 activity in 2024; 0.270 in 2045
>
> ```bash
> python3 scripts/check_dashboard.py munich-cycling-coverage
> ```

## What the data can't tell you

- **Supply only:** network length and path type. Nothing on width, surface, continuity, gaps, junction safety or motor traffic.
- **Demand is measured at 5 points,** January to July 2026; Arnulfstraße only to April. One counter can't stand for a whole district.
- **The weights are assumptions,** not an official quality scale.
- **The 2045 view assumes no new paths.** There are no planned cycling projects in the dataset.

## How it works

Usable segments, direction and weight in `queries/cycling.sql`:

```sql
           REPLACE("path_type", ' (Zweirichtungsradweg)', '') AS base_type,
           CASE WHEN INSTR("path_type", '(Zweirichtungsradweg)') > 0 THEN 2 ELSE 1 END AS dir_factor
    FROM MUNICH_DATASET.CYCLING_INFRASTRUCTURE
    WHERE "path_type" NOT IN ('Dummy', 'Übergang', 'Anschlussabschnitt') AND "district_no" IS NOT NULL
```
```sql
           SUM(length_m * dir_factor * weight) / 1000.0 AS weighted_km,
```

The weights arrive as float placeholders (`{w_radweg!f}`, …), never as raw SQL. The demand side is the `dem` CTE from the planning series, unchanged. The two ratios:

```sql
       ROUND(km_per_1k_act / city_km_per_1k_act_24, 3) AS ratio_person,
```
```sql
       ROUND(km_per_km2 / city_km_per_km2, 3) AS ratio_area,
```

The full spec is in [dashboards/munich-cycling-coverage/README.md](../dashboards/munich-cycling-coverage/README.md).

## Exercises: continue the series

Each one is a version you can build with the same pattern: a spec, a Claude prompt, a Check. Write the spec as a README next to your app, the way the `dashboards/` READMEs are written.

1. **A demand layer from MVG Rad trips.** The Munich open data portal download includes the historical MVG Rad bike-share trips. The service ended in September 2025, so use them for history only. Rebuild the dataset with them and load the extra table:
   ```bash
   python3 scripts/prepare_dataset.py ~/Downloads/munich-open-data.zip --out data/munich-dataset --with-mvg-bikes 2024 2025
   ```
   Then load it as in [02-load-data.md](02-load-data.md). This adds `MVG_BIKE_TRIPS` (start and end positions and times). Count trip starts and ends per district and set them against the weighted network.
2. **Cycling projects as scenarios,** like v4. The dataset has none, but `research/plans-facts.md` lists cycling projects citywide and by street (section 3). Curate them into a table like `PT_PROJECT_STATIONS` (segment, district, path type, length, opening year, source) and add them from their opening year.
3. **A change-since-2024 chart,** like v3: the % change in weighted km per 1,000 activity per district, with a Munich overall bar. `cycling.sql` already returns `pct_change_person`.
4. **An assistant,** like v5: reuse `assistant.py`, write a context pack from `research/cycling-coverage.md` and the data model, and give it a `dashboard_scenario` over `cycling.sql`.
5. **Roadworks on cycle paths.** `ROADWORKS` has `affected_areas` (e.g. Radweg) and a centroid. Find active roadworks within 100 m of cycle-path midpoints (the haversine formula is in `skill/munich-mobility-agents/references/data-model.md`), and weight them by the path's quality weight.

Stuck? See [10-troubleshooting.md](10-troubleshooting.md).
