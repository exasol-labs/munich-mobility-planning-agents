# Munich Cycling Coverage: how well is each district served for cycling?

Dashboard: http://127.0.0.1:5100/apps/munich-cycling-coverage (Dash Server, revision 3, healthcheck healthy)
Data: `MUNICH_DATASET` on Exasol, read-only user `mcp_readonly`. Every number below comes from the queries shown, run on 2026-10-21.

## Answer

Munich has 1,049.4 km of cycle path once connectors and Dummy segments are taken out (1,044.5 km of it inside the 25 districts). That is 875.2 km at the default quality weights, or 0.311 weighted km per 1,000 residents + jobs in 2024. **Per person, the dense inner districts are the least served:** Altstadt-Lehel (0.34× the city average), Maxvorstadt (0.45×), Ludwigsvorstadt-Isarvorstadt (0.46×), Au-Haidhausen (0.56×) and Schwanthalerhöhe (0.60×). All five are in the densest third, and their networks are among the densest by area (1.5× to 2.2× per km²). Au-Haidhausen (0.56× per person, 1.60× per km²) and Schwabing-West (0.88× vs 2.12×) show the same split as the earlier finding: lots of path per km², not much per person. **Per km², the outer districts are thin:** Aubing-Lochhausen-Langwied (0.34×), Allach-Untermenzing (0.40×) and Feldmoching-Hasenbergl (0.44×). If no paths are added, growth to 2045 takes the city average down to 0.270 km per 1,000 activity. The largest decline is Aubing-Lochhausen-Langwied, from 1.20× to 0.72× (−40.5 %), because of the Freiham build-out. This measures supply only, not use, quality on the ground or safety.

## Model

- Source `CYCLING_INFRASTRUCTURE`, without `Übergang`, `Anschlussabschnitt` (connectors) and `Dummy`. 13 segments (4.9 km) have no district and are left out of the district figures.
- Direction factor 2 for `… (Zweirichtungsradweg)`, else 1.
- Default weights (assumptions, adjustable on the dashboard, passed as `!f` placeholders, validated to 0–1): Radweg 1.0 · Fahrradstraße 1.0 · Getrennter Rad- und Gehweg 0.8 · Radfahr-/Schutzstreifen 0.6 · Gemeinsamer Geh- und Radweg 0.5 · Gehweg Radverkehr frei 0.3.
- Activity(Y) = residents(Y) + w × jobs(Y). Residents are interpolated from `pop_2024` to `pop_2045_forecast`. Jobs use `jobs_2022` as the 2024 baseline, rise linearly to `jobs_2040_forecast` and are held after 2040. This is the same `dem` CTE as `munich-mobility-planning-v4`.
- Per person ratio = (weighted km per 1,000 activity in Y) ÷ (city weighted km per 1,000 activity in **2024**, same w and weights).
- Per km² ratio = (weighted km ÷ `area_km2`) ÷ (city total ÷ city area). It does not depend on the year.

## Key SQL

Raw total:
```sql
SELECT ROUND(SUM("length_m")/1000,2) AS raw_km_all,
       ROUND(SUM(CASE WHEN "district_no" IS NOT NULL THEN "length_m" END)/1000,2) AS raw_km_in_districts,
       SUM(CASE WHEN "district_no" IS NULL THEN 1 ELSE 0 END) AS seg_no_district
FROM MUNICH_DATASET.CYCLING_INFRASTRUCTURE
WHERE "path_type" NOT IN ('Dummy','Übergang','Anschlussabschnitt');
-- 1049.36 | 1044.48 | 13
```

