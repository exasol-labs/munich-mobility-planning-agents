# munich-cycling-coverage: How well is each district served for cycling?

**Question:** how much cycle network does each district have, weighted by path quality, per person and per km², against the city average, and how does that change as Munich grows to 2045?

**URL once deployed:** http://127.0.0.1:5100/apps/munich-cycling-coverage · tutorial chapter: [09-cycling-series.md](../../tutorial/09-cycling-series.md)

This is the first dashboard of a new series. It uses the planning series' look, map, demand model and "SQL executed" foldout, but measures supply from `CYCLING_INFRASTRUCTURE`. The six bicycle counters are drawn on the map as measured context: five have data, one is empty.

## What it shows (top to bottom)

1. **Header:** eyebrow "Urban planning", title "Munich Cycling Coverage", subtitle "How well is each district served for cycling? Cycle-network supply per person or per km², 2024 to 2045, with the bicycle counters as measured context."
   - The meta line, e.g. "Year 2026 · lens per person · w = 1.0 · path weights defaults · city 875.2 weighted km of 1,044.5 km raw path length; 2024 average 0.311 km per 1,000 activity at w = 1.0 · source: MUNICH_DATASET on Exasol, read-only".
2. **Intro card** (verbatim):
   > **The map shows how much cycle network each district has, weighted by path quality, against the city average.** *Per person* divides it by residents + w × jobs in the selected year and compares with the 2024 city average, so growth without new paths darkens the map. *Per km²* compares network density by area and does not change with the year. This is supply only (length and type of path from the city's network data), not use or safety. Green dots are the bicycle counters: measured demand, but at 5 points only.
3. **Control card:**
   - "Year": a slider from 2024 to 2045, default 2026. The mark at 2026 reads "now"; the other marks are 2024, 2030, 2035, 2040 and 2045.
   - "Lens": "per person" (default) or "per km²".
   - "Job weight (w)": 0 to 1.5, step 0.25, default 1.0, with the hint "Activity = residents + w × jobs, 0 to 1.5 in steps of 0.25. Per-person lens only." The input is disabled in the per-km² lens.
4. **"Path weights" foldout** (folded). The summary shows "defaults" or "N changed from the default". Inside is one number input per path type (0 to 1, step 0.1) and a **Reset weights** button:

   | Path type (as in the data) | Label | Default weight |
   |---|---|---|
   | Radweg | cycle track | 1.0 |
   | Fahrradstraße | cycle street | 1.0 |
   | Getrennter Rad- und Gehweg | separated cycle and footpath | 0.8 |
   | Radfahr-/Schutzstreifen | painted lane | 0.6 |
   | Gemeinsamer Geh- und Radweg | shared footpath | 0.5 |
   | Gehweg Radverkehr frei | footway, cycling allowed | 0.3 |

5. **Map** "How well is each district served for cycling? – <year> (per person)", or "– per km² (does not change with the year)". Full width, 640 px high.
   - **Colours and labels:** the planning series' choropleth. Log scale centred on 1.0×, clamped 0.4–2.5, colour bar "× city average", the top third by activity per km² outlined, name and ratio labels.
   - **District hover:** both ratios, residents, jobs, activity, weighted and raw km, km per 1,000 activity, m per km², and the share of high-quality paths (cycle track, cycle street, separated).
   - **Counter markers:** green dots sized by average bikes per day (legend: "bicycle counter, sized by bikes/day (measured at 5 points only)"). Hover shows the average, the rain penalty and the data period. Margaretenstraße has no data and is drawn as a ring, "counter without data".
6. **"Path-quality mix"** (720 px high): a stacked horizontal bar per district, in km by class, sorted by the map's ratio, lowest on top. Each label reads e.g. "Altstadt-Lehel 0.34×". The classes are:
   - Cycle track and cycle street (Radweg, Fahrradstraße)
   - Separated cycle and footpath
   - Painted lane (Radfahr-/Schutzstreifen)
   - Shared footpath (Gemeinsamer Geh- und Radweg, Gehweg Radverkehr frei)

   Two-way paths count twice. Connectors are excluded.
7. **Caveat line:** "Supply only: network length and path type, not width, surface, continuity, safety or traffic. Counters measure at 5 points only (Jan–Jul 2026; Arnulfstraße to April; Margaretenstraße no data). Residents interpolated to the 2045 forecast. Jobs: the 2022 estimate as the 2024 baseline, rising to the 2040 forecast, held after. Path weights are assumptions. Two-way paths count twice; connectors (Übergang, Anschlussabschnitt) and Dummy segments are excluded."
8. **"SQL executed" foldout** at the very bottom: `cycling.sql`, `geo.sql`, `counters.sql`, `pathmix.sql`.

## Files

| File | Role |
|---|---|
| `app.py` | Layout, controls, the map (`coverage_map`, with `counter_traces`), the mix chart (`pathmix_chart`). One `refresh` callback (year, lens, w, six weights → map, mix, titles, meta, SQL list), plus `set_w` (as in the planning series), `w_enabled` (disables w in the per-km² lens) and `reset_weights`. The map is built as a fresh figure on every call, so a control change always redraws it. |
| `queries/cycling.sql` | Per district: weighted, raw and two-way km, activity for year Y, both ratios, the high-quality share. Parameters: `year`, `w_jobs` and the six weights. |
| `queries/pathmix.sql` | km by path class per district (two-way × 2). Cached for an hour. |
| `queries/counters.sql` | The six counters: average per day, rain penalty, data period. Cached. |
| `queries/geo.sql` | District polygons and centroids, as in the planning series. Cached. |
| `queries/sql_smoke.json` | `cycling.sql` at `year = 2045`, `w_jobs = 1.0` and the default weights; the other three without parameters. |
| `sql_log.py`, `munich_ui.py`, `dash_server_exasol.py`, `requirements.txt` | As in the planning series. |
| `dash-app.json` | Route `/apps/munich-cycling-coverage`, title "Munich Cycling Coverage", profile `starter-kit`. |

`NOW_YEAR = 2026` is fixed in `app.py`. It is the slider default and the "now" mark.

## How it computes

**1. Usable segments, direction and weight** (`cycling.sql`). The connectors `Übergang` and `Anschlussabschnitt` and the `Dummy` segments are dropped. A two-way path (`… (Zweirichtungsradweg)`) counts twice. Each base path type gets its weight from a numeric placeholder:

```sql
WITH seg AS (
    SELECT "district_no" AS district_no, "length_m" AS length_m,
           REPLACE("path_type", ' (Zweirichtungsradweg)', '') AS base_type,
           CASE WHEN INSTR("path_type", '(Zweirichtungsradweg)') > 0 THEN 2 ELSE 1 END AS dir_factor
    FROM MUNICH_DATASET.CYCLING_INFRASTRUCTURE
    WHERE "path_type" NOT IN ('Dummy', 'Übergang', 'Anschlussabschnitt') AND "district_no" IS NOT NULL
),
segw AS (
    SELECT district_no, length_m, dir_factor, base_type,
           CASE base_type WHEN 'Radweg' THEN {w_radweg!f}
                          WHEN 'Fahrradstraße' THEN {w_fahrradstrasse!f}
                          WHEN 'Getrennter Rad- und Gehweg' THEN {w_getrennt!f}
                          WHEN 'Radfahr-/Schutzstreifen' THEN {w_streifen!f}
                          WHEN 'Gemeinsamer Geh- und Radweg' THEN {w_gemeinsam!f}
                          WHEN 'Gehweg Radverkehr frei' THEN {w_gehweg!f}
                          ELSE 0 END AS weight,
           CASE WHEN base_type IN ('Radweg', 'Fahrradstraße', 'Getrennter Rad- und Gehweg') THEN 1 ELSE 0 END AS high_quality
    FROM seg
),
net AS (
    SELECT district_no,
           SUM(length_m * dir_factor * weight) / 1000.0 AS weighted_km,
           SUM(length_m) / 1000.0 AS raw_km,
           SUM(length_m * dir_factor) / 1000.0 AS dir_km,
           SUM(length_m * dir_factor * high_quality) / 1000.0 AS hq_km,
           COUNT(*) AS segments
    FROM segw GROUP BY district_no
),
```

The weights are placeholders (`!f`), never raw SQL. `app.py` validates each one: a value outside 0–1, or one that isn't a number, falls back to the default (`clean_weight`). 13 segments (4.9 km) have no district and are left out of the district figures.

**2. Demand:** the same `dem` CTE as the planning series. Residents are interpolated from `pop_2024` to `pop_2045_forecast`. Jobs start from `jobs_2022` as the 2024 baseline, rise to `jobs_2040_forecast` and are held after 2040. Activity = residents + w × jobs.

**3. The two ratios:**

```sql
           1000.0 * weighted_km / activity AS km_per_1k_act,
           1000.0 * weighted_km / activity_24 AS km_per_1k_act_24,
           weighted_km / area_km2 AS km_per_km2,
           1000.0 * SUM(weighted_km) OVER () / SUM(activity_24) OVER () AS city_km_per_1k_act_24,
           1000.0 * SUM(weighted_km) OVER () / SUM(activity) OVER () AS city_km_per_1k_act,
           SUM(weighted_km) OVER () / SUM(area_km2) OVER () AS city_km_per_km2,
```
```sql
       ROUND(km_per_1k_act / city_km_per_1k_act_24, 3) AS ratio_person,
       ROUND(km_per_1k_act_24 / city_km_per_1k_act_24, 3) AS ratio_person_2024,
       ROUND(km_per_km2 / city_km_per_km2, 3) AS ratio_area,
```

- **Per person** compares year Y with the **2024** city average at the same w and weights. Growth without new paths lowers the ratio.
- **Per km²** doesn't depend on the year.

**4. Counters** (`counters.sql`): the rain penalty compares days with more than 1 mm of rain with dry days.

```sql
       ROUND(100 * (1 - AVG(CASE WHEN b."rain_mm" > 1 THEN b."total" END)
                        / NULLIF(AVG(CASE WHEN b."rain_mm" <= 1 THEN b."total" END), 0)), 1) AS rain_penalty_pct,
```

**5. Path-quality mix** (`pathmix.sql`):

```sql
           CASE WHEN base_type IN ('Radweg', 'Fahrradstraße') THEN 'Cycle track and cycle street'
                WHEN base_type = 'Getrennter Rad- und Gehweg' THEN 'Separated cycle and footpath'
                WHEN base_type = 'Radfahr-/Schutzstreifen' THEN 'Painted lane'
                ELSE 'Shared footpath' END AS path_class
```

## Controls

| Control | Effect |
|---|---|
| Year (2024–2045, default 2026) | Per-person lens only: activity in year Y. |
| Lens | per person or per km²; the map colours, labels and the mix order follow. |
| Job weight (w) | Per-person lens only; disabled in the per-km² lens. Snaps to 0.25. |
| Path weights (0–1, step 0.1) | Re-weights every path type; Reset weights restores the defaults. |

## Reference checks

From `research/cycling-coverage.md` (2026, w = 1, default weights unless stated):

| Check | Expected |
|---|---|
| Network | 1,049.4 km after connectors and Dummy are removed, 1,044.5 km of it in the 25 districts (the meta line shows 1,044.5); 875.2 weighted km |
| City average | 0.311 weighted km per 1,000 activity in 2024; 0.270 in 2045 if no paths are added; 2,817 weighted m per km² |
| Lowest per person | Altstadt-Lehel 0.34×, Maxvorstadt 0.45×, Ludwigsvorstadt-Isarvorstadt 0.46×, Au-Haidhausen 0.56×, Schwanthalerhöhe 0.60× (all dense; 1.5× to 2.2× per km²) |
| Lowest per km² | Aubing-Lochhausen-Langwied 0.34×, Allach-Untermenzing 0.40×, Feldmoching-Hasenbergl 0.44× |
| Split | Au-Haidhausen 0.56× per person vs 1.60× per km²; Schwabing-West 0.88× vs 2.12× |
| 2045 | largest decline Aubing-Lochhausen-Langwied, 1.20× (2024) to 0.72× (−40.5 %) |
| Counters | Erhardtstr. 4,765 bikes/day, rain penalty 37.4 %; Rudolf-Harbig-Weg 2,718 (36.2 %); Birketweg 1,704 (31.3 %); Arnulfstr. 899 (33.5 %, to 30 Apr); Bad-Kreuther-Str. 686 (32.5 %); Margaretenstr. no data |
| Path mix (city, km, two-way × 2) | separated 583.5 · shared footpath 299.6 · cycle track and street 236.5 · painted lane 46.0 (total 1,165.7) |
| Map | 25 polygons, 5 counter dots and 1 no-data ring on first load; 2045 differs from 2026 |
| Healthcheck | healthy (SQL smoke on all four query files) |

## Deploy

```text
Deploy the app in dashboards/munich-cycling-coverage to Dash Server as munich-cycling-coverage (app_create_exasol_dashboard, copy all files, app_deploy_draft, app_run_healthcheck) and give me the URL.
```

The steps are as in [v1](../munich-mobility-planning-v1/README.md#deploy): create with profile `starter-kit`, copy the files byte for byte, remove the scaffold's sample queries before the first deploy, deploy the draft, run the healthcheck.

**Verify:** `python3 scripts/check_dashboard.py munich-cycling-coverage` (run from the repo root after deploying).

## What it can't tell you

- **Supply only:** network length and path type. Nothing on width, surface, continuity, gaps, junction safety or motor traffic.
- **Measured demand at 5 points only,** January to July 2026, Arnulfstraße only to April. It doesn't extrapolate to uncounted streets or districts.
- **The path weights are assumptions,** not an official quality scale. The ranking moves when you change them.
- **The 2045 view assumes no new cycle paths.** There are no planned cycling projects in the dataset.