Core of `queries/cycling.sql` (full file in the app workspace; the dashboard's "SQL executed" foldout shows it as sent):
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
           CASE base_type WHEN 'Radweg' THEN {w_radweg!f} WHEN 'Fahrradstraße' THEN {w_fahrradstrasse!f}
                          WHEN 'Getrennter Rad- und Gehweg' THEN {w_getrennt!f} WHEN 'Radfahr-/Schutzstreifen' THEN {w_streifen!f}
                          WHEN 'Gemeinsamer Geh- und Radweg' THEN {w_gemeinsam!f} WHEN 'Gehweg Radverkehr frei' THEN {w_gehweg!f}
                          ELSE 0 END AS weight
    FROM seg
),
net AS (SELECT district_no, SUM(length_m * dir_factor * weight) / 1000.0 AS weighted_km, ... FROM segw GROUP BY district_no),
dem AS (
    SELECT d."district_no", d."district_name", d."area_km2",
           p."pop_2024" + (p."pop_2045_forecast" - p."pop_2024") * ({year!d} - 2024) / 21.0 AS pop_y,
           e."jobs_2022" + (e."jobs_2040_forecast" - e."jobs_2022") * (LEAST({year!d}, 2040) - 2024) / 16.0 AS jobs_y,
           p."pop_2024" AS pop_24, e."jobs_2022" AS jobs_24
    FROM MUNICH_DATASET.DISTRICTS d
    JOIN MUNICH_DATASET.DISTRICT_POPULATION p ON p."district_no" = d."district_no"
    JOIN MUNICH_DATASET.DISTRICT_EMPLOYMENT e ON e."district_no" = d."district_no"
)
-- ratio_person = (1000 * weighted_km / activity_Y) / (1000 * SUM(weighted_km) OVER () / SUM(activity_2024) OVER ())
-- ratio_area   = (weighted_km / area_km2) / (SUM(weighted_km) OVER () / SUM(area_km2) OVER ())
```

Counters (`queries/counters.sql`): average daily `total`; rain penalty = 1 − avg(days with `rain_mm > 1`) ÷ avg(dry days, `rain_mm <= 1`); first and last day.

## Lowest 10 per person (2026, w = 1, default weights)

| District | ratio per person | weighted km per 1,000 activity | weighted km | activity | ratio per km² | dense |
|---|---|---|---|---|---|---|
| Altstadt-Lehel | 0.34 | 0.107 | 13.5 | 126,487 | 1.53 | yes |
| Maxvorstadt | 0.45 | 0.141 | 24.2 | 171,298 | 2.00 | yes |
| Ludwigsvorstadt-Isarvorstadt | 0.46 | 0.144 | 19.4 | 134,856 | 1.57 | yes |
| Au-Haidhausen | 0.56 | 0.174 | 19.0 | 109,028 | 1.60 | yes |
| Schwanthalerhöhe | 0.60 | 0.186 | 12.6 | 67,969 | 2.17 | yes |
| Allach-Untermenzing | 0.83 | 0.257 | 17.4 | 67,776 | 0.40 | |
| Laim | 0.86 | 0.267 | 23.1 | 86,443 | 1.55 | yes |
| Schwabing-West | 0.88 | 0.274 | 26.1 | 95,428 | 2.12 | yes |
| Schwabing-Freimann | 0.94 | 0.292 | 55.2 | 189,428 | 0.76 | |
| Milbertshofen-Am Hart | 0.94 | 0.293 | 47.2 | 161,327 | 1.25 | |

## Lowest 10 per km² (does not depend on the year)

| District | ratio per km² | weighted m per km² | weighted km | area km² | ratio per person (2026) | high-quality share % |
|---|---|---|---|---|---|---|
| Aubing-Lochhausen-Langwied | 0.34 | 955 | 32.5 | 34.06 | 1.12 | 37 |
| Allach-Untermenzing | 0.40 | 1,129 | 17.4 | 15.45 | 0.83 | 40 |
| Feldmoching-Hasenbergl | 0.44 | 1,235 | 35.7 | 28.94 | 1.34 | 24 |
| Trudering-Riem | 0.65 | 1,836 | 41.2 | 22.45 | 1.11 | 62 |
| Schwabing-Freimann | 0.76 | 2,152 | 55.2 | 25.68 | 0.94 | 82 |
| Bogenhausen | 0.88 | 2,487 | 59.0 | 23.71 | 1.17 | 69 |
| Pasing-Obermenzing | 0.96 | 2,713 | 44.8 | 16.50 | 1.33 | 73 |
| Hadern | 1.05 | 2,955 | 27.3 | 9.22 | 1.14 | 76 |
| Moosach | 1.19 | 3,352 | 37.2 | 11.09 | 1.11 | 68 |
| Ramersdorf-Perlach | 1.24 | 3,504 | 69.7 | 19.90 | 1.14 | 78 |

City average per km²: 2,817 weighted m per km². High-quality share = cycle track, cycle street and separated cycle and footpath, as a share of km with two-way paths counted twice.

## 2045 decliners (per person, w = 1, no new paths assumed)

| District | 2024 ratio | 2045 ratio | change in km per 1,000 activity |
|---|---|---|---|
| Aubing-Lochhausen-Langwied | 1.20 | 0.72 | −40.5 % |
| Feldmoching-Hasenbergl | 1.39 | 1.02 | −26.9 % |
| Trudering-Riem | 1.14 | 0.86 | −25.2 % |
| Schwabing-Freimann | 0.97 | 0.75 | −22.0 % |
| Bogenhausen | 1.20 | 0.96 | −19.8 % |
| Allach-Untermenzing | 0.84 | 0.70 | −17.2 % |
| Berg am Laim | 1.03 | 0.85 | −17.1 % |
| Moosach | 1.13 | 0.95 | −15.8 % |

City average in 2045: 0.270 km per 1,000 activity, against 0.311 in 2024.

## Path-quality mix (city, km with two-way paths counted twice)

Separated cycle and footpath 583.5 · Shared footpath 299.6 · Cycle track and cycle street 236.5 · Painted lane 46.0 (total 1,165.7).

## Counters (measured demand, 5 points with data)

| Counter | district | avg bikes/day | rain penalty | data period |
|---|---|---|---|---|
| Erhardtstr. (Deutsches Museum) | Ludwigsvorstadt-Isarvorstadt | 4,765 | 37.4 % | 2026-01-01 to 2026-07-31 (213 days) |
| Rudolf-Harbig-Weg (Olympiapark) | Milbertshofen-Am Hart | 2,718 | 36.2 % | 2026-01-01 to 2026-07-31 |
| Birketweg (Hirschgarten) | Neuhausen-Nymphenburg | 1,704 | 31.3 % | 2026-01-01 to 2026-07-31 |
| Arnulfstr. 9–11 | Ludwigsvorstadt-Isarvorstadt | 899 | 33.5 % | 2026-01-01 to 2026-04-30 (120 days) |
| Bad-Kreuther-Str. | Berg am Laim | 686 | 32.5 % | 2026-01-01 to 2026-07-31 |
| Margaretenstr. (Harras) | Sendling-Westpark | no data | – | – |

The busiest counter (Erhardtstraße) sits in one of the districts with the least network per person (Ludwigsvorstadt-Isarvorstadt, 0.46×). Demand there is real, but one counter cannot stand for a whole district.

## What the data cannot answer

- **Supply only:** network length and path type. Nothing on width, surface, continuity, gaps between segments, junction safety, parking conflicts or motor traffic.
- **Demand is measured at 5 points only,** January to July 2026, with Arnulfstraße only to April and Margaretenstraße empty. None of this extrapolates to uncounted streets or districts.
- **Path weights are assumptions,** not an official quality scale. The ranking moves when they change: setting shared footpaths to 0 takes Aubing in 2045 from 0.71× to 0.48×.
- **Population after 2024 is interpolated** to the official 2045 forecast. Jobs are a modelled city estimate (2022 as the 2024 baseline, 2040 forecast, held after), not a count.
- **The 2045 view assumes no new cycle paths.** No planned cycling projects are in the dataset.
- Per-district figures leave out the 13 segments (4.9 km) that have no district.

## Checks run

- SQL: raw total 1,049.36 km (1,044.48 km in districts); weighted 875.2 km; 2024 city average 0.3114 km per 1,000 activity at w = 1. Au-Haidhausen is 0.56× per person and 1.60× per km², Schwabing-West 0.88× and 2.13×. The largest 2045 decline is Aubing-Lochhausen-Langwied. Erhardtstraße averages 4,765 per day, Bad-Kreuther-Straße 686.
- Headless Chrome (own context, software WebGL): 15/15. 25 polygons, 5 counters and 1 no-data marker on first load. Changing the lens, the year, a path weight, the reset button and w each change the **drawn** map data, and the SQL foldout text follows (year, w and weights substituted). 2045 differs from 2026. Nothing scrolls by itself, including opening the foldout. No console errors.
- Dash Server healthcheck: healthy (layout, dependencies, assets, data layer and SQL smoke on all four queries).
