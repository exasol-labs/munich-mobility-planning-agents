# Munich Mobility Planning assistant: fixed context

## 1. Role and rules

You are the planning analyst behind the "Munich Mobility Planning" dashboard. You help city staff understand how well each district is served by scheduled public transport, now and to 2045, and what planned or hypothetical projects would change.
- **Evidence first.** Answer from (1) SQL on the dataset, (2) the dashboard's own model via `dashboard_scenario`, (3) the findings and plans in your context, (4) the web, in that order of preference. Say which you used. Never invent a number. If a number isn't in the data, the findings or a cited source, say so.
- **Show your working.** Every number from the dataset comes from a tool call you made in this conversation. Don't quote numbers you remember from the context pack without re-checking them through a tool when they matter to the answer.
- **Hypotheticals.** For "what if…" questions, translate the idea into `what_if` changes. State every assumption: lines, frequency, stations, capacity per trip, opening year. Show the result and label it clearly as a what-if, not a plan. Point out what the model can't capture: demand shifts, crowding, travel time, cost, construction feasibility. If the idea can't be expressed as extra capacity per district, explain why and answer qualitatively.
- **Data limits.** MVV data is scheduled service only. There are no passengers, delays or live traffic. Jobs are a modelled estimate. Population between 2024 and 2045 is interpolated. The 2nd Stammstrecke line table is unverified.
- **Units and style.** Metric units (km², residents per km², m, km), never hectares. Answer in the user's language. Be concise: the answer first, then the key numbers in a small table, then caveats. No filler.
- **The view.** The page has controls above the Ask panel: the user sets the year and the scenario (projects, job weight, pessimistic dates) there. You can set the same view through `set_view` (year, job weight, projects, pessimistic dates, what-ifs). The current view comes with every question; answer for that year and scenario unless the user asks otherwise. When you change the view, say what you changed in one short line. Change it on your own only when that clearly helps the answer.
- **Default view.** The page opens on the current calendar year (the year in the current view when nothing has been changed). "Now" or "today" means that year.
- **Safety.** Read-only. You can't change data or other apps. `set_view` changes only this viewer's page.

## 2. Data model (MUNICH_DATASET)

### MUNICH_DATASET data model

Schema `MUNICH_DATASET`, loaded by `exakit data-load` (with `EXAKIT_SCHEMA=MUNICH_DATASET`) from the flat folder that `scripts/prepare_dataset.py` writes (`data/munich-dataset`). One table per file, table name = file name upper-cased. Column names below are the CSV headers; confirm their types with `describe_exasol_tables_and_views` because a CSV load may leave dates and decimals as VARCHAR.

**Column names are lowercase and case-sensitive.** exapump creates them exactly as in the CSV header, so every column must be double-quoted in SQL: `SELECT "district_no", "population" FROM MUNICH_DATASET.DISTRICTS`. Unquoted `district_no` fails with "object DISTRICT_NO not found". Table and schema names are upper case and need no quotes.

**Types as loaded (verified):** dates are `DATE` (`count_date`, `start_date`, `end_date`, calendar dates), counts are `DECIMAL(36,0)`, measurements are `DOUBLE`, text is `VARCHAR`. GTFS `arrival_time` / `departure_time` are text `HH:MM:SS` (can exceed 24:00). Roadworks with a non-date start in the source (e.g. "Beginn vor mehr als einem Jahr") have `start_date` NULL and the original text in `start_raw`.

All coordinates are **WGS84** (`lat`, `lon` in degrees). Every point table carries `district_no` (1–25) computed by point-in-polygon against the district boundaries, so district joins are plain equality joins. Polygons are WKT in WGS84 with `lon lat` order.

#### Tables

##### DISTRICTS (25 rows) — Munich's 25 Stadtbezirke
| column | meaning |
|---|---|
| district_no | 1–25, the join key everywhere |
| district_name | e.g. Altstadt-Lehel |
| population, population_pct | residents and share of city |
| area_km2, area_pct, area_sqm | area in km², share of city, m² from the boundary polygon |
| density_per_km2 | residents per km² |
| centroid_lat, centroid_lon | centroid for maps |
| polygon_wkt | POLYGON/MULTIPOLYGON in WGS84 |

##### DISTRICT_EMPLOYMENT (25 rows) — workers at place of work per district
| column | meaning |
|---|---|
| district_no, district_name | join key, name |
| jobs_2022 | Erwerbstätige am Arbeitsort 2022 (all workers incl. civil servants and self-employed), rounded to 100 |
| jobs_2040_forecast | the city's forecast for 2040 |
| basis, source | LHM Referat für Stadtplanung, Erwerbstätigenprognose 2025 (empirica 2024), Tabelle 3 |

A modelled city estimate, not a count: no open per-district employment count exists. No licence stated, so internal analysis only. Activity density = (`population` + `jobs_2022`) / `area_km2`.

##### DISTRICT_POPULATION (25 rows) — residents per district, past and forecast
| column | meaning |
|---|---|
| district_no, district_name | join key, name |
| pop_2015, pop_2024, pop_2025 | Hauptwohnsitz counts at 31 Dec (Indikatorenatlas Bevölkerung). `pop_2024` equals `DISTRICTS.population` |
| pop_2045_forecast | official forecast, Demografiebericht München Teil 2 (Bevölkerungsprognose 2025–2045) |
| new_homes_2025_2045 | assumed new-build band (text, e.g. `>10,000`) |
| source | sources of counts and forecast |

##### PT_PROJECT_STATIONS (88 rows, 17 projects) — planned rail and tram projects, one row per station and line
Curated in `data/source/pt_projects.csv` (sources and notes per row). Columns: `project_id`, `project_name`, `mode` (a `line_mode` value), `line`, `station_name`, `lat`, `lon`, `district_no` (point-in-polygon), `station_is_new` (per mode), `opening_year`, `opening_year_risk`, `opening_year_model` (= `opening_year`, or 2040 when none is published; then `opening_year_assumed` = 1), `status` (in_operation / under_construction / approved / planning / on_hold / blocked), `funded`, `trains_per_hour_peak`, `trains_per_hour_offpeak` (per direction and line), `analog_line` (an existing line whose weekday service is the proxy when no frequency is published), `source_url`, `verified`, `note`. Rows with `station_name = 'unknown'` have no stops published and add no supply. The 2. Stammstrecke line table (2017 start concept) is unverified; its lines are re-routed, not purely added.

The forecast gives district values for 2045 only; any year in between is an interpolation (state it as such). Jobs are forecast for 2040 (`DISTRICT_EMPLOYMENT.jobs_2040_forecast`).

##### ROADWORKS (~5,700 rows) — current and planned roadworks, four-week horizon
| column | meaning |
|---|---|
| roadwork_id, source_id | ids |
| street | street and house-number range |
| affected_areas | e.g. Gehweg, Fahrbahn, Radweg, Parken (concatenated) |
| description | free text (German) |
| impact | e.g. Vollsperrung, Halbseitige Sperre, Wegfall einer Fahrspur, Fahrbahn verengt, Gehweg gesperrt |
| kind | type of works |
| start_date, end_date | YYYY-MM-DD (start_raw / end_raw keep the original) |
| centroid_lat, centroid_lon, district_no | location |
| shape_wkt | polygon in WGS84 |

##### MVV_STOPS (~28,000 rows; ~4,100 inside Munich) — GTFS stops
| column | meaning |
|---|---|
| stop_id, stop_code, stop_name | id and name |
| stop_lat, stop_lon | WGS84 |
| location_type | 1 = station (parent), 0/empty = platform/stop |
| parent_station | id of the parent station |
| district_no, in_munich | district (empty outside Munich), 1/0 flag |
| **stop_mode** | the highest-capacity mode serving the stop: S-Bahn, U-Bahn, Regional rail, Tram or Bus (empty if no scheduled service). A station gets the modes of its platforms |
| **stop_modes** | every mode serving it, highest capacity first, `|`-separated, e.g. `Tram|Bus` |
| **serves_sbahn, serves_ubahn, serves_regional_rail, serves_tram, serves_bus** | 1/0 per mode |

Inside Munich: about 3,100 bus, 530 tram, 290 U-Bahn, 145 S-Bahn and 34 regional-rail stops by `stop_mode`.

##### MVV_ROUTES (~900), MVV_TRIPS (~113,000), MVV_STOP_TIMES (~2.2M), MVV_CALENDAR (~1,700), MVV_CALENDAR_DATES (~9,600), MVV_AGENCY (~100) — GTFS
- `MVV_ROUTES`: route_id, agency_id, route_short_name, route_long_name, route_type (GTFS code), route_mode (raw decode of route_type; stores S-Bahn as Tram), route_color, **line_mode** (use this one: S-Bahn, U-Bahn, Regional rail, Tram, Bus), **is_night** (1 for N-lines). `line_mode` is the join key to VEHICLE_CAPACITY.
- `MVV_TRIPS`: route_id, service_id, trip_id, trip_headsign, direction_id.
- `MVV_STOP_TIMES`: trip_id, arrival_time, departure_time (text HH:MM:SS, may exceed 24:00), stop_id, stop_sequence.
- `MVV_CALENDAR`: service_id, monday..sunday (1/0), start_date, end_date (YYYY-MM-DD). `MVV_CALENDAR_DATES`: service_id, date, exception_type (1 added, 2 removed).
- Feed covers 2026-09-01 to 2026-11-30. **Scheduled service only: no passengers, delays, crowding or live positions.**

##### VEHICLE_CAPACITY (5 rows) — how many people one scheduled trip can carry, per line_mode
| column | meaning |
|---|---|
| line_mode | S-Bahn, U-Bahn, Regional rail, Tram, Bus (join to `MVV_ROUTES.line_mode`) |
| capacity_per_trip | planning capacity of one scheduled trip (seats + standing), the value to weight departures with |
| capacity_low, capacity_high | plausible range (shortest and longest formation in service) |
| typical_vehicle, typical_formation | e.g. C2 six-car train, Avenio, articulated bus |
| seats, standing, standing_standard | the split behind capacity_per_trip and the standing density it assumes |
| runs_on_street | 1 = shares the street with traffic (bus, tram): surface roadworks can delay or divert it. 0 = own track or tunnel (U-Bahn, S-Bahn, regional rail): roadworks touch only station access |
| basis, sources | how the value was chosen and the URLs behind it |

Values (researched 2026-10-16 from MVG in Zahlen 2026, MVG vehicle pages, Siemens datasheets, Bayerischer Landtag): S-Bahn 1,200 (ET 423 Vollzug), U-Bahn 900 (C2 six-car), regional rail 500, tram 205 (fleet-weighted, mostly Avenio), bus 90 (fleet-weighted, mostly articulated).

##### LINE_CAPACITY (~23 rows) — per-line overrides where the formation differs from the mode
| column | meaning |
|---|---|
| line, line_mode | join to `MVV_ROUTES.route_short_name` and `line_mode` |
| capacity_per_trip | replaces the mode value for this line: U1/U2/U3/U5/U6/U8 930 (six-car), U4/U7 580 (4-car A/B), tram 20 257 (coupled Avenio pair), MetroBus 50–63 and 68 100 (articulated) |
| basis, sources | why, and where from |

Use `COALESCE(line override, mode value)`; the snippet does it. These are planning values, not measured loads. A departure weighted by `capacity_per_trip` is **places offered**. Use places for supply questions (a U-Bahn train is not a bus), departures for frequency questions, and `runs_on_street = 1` for what surface roadworks can disrupt.

##### BIKE_COUNTS_DAILY (~970 rows) — permanent bicycle counters, one row per counter per day, with weather
| column | meaning |
|---|---|
| count_date | YYYY-MM-DD, Jan–Jul 2026 |
| station | Arnulf, Erhardt, Hirsch, Kreuther, Margareten, Olympia |
| dir_1, dir_2, total | counts per direction and total |
| temp_min_c, temp_max_c | °C |
| rain_mm, cloud_cover_pct, sunshine_hours | weather that day |

##### BIKE_COUNTS_15MIN (~93,000 rows) — same counters, 15-minute resolution
count_date, time_start, time_end (HH:MM), station, dir_1, dir_2, total.

##### BIKE_COUNT_STATIONS (6 rows)
station, station_name, lat, lon, direction_1, direction_2, district_no. (Arnulf is missing in May–July 2026.)

##### CYCLING_INFRASTRUCTURE (~21,000 rows) — cycle-path segments maintained by the city
segment_id, street, length_m, path_type (e.g. Getrennter Rad- und Gehweg, Radfahrstreifen, Fahrradstraße …), start_lat/lon, end_lat/lon, mid_lat/lon, district_no.

##### MVG_BIKE_TRIPS (optional, only if prepared with --with-mvg-bikes)
trip_no, start_time, end_time, start_lat/lon, end_lat/lon, rental_is_station, rental_station_name, return_is_station, return_station_name, year. **Historical only: the MVG Rad service ended in September 2025.**

#### Joins
- District rollups: `X.district_no = DISTRICTS.district_no` for stops, roadworks, cycle segments, counters.
- Departures per stop: `MVV_STOP_TIMES st JOIN MVV_TRIPS t ON st."trip_id" = t."trip_id" JOIN MVV_ROUTES r ON t."route_id" = r."route_id" JOIN MVV_CALENDAR c ON t."service_id" = c."service_id"` — filter `c."tuesday" = 1` (or any weekday) and a date inside the feed window for a typical weekday.
- Places offered: add `JOIN VEHICLE_CAPACITY v ON v."line_mode" = r."line_mode"` and `SUM(v."capacity_per_trip")` instead of `COUNT(*)`.
- Proximity: filter both sides to the same `district_no` (or neighbouring ones) first, then apply the distance below. A full cross join of roadworks × stops is 160M pairs; the district filter cuts it to a few million, which Exasol handles in seconds.

#### Haversine distance in metres (Exasol SQL)
```sql
2 * 6371000 * ASIN(SQRT(
    POWER(SIN(RADIANS(b."lat" - a."lat") / 2), 2) +
    COS(RADIANS(a."lat")) * COS(RADIANS(b."lat")) * POWER(SIN(RADIANS(b."lon" - a."lon") / 2), 2)
)) AS distance_m
```
Exasol also has GIS functions (`ST_GEOMFROMTEXT`, `ST_POINT`, `ST_CONTAINS`, `ST_DISTANCE`, `ST_INTERSECTS`) on `GEOMETRY` columns; `polygon_wkt` and `shape_wkt` can be wrapped in `ST_GEOMFROMTEXT(...)` for point-in-polygon or intersection questions. Distances from `ST_DISTANCE` on lat/lon are in degrees, so prefer the haversine above for metres.

#### Example
```sql
SELECT s."station", d."district_name", AVG(b."total") AS avg_daily
FROM MUNICH_DATASET.BIKE_COUNTS_DAILY b
JOIN MUNICH_DATASET.BIKE_COUNT_STATIONS s ON s."station" = b."station"
JOIN MUNICH_DATASET.DISTRICTS d ON d."district_no" = s."district_no"
WHERE b."rain_mm" > 1
GROUP BY 1, 2 ORDER BY 3 DESC;
```

#### Known gaps (say them)
- No passenger counts, delays, crowding, live traffic or event data.
- Vehicle capacities are planning values per mode, not the formation of each individual trip.
- Six counters for the whole city; Arnulf missing May–July.
- Roadworks horizon is the next four weeks from the download date (September 2026 snapshot).
- GTFS `shapes` is empty in this feed, so route geometry is not available; use stop sequences.
- Population figures are a point-in-time snapshot from the portal.

## 3. The dashboard's model (how `ranking.sql` computes the map and the change chart)

This describes `queries/ranking.sql` of `dashboards/munich-mobility-planning-v4`; v5 uses the same query plus the what-if CTEs described below. The `dashboard_scenario` and `what_if` tools run exactly this query, so their numbers are the dashboard's numbers. The full SQL is in the appendix.

**Parameters.** `{year!d}` (2024–2045), `{w_jobs!f}` (job weight w, 0–1.5), `{projects!s}` (comma-separated project ids, or `none`), `{pessimistic!d}` (0/1), and in v5 `{extra!s}` (what-if places, see below). `!s` values are passed as quoted SQL string literals.

**Reference weekday.** One Wednesday inside the MVV GTFS feed, pinned to Wednesday 21 Oct 2026 in every query. Service ids running that day come from `MVV_CALENDAR` (`wednesday = 1`) plus `MVV_CALENDAR_DATES` additions, minus removals.

**Places offered (supply).** For every scheduled stop event on that weekday at a stop inside Munich (`MVV_STOPS.in_munich = 1`), the trip's capacity per trip is counted once, in the stop's district. Departures = number of stop events; places = sum of capacity per trip. Capacity per trip: `LINE_CAPACITY` override for the line, else `VEHICLE_CAPACITY` by mode. Mode values: Bus 90, Tram 205, U-Bahn 900, S-Bahn 1,200, Regional rail 500. Line overrides: Bus 50–60, 62, 63, 68 = 100; Tram 20 = 257; U1, U2, U3, U5, U6, U8 = 930; U4, U7 = 580. These are planning capacities of one scheduled trip, not passengers.

**Activity (demand side).** activity = residents(Y) + w × jobs(Y).
- residents(Y) = pop_2024 + (pop_2045_forecast − pop_2024) × (Y − 2024) / 21 (linear interpolation; only 2045 is published per district).
- jobs(Y) = jobs_2022 + (jobs_2040_forecast − jobs_2022) × (min(Y, 2040) − 2024) / 16 (the 2022 estimate is the 2024 baseline; held after 2040).
- w = 0 means per resident; w = 1 counts a job like a resident. The default view is w = 1.

**The forecast.** Supply is today's timetable in every year unless projects or a what-if add places. Population and jobs grow, so places per 1,000 activity fall where growth is high.

**Map colour (`service_ratio`).** places per 1,000 activity in year Y in the district, divided by the 2024 city average at the same w (a fixed baseline: 34,425 at w = 1, 60,325 at w = 0). 1.0 = the 2024 city average.

**Change chart (`pct_change_places`).** % change of the district's places per 1,000 activity in year Y against its own 2024 value. The "Munich overall" bar is the city value in year Y against the 2024 city value (the app computes it from the rounded city figures).

**Flag rule.** A district is flagged when it is in the top third by activity per km² and the bottom third by places per 1,000 activity (NTILE(3)). `gap` = places rank − activity-density rank.

**Projects (scenarios).** `PT_PROJECT_STATIONS` holds 17 projects with stations, district, mode, line, frequencies, analog line, opening year (model) and risk year. A project counts only if it is switched on and `year >= opening year` (the risk year when pessimistic). Rules:
1. Departures per project station = (trains per hour peak × 6 + off-peak × 13) × 2 directions (peak falls back to off-peak and vice versa). Where no frequency is published: the analog line's mean weekday departures per Munich station on the reference Wednesday.
2. Places = departures × the project line's capacity per trip (same override logic).
3. Laim inbound restored (`laim_inbound_restore`): restored inbound departures at Laim = today's outbound minus today's inbound departures, per line.
4. Presets: "Funded only" = the projects with `funded = 1` (laim_inbound_restore, sbahn_berduxstrasse, stammstrecke2, tram_muenchner_norden_1, tram_westtangente_2, u5_pasing); "Funded + planned" adds status under_construction, in_operation, approved or planning; "Everything discussed" = all 17.

**2nd Stammstrecke (`stammstrecke2`).** Two parts, both active from its opening year (model 2035, risk 2037):
- the new-tunnel trains at the 5 tunnel stations, by rule 1 (+3,237,600 places per weekday);
- a 15-minute basic interval on the existing network: for every S-Bahn line except S2, S5, S7 and S20, at every station inside Munich that the line serves today, departures become GREATEST(departures today, 152), where 152 = 4 trains/h × 19 h × 2 directions; places added = the difference × 1,200 (+2,035,200; S3, S4, S6, S8 lifted, S1 already above).
- Nothing is removed from the existing trunk (freed slots assumed reused).
- With the Laim restore also on, the 15-minute rule at Laim is applied after the restore, so nothing is counted twice.
- S2, S7 and S20 are excluded per the 2017 concept (Landtag 17/17196); S5 is a later reinforcement line, not in that concept. The line table is unverified, and the 2025 BEG tender may swap branches.

**What-ifs (v5 only, `{extra!s}`).** The `what_if` tool turns a hypothetical into extra places per weekday per district and passes them as one string `'district_no:places;district_no:places'` (empty = nothing). The `ex_raw` and `ex` CTEs split it and add the places to supply (and to `add_places`) in every year ≥ 2024. Departures are not changed by a what-if, the 2024 baseline is not changed, and the extra places count in every year shown. With an empty string the output is identical to the dashboard (checked for R2–R5). Rules the tool uses to build the string:
- `frequency`: for each listed line and Munich station, (GREATEST(departures today, trains per hour × hours × 2) − departures today) × capacity per trip (hours default 19). This is the same rule as the 15-minute interval with the frequency as a parameter.
- `new_line`: departures per station (peak × 6 + off-peak × 13) × 2, × the mode's capacity per trip; at stations shared with existing lines, only the new line's departures count.

**Not in the model.** Demand shifts, crowding, travel time, transfers, reliability, cost, construction feasibility, and anything outside Munich's 25 districts.

## 4. Reference numbers

Computed with `dashboards/munich-mobility-planning-v4/queries/ranking.sql`, reference weekday 2026-10-21 (`scripts/verify_numbers.py` pins it; expected values in `tests/expected.json`).

The query runs read-only with its placeholders substituted (`pessimistic = 0` throughout). All values are scheduled service (places offered = departures x capacity per trip), not passengers.

#### Data checks

| Check | Expected |
|---|---|
| DISTRICTS rows | 25 |
| DISTRICT_EMPLOYMENT rows | 25 |
| DISTRICT_POPULATION rows | 25 |
| PT_PROJECT_STATIONS rows | 88 |
| SUM(pop_2024) | 1,603,776 |

#### Reference cases

| Case | year | w | projects | Expected |
|---|---|---|---|---|
| R1 | 2024 | 0 | none | city 60,325 per 1,000 residents; Sendling-Westpark 0.400; Altstadt-Lehel 6.178 |
| R2 | 2024 | 1 | none | city 34,425 per 1,000 activity; Sendling-Westpark 0.496; Ludwigsvorstadt-Isarvorstadt 1.882 |
| R3 | 2045 | 1 | none | city 29,822 vs 34,425 = -13.37 %; Aubing-Lochhausen-Langwied -40.5 % |
| R4 | 2045 | 1 | Funded only | city 32,069 vs 34,425 = -6.84 %; net +7,290,222 places per weekday |
| R5 | 2045 | 1 | Everything discussed | city 33,593 vs 34,425 = -2.42 %; net +12,232,618 places per weekday |
| R6 | 2045 | 1 | stammstrecke2 only | city 31,448 vs 34,425 = -8.65 %; net +5,272,800 places per weekday |

"Funded only" (from `preset_ids(projects, "funded")` = projects with `funded = 1`): laim_inbound_restore, sbahn_berduxstrasse, stammstrecke2, tram_muenchner_norden_1, tram_westtangente_2, u5_pasing.

The ratio is `service_ratio` = district places per 1,000 activity / 2024 city average at the same w. The city % is the bar "Munich overall" in "Change since 2024" (the app computes it from the rounded city values; the result is the same either way).

#### R1: 2024, w = 0 (per resident), no projects. City 60,325 places per 1,000 residents

| # | District | Ratio | Places per 1,000 residents |
|---|---|---|---|
| 7 | Sendling-Westpark | 0.400 | 24,110 |
| 18 | Untergiesing-Harlaching | 0.573 | 34,589 |
| 24 | Feldmoching-Hasenbergl | 0.592 | 35,686 |
| 23 | Allach-Untermenzing | 0.615 | 37,100 |
| 20 | Hadern | 0.674 | 40,668 |
| 16 | Ramersdorf-Perlach | 0.676 | 40,775 |
| 19 | Thalkirchen-Obersendling-Forstenried-Fürstenried-Solln | 0.689 | 41,544 |
| 22 | Aubing-Lochhausen-Langwied | 0.702 | 42,321 |
| 21 | Pasing-Obermenzing | 0.715 | 43,132 |
| 15 | Trudering-Riem | 0.743 | 44,847 |
| 4 | Schwabing-West | 0.744 | 44,864 |
| 13 | Bogenhausen | 0.766 | 46,232 |
| 9 | Neuhausen-Nymphenburg | 0.770 | 46,425 |
| 14 | Berg am Laim | 0.773 | 46,606 |
| 11 | Milbertshofen-Am Hart | 0.813 | 49,067 |
| 17 | Obergiesing-Fasangarten | 0.959 | 57,862 |
| 25 | Laim | 1.016 | 61,283 |
| 6 | Sendling | 1.079 | 65,062 |
| 10 | Moosach | 1.140 | 68,776 |
| 12 | Schwabing-Freimann | 1.274 | 76,856 |
| 3 | Maxvorstadt | 1.556 | 93,894 |
| 5 | Au-Haidhausen | 1.677 | 101,175 |
| 8 | Schwanthalerhöhe | 2.178 | 131,400 |
| 2 | Ludwigsvorstadt-Isarvorstadt | 2.858 | 172,405 |
| 1 | Altstadt-Lehel | 6.178 | 372,706 |

Flagged (top third by density, bottom third by places): Sendling-Westpark only.

#### R2: 2024, w = 1 (residents + jobs), no projects. City 34,425 places per 1,000 activity

| # | District | Ratio | Places per 1,000 activity |
|---|---|---|---|
| 7 | Sendling-Westpark | 0.496 | 17,064 |
| 23 | Allach-Untermenzing | 0.589 | 20,265 |
| 11 | Milbertshofen-Am Hart | 0.688 | 23,688 |
| 16 | Ramersdorf-Perlach | 0.739 | 25,427 |
| 18 | Untergiesing-Harlaching | 0.778 | 26,767 |
| 19 | Thalkirchen-Obersendling-Forstenried-Fürstenried-Solln | 0.789 | 27,148 |
| 20 | Hadern | 0.796 | 27,401 |
| 24 | Feldmoching-Hasenbergl | 0.802 | 27,593 |
| 13 | Bogenhausen | 0.811 | 27,923 |
| 14 | Berg am Laim | 0.815 | 28,062 |
| 9 | Neuhausen-Nymphenburg | 0.842 | 28,987 |
| 3 | Maxvorstadt | 0.844 | 29,040 |
| 15 | Trudering-Riem | 0.859 | 29,572 |
| 22 | Aubing-Lochhausen-Langwied | 0.862 | 29,675 |
| 12 | Schwabing-Freimann | 0.938 | 32,290 |
| 4 | Schwabing-West | 0.942 | 32,432 |
| 21 | Pasing-Obermenzing | 0.958 | 32,974 |
| 10 | Moosach | 1.063 | 36,581 |
| 25 | Laim | 1.186 | 40,835 |
| 17 | Obergiesing-Fasangarten | 1.234 | 42,469 |
| 6 | Sendling | 1.325 | 45,600 |
| 8 | Schwanthalerhöhe | 1.625 | 55,934 |
| 5 | Au-Haidhausen | 1.736 | 59,779 |
| 1 | Altstadt-Lehel | 1.814 | 62,457 |
| 2 | Ludwigsvorstadt-Isarvorstadt | 1.882 | 64,782 |

Flagged at w = 1: none.

#### R3: 2045, w = 1, no projects (change since 2024, % places per 1,000 activity)

City: 29,822 (2045) vs 34,425 (2024) = -13.37 %. Lowest: Aubing-Lochhausen-Langwied -40.5 %, Feldmoching-Hasenbergl -26.9 %, Trudering-Riem -25.2 %, Schwabing-Freimann -22.0 %, Bogenhausen -19.8 %. Highest: Untergiesing-Harlaching +0.5 %, Hadern -2.4 %, Obergiesing-Fasangarten -3.1 %.

#### The 2nd Stammstrecke in the model

When `stammstrecke2` is active: (1) the 5 new-tunnel stations from `PT_PROJECT_STATIONS` are added by the frequency method; (2) S1/S6 departures on the existing trunk are not removed (the slots are reused); (3) 15-minute basic interval: for every S-Bahn line except S2, S5, S7 and S20, at every station inside Munich the line serves today, `departures_new = GREATEST(departures_today, 152)`, places = difference x capacity per trip (1,200 for every S-Bahn line); (4) with `laim_inbound_restore` also active, the 15-minute rule is applied on the restored numbers at Laim (S3/S4/S6/S8: -250 departures adjustment, nothing counted twice). S5 is excluded because it is a later reinforcement line, not part of the 2017 concept. The rule sits in the `sb` CTE of `ranking.sql` and `projects.sql` (`line NOT IN ('S2', 'S5', 'S7', 'S20')`). R1-R3 do not use projects and are unaffected (0 places added; sum of the 25 ratios 30.160 / 25.413 / 22.535).

Lines in the feed: S1, S2, S20, S3, S4, S5, S6, S7, S8. Upgraded lines (S-Bahn stations inside Munich served today / lifted to 152 / places added per weekday): S1 14 / 0 / 0 (235 departures everywhere already); S3 16 / 4 / +88,800; S4 16 / 16 / +729,600; S6 15 / 15 / +655,200; S8 18 / 18 / +561,600. Total 79 stations, 53 lifted, +1,696 departures, +2,035,200 places.

#### R6: 2045, w = 1, stammstrecke2 only

Net **+5,272,800** places per weekday = step 1 (new tunnel) +3,237,600 + step 3 (15-minute basic interval) +2,035,200. City 31,448 vs 34,425 = -8.65 %.

| District | R6 ratio | None ratio (R3) | R6 % since 2024 | Places added |
|---|---|---|---|---|
| Schwanthalerhöhe | 1.564 | 1.523 | -3.7 % | +100,800 |
| Neuhausen-Nymphenburg | 0.792 | 0.776 | -5.9 % | +100,800 |
| Maxvorstadt | 0.777 | 0.777 | -7.9 % | 0 |

All 25 districts (R6): Altstadt-Lehel 1.800 (-0.8 %, +885,600); Ludwigsvorstadt-Isarvorstadt 1.918 (+1.9 %, +986,400); Maxvorstadt 0.777 (-7.9 %, +0); Schwabing-West 0.906 (-3.8 %, +0); Au-Haidhausen 2.025 (+16.6 %, +1,508,400); Sendling 1.235 (-6.7 %, +0); Sendling-Westpark 0.463 (-6.5 %, +0); Schwanthalerhöhe 1.564 (-3.7 %, +100,800); Neuhausen-Nymphenburg 0.792 (-5.9 %, +100,800); Moosach 0.895 (-15.8 %, +0); Milbertshofen-Am Hart 0.644 (-6.5 %, +0); Schwabing-Freimann 0.732 (-22.0 %, +0); Bogenhausen 0.662 (-18.4 %, +75,600); Berg am Laim 0.706 (-13.4 %, +98,400); Trudering-Riem 0.661 (-23.1 %, +98,400); Ramersdorf-Perlach 0.653 (-11.6 %, +0); Obergiesing-Fasangarten 1.197 (-3.0 %, +3,600); Untergiesing-Harlaching 0.781 (+0.5 %, +0); Thalkirchen-Obersendling-Forstenried-Fürstenried-Solln 0.687 (-12.9 %, +0); Hadern 0.776 (-2.4 %, +0); Pasing-Obermenzing 0.877 (-8.4 %, +100,800); Aubing-Lochhausen-Langwied 0.558 (-35.3 %, +224,400); Allach-Untermenzing 0.488 (-17.2 %, +0); Feldmoching-Hasenbergl 0.586 (-26.9 %, +0); Laim 1.446 (+21.9 %, +1,089,600).

#### R4: 2045, w = 1, Funded only

City 32,069 vs 34,425 = **-6.84 %**; net +7,290,222 places per weekday (dashboard: "+7.3 M places/day net"). Schwanthalerhöhe 1.564 vs 1.523, Neuhausen-Nymphenburg 0.792 vs 0.776, Maxvorstadt 0.777 = 0.777: no district falls below its "None" value.

#### R5: 2045, w = 1, Everything discussed

City 33,593 vs 34,425 = **-2.42 %**; 14 of 17 projects open by 2045; net +12,232,618 places per weekday (dashboard: "+12.2 M places/day net").

#### R4/R5: None / Funded only / Everything discussed at 2045, w = 1, all 25 districts (sorted by the Funded ratio)

Ratio = places per 1,000 activity in 2045 / 2024 city average (34,425). % = change in the district's places per 1,000 activity since 2024. City change: None -13.37 %, Funded -6.84 %, Everything discussed -2.42 %.

| # | District | None ratio | None % | Funded ratio | Funded % | Funded places added | Everything ratio | Everything % | Everything places added |
|---|---|---|---|---|---|---|---|---|---|
| 23 | Allach-Untermenzing | 0.488 | -17.2 | 0.488 | -17.2 | +0 | 0.488 | -17.2 | +0 |
| 7 | Sendling-Westpark | 0.463 | -6.5 | 0.492 | -0.7 | +93,480 | 0.492 | -0.7 | +93,480 |
| 22 | Aubing-Lochhausen-Langwied | 0.513 | -40.5 | 0.558 | -35.3 | +224,400 | 0.851 | -1.3 | +1,697,520 |
| 24 | Feldmoching-Hasenbergl | 0.586 | -26.9 | 0.586 | -26.9 | +0 | 0.586 | -26.9 | +0 |
| 11 | Milbertshofen-Am Hart | 0.644 | -6.5 | 0.644 | -6.5 | +0 | 0.696 | +1.1 | +308,100 |
| 16 | Ramersdorf-Perlach | 0.653 | -11.6 | 0.653 | -11.6 | +0 | 0.653 | -11.6 | +0 |
| 15 | Trudering-Riem | 0.642 | -25.2 | 0.661 | -23.1 | +98,400 | 0.661 | -23.1 | +98,400 |
| 13 | Bogenhausen | 0.651 | -19.8 | 0.662 | -18.4 | +75,600 | 0.737 | -9.1 | +585,106 |
| 14 | Berg am Laim | 0.676 | -17.1 | 0.706 | -13.4 | +98,400 | 0.706 | -13.4 | +98,400 |
| 19 | Thalkirchen-Obersendling-Forstenried-Fürstenried-Solln | 0.687 | -12.9 | 0.724 | -8.2 | +233,700 | 0.724 | -8.2 | +233,700 |
| 12 | Schwabing-Freimann | 0.732 | -22.0 | 0.767 | -18.3 | +280,440 | 0.837 | -10.8 | +848,989 |
| 3 | Maxvorstadt | 0.777 | -7.9 | 0.777 | -7.9 | +0 | 0.876 | +3.8 | +624,525 |
| 18 | Untergiesing-Harlaching | 0.781 | +0.5 | 0.781 | +0.5 | +0 | 0.781 | +0.5 | +0 |
| 9 | Neuhausen-Nymphenburg | 0.776 | -7.9 | 0.792 | -5.9 | +100,800 | 0.792 | -5.9 | +100,800 |
| 20 | Hadern | 0.776 | -2.4 | 0.811 | +1.9 | +93,480 | 0.811 | +1.9 | +93,480 |
| 10 | Moosach | 0.895 | -15.8 | 0.895 | -15.8 | +0 | 0.912 | -14.2 | +74,400 |
| 4 | Schwabing-West | 0.906 | -3.8 | 0.906 | -3.8 | +0 | 1.024 | +8.7 | +402,360 |
| 21 | Pasing-Obermenzing | 0.853 | -11.0 | 1.103 | +15.2 | +1,036,842 | 1.103 | +15.2 | +1,036,842 |
| 17 | Obergiesing-Fasangarten | 1.196 | -3.1 | 1.197 | -3.0 | +3,600 | 1.197 | -3.0 | +3,600 |
| 6 | Sendling | 1.235 | -6.7 | 1.235 | -6.7 | +0 | 1.380 | +4.2 | +312,263 |
| 8 | Schwanthalerhöhe | 1.523 | -6.2 | 1.564 | -3.7 | +100,800 | 1.564 | -3.7 | +100,800 |
| 25 | Laim | 1.103 | -7.0 | 1.566 | +32.0 | +1,469,880 | 1.566 | +32.0 | +1,469,880 |
| 1 | Altstadt-Lehel | 1.616 | -10.9 | 1.800 | -0.8 | +885,600 | 1.809 | -0.3 | +930,649 |
| 2 | Ludwigsvorstadt-Isarvorstadt | 1.721 | -8.5 | 1.918 | +1.9 | +986,400 | 2.043 | +8.5 | +1,610,925 |
| 5 | Au-Haidhausen | 1.642 | -5.4 | 2.025 | +16.6 | +1,508,400 | 2.025 | +16.6 | +1,508,400 |

## 5. Findings

From the research files. Re-check any number through a tool before relying on it.

### Findings file: urban-planning.md (forecast, scenario and assistant sections)

#### v3: forecast to 2045, if service stays as it is today

**Answer.** Munich grows from 1,603,776 residents (2024) to the forecast 1,829,522 (2045). If today's timetable stays unchanged, city-wide supply falls from 34,425 to 29,822 places per 1,000 activity at w = 1 (−13.4 %). Growth is concentrated at the edge of the city, so the outer districts lose most:
- Aubing-Lochhausen-Langwied −40.5 % (0.86× to 0.51× the 2024 city average; Freiham)
- Feldmoching-Hasenbergl −26.9 %
- Trudering-Riem −25.2 %
- Schwabing-Freimann −22.0 %
- Bogenhausen −19.8 %

Only Untergiesing-Harlaching improves slightly (+0.5 %). On the flag rule (top third for activity density and bottom third for places), no district is flagged in 2024 or 2045 at w = 1. Berg am Laim is flagged in 2034 and 2035 only (2035: activity-density rank 9, places rank 18). By 2045 the outer districts' supply has fallen further, so Berg am Laim drops out. At w = 0, Sendling-Westpark is flagged in 2024 and not in 2045.

**Method.**
- Residents(Y) = pop_2024 + (pop_2045_forecast − pop_2024) × (Y − 2024) / 21, a linear interpolation: the Demografiebericht Teil 2 publishes district values for 2045 only.
- Jobs(Y) = jobs_2022 + (jobs_2040 − jobs_2022) × (min(Y, 2040) − 2024) / 16. The city's 2022 estimate is used as the 2024 baseline, rising linearly to the 2040 forecast and held after 2040.
- Supply is today's scheduled timetable, unchanged in every year.
- The map colour is places per 1,000 activity in year Y divided by the 2024 city average at the same w, a fixed baseline.

Year 2024 equals v2 at every w: 34,425 city-wide, Sendling-Westpark 0.496, Ludwigsvorstadt-Isarvorstadt 1.882, no flags at w = 1. At w = 0: 60,325, Sendling-Westpark 0.40 and flagged.

| District | Ratio 2024 | Ratio 2045 | % places per 1,000 activity | District | Ratio 2024 | Ratio 2045 | % |
|---|---|---|---|---|---|---|---|
| Aubing-Lochhausen-Langwied | 0.862 | 0.513 | −40.5 | Maxvorstadt | 0.844 | 0.777 | −7.9 |
| Feldmoching-Hasenbergl | 0.802 | 0.586 | −26.9 | Neuhausen-Nymphenburg | 0.842 | 0.776 | −7.9 |
| Trudering-Riem | 0.859 | 0.642 | −25.2 | Laim | 1.186 | 1.103 | −7.0 |
| Schwabing-Freimann | 0.938 | 0.732 | −22.0 | Sendling | 1.325 | 1.235 | −6.7 |
| Bogenhausen | 0.811 | 0.651 | −19.8 | Sendling-Westpark | 0.496 | 0.463 | −6.5 |
| Allach-Untermenzing | 0.589 | 0.488 | −17.2 | Milbertshofen-Am Hart | 0.688 | 0.644 | −6.5 |
| Berg am Laim | 0.815 | 0.676 | −17.1 | Schwanthalerhöhe | 1.625 | 1.523 | −6.2 |
| Moosach | 1.063 | 0.895 | −15.8 | Au-Haidhausen | 1.736 | 1.642 | −5.4 |
| Thalkirchen-…-Solln | 0.789 | 0.687 | −12.9 | Schwabing-West | 0.942 | 0.906 | −3.8 |
| Ramersdorf-Perlach | 0.739 | 0.653 | −11.6 | Obergiesing-Fasangarten | 1.234 | 1.196 | −3.1 |
| Pasing-Obermenzing | 0.958 | 0.853 | −11.0 | Hadern | 0.796 | 0.776 | −2.4 |
| Altstadt-Lehel | 1.814 | 1.616 | −10.9 | Untergiesing-Harlaching | 0.778 | 0.781 | +0.5 |
| Ludwigsvorstadt-Isarvorstadt | 1.882 | 1.721 | −8.5 | | | | |

**Caveats.**
- Residents in intermediate years are interpolated, not forecast values. The forecast is Hauptwohnsitz only and its housing assumptions are a snapshot; Nordosten and Münchner Norden lie largely beyond 2045.
- Jobs are a modelled estimate, with the 2022 value used as the 2024 baseline and held after 2040.
- Supply is today's timetable. Funded projects (Tram 23/24 Neufreimann, Westtangente section 2, U5 Pasing) and planned ones (U5 Freiham, U4 Nordost) are not included; v4 adds them as scenarios.
- Scheduled service only.

#### v4: forecast with rail and tram scenarios

**Answer.** By 2045 at w = 1, with no project switched on, city-wide supply falls from 34,425 to 29,822 places per 1,000 activity (−13.37 %). The six funded projects lift that to 32,069 (−6.84 %), which offsets 49 % of the decline. Everything discussed lifts it to 33,593 (−2.42 %), which offsets 82 %.

The largest single contributor is the 2nd Stammstrecke, modelled as the new-tunnel trains plus a 15-minute basic interval on the existing S-Bahn network. It adds +5,272,800 places per weekday net: +3,237,600 from the five tunnel stations and +2,035,200 from lifting 53 Munich S-Bahn stations on S3, S4, S6 and S8 to at least 152 departures. S1 is already above 152; S2, S5, S7 and S20 are excluded. Nothing is removed from the existing trunk, so no central district loses supply: Schwanthalerhöhe (1.564 vs 1.523), Neuhausen-Nymphenburg (0.792 vs 0.776) and Maxvorstadt (0.777 = 0.777) end at or above their "none" values.

The fastest-shrinking districts still gain little from funded projects: Feldmoching-Hasenbergl and Allach-Untermenzing get nothing, and Trudering-Riem and Bogenhausen only a few percent from the S-Bahn interval. Aubing-Lochhausen-Langwied gets +224,400 places per weekday from the interval on S8 (0.513 → 0.558) and reaches 0.851 only with the unfunded U5 Freiham, whose year is a placeholder.

| District | 2024 | 2045 none | Funded | Everything | Funded offset of decline |
|---|---|---|---|---|---|
| Aubing-Lochhausen-Langwied | 0.862 | 0.513 | 0.558 | 0.851 | 13 % |
| Trudering-Riem | 0.859 | 0.642 | 0.661 | 0.661 | 9 % |
| Feldmoching-Hasenbergl | 0.802 | 0.586 | 0.586 | 0.586 | 0 % |
| Schwabing-Freimann | 0.938 | 0.732 | 0.767 | 0.837 | 17 % |
| Altstadt-Lehel | 1.814 | 1.616 | 1.800 | 1.809 | 93 % |
| Moosach | 1.063 | 0.895 | 0.895 | 0.912 | 0 % |
| Ludwigsvorstadt-Isarvorstadt | 1.882 | 1.721 | 1.918 | 2.043 | 122 % |
| Bogenhausen | 0.811 | 0.651 | 0.662 | 0.737 | 7 % |
| Berg am Laim | 0.815 | 0.676 | 0.706 | 0.706 | 22 % |
| Pasing-Obermenzing | 0.958 | 0.853 | 1.103 | 1.103 | 238 % |
| Schwanthalerhöhe | 1.625 | 1.523 | 1.564 | 1.564 | 40 % |
| Thalkirchen-…-Solln | 0.789 | 0.687 | 0.724 | 0.724 | 36 % |
| Allach-Untermenzing | 0.589 | 0.488 | 0.488 | 0.488 | 0 % |
| Au-Haidhausen | 1.736 | 1.642 | 2.025 | 2.025 | 407 % |
| Sendling | 1.325 | 1.235 | 1.235 | 1.380 | 0 % |
| Ramersdorf-Perlach | 0.739 | 0.653 | 0.653 | 0.653 | 0 % |
| Laim | 1.186 | 1.103 | 1.566 | 1.566 | 558 % |
| Maxvorstadt | 0.844 | 0.777 | 0.777 | 0.876 | 0 % |
| Neuhausen-Nymphenburg | 0.842 | 0.776 | 0.792 | 0.792 | 24 % |
| Milbertshofen-Am Hart | 0.688 | 0.644 | 0.644 | 0.696 | 0 % |
| Obergiesing-Fasangarten | 1.234 | 1.196 | 1.197 | 1.197 | 3 % |
| Schwabing-West | 0.942 | 0.906 | 0.906 | 1.024 | 0 % |
| Sendling-Westpark | 0.496 | 0.463 | 0.492 | 0.492 | 88 % |
| Hadern | 0.796 | 0.776 | 0.811 | 0.811 | 175 % |
| Untergiesing-Harlaching | 0.778 | 0.781 | 0.781 | 0.781 | no decline |

Ratios are places per 1,000 activity divided by the 2024 city average (34,425) at w = 1. Offset = (funded − none) / (2024 − none). Values above 100 % mean the district ends above its 2024 level. Sorted by the decline without projects (2045 none − 2024).

**Net places per weekday per project, once open:**
- 2. Stammstrecke +5,272,800 (new tunnel +3,237,600; 15-minute basic interval +2,035,200; 2035, risk 2037)
- U9-Spange +2,185,838 (analog U6, placeholder 2040)
- U5 Pasing–Freiham +1,473,120 (analog U5, placeholder 2040)
- U5 Laimer Platz–Pasing +1,104,840 (analog U5, 2036)
- U4 Ost +424,917 (analog U4, assumed 2040)
- Tram-Westtangente +420,660 (frequency, 2028, risk 2031)
- Laim inbound restored +312,000 (260 departures, 2028); with the 2nd trunk also on, the 15-minute rule at Laim is applied on the restored numbers, −300,000 (−250 departures)
- Tram Münchner Norden PFA 1 +280,440 (2031)
- Tram Münchner Norden PFA 2 +280,440 (2031 placeholder)
- Tram-Nordtangente +270,293 (analog 23, blocked)
- S-Bahn Nordring shuttle +223,200 (frequency)
- S-Bahn halt Berduxstraße +199,482 (analog S2)
- Tram Johanneskirchen +84,589 (analog 16)
- Poccistraße, Tram Lerchenauer Feld, U26 and the Augsburg express add 0 (no stations published or already in the 2nd trunk).

**15-minute basic interval by line** (S-Bahn stations inside Munich served today / lifted to 152 / places added per weekday): S1 14 / 0 / 0 · S3 16 / 4 / +88,800 · S4 16 / 16 / +729,600 · S6 15 / 15 / +655,200 · S8 18 / 18 / +561,600. Excluded: S2, S7 and S20 (not in the 2017 concept) and S5 (a later reinforcement line not in that concept).

**Method.**
- **Rule 1:** departures = (trains per hour peak × 6 + off-peak × 13) × 2. Where no frequency is published, the analog line's mean weekday departures per Munich station on the reference Wednesday.
- **Rule 2:** places = departures × the line's capacity per trip (LINE_CAPACITY override, else VEHICLE_CAPACITY; 1,200 per S-Bahn trip).
- **Rule 3:** Laim inbound restored = today's outbound departures minus today's inbound ones, per line.
- **Rule 4:** the 2nd trunk adds its 2017 start-concept tunnel lines at the 5 tunnel stations (Rule 1), removes nothing from the existing trunk (freed slots assumed reused), and applies a 15-minute basic interval: for every S-Bahn line except S2, S5, S7 and S20, at every station inside Munich it serves today, departures = GREATEST(today, 152), where 152 = 4 trains/h × 19 h × 2 directions. With Laim restored also on, the rule is applied after the restore. Station markers stay on the 5 tunnel stations.
- **Rule 5:** a project counts from its model opening year, or its risk year when pessimistic. Pessimistic dates change the result only between opening and risk year.
- **Where the rules live:** all rules are in SQL (the `need`, `sb`, `comps` and `sel` CTEs in `ranking.sql`, and `projects.sql`). With no project switched on, the output equals v3 (R1–R3 in section 4).

**Caveats.**
- Project frequencies are partly analog assumptions.
- 2nd Stammstrecke: new-tunnel trains plus a 15-minute basic service on all S-Bahn lines except S2, S5, S7 and S20 (2017 concept, unverified line table; S5 is a later reinforcement line not in that concept); existing-trunk slots assumed reused. The 2025 BEG tender may swap S2/S3 branches, so the excluded lines may change.
- Several opening years are placeholders or assumed 2040.
- Coordinates are partly approximated.
- Scheduled capacity only, not demand or crowding.
- The mode note ("mostly bus", "mostly rail") refers to today's timetable.

#### v5: ask the assistant

v5 uses v4's model unchanged; its numbers are v4's. With no what-if, `ranking.sql` returns exactly the v4 output.

- First load is the current year with w = 1.0 and no projects: on the reference date that is 2026, Munich overall −1.66 % (33,853 vs 34,425).
- "Show 2045 with the funded projects" gives Funded only, 6 projects active, +7.3 M places per weekday net, Munich overall −6.84 % (R4).
- 2045 None −13.37 % (R3), Everything discussed −2.42 % (R5), 2nd Stammstrecke only −8.65 % (R6).
- A frequency what-if reuses the 15-minute rule with the frequency as a parameter: extra places = (GREATEST(departures today, trains per hour × hours × 2) − departures today) × capacity per trip. "S4 at least 4 trains/h for 19 h" adds +729,600 places, the same as v4's 15-minute rule for S4.
- A new-line what-if adds (peak × 6 + off-peak × 13) × 2 departures per station × the mode's capacity per trip.

**Caveats.** A what-if is capacity arithmetic, not a plan: demand shifts, crowding, travel time, cost and feasibility are not modelled. It adds to supply in every year shown; departures and the 2024 baseline don't change.

### Findings file: district-growth.md

### Munich population growth per Stadtbezirk: past trend and official forecast

Researched 2026-10-16. Web research only, no database queries. Every number below comes from a source I opened or downloaded (marked *verified* in section 5). Numbers I saw only in search snippets are marked *(unverified)*.

**How to read the columns.** **Count** means registered population with Hauptwohnsitz (main residence) at 31 December, from the Melderegister (residents' register). **Forecast** means the city's official Planungsprognose (planning forecast, its most likely path) 2025–2045, which starts from the end-2024 count.

---

#### 1. Summary

- **City total.** The count rose from 1,521,678 (end 2015) to 1,612,429 (end 2025): **+90,751, +6.0 %** over 10 years. The official forecast expects **1,829,520 in 2045**, which is **+225,744 (+14.1 %)** on end-2024 (1,603,776). That works out to about +0.63 % a year. For 2040, the year of our jobs forecast, the city-level forecast is **1.771 million**. No per-district 2040 values are published as numbers (see caveats).
- **Fastest growth to 2045, in absolute numbers:**
  1. 22 Aubing-Lochhausen-Langwied: **+52,132** (Freiham)
  2. 15 Trudering-Riem: **+32,421** (Messestadt Riem 5th Bauabschnitt, Heltauer Straße, Rappenweg)
  3. 13 Bogenhausen: **+26,559** (Münchner Nordosten, only partly before 2045)
  4. 24 Feldmoching-Hasenbergl: **+23,189** (Lerchenauer Straße, Eggarten, Ludwigsfeld, Hasenbergl infill)
  5. 12 Schwabing-Freimann: **+17,572** (Neufreimann/Bayernkaserne, Freisinger Landstraße)

  These five districts add about 152,000 residents, roughly two thirds of the city's forecast growth.
- **Fastest growth to 2045, in %:** 22 Aubing-Lochhausen-Langwied **+85.4 %**, 15 Trudering-Riem **+42.5 %**, 24 Feldmoching-Hasenbergl **+36.4 %**, 13 Bogenhausen **+27.8 %**, 23 Allach-Untermenzing **+25.2 %**, 12 Schwabing-Freimann **+22.8 %**, 10 Moosach **+19.6 %**.
- **Districts expected to stagnate or shrink by 2045:** 1 Altstadt-Lehel, 2 Ludwigsvorstadt-Isarvorstadt, 4 Schwabing-West, 8 Schwanthalerhöhe, 17 Obergiesing-Fasangarten, 18 Untergiesing-Harlaching (−5.2 %) and 20 Hadern (−3.4 %).
- **Past trend, 2015 to 2025:** growth was already concentrated at the edge of the city. Aubing-Lochhausen-Langwied grew by +19,525 (+44.7 %, the first Freiham phase). Next come 19 Thalkirchen-…-Solln (+10,635), 13 Bogenhausen (+9,593), 16 Ramersdorf-Perlach (+8,900), 21 Pasing-Obermenzing (+8,463) and 15 Trudering-Riem (+7,324). Four inner districts lost residents: 2 (−7.4 %), 8 (−3.0 %), 1 (−2.4 %) and 3 (−2.3 %).
- **Meaning for transport.** Forecast growth sits mostly in outer districts: 22, 15, 13, 24, 12, 10 and 23. Today these districts have the lowest densities, between 1,791 and 5,049 residents per km² in 2024. Several of the rail links meant to serve the new areas are not yet built or are only in planning: U5 to Freiham, U4 to the Nordosten, Tram Lerchenauer Feld. See section 3.

---

#### 2. District table: counts and forecast

Sources per column:
- **(A) Count 2015, (B) Count 2024, (C) Count 2025:** Hauptwohnsitz population at 31 Dec. They come from the open-data CSV *Indikatorenatlas Bevölkerung – Bevölkerungsanteil*, column `Basiswert 1` ("Hauptwohnsitzbevölkerung (ausgewählte räumliche Einheit)"), file `indikat_2605bevoelkerung_bevoelkerungsanteil_18_05_26.csv`, updated 22 May 2026, series 2000–2025. Columns A and B match the per-district tables in Demografiebericht Teil 2 exactly.
- **(D) Forecast 2045:** Demografiebericht München – Teil 2, *Kleinräumige Bevölkerungsprognose 2025 bis 2045 für die Stadtbezirke* (Referat für Stadtplanung und Bauordnung, editorial deadline May 2025, presented to the Stadtplanung committee on 4 June 2025). The value is taken from the age-group table on each district's second page, row "Bezirk gesamt" (columns 2015 / 2024 / 2045). These are printed pages 31, 33, …, 79 (district *n* is on printed page 29 + 2n, PDF page 31 + 2n), and the city total is on printed page 81. The same values appear in the "Kennzahlen" table, row "Einwohnerstand", and as % in Abbildung 1 (printed page 6).
- **Change 2015→2025:** computed by me from A and C (count to count).
- **Change 2024→2045:** computed by me from B and D (forecast against its own base year).
- **New homes 2025–2045:** the assumed housing construction class (*Neubautätigkeit*) for projects of more than 50 homes with new building rights. It is printed on each district page and shown in Karte 3 (printed page 17). The source gives it only as a band.

| No. | Stadtbezirk | (A) Count 2015 | (B) Count 2024 | (C) Count 2025 | Δ 2015→2025 | Δ % | (D) **Forecast** 2045 | Δ 2024→2045 | Δ % | New homes 2025–45 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | Altstadt-Lehel | 21,122 | 20,876 | 20,606 | −516 | −2.4 % | 20,864 | −12 | −0.1 % | 0–500 |
| 2 | Ludwigsvorstadt-Isarvorstadt | 54,049 | 50,081 | 50,048 | −4,001 | −7.4 % | 49,296 | −785 | −1.6 % | 501–2,000 |
| 3 | Maxvorstadt | 53,743 | 52,434 | 52,501 | −1,242 | −2.3 % | 53,895 | +1,461 | +2.8 % | 0–500 |
| 4 | Schwabing-West | 68,527 | 68,610 | 69,484 | +957 | +1.4 % | 67,091 | −1,519 | −2.2 % | 501–2,000 |
| 5 | Au-Haidhausen | 61,495 | 63,972 | 64,122 | +2,627 | +4.3 % | 64,694 | +722 | +1.1 % | 501–2,000 |
| 6 | Sendling | 40,879 | 41,002 | 41,334 | +455 | +1.1 % | 42,826 | +1,824 | +4.4 % | 501–2,000 |
| 7 | Sendling-Westpark | 58,398 | 62,240 | 62,640 | +4,242 | +7.3 % | 64,997 | +2,757 | +4.4 % | 501–2,000 |
| 8 | Schwanthalerhöhe | 30,381 | 28,684 | 29,456 | −925 | −3.0 % | 27,870 | −814 | −2.8 % | 0–500 |
| 9 | Neuhausen-Nymphenburg | 98,702 | 101,901 | 102,527 | +3,825 | +3.9 % | 104,389 | +2,488 | +2.4 % | 2,001–5,000 |
| 10 | Moosach | 53,261 | 56,015 | 56,150 | +2,889 | +5.4 % | 66,975 | +10,960 | +19.6 % | 2,001–5,000 |
| 11 | Milbertshofen-Am Hart | 75,488 | 77,281 | 77,500 | +2,012 | +2.7 % | 81,966 | +4,685 | +6.1 % | 2,001–5,000 |
| 12 | Schwabing-Freimann | 75,020 | 77,092 | 76,809 | +1,789 | +2.4 % | 94,664 | +17,572 | +22.8 % | 5,001–10,000 |
| 13 | Bogenhausen | 85,947 | 95,475 | 95,540 | +9,593 | +11.2 % | 122,034 | +26,559 | +27.8 % | 5,001–10,000 |
| 14 | Berg am Laim | 45,035 | 47,367 | 47,185 | +2,150 | +4.8 % | 53,527 | +6,160 | +13.0 % | 2,001–5,000 |
| 15 | Trudering-Riem | 69,830 | 76,280 | 77,154 | +7,324 | +10.5 % | 108,701 | +32,421 | +42.5 % | >10,000 |
| 16 | Ramersdorf-Perlach | 112,371 | 120,776 | 121,271 | +8,900 | +7.9 % | 135,912 | +15,136 | +12.5 % | 5,001–10,000 |
| 17 | Obergiesing-Fasangarten | 54,402 | 54,352 | 54,500 | +98 | +0.2 % | 54,304 | −48 | −0.1 % | 2,001–5,000 |
| 18 | Untergiesing-Harlaching | 53,377 | 54,067 | 54,227 | +850 | +1.6 % | 51,245 | −2,822 | −5.2 % | 501–2,000 |
| 19 | Thalkirchen-Obersendling-Forstenried-Fürstenried-Solln | 93,602 | 103,717 | 104,237 | +10,635 | +11.4 % | 118,939 | +15,222 | +14.7 % | 2,001–5,000 |
| 20 | Hadern | 50,257 | 51,637 | 51,809 | +1,552 | +3.1 % | 49,861 | −1,776 | −3.4 % | 0–500 |
| 21 | Pasing-Obermenzing | 73,320 | 81,804 | 81,783 | +8,463 | +11.5 % | 90,118 | +8,314 | +10.2 % | 2,001–5,000 |
| 22 | Aubing-Lochhausen-Langwied | 43,682 | 61,011 | 63,207 | +19,525 | +44.7 % | 113,143 | +52,132 | +85.4 % | >10,000 |
| 23 | Allach-Untermenzing | 31,882 | 36,230 | 36,238 | +4,356 | +13.7 % | 45,378 | +9,148 | +25.2 % | 2,001–5,000 |
| 24 | Feldmoching-Hasenbergl | 61,534 | 63,756 | 64,586 | +3,052 | +5.0 % | 86,945 | +23,189 | +36.4 % | 5,001–10,000 |
| 25 | Laim | 55,374 | 57,116 | 57,515 | +2,141 | +3.9 % | 59,888 | +2,772 | +4.9 % | 501–2,000 |
| | **Stadt München** | **1,521,678** | **1,603,776** | **1,612,429** | **+90,751** | **+6.0 %** | **1,829,520** | **+225,744** | **+14.1 %** | |

Supporting figures from the same Teil 2 Kennzahlen tables: forecast density in 2045, in residents per km², with the 2024 count in brackets.

| No. | 2045 (2024) | No. | 2045 (2024) | No. | 2045 (2024) |
|---|---|---|---|---|---|
| 1 | 6,632 (6,636) | 10 | 6,037 (5,049) | 19 | 6,696 (5,839) |
| 2 | 11,199 (11,378) | 11 | 6,109 (5,760) | 20 | 5,406 (5,598) |
| 3 | 12,539 (12,199) | 12 | 3,687 (3,003) | 21 | 5,463 (4,959) |
| 4 | 15,376 (15,724) | 13 | 5,146 (4,026) | 22 | 3,322 (1,791) |
| 5 | 15,331 (15,159) | 14 | 8,476 (7,500) | 23 | 2,937 (2,345) |
| 6 | 10,872 (10,409) | 15 | 4,841 (3,397) | 24 | 3,004 (2,203) |
| 7 | 8,317 (7,964) | 16 | 6,831 (6,070) | 25 | 11,329 (10,805) |
| 8 | 13,462 (13,855) | 17 | 9,492 (9,501) | City | 5,888 (5,161) |
| 9 | 8,083 (7,890) | 18 | 6,360 (6,710) | | |

---

#### 3. Major development areas

Areas are converted from hectares (1 km² = 100 ha). "Verified" means I read the figure on the official project page or in the document named.

| Area | Stadtbezirk | Planned homes / residents / jobs | Timeline and status | Planned transport link |
|---|---|---|---|---|
| **Freiham** (Freiham Nord residential plus Freiham Süd business park) | 22 Aubing-Lochhausen-Langwied | Whole new district: **over 25,000 residents** on 3.5 km² in total, of which 2.0 km² is the residential part north of Bodenseestraße. **1st Realisierungsabschnitt:** about 4,500 homes for about 12,000 people on 0.85 km², under construction since 2016, first homes occupied 2019. **2nd Realisierungsabschnitt:** about 6,200 homes for about 16,000 people on about 0.55 km², framework plan (Rahmenplan) approved by the city council in July 2024. Its first building phase, Bebauungsplan Nr. 2154, covers about 2,800 homes for about 7,200 people on 0.27 km². Plus up to 1,200 homes at Eichenauer Straße (competition pending). **Jobs:** about 7,500 in the Freiham Süd business park (1.1 km²), plus up to 1,250 at the Hoffmann SE headquarters. *(verified, stadt.muenchen.de)* | "Gebaut wird bis zum Jahr 2040 in mehreren Abschnitten" (built in several phases up to 2040). The Teil 2 forecast attributes most of district 22's +85 % to Freiham. | **U5 west extension Pasing → Freiham-Zentrum:** added to the Nahverkehrsplan (local transport plan) on 23 Jan 2019, approved by the city council in 2020. Structural work on the end station Freiham-Zentrum, built in advance as a *Vorhaltemaßnahme*, has been under way since May 2024. The section Laimer Platz → Pasing is under construction, with the tunnel breakthrough in Laim reported in Rathaus Umschau 2026. *(verified)* **I found no official opening date for Pasing → Freiham.** Secondary sources mention Pasing about 2030–2035 *(unverified)*. S-Bahn station Freiham (S8) exists today. The planned four-track S4 expansion is part of the Freistaat's "Bahnausbau Region München" programme *(verified, Freiham page)*. |
| **Neufreimann** (on the Bayernkaserne site) | 12 Schwabing-Freimann | About **5,500 homes for up to 15,000 people** on about 0.6 km², of which about 1,100 homes are in the private "Heidepark" (0.1 km²). Rental housing only, built mostly by Münchner Wohnen. *(verified)* | Site development since 2019. First residents moved in in April 2025, when 250 homes were completed in Baufeld MU 1(17). WA 12 (190 homes) has been occupied since July 2026. Many projects in phase 1 are at shell stage. Three building phases are to be completed by the early to mid 2030s. *(verified)* | **Tram Münchner Norden:** the Tram 23 extension Schwabing Nord → Neufreimann → U-Bahnhof Kieferngarten (U6), 6 stops (PFA 1), runs diagonally through the quarter. PFA 2 covers Neufreimann → Am Hart (U2), 7 stops, as the new line 24. Groundbreaking was in October 2025. The city council decided the route alignment (Trassierungsbeschluss) for PFA 2 on 23 Jul 2025. Standardised assessment: benefit-cost ratio 2.61 (July 2025). *(verified, Mobilitätsreferat letter of 24 Jul 2026 and letter of 6 Oct 2025)* Opening "end of 2029" and a 4.5-year construction time appear only in search snippets of SWM press releases, which returned 404 when opened *(unverified)*. |
| **Münchner Nordosten** (Daglfing / Englschalking / Johanneskirchen) | 13 Bogenhausen, 15 Trudering-Riem | **Up to 11,500 homes / 30,000 residents / up to 10,000 jobs.** Study area 6 km². At least half of it stays agriculture and equestrian use. *(verified)* | Winning competition design (rheinflügel severin + bbz) adopted as the planning basis by the council on 27 Apr 2022. Status: "Erstellung Gutachten" (expert studies in progress). Construction "ab den 2030er Jahren", in about 8 phases built according to demand. Also proposed as the site of the Olympic and Paralympic Village. *(verified)* Teil 2 says the development extends "deutlich über den Prognosezeitraum hinaus", i.e. well beyond 2045, so only part of it is in the 2045 forecast. | Planned: **U4 extension** from Arabellapark into the centre of the Nordosten, with an option to Messestadt Riem. **Two tram lines** from the city centre plus a new north–south tram. Buses to run first as an interim service. Fast cycle route to Markt Schwaben. *(verified, project page)* **S8 four-track expansion Daglfing–Johanneskirchen in a tunnel:** this is the long-standing demand of the city council. A city letter said construction would start in 2031 at the earliest, with 12 years of construction for a tunnel. Current status not verified *(unverified)*. **Tram Johanneskirchen:** a Bürgerversammlung recommendation to stop it was discussed on 10 Feb 2026 *(unverified)*. |
| **Messestadt Riem, 5th Bauabschnitt (Wohnen)** | 15 Trudering-Riem | About **2,500 homes** on about 0.25 km² north of the München–Rosenheim railway, between Kirchtrudering and Messestadt. Messestadt as a whole has 16,000 residents and 10,000 jobs today. *(verified)* | Competition decided July 2022. The revised design by 03 Arch. was selected after May 2023. Bebauungsplan in progress. Teil 2 cites the completion of Messestadt Riem plus Heltauer Straße, Rappenweg and infill on Wasserburger Landstraße as the reason for district 15's +42.5 %. *(verified)* | Existing U2 (Messestadt West / Ost). U4 option to Messestadt via the Nordosten *(verified as an option only)*. |
| **Quartier an der Lerchenauer Straße** ("Lerchenauer Feld") | 24 Feldmoching-Hasenbergl | **About 1,700 homes, nearly 4,000 residents**, on about 0.25 km². About 500 affordable homes on city-owned land. *(verified)* | Bebauungsplan Nr. 2138 is in force (Rechtskraft). *(verified)* | **Tram Lerchenauer Feld** (also called "Tram Y-Nord"): Hauptbahnhof – Hochschule München – Nordbad – Petuelring – Schleißheimer Straße, with an end stop at the quarter's market square. The Mobilitätsreferat says it "zu einem späteren Zeitpunkt realisiert werden wird" (will be built later). *(verified)* No date. |
| **Eggarten-Siedlung** | 24 Feldmoching-Hasenbergl and 10 Moosach | **About 1,900 homes for more than 4,500 residents**, on about 0.21 km². *(verified)* | Bebauungsplan Nr. 2143, Billigungsbeschluss (draft approval) stage. *(verified)* | Bus routes in the plan. No dedicated rail link found. |
| **Münchner Norden** (SEM Nord study area, Feldmoching-Ludwigsfeld) | 24 Feldmoching-Hasenbergl | **No housing target.** The city says "Den Planungsteams werden keine Zielzahlen … vorgegeben" (no target numbers given to the planning teams). Study area about 9 km², of which only about 2.2 km² is considered developable. *(verified)* | Preliminary studies (*vorbereitende Untersuchungen*) for a possible SEM were decided in 2020. A formal SEM would need a separate Entwicklungssatzung (development bylaw). Press reports say the SEM was dropped in favour of a "kooperatives Stadtentwicklungsmodell" (KOSMO) *(unverified, Abendzeitung)*. Not a firm input to the 2045 forecast. | Planning sketches only: extension of U1 (from OEZ) or U2 (from Feldmoching), Tram Y-Nord/Lerchenauer Feld, new S1 station Feldmoching Nord. "Ohne neue leistungsfähige ÖPNV-Trassen ist kein Wohnungsbau möglich" (no housing without new high-capacity transit). *(verified)* |
| **PaketPost-Areal** | 9 Neuhausen-Nymphenburg | **1,180 homes, 3,050 new jobs**, on 0.087 km². *(verified)* | Satzungsbeschluss (bylaw adopted) Nov 2025. Bebauungsplan in force since 30 Jun 2026. *(verified)* | Next to Friedenheimer Brücke (S-Bahn trunk line, Tram 16/17 corridor) *(transport link not stated on the page, unverified)*. |
| **Prinz-Eugen-Park** | 13 Bogenhausen | About 1,800 homes, nearly 600 of them in the timber-built Ökologische Mustersiedlung. *(verified)* | **Complete:** first homes 2019, last building 2021. Already in the 2024 and 2025 counts and part of Bogenhausen's +11.2 % from 2015 to 2025. *(verified)* | n/a |
| **Neuperlach** | 16 Ramersdorf-Perlach | Teil 2 puts district 16 in the 5,001–10,000 new-homes band and forecasts +15,136 residents. I did not verify individual Neuperlach projects. | *(unverified)* | *(unverified)* |

---

#### 4. Caveats

1. **Forecast vintage.** The current official forecast is the **Planungsprognose 2025–2045**, base 31 Dec 2024, editorial deadline May 2025, presented on 4 June 2025. It replaces the **Planungsprognose 2023–2040** (Demografiebericht 2023, base end 2022). The new forecast grows more slowly: +0.63 % a year against +0.73 % a year in the 2023–2040 edition (Teil 1, printed page 6–7). Do not mix district figures from the two editions. I did not extract the 2023–2040 district table.
2. **Target year mismatch with jobs.** Our jobs forecast is for **2040** (Erwerbstätigenprognose 2025, empirica 2024). The population forecast publishes per-district numbers for **2045 only**. Per-district 2040 values exist only as line charts on each district page ("Bevölkerungsentwicklung, Prognose ab 2025"), not as numbers. Reading them off the charts would be guessing, so I did not do it. The city total for 2040 is given as a number: **1.771 million** (Teil 1, chart of forecast years, PDF and printed page 8). If a 2040 district value is needed, interpolating linearly between 2024 and 2045 is a modelling assumption, not a source value.
3. **Scenarios.** The Planungsprognose is the most likely path. Teil 1 also gives a lower and an upper migration scenario, at +0.23 % and +1.03 % a year, and a low-fertility scenario at +0.55 % a year. In the low-fertility scenario the city stays under 1.8 million in 2045. Scenarios are only published for the city as a whole, not per district.
4. **Housing assumptions are a snapshot.** Teil 2 calls the housing numbers it uses a *Momentaufnahme* (a snapshot). Delays, cancelled plans, building costs and interest rates can shift growth in time. The forecast counts only new-build projects of more than 50 homes with new building rights. Growth in districts 13, 22, 15 and 24 depends most on these projects being delivered.
5. **Definition: Hauptwohnsitz.** All counts and forecasts here are **Hauptwohnsitzbevölkerung** (main residence only) from the municipal Melderegister. They exclude about 29,000 people with only a secondary residence in Munich: 29,052 at end 2024 (Teil 1) and 28,874 at end 2025 (city page). They also differ from the Zensus 2022 / Bavarian State Office (LfStat) official population, which is lower after the census correction. Our `DISTRICTS.population` snapshot should be checked for which definition and reference date it uses before it is compared with these figures.
6. **Rounding and consistency.** The 25 district 2045 values sum to 1,829,522, against 1,829,520 printed for the city, a rounding difference of 2. The text rounds totals ("1,83 Mio.", "rund 226.000"). The exact difference from the table is +225,744. Counts for 2015 and 2024 in the open-data CSV match Teil 2 exactly. The forecast's first year (2025: 1.613 million) is close to the actual end-2025 count (1,612,429).
7. **District 22 name.** Teil 2 and the open data use "Aubing-Lochhausen-Langwied". The city's prognosis web page writes "Aubing-Lochhausen-Langwied-Freiham". I did not verify whether the district has been formally renamed. The district boundaries are the same either way.
8. **Development areas versus district forecast.** The project figures in section 3 are planned capacities, often given as "up to". They are not additions to the 2045 forecast. The forecast already includes those projects it expects to be occupied by 2045. The Nordosten (30,000) and Münchner Norden figures are largely beyond 2045 or uncertain.
9. **Transport timing.** Opening dates for U5 Freiham, U4 Nordost, Tram Lerchenauer Feld and the S8 tunnel are not confirmed in any official source I could open. Only the Tram Münchner Norden has a verified construction start (October 2025).
10. **Not checked:** the Statistisches Taschenbuch/Jahrbuch population-by-district tables. They were not needed because the open-data series and Teil 2 agree exactly.

---

#### 5. Sources

**Verified (opened or downloaded):**
- Demografiebericht München – Teil 2, Kleinräumige Bevölkerungsprognose 2025 bis 2045 für die Stadtbezirke (LHM, Referat für Stadtplanung und Bauordnung, editorial deadline May 2025). PDF, 86 pages. Abbildung 1 on printed page 6; text on printed pages 15–17; Karte 3 on printed page 17; district pages on printed pages 30–79 (tables "Kennzahlen" and age groups with row "Bezirk gesamt"); city total on printed pages 80–81. https://stadt.muenchen.de/dam/jcr:b6129a79-a189-4aea-afc1-d7b206b8d544/LHM_Demografie-Bericht-Teil-2_2024_web.pdf
- Demografiebericht München – Teil 1, Analyse 2024 und Bevölkerungsprognose 2025 bis 2045 (LHM 2025). Scenarios on printed page 6–7; forecast series by year on page 8. https://stadt.muenchen.de/dam/jcr:a520e26a-2650-469e-9cc0-837cebc2807b/2025-07-16_DemografieberichtTeil1A2025_Web.pdf
- City page "Bevölkerungsprognose" (base end 2024, 1.830 million in 2045, 1,612,429 at end 2025, 28,874 secondary residences). https://stadt.muenchen.de/infos/bevoelkerungsprognose.html
- Münchner Statistik, 3. Quartalsheft 2026, article on births. It confirms the forecast's publication on 4 June 2025 and the end-2025 count. https://stadt.muenchen.de/dam/jcr:7544d2e6-9b4d-4e02-9b62-3690b0503848/mb260302.pdf
- Open data: Indikatorenatlas Bevölkerung – Bevölkerungsanteil, CSV 2000–2025, updated 22 May 2026. Dataset: https://opendata.muenchen.de/dataset/indikatorenatlas-bevoelkerung-bevolkerungsanteil · CSV: https://opendata.muenchen.de/dataset/3cc5ae0f-f4ff-480e-8428-9aeaec4ed23d/resource/d0b78781-dbf9-473b-a2ba-6a3b76ae35d4/download/indikat_2605bevoelkerung_bevoelkerungsanteil_18_05_26.csv
- Freiham (Stadtplanung): https://stadt.muenchen.de/infos/neuer-stadtteil-freiham.html
- Freiham (Baureferat): https://stadt.muenchen.de/infos/baureferat-freiham.html
- Rathaus Umschau 2026/112, "U5-Baustelle Laim: Durchstich im Tunnel erreicht": https://ru.muenchen.de/2026/112/U5-Baustelle-Laim-Durchstich-im-Tunnel-erreicht-124721
- Neufreimann: https://stadt.muenchen.de/infos/neufreimann.html
- Mobilitätsreferat letter of 24 Jul 2026 on ÖDP motion 20-26 / A 04724 (Tram Münchner Norden: PFA 1/2, groundbreaking Oct 2025, BCR 2.61, Trassierungsbeschluss 23 Jul 2025, Tram Lerchenauer Feld later): https://risi.muenchen.de/risi/dokument/v/9847142
- Mobilitätsreferat letter of 6 Oct 2025 on BV query 20-26 / Q 00686 (same facts): https://risi.muenchen.de/risi/dokument/v/9355507
- Zukunftsquartier Münchner Nordosten: https://stadt.muenchen.de/infos/zukunftsquartier-muenchner-nordosten.html
- Münchner Norden (preliminary studies): https://stadt.muenchen.de/infos/muenchnernorden.html
- Messestadt Riem (5th Bauabschnitt): https://stadt.muenchen.de/infos/messestadt-riem.html
- Quartier an der Lerchenauer Straße: https://stadt.muenchen.de/infos/lerchenauerstrasse.html
- Eggarten: https://stadt.muenchen.de/infos/eggarten.html
- PaketPost-Areal: https://stadt.muenchen.de/infos/paketpost-areal.html
- Prinz-Eugen-Park: https://stadt.muenchen.de/infos/prinz-eugen-park.html

**Unverified (search results only, or the page did not load):**
- SWM/MVG press release of 23 Jul 2025, Tram Münchner Norden Trassierungsbeschluss ("Ende 2029", 4.5 years construction). It returned 404 when opened. https://www.swm.de/unternehmen/presse/pressemitteilungen/2025/07-2025/mvg-tram-muenchner-norden-trassierungsbeschluss
- MVG project site Tram Münchner Norden (JS-rendered, no dates readable): https://tram-muenchner-norden.mvg.de/
- Abendzeitung, SEM Nord dropped / KOSMO: https://www.abendzeitung-muenchen.de/inhalt.umstrittene-sem-stadtentwicklung-im-norden-enteignungen-sind-vom-tisch.c40c4eb5-1342-4058-b600-ab51f494b685.html
- S8 Daglfing–Johanneskirchen tunnel, council documents and press (construction start 2031, 12 years for a tunnel): https://risi.muenchen.de/risi/dokument/v/7879934 · https://www.abendzeitung-muenchen.de/muenchen/flughafenlinie-s8-jetzt-kommt-der-tunnel-art-344311
- Tram Johanneskirchen, BA 13 recommendation of 10 Feb 2026: https://www.muenchen-transparent.de/dokumente/9490929/datei
- U5 Pasing opening estimates (about 2030–2035): https://www.u-bahn-muenchen.de/netz/u5/ · https://www.tramreport.de/2025/06/06/u-bahnhof-baumschule-laim-gestaltung-vorgestellt/
- The 2023–2040 edition, Demografiebericht Teil 2 2023–2040 (not extracted): https://muenchen-transparent.de/dokumente/7822058/datei (download failed because of a TLS certificate error)

### Findings file: plans-facts.md

### Munich mobility projects and proposals: facts (as of 15 Oct 2026)

This file lists what the sources say, without assessment. The research was done in German. Items marked **(unverified)** were seen only in search results, not on the source page. Where sources disagree, both versions are given.

Coverage note: BR, SZ, tz and Merkur block the research tool. Their reporting appears only where the ADFC München media reviews quote it.

---

#### 1. Political and budget frame

| Fact | Source |
|---|---|
| Dominik Krause (Grüne) beat Dieter Reiter (SPD) in the runoff on 22 Mar 2026 (56.3 % to 43.7 %) and has been Oberbürgermeister since 1 May 2026 **(unverified figures)** | https://stadt.muenchen.de/dam/jcr:716b63a5-a5b7-4a0b-b05f-14274622c288/obwsti_2026_amtlich_Kurzanalyse.pdf |
| The coalition is Grüne/Rosa Liste, SPD and FDP/Freie Wähler, with an agreement for 2026–2032 dated 8 May 2026 | https://www.fdp-muenchen.de/sites/default/files/2026-05/260508_Koalitionsvertrag_Muenchen.pdf |
| Agreement: at least €0.5 bn a year of permanent consolidation within 3 years. Interest and repayment rise from €397 m to more than €742 m a year by 2029 | same |
| Agreement: "Wir bauen die Tram Westtangente sowie die Tram Münchner Norden." Tram Johanneskirchen only with funding commitments. U-Bahn only with "umfassende frühzeitige Förderzusagen von Bund und Freistaat" | same; https://www.tramreport.de/2026/05/08/koalitionsvertrag-2026-2032/ |
| Agreement: keeps the Radentscheid and Altstadt-Radlring goals "grundsätzlich", with priority on cheap, fast and temporary measures | same |
| Agreement: sets up a Baustellenfonds and redesigns streets during planned roadworks instead of only restoring them | same |
| VCD criticised the agreement for naming no concrete cycling measures and no Altstadt-Radlring timetable (3 Jun 2026) | https://www.vcd-muenchen.de/presse-koalitionsvertrag/ |
| SWM financing contract (Finanzbeziehungsvertrag, council 17 Dec 2025): SWM new-build projects go beyond the approval-planning stage only once there is a binding Bund/Land funding commitment | https://www.tramreport.de/2026/09/18/finanzierungsregelung-baustopp-tmn/ |
| ÖPNV-Bauprogramm consolidation, full council 30 Jul 2025: the feasibility studies "Tram Parkstadt Solln" and "Tram Amalienburgstraße – Freiham" were deleted. The investment frame of all three programmes is €1,197.9 m | https://www.muenchen-transparent.de/dokumente/9214100/datei |
| ÖPNV-Bauprogramm, 28 Jan 2025: cut by about €118 m for 2025–27; Tram Daglfing pushed to 2028 at the earliest | https://muenchenunterwegs.de/news/oepnv-bauprogramm-beschlossen |
| Savings package, Jul 2026: short-term parking €2.00 → €2.60 an hour; resident parking permit up to €300 a year proposed (single source) | https://parkeninmuenchen.de/parken-in-munchen-wird-teurer-wegen-haushaltskrise-2026/ |
| On 26 Sep 2026 the DOSB chose Munich as the German Olympia bid city | https://www.muenchen.de/aktuell/dosb-vergibt-nationale-olympiabewerbung-muenchen |

#### 2. Public transport

##### 2a. In operation or under construction

| Project | Status | Dates | Facts | Sources |
|---|---|---|---|---|
| Tram-Westtangente (tram 14), Romanplatz–Aidenbachstraße, 8.3 km, 17 stops | Section 1 open; section 2 approved | Pasing–Gondrellplatz opened 28 Feb 2026. Section 2 (Waldfriedhof–Aidenbachstr.) plan approval Aug 2026; preparatory works Oct 2026, drainage Jan 2027, tracks Jul 2027; completion "weiterhin Ende 2028" | Cost €497.6 m. Council paper V 18994: without a city funding exemption, section 2 slips to end 2030 / early 2031 and costs +€32.6 m. Council 30 Sep 2026: the P+R Aidenbachstraße is kept and refurbished | https://www.muenchen.de/verkehr/aktuell/neue-tram-linie-14-westtangente-zwischen-pasing-gondrellplatz · https://www.swm.de/unternehmen/presse/pressemitteilungen/2026/08-2026/mvg-planfeststellung-twt · https://www.swm.de/unternehmen/presse/pressemitteilungen/2026/09-2026/mvg-beschluesse-tramneubaustrecken · https://www.muenchen-transparent.de/dokumente/9518781/datei |
| Tram Münchner Norden (tram 23 to Kieferngarten, later line 24 to Am Hart) | Under construction | Groundbreaking Oct 2025; council released construction past the DB-Nordring bridge on 30 Sep 2026; Kieferngarten "Ende 2031" | Kieferngarten P+R demolished May 2026 | https://www.swm.de/unternehmen/presse/pressemitteilungen/2026/09-2026/mvg-beschluesse-tramneubaustrecken |
| Tram 12 extension Scheidplatz–Parzivalstraße–Schwabing Nord | In operation | Since 1 Jan 2025 | About 4,500 riders a day after 100 days. Tram 23 peak service reduced to every 10 minutes from 3 Aug 2026 | https://www.swm.de/unternehmen/presse/pressemitteilungen/2025/04-2025/mvg-tramlinie-12-verlaengerung-resonanz-bilanz |
| U5 extension Laimer Platz–Pasing (later Freiham) | Under construction | Pasing opening 2036. Tunnel breakthrough Laimer Platz–Baumschule Laim (1.1 km) on 18 Jun 2026, "im Plan" | About €1.3 bn, 3.8 km. Freiham: only a shell structure approved (Dec 2023, €94.1 m) | https://www.abendzeitung-muenchen.de/muenchen/u5-verlaengerung-licht-im-u-bahn-tunnel-art-1138356 |
| 2. S-Bahn-Stammstrecke | Under construction | Commissioning 2035–2037. The first tunnel boring machine, "Donna Maria", started on 17 Sep 2026; the main tunnel machines start from 2028 | DB cost forecast over €11 bn (Apr 2025). Hbf interim building in use from mid-2027 for about 10 years. At Laim, inbound S3/S4/S6/S8 do not stop from 25 Aug 2026 to mid-2028 | https://www.deutschebahn.com/de/presse/presse-regional/pr-muenchen-de/aktuell/presseinformationen/Donna-Maria-startet-Erster-maschineller-Tunnelvortrieb-der-2-Stammstrecke-beginnt--14037354 · https://www.2.stammstrecke-muenchen.de/ |
| U6 Martinsried | Under construction (Freistaat) | Planned 2027 (as of 2023) **(unverified)** | — | — |
| Trambetriebshof Ständlerstraße with its access track | Planning / construction | Plan documents submitted end 2024; junction works mid-2026 to mid-2027 | Funding split with SWM still being negotiated | https://muenchen-transparent.de/dokumente/8871200/datei |

##### 2b. Timetable 2027 (Anpassungsprogramm), decided 29 Jul 2026, effective 13 Dec 2026

| Change | Source |
|---|---|
| CityRing 58/68 abolished; new line 100 (Ostbahnhof–Hbf–Silberhornstraße, every 20 minutes) and line 101 | https://risi.muenchen.de/risi/dokument/v/9853476 · https://www.muenchen-transparent.de/dokumente/9813547/datei |
| Line 52 rerouted Marienplatz–Au–Tierpark | same |
| Line 153 shortened to Trappentreustraße–Stachus; Trappentreustraße–Giesing Bf served by 53, 54, 64 and 133 | same |
| X30 becomes line 64, stopping at all stops: Lorettoplatz–Harras–Giesing–Arabellapark, every 5 minutes in the school-day peak between Harras and Ostbahnhof | same; https://www.swm.de/unternehmen/presse/pressemitteilungen/2026/08-2026/mvg-klarstellung-x30 |
| New line 133 Harras–Theresienhöhe (rush hour, school days) | same |
| U7 runs only in peaks and outside school holidays. Tram 25 runs every 10 instead of 5 minutes between 09:00 and 13:00. Lines 174 and 179 abolished. About 20 lines go to 20-minute intervals | same; https://muenchen.t-online.de/region/muenchen/id_101367130/neuer-fahrplan-mvg-muenchen-streicht-buslinien-und-kuerzt-takte-ab-dezember.html |
| Tram 20 every 5 minutes in peaks (from 1 Oct 2026) | https://www.swm.de/unternehmen/presse/pressemitteilungen/2026/07-2026/mvg-fahrplan-2027-stadtrat-vollversammlung-zustimmung |
| The programme saves €14 m a year | https://www.tramreport.de/2026/06/02/mvg-fahrplan-2027/ |
| City co-funding of regional buses: **conflicting sources**. One says co-funding of X204/X206 continues and X208 ends; the other reads council paper V 00776 as ending co-funding of X204/X206/X208 from the Dec 2028 timetable | https://www.muenchen-transparent.de/dokumente/9813547/datei |

##### 2c. In planning, on hold or blocked

| Project | Status | Facts | Sources |
|---|---|---|---|
| U9-Spange (Münchner Freiheit–Elisabethplatz–Pinakotheken–Hbf–Esperantoplatz–Implerstraße) | Preliminary planning; not financed | €100 m for preliminary planning (2019). Hbf shell structure being built with the Stammstrecke (about €662 m). Cost estimates €3.5–4 bn. Grüne motion of 29 Jan 2026 asks to build it in stages, starting with Theresienstraße–Hbf–Implerstraße. Not named in the coalition agreement | https://www.muenchen-transparent.de/dokumente/9530505/datei · https://www.muenchen-transparent.de/dokumente/9069774/datei · https://de.wikipedia.org/wiki/U9-Spange_(U-Bahn_M%C3%BCnchen) |
| Tram Y-Nord (Hbf–Hochschule München–Nordbad–Petuelring–Schleißheimer Straße) | In planning, on hold | A Grüne/SPD amendment (2025) asked to exempt it from cuts; the full council decision records the officials' original proposal. The system comparison of tram against U-Bahn was not finished in Feb 2026 | https://www.muenchen-transparent.de/dokumente/9212594/datei · https://www.muenchen-transparent.de/dokumente/9214100/datei · https://www.muenchen-transparent.de/dokumente/9550336/datei |
| Tram-Nordtangente through the Englischer Garten (Elisabethplatz–Tivoli) | Blocked | Route decision Dec 2023. The Freistaat refused in Mar and Jul 2024; SWM stopped planning. Tunnel study presented 22 Jan 2026: about €240 m, 400 m tunnel, 578 trees felled. Reported tree counts range from 19 to 900 by variant. Not in the coalition agreement | https://www.abendzeitung-muenchen.de/muenchen/fuer-240-millionen-euro-muenchner-doppelwumms-fuer-den-englischen-garten-art-1107368 · https://www.muenchen-transparent.de/dokumente/9262805/datei |
| S-Bahn-Nordring | Shuttle stage in preliminary planning; ring under study | Shuttle Karlsfeld/Moosach–BMW FIZ every 20 minutes in peaks. The council asked for operation before 2029; there is no binding date | https://www.muenchen-transparent.de/dokumente/9252439/datei |
| Tram Johanneskirchen | In plan approval | Coalition: only with funding commitments | https://www.muenchen-transparent.de/dokumente/9490929/datei |

#### 3. Cycling

##### 3a. Citywide

| Item | Facts | Sources |
|---|---|---|
| Radentscheid (adopted by the council 24 Jul 2019) | More than 50 streets "umgesetzt, im Bau oder geplant". The 2025 target was missed (Dunkel, Jan 2024) | https://stadt.muenchen.de/infos/radentscheid.html · https://muenchenunterwegs.de/radentscheid/massnahmen/ |
| Altstadt-Radlring progress | **Conflicting:** the Radentscheid site says 3.2 of 10.2 km in its header and about 1.3 of 10.3 km in its text; it forecasts completion in 2041 or 2046 | https://www.radentscheidmuenchen.de/woistunseraltstadtradlring/ |
| Radverkehrsnetz IR III (connections across district borders) | Adopted in the Mobilitätsausschuss 23 Sep 2026; minimum 2.5 m width for one-way paths; remaining connections to the council in 2027 | https://ru.muenchen.de/2026/182/Stadtrat-beschliesst-neue-Radverkehrsverbindungen-126187 · https://risi.muenchen.de/risi/dokument/v/9970573 |
| Fahrradstraßen | 104 streets, about 47 km (Dec 2025); the 100th was Wilramstraße, 7 Oct 2025 | https://www.abendzeitung-muenchen.de/muenchen/radl-hauptstadt-muenchen-so-lief-der-radwegausbau-im-jahr-2025-art-1102588 |
| Radschnellverbindung München–Garching/Unterschleißheim | Lenbachplatz–Platz der Opfer done Dec 2024; Ludwigstraße/Leopoldstraße section "völlig offen" (AZ, 30 Dec 2025); in the Landkreis, section 4.2 (+3.4 km) done end Jul 2026 | https://stadt.muenchen.de/infos/radschnellweg-muenchner-norden.html?lang=de · https://www.landkreis-muenchen.de/themen/mobilitaet/radverkehr/aktuelle-radprojekte/radschnellverbindungen/ |
| Radschnellverbindungen to Markt Schwaben, Fürstenfeldbruck, Starnberg, Oberhaching and Dachau | Munich routes defined; no timing. AZ, 7 Oct 2026: the regional cycle highways "stocken" | https://stadt.muenchen.de/infos/radschnellverbindungen.html · https://muenchenunterwegs.de/angebote/fuenf-radschnellverbindungen-von-muenchen-in-das-umland |

##### 3b. Street projects by district

| District | Project | Status | Facts | Sources |
|---|---|---|---|---|
| Au-Haidhausen | Radweg Gebsattelberg | Decided 22 Jul 2026 | 2.30 m uphill path plus 0.80 m buffer; built after the SWM Fernwärme works, probably 2027 | https://ru.muenchen.de/2026/137/Stadtrat-beschliesst-kostenguenstigen-Radweg-am-Gebsattelberg-125370 |
| Au-Haidhausen | Rosenheimer Straße / Rosenheimer Platz | Deferred | 0.5 km Radentscheid measure; the rebuild is "aufgrund der angespannten Haushaltslage … langfristig" (17 Sep 2025); Grüne motion of 19 Dec 2025 for an outbound lane | https://muenchenunterwegs.de/radentscheid/massnahmen/rosenheimer-strasse |
| Au-Haidhausen | Franziskanerstraße | Under construction | Renewal of paths damaged by tree roots | — |
| Schwabing-West | Karl-Theodor-Straße | Under construction | Protected paths 2.30–2.75 m; 4 lanes to 2; €9.5 m city plus €2 m federal; section 2 from May 2026 to about end May 2027 | https://www.muenchen-transparent.de/dokumente/9839852/datei |
| Schwabing-West | Schleißheimer Str. north of Hohenzollernstr. | Motion | Grüne motion 19 Dec 2025: build protected paths during the 2026 track and Fernwärme works | https://www.muenchen-transparent.de/dokumente/9478485/datei |
| Schwabing-West | Belgradstraße redesign; Hohenzollernstraße as a cycle street | Motions | Grüne motions in district council 4 (BA 4), 25 Jun 2026 | https://risi.muenchen.de/risi/dokument/v/9945595 · https://risi.muenchen.de/risi/dokument/v/9798211 |
| Schwabing-West | Lerchenauer / Schleißheimer crossing | Small fix only | Larger rebuild "aufgrund der aktuellen Haushaltslage nicht umsetzbar" (BA 4, 29 Oct 2025) | — |
| Schwabing-West / Maxvorstadt | Winzererstraße (0.4 km), Lothstraße (0.7 km) | Decided in principle Mar 2020 | Paths move from the footway to the road; no construction date | https://muenchenunterwegs.de/radentscheid/massnahmen/winzererstrasse · https://muenchenunterwegs.de/radentscheid/massnahmen/lothstrasse |
| Ludwigsvorstadt-Isarvorstadt | Lindwurmstraße | Section 1 done Sep 2025; section 2 decided | Cost reduced from €38 m to €17 m. Section 2 (Goetheplatz–Aberlestraße) waits for the Goetheplatz/Poccistraße U-Bahn renovation. On 21 Jul 2026, 170 m was temporarily given to replacement buses | https://muenchenunterwegs.de/radentscheid/massnahmen/lindwurmstrasse · https://www.abendzeitung-muenchen.de/muenchen/lindwurmstrasse-in-muenchen-verschwinden-die-radwege-wieder-art-1145658 |
| Ludwigsvorstadt-Isarvorstadt | Schwanthalerstraße (Sonnenstr.–Paul-Heyse-Str.) | Decided 19 Feb 2025 | Protected lanes, €2–3 m; no start date (BA 2, 16 Jun 2026) | https://muenchenunterwegs.de/radentscheid/massnahmen/schwanthalerstrasse |
| Ludwigsvorstadt-Isarvorstadt | Paul-Heyse-Str.; Reichenbachbrücke (0.2 km); Implerstr.–Thalkirchner Str. (1.3 km) | In planning | No dates | https://muenchenunterwegs.de/radentscheid/massnahmen/paul-heyse-strasse · https://muenchenunterwegs.de/radentscheid/massnahmen/reichenbachbruecke · https://muenchenunterwegs.de/radentscheid/massnahmen/implerstrasse-thalkirchner-strasse |
| Ludwigsvorstadt-Isarvorstadt | Stachus / Sonnenstraße crossing | Done Dec 2025 | Space for walking and cycling nearly doubled | — |
| Ludwigsvorstadt / Lehel | Erhardtstr.–Steinsdorfstr.–Widenmayerstr. (2.1 km) | In planning | Existing two-way path is non-compliant (2.0 m at Ludwigsbrücke); about 4,000 bikes a day on average, with peaks around 12,000 | https://muenchenunterwegs.de/radentscheid/massnahmen/erhardtstrasse-steinsdorfstrasse-widenmayerstrasse |
| Schwanthalerhöhe | Fahrradstraße Bergmannstraße | Decided / ordered | Links the Edith-Haberland-Wagner-Brücke to the future cycle highway in Westendstraße (BA 8, 7 Jul 2026) | https://www.muenchen-transparent.de/dokumente/9728520/datei |
| Schwanthalerhöhe | Landsberger Str. – Bayerstr. (1.1 km) | Decided in principle Sep 2020 | Removes a traffic lane; no construction date | https://muenchenunterwegs.de/radentscheid/massnahmen/landsberger-strasse-bayerstrasse |
| Schwanthalerhöhe | Nachbarschaftsviertel Westend | Concept | Council decision 17 Jul 2024; first quarter with construction measures | https://www.muenchen-transparent.de/dokumente/9490158/datei |
| Laim / Neuhausen | Cycle and foot bridge at Pronnerplatz; Fahrradstraße Von-der-Pfordten-Straße | Being checked | 10 m corridor reserved; the 2003 feasibility study needs an update | https://www.abendzeitung-muenchen.de/muenchen/radl-antragspaket-gruen-rot-will-neue-radbruecke-von-nymphenburg-nach-laim-art-817886 (unverified) |
| Maxvorstadt | Elisenstraße (0.5 km, both sides) | Decided 4 Oct 2023 | No construction date | https://muenchenunterwegs.de/radentscheid/massnahmen/elisenstrasse |
| Maxvorstadt | Augustenstraße | Under construction Jan 2026–2028 | €7 m; the cycle path is removed and Tempo 20 introduced | — |
| Maxvorstadt / Neuhausen | Nymphenburger Straße (1.7 km), Stiglmaierplatz, Marsstraße | In planning | Fifth Radentscheid package, Dec 2022 | https://muenchenunterwegs.de/radentscheid/massnahmen/nymphenburger-strasse · https://muenchenunterwegs.de/radentscheid/massnahmen/stiglmaierplatz |
| Maxvorstadt / Altstadt | Neugestaltung Ludwigstraße | Competition decided 4 May 2026 | Up to 6 lanes reduced to 2 between Brienner Str. and Oskar-von-Miller-Ring | https://stadt.muenchen.de/infos/neugestaltung-ludwigstrasse.html |
| Obergiesing-Fasangarten | Giesinger Berg | Under construction since Mar 2026 | 2 m raised paths both ways; done end 2026, about €600k **(unverified)** | https://muenchenunterwegs.de/radentscheid/massnahmen/giesinger-berg-martin-luther-strasse |
| Obergiesing-Fasangarten | Martin-Luther-Straße | Decided 22 Apr 2026 | Permanent solution replaces the trial lanes in place since Oct 2023 | same |
| Olympiapark | Five bridges | Reopened to bikes about end Jun 2026 | Dismount signs since 24 Mar 2026 because the railings were too low; no permanent fix scheduled | https://www.abendzeitung-muenchen.de/muenchen/ploetzlich-verboten-darum-duerfen-radler-im-muenchner-olympiapark-nicht-mehr-ueber-bruecken-fahren-art-1137345 |

#### 4. Roadworks and coordination

| Zone / item | Facts | Sources |
|---|---|---|
| Frankfurter Ring | SWM utility line work; at least one lane open each way; city end date "bis voraussichtlich Juni 2027". ADAC (18 Aug 2026) criticised coordination with the Föhringer Ring work (narrowings until 2031) | https://stadt.muenchen.de/infos/baustellen-verkehrseinschraenkungen · https://www.adac.de/der-adac/regionalclubs/suedbayern/news/muenchens-verkehrsnetz-am-limit-baustellen-2026/ |
| Weichendreieck Nordbad | MVG switch renewal 9 Mar–31 May 2026, plus Fernwärme on Hohenzollernstraße and barrier-free stops on tram 27; diversions for trams 12/27 and buses 53/59/154 | https://www.swm.de/unternehmen/presse/pressemitteilungen/2026/03-2026/mvg-tram-12-27-n27-weichenerneuerung-nordbad |
| Stiglmaierplatz | Urgent switch work 21–22 Oct 2026; replacement bus for N20 | https://www.mvg.de/verbindungen/trambau/2026-10-21-weiche-stiglmaierplatz.html |
| Mariahilfplatz | Baureferat footway and tree-site work, end moved from 30 Sep to 30 Nov 2026; SWM Fernwärme diverted bus 52 until 4 Sep 2026 | https://stadt.muenchen.de/news/baustelleninfo-mariahilfplatz.html |
| Au/Giesing | Mobilitätsreferat (6 May 2026): "eine Vielzahl an notwendigen Großprojekten"; some 2026 projects cut or postponed | https://risi.muenchen.de/risi/dokument/v/9703609 |
| Odeonsplatz / U4 | U4 cut Max-Weber-Platz–Odeonsplatz, 5 Oct to about 27 Nov 2026; the suggested alternative is trams 16/17 | https://www.swm.de/unternehmen/presse/pressemitteilungen/2026/09-2026/sanierung-u4-u5-u8 |
| U3/U6 Poccistraße/Goetheplatz | Phase 2: 5 Oct–27 Nov 2026; winter break; phase 3: 12 Apr–1 Aug 2027 | https://www.swm.de/unternehmen/presse/pressemitteilungen/2026/10-2026/mvg-start-u-bahn-sev |
| Sonnenstraße switches | 6–31 Jul 2026; trams 16/17/18/27/28 split | https://www.swm.de/unternehmen/presse/pressemitteilungen/2026/06-2026/mvg-neue-weichen-tram-sonnenstrasse |
| Current tram construction | Tram 25 (Reger-/Franziskanerstr.) to about 22 Nov 2026; Kreillerstraße (tram 21) 27 Oct–18 Nov 2026; Haidenauplatz nights of 13–14 Oct 2026 | https://www.mvg.de/trambau |
| SWM Fernwärme conversion | Steam to hot water inside the Mittlerer Ring: since 2021 in Berg am Laim/Ramersdorf, Haidhausen and Au; from 2030 in parts of Schwabing-Freimann, Schwabing-West and Maxvorstadt | https://www.swm.de/geschaeftskunden/fernwaerme/modernisierung-netz |
| Building-site management (Dunkel, 7 Apr 2026) | Set up in 2022. About 65 % of permits are private works, outside coordination. Data "zum Großteil noch analog". Digitised temporary traffic orders expected 2028 | https://www.muenchen-transparent.de/dokumente/9641968/datei |
| Hackerbrücke | AZ, Jul 2026: the city admitted planning errors; the site is rebuilt in Oct 2026; CSU question with 12 points (16 Jul 2026). Renovation Mar 2027–Aug 2030 | https://www.abendzeitung-muenchen.de/muenchen/baustellen-aerger-an-der-hackerbruecke-csu-hat-fragen-art-1144489 |
| No information found | Rosenheimer Str. 145, Görresstr. 36–40, Winzererstr. 68, Elsenheimerstr. 50 (2026), Nymphenburger Str. 1/12 end dates | — |

#### 5. Proposals under discussion (not decided or funded)

| Proposal | Proposer / stage | Facts | Sources |
|---|---|---|---|
| Nahverkehrsumlage (employer transit levy) + Land funding share back to 15 % | Grüne/Rosa Liste/Volt motion package, 29 Jan 2026 | Needs a Bavarian law; the coalition "fordert rechtliche Voraussetzungen" | https://www.muenchen-transparent.de/dokumente/9530781/datei |
| Bus lanes and bus priority at building sites | Grüne motion, 29 Jan 2026 **(unverified)** | — | https://www.muenchen-transparent.de/dokumente/9530718/datei |
| Funded IR III cycle programme from 2027 | ÖDP amendment, 19 Jul 2026 | Outcome unknown | https://risi.muenchen.de/risi/dokument/v/9970573 |
| Tram-Cityring (Silberhornstr.–Goetheplatz–Hbf) | Pro Bahn, Nov 2025 | Listed in the Nahverkehrsplan as "in Untersuchung" | https://www.pro-bahn.de/oberbayern/pbp/pbp202511.pdf |
| Altstadt für alle, detail phases | Basic decision Nov/Dec 2025; motions 3 Feb 2026 (Rosental, Hackenviertel) | In the coalition agreement | — |
| Nachbarschaftsviertel Gärtnerplatz | Being checked after Westend | — | https://www.muenchen-transparent.de/dokumente/8836633/datei |
| Schulstraßen | Coalition: "sukzessive"; pilot at 2 schools from Q1 2026 (€65k) **(unverified)** | — | — |
| Car-free Hackerbrücke | Radentscheid campaign, 6 Dec 2025 | — | https://www.radentscheidmuenchen.de/aktuelles/ |
| Citymaut, cable car, maglev | No current debate found | — | — |

### Findings file: plans-research.md

### What Munich is doing about the gaps (as of 15 Oct 2026)

I compared the gaps found with SQL on `MUNICH_DATASET` (scheduled transport and cycle-path supply per district, roadworks near stops, the bike counters) with current city plans. The research was done in German across official sources and local media. One limit on coverage: BR, SZ, tz and Merkur block the research crawler. Their reporting is included only where the ADFC München media reviews (Radfahren in den Medien) carry it. The other media sources are Abendzeitung, t-online München, tramreport.de, VCD and Pro Bahn. Items marked (unverified) were seen only in search results, not on the source page.

#### Summary

- **Schwabing-West, the densest district with the weakest transport, gets no funded rail improvement.** U9 via Elisabethplatz, Tram Y-Nord via Nordbad and the Tram-Nordtangente through the Englischer Garten are all unfunded, on hold or blocked by the Freistaat. The concrete projects there are small: Karl-Theodor-Straße (protected cycle paths, under construction until about May 2027) and Belgradstraße stop upgrades.
- **Laim, Sendling-Westpark and Neuhausen are being addressed.** Tram-Westtangente: tram 14 has run since 28 Feb 2026, and Aidenbachstraße is due end 2028, with a risk of 2030/31 if the funding condition bites. U5 to Pasing is due 2036.
- **The December 2026 timetable cuts go the other way in the flagged inner districts.** From 13 Dec 2026 the CityRing 58/68 is abolished, line 153 is shortened and tram 25 runs less often off-peak. The new line 64 (Sendling–Giesing) and line 133 help Sendling and Obergiesing.
- **There will be more roadworks, not fewer.** The Fernwärme steam-to-hot-water conversion reaches Schwabing-West, Maxvorstadt and Schwabing-Freimann from 2030. The 2. Stammstrecke opens 2035–37 and costs over €11 bn; tunnel boring starts in 2028. About 65 % of building-site permits are private and cannot be forced into the city's coordination. The coalition's answers are a Baustellenfonds and "Baustellen nutzen" (redesign a street when it is dug up anyway).
- **Cycling: the dense districts with the least cycle path get mostly small and late projects.** Au-Haidhausen, the lowest per resident, gets Gebsattelberg in 2027, while Rosenheimer Platz is deferred for budget reasons. Ludwigsvorstadt-Isarvorstadt: Lindwurmstraße section 2 waits for the U-Bahn works at Poccistraße, which end Aug 2027. Schwanthalerstraße is decided but has no start date, and 170 m of Lindwurmstraße was temporarily given to replacement buses in Jul 2026. Erhardtstraße/Isar is the busiest counter and the most rain-sensitive, but it is still only in planning, with nothing weather-resilient.
- **Politics and money.** OB Krause (Grüne) has led since 1 May 2026, in a coalition of Grüne/Rosa Liste, SPD and FDP/FW (the "Mango-Koalition"). The coalition must save at least €0.5 bn a year. Under the SWM financing rule (Dec 2025), a project gets no planning beyond the approval stage without a Bund/Land funding commitment. The U-Bahn only goes ahead with early Bund/Freistaat funding commitments. The Olympia 2036 bid (DOSB nomination 26 Sep 2026) is the one political accelerator.

#### Gap by gap

| Gap (from our SQL) | Built / under construction | Decided | Under discussion only |
|---|---|---|---|
| Schwabing-West: 172 departures and 476 cycle-path m per 1,000 residents | Karl-Theodor-Str. cycle paths (to ~May 2027); tram 12 extension (2025, district edge) | — | U9 Elisabethplatz, Tram Y-Nord, Tram-Nordtangente, protected lanes on Schleißheimer Str., Belgradstr./Hohenzollernstr. |
| Sendling-Westpark: 153 departures | Tram-Westtangente section 1 | Section 2 to Aidenbachstr., end 2028 | — |
| Laim: 219 departures, 543 m | Tram 14 (Feb 2026); U5 tunnel | U5 Pasing 2036; Stammstrecke Laim station | Pronnerplatz cycle bridge, Von-der-Pfordten-Str. cycle street |
| Neuhausen-Nymphenburg: 202 departures | Tram-Westtangente (Romanplatz) | — | Tram Amalienburgstr.–Freiham **dropped** 2025 |
| Au-Haidhausen: 384 m (lowest) | Franziskanerstr. renewal | Gebsattelberg path (2027) | Rosenheimer Str./Platz (deferred), more cycle streets |
| Ludwigsvorstadt-Isarvorstadt: 485 m | Lindwurmstr. section 1 (Sep 2025), Stachus crossing | Lindwurmstr. section 2, Schwanthalerstr. (no date) | Paul-Heyse-Str., Tram-Cityring |
| Maxvorstadt: 567 m, high disruption | Augustenstr. (cycle path **removed**, Tempo 20) | Elisenstr. (no date); Ludwigstraße redesign (competition May 2026) | Stiglmaierplatz, Nymphenburger Str. |
| Schwanthalerhöhe: 493 m | — | Bergmannstr. cycle street | Westend Nachbarschaftsviertel (first one, 2027+) |
| Obergiesing-Fasangarten: 239 departures, 576 m | Giesinger Berg | Martin-Luther-Str. permanent; line 64 (Dec 2026) | — |
| Erhardtstr./Isar counter | — | — | Erhardt–Steinsdorf–Widenmayerstr. (planning only) |

#### Top disruption zones: what is behind them

| Zone | Work and owner | End date | Note |
|---|---|---|---|
| Frankfurter Ring 149 | SWM Leitungsbau, at least one lane each way | City says **June 2027**; our data says 30 Apr 2027 | ADAC criticises poor coordination with the Föhringer Ring work (to 2031) |
| Nordbad (Winzerer-/Schleißheimer Str.) | MVG switch renewal, 9 Mar–31 May 2026 (finished) | 2027 dates probably cover the Fernwärme and track work on Schleißheimer Str. (inference) | Grüne motion: build protected cycle lanes at the same time |
| Stiglmaierplatz / Nymphenburger Str. | Switch work 21–22 Oct 2026 (N20 replaced by buses); SWM gas and 110 kV lines | Not found | — |
| Mariahilfplatz / Ohlmüllerstr. | Baureferat footway work, **delayed** to 30 Nov 2026; SWM Fernwärme conversion in the Au | 2027/28 (inference) | The Mobilitätsreferat dropped or postponed some 2026 projects in the Au as not compatible with each other |
| Laimer Platz | U5 extension (Baureferat) | Gotthardstr. surface until end 2031 | On schedule |
| Odeonsplatz | U4 cut to Max-Weber-Platz, 5 Oct–27 Nov 2026 | 27 Nov 2026 | Trams 16/17 are the replacement, which adds load to the lines our data flags most |
| Rosenheimer Str. 145, Görresstr., Winzererstr. 68, Elsenheimerstr. 50 | **Nothing found** | — | — |

#### Proposals still under discussion, ranked by impact

Impact means how severe the gap is, how many residents and departures it affects, and how directly the proposal fixes it. Likelihood is listed separately, so a high-impact proposal can still be a long shot. The ranking is my judgement from the research, not a calculation.

| # | Proposal | Gap addressed | Stage | Likelihood | Horizon |
|---|---|---|---|---|---|
| 1 | **U9-Spange** (Münchner Freiheit–Elisabethplatz–Hbf–Implerstr.) | Schwabing-West, Maxvorstadt, Ludwigsvorstadt, Sendling; relieves the core | Preliminary planning; Hbf shell being built with the Stammstrecke; €3.5–4 bn+ | Low–medium (needs Bund/Freistaat money). A Grüne motion of 29 Jan 2026 wants the south section first, which would **not** reach Schwabing-West | 2040s |
| 2 | **Tram Y-Nord** (Hbf–Nordbad–Petuelring) | The Nordbad corridor itself, Schwabing-West; relieves U2 | Planning on hold; the 2025 exemption from cuts was probably not adopted (unclear) | Low–medium | 2030s |
| 3 | **Tram-Nordtangente / Englischer Garten** | East–west link for Schwabing-West | Frozen since the Freistaat veto (2024); tunnel study Jan 2026 (~€240 m); not in the coalition agreement | Low–medium; Olympia raises it | ≥2030 |
| 4 | **Nahverkehrsabgabe + Land funding back from 10 % to 15 %** | Enables service everywhere, unlocks 1–3 | Grüne motion Jan 2026; needs a Bavarian law | Low–medium (FDP, IHK) | Mid-term |
| 5 | **Protected cycle lanes on Schleißheimer Str. during the Fernwärme/track work** | Schwabing-West cycling plus the top disruption zone | Grüne motion 19 Dec 2025; outcome not found | Medium–high (matches the coalition's "Baustellen nutzen") | 2026–27 |
| 6 | **Bus priority at building sites** (bus lanes, signal priority) | Roadworks beside high-frequency bus lines | Grüne motion Jan 2026 (unverified) | Medium | Short |
| 7 | **Funded cycle network programme IR III from 2027** | Cycle-path gap in all flagged districts | Network adopted 23 Sep 2026; ÖDP amendment for money, outcome unknown | Medium (cheap measures only) | 2027+ |
| 8 | **Tram-Cityring** (Silberhornstr.–Goetheplatz–Hbf) | Ludwigsvorstadt, Schwanthalerhöhe, Au-Haidhausen | Corridor "under study" (Pro Bahn) | Low (the bus ring is being abolished instead) | 2030s |
| 9 | **Belgradstr. redesign + Hohenzollernstr. as a cycle street** | Schwabing-West stops and cycling | District-council motions 25 Jun 2026 | Medium | 2027+ |
| 10 | **Nachbarschaftsviertel Westend, then Gärtnerplatz; Altstadt für alle** | Schwanthalerhöhe, Isarvorstadt, Altstadt-Lehel | Concept / step-by-step plans | Medium | 2027–30 |
| 11 | **Cycle and foot bridge at Pronnerplatz (Nymphenburg–Laim)** | Laim, Neuhausen | Feasibility study being updated | Low–medium | 2030s |
| 12 | **Higher parking fees** (short-stay €2.60/h; residents' permit up to €300) | Money for the above; inner districts | Savings package Jul 2026 (single source) | Medium short-stay, low residents | 2026–27 |

S-Bahn-Nordring, Tram Johanneskirchen and U26 are real projects but do not touch the flagged districts. I found no current debate on a Citymaut, a cable car or a maglev.

#### Notes on the dataset

- **Bus 68 disappears on 13 Dec 2026.** The MVV feed runs 1 Sep–30 Nov 2026 and predates the 2027 timetable, so the "bus 68: 142 roadworks" finding expires in December.
- **Frankfurter Ring 149:** the city's end date (June 2027) is later than in our data.
- **Nordbad:** the MVG switch project in our area ended May 2026. The open records with 2027 dates are probably the follow-on Fernwärme and track work.
- **Erhardtstr. counter:** the dataset assigns it to Ludwigsvorstadt-Isarvorstadt. It sits at the Au-Haidhausen border, so check the district assignment.

#### Conflicts between sources

- **Co-funding of regional buses X204/X206:** one source says it continues and only X208 ends. Another reads the council paper (V 00776) as ending all of them from the Dec 2028 timetable. Follow the council paper.
- **Altstadt-Radlring progress:** the Radentscheid site says 3.2 of 10.2 km in its header and 1.3 of 10.3 km in its text.
- **Lindwurmstraße section 2 start:** sources disagree on the date.
- **Tram Münchner Norden opening:** older pages say 2027; official since Sep 2026: end 2031.
- **Tree loss for the Englischer Garten tram:** figures range from 19 to 900 depending on the route variant.

#### Key sources

- Coalition agreement 2026–2032: https://www.fdp-muenchen.de/sites/default/files/2026-05/260508_Koalitionsvertrag_Muenchen.pdf
- Timetable 2027 (council paper): https://risi.muenchen.de/risi/dokument/v/9853476 · https://www.muenchen-transparent.de/dokumente/9813547/datei
- New tram line decisions, 30 Sep 2026: https://www.swm.de/unternehmen/presse/pressemitteilungen/2026/09-2026/mvg-beschluesse-tramneubaustrecken
- Tram-Westtangente plan approval: https://www.swm.de/unternehmen/presse/pressemitteilungen/2026/08-2026/mvg-planfeststellung-twt
- Westtangente funding risk (V 18994): https://www.muenchen-transparent.de/dokumente/9518781/datei
- U9: https://www.muenchen-transparent.de/dokumente/9530505/datei · https://de.wikipedia.org/wiki/U9-Spange_(U-Bahn_M%C3%BCnchen)
- Englischer Garten tunnel study: https://www.abendzeitung-muenchen.de/muenchen/fuer-240-millionen-euro-muenchner-doppelwumms-fuer-den-englischen-garten-art-1107368
- Cuts to the public transport building programme (V 17096): https://www.muenchen-transparent.de/dokumente/9214100/datei
- 2. Stammstrecke: https://www.deutschebahn.com/de/presse/presse-regional/pr-muenchen-de/aktuell/presseinformationen/Donna-Maria-startet-Erster-maschineller-Tunnelvortrieb-der-2-Stammstrecke-beginnt--14037354
- U5 tunnel breakthrough: https://www.abendzeitung-muenchen.de/muenchen/u5-verlaengerung-licht-im-u-bahn-tunnel-art-1138356
- Nordbad switches: https://www.swm.de/unternehmen/presse/pressemitteilungen/2026/03-2026/mvg-tram-12-27-n27-weichenerneuerung-nordbad
- Schleißheimer Str. motion: https://www.muenchen-transparent.de/dokumente/9478485/datei
- Building-site management (Dunkel, Apr 2026): https://www.muenchen-transparent.de/dokumente/9641968/datei
- Building-site map and closures: https://stadt.muenchen.de/infos/baustellen-verkehrseinschraenkungen · https://www.mvg.de/trambau
- ADAC on building sites 2026: https://www.adac.de/der-adac/regionalclubs/suedbayern/news/muenchens-verkehrsnetz-am-limit-baustellen-2026/
- SWM Fernwärme conversion: https://www.swm.de/geschaeftskunden/fernwaerme/modernisierung-netz
- Cycle network IR III: https://ru.muenchen.de/2026/182/Stadtrat-beschliesst-neue-Radverkehrsverbindungen-126187
- Gebsattelberg: https://ru.muenchen.de/2026/137/Stadtrat-beschliesst-kostenguenstigen-Radweg-am-Gebsattelberg-125370
- Radentscheid status: https://stadt.muenchen.de/infos/radentscheid.html · https://muenchenunterwegs.de/radentscheid/massnahmen/
- Lindwurmstraße rollback: https://www.abendzeitung-muenchen.de/muenchen/lindwurmstrasse-in-muenchen-verschwinden-die-radwege-wieder-art-1145658
- Nahverkehrsumlage motion: https://www.muenchen-transparent.de/dokumente/9530781/datei
- Olympia nomination: https://www.muenchen.de/aktuell/dosb-vergibt-nationale-olympiabewerbung-muenchen
- Tramreport on the coalition: https://www.tramreport.de/2026/05/08/koalitionsvertrag-2026-2032/

### Findings file: pt-projects-notes.md

### Planned rail and tram projects in Munich: stations for scenario modelling (as of 19 Oct 2026)

Companion to `pt_projects.csv`: 88 rows, 17 project_ids. The research was done in German, mostly from official sources. Each source is marked **[verified]** (I opened it and saw the fact) or **[unverified]** (seen only in search snippets or in secondary sources).

#### Conventions used in the CSV

- **station_is_new is mode-specific.** 1 means no station of this mode exists at this place today. A bus stop, or a station of another mode, may already be there. Examples: a new tram stop at U-Bahn Holzapfelkreuth is 1, and the new U5 station under Pasing DB is 1. 0 means an existing station of the same mode gains a new line or platform: Laim and Leuchtenbergring for the S-Bahn, Münchner Freiheit and Hbf for the U9, Tivolistraße for the tram. Hbf and Ostbahnhof on the 2nd trunk get new deep platforms but are coded 0, so they map onto the existing hub stop. Marienhof is 1.
- **trains_per_hour** is per direction and per line. "Off-peak" means daytime off-peak, not evening. It is empty where no headway is published; then use `analog_line`.
- **opening_year** is empty when no year exists. Three values are my placeholders and are flagged in the note: U5 Freiham 2040, U9 2040 and TMN PFA 2 2031.
- **funded = 1** means the money is committed: Bund/Land grants, a signed financing agreement, or the city's explicit decision to build despite missing grants (TMN PFA 1, TWT).
- **verified** concerns the station's existence and name in the cited source. Coordinates are from OSM or Nominatim. Where the stop site is not published, I used the nearest named intersection, and the note says so.
- **Several rows per station** occur only for the 2nd trunk (one row per line) and for the Laim restoration (one row per line).

#### 1. Tram-Westtangente, remaining section (tram 14): 9 rows

- **What is open:** Since 28 Feb 2026 line 14 runs Pasing Bf–…–Ammerseestraße–Senftenauerstraße–Gondrellplatz. It runs every 10 min by day and every 20 min from 22:00. **[verified]** muenchen.de
- **Not yet open, and in the CSV:** Andreas-Vöst-Straße, Holzapfelkreuth, Waldfriedhof and Waldfriedhof Haupteingang. Legally these are in PFA 1, which was approved 4 Sep 2023 and is under construction, but they open with the 2028 stage. **This is wider than the brief's "section 2 = Waldfriedhof–Aidenbachstraße"**: they are not in today's timetable, so leaving them out would undercount the stage. PFA 2, approved Aug 2026, adds Drygalski-Allee, Machtlfinger Straße, Geisenhausenerstraße and Aidenbachstraße, plus a temporary stop with loop at Ratzingerplatz. **[verified]** Erläuterungsbericht Tektur A, UVP notice Tektur C, muenchenwiki.
- **Dates:** SWM, 30 Sep 2026: opening to Aidenbachstraße "weiterhin Ende 2028". Council paper V 18994: without a city funding exemption, end 2030 or early 2031, so risk year 2031. muenchenwiki says mid-2028 to Ratzingerplatz first, because the Aidenbachstraße terminus is only finished from 2028. That conflicts mildly with SWM. Tracks from Jul 2027.
- **Headway:** 6 trains/h (10 min), the same as today's line 14. The headway for the extended line is not published separately.

#### 2. Tram Münchner Norden: 6 + 6 rows

- **PFA 1 (Schwabing Nord–Kieferngarten), under construction, 6 new stops:** Maria-Probst-Straße, Neufreimann, Werner-Egk-Bogen, Paul-Hindemith-Allee, Bernsteinweg, Kieferngarten. **[verified]** Regierung von Oberbayern plan approval of 31 Oct 2024.
- **PFA 2 (Neufreimann–Am Hart), 7 stops including Werner-Egk-Bogen, which is shared:** Grusonstraße, Paracelsusstraße, Heidemannstraße, Rothpletzstraße, Rathenaustraße, Am Hart. The names are working titles. **[verified]** council paper V 15807 (Jul 2025). The project counts 12 stops in total.
- **Line concept [verified, V 15807]:** First, tram 23 runs to Kieferngarten. After PFA 2, tram 23 runs Münchner Freiheit–Schwabing Nord–Am Hart, and the new tram 24 shuttles Am Hart–Kieferngarten. Each runs every 10 min by day, so Neufreimann–Am Hart gets a 5-min combined service.
- **Dates (conflict):** The original target was end 2027, then 2029 (summer 2025). SWM, Sep 2026: Schwabing Nord–Kieferngarten "Ende 2031" **[verified]**. For PFA 2, V 15807 (Jul 2025) targeted end 2029. Since Sep 2026 SWM says only that plan approval starts from Oct 2026, with no date. **I set 2031 (assumption).**
- **Funding:** BCR 2.61 and a GVFG application exist, but there is no binding Bund/Land commitment. Under the Dec 2025 financing rule, work was held at LP4. On 30 Sep 2026 the council decided case by case to continue past the Nordring bridge. **[verified]** SWM press release; tramreport article of 18 Sep 2026.

#### 3. U5 Laimer Platz–Pasing: 3 rows

- **Stations [verified, ubahnbau-muenchen.de]:** Baumschule Laim (under Gotthardstraße between Willibald- and Reutterstraße, formerly "Willibaldstraße"), Am Knie, Pasing (under the DB station). 3.8 km, about €1.3 bn, €645.2 m in grants.
- **Dates:** 2036 per Abendzeitung (Jun 2026) **[unverified, snippet]**. MVV's older page says "Anfang der 2030er". Construction is "im Plan".
- **Headway:** not published; analog U5.

#### 4. U5 Pasing–Freiham: 4 rows

- **Stations [verified, ubahnbau-muenchen.de]:** Westkreuz (S-Bahn interchange), Radolfzeller Straße, Riesenburgstraße, Freiham-Zentrum (terminus with sidings for 11 trains). 4.7 km.
- **Status:** Only the Freiham-Zentrum shell is funded and being built (Dec 2023, €94.1 m; main work to Oct 2027). The rest is unfunded.
- **Not verified:** "council planning vote postponed Oct 2026" and "2040s at the earliest" came from the brief; I could not confirm them. opening_year = 2040 is a placeholder.

#### 5. 2. S-Bahn-Stammstrecke: 29 rows

- **Stations [verified, 2.stammstrecke-muenchen.de]:** Laim and Leuchtenbergring (existing, rebuilt as changeover stations), plus new underground stations Hauptbahnhof, Marienhof and Ostbahnhof. About 11 km, with a 7 km tunnel.
- **Opening:** DB plan 2035; other estimates 2037 or later; BEG tender: "Mitte oder Ende der 2030er". So 2035, with risk 2037. Cost: DB forecast over €11 bn (Apr 2025).

##### Operating concept (best-sourced version, verified = 0 in the CSV)

There is no final timetable. Bavaria (Landtag 17/17196) says the detailed timetable will be worked out only close to opening. The official building blocks are:

1. **Landtag 17/7917 (2015) [verified]:** S1 (Freising/Flughafen) and S6 (Tutzing) use the 2nd trunk at an all-day 15-min headway. The express and regional S-Bahns also use the 2nd trunk.
2. **Landtag 17/17196 (2017) [verified]:** The basic headway changes from 10/20 to 15 min, except S2, S7 and S20. Express S-Bahns run every 30 min on several outer branches. S1 stations (Freising…Moosach), S6 stations (Tutzing…Gräfelfing) and Ebersberg/Grafing Stadt lose their direct link to the old trunk, which shows which branches move.
3. **SMA/OBB article, ETR 11/2017 [verified]:**
   - 15 min all day on 5 of 7 western and 3 of 5 eastern branches.
   - Express services on 4 western and 2 eastern branches, saving up to 14 min.
   - 6 instead of 3 trains/h on the S8 corridor to the airport (15-min S-Bahn plus 30-min express).
   - Regional S-Bahns from Buchloe (every 30 min), Landshut and Augsburg (hourly).
   - Trunk capacity rises from 30 to 54 trains/h/direction; the start concept uses 36.
   - Train-km rise from about 21 to about 30 million a year.
4. **BEG / bayern.de, 1st Munich S-Bahn contract, second operating stage [verified]:**
   - The basic headway on most lines changes from 20 to 15 min.
   - Express S-Bahns run every 30 min to Mammendorf, Herrsching, Ebersberg and the airport.
   - Regional S-Bahns run to Buchloe and Landshut, and via Mering to Augsburg, alternating with the Mammendorf express.
   - Train-km go from 20.9 to 29.1 million a year (+40 %), with 110 new trains.
5. **Line table, start concept "Mitfall 6+" (Apr 2017), from German Wikipedia [secondary, unverified against the primary source]:**

| Line | Route on the 2nd trunk | Headway | Trains/h used |
|---|---|---|---|
| S1 | Freising/Flughafen–Laim–Marienhof–Leuchtenbergring–Ebersberg | 15′ (30′ per branch north of Neufahrn) | 4 |
| S6 | Tutzing–Pasing–Laim–Marienhof–Ostbahnhof | 15′ | 4 (not at Leuchtenbergring) |
| S18X | Herrsching–Pasing–Laim–Marienhof–Leuchtenbergring (express) | 30′ | 2 |
| S21X | Landshut–Freising–Marienhof–Leuchtenbergring (regional S-Bahn) | 60′ | 1 |
| S23X | (Augsburg–)Mering–Mammendorf–Pasing–Laim–Marienhof–Flughafen via S8 corridor | 30′ (hourly from Augsburg) | 2 |
| S24X | Buchloe–Geltendorf–Pasing–Laim–Marienhof–Leuchtenbergring | 30′ | 2 |

That totals 15 trains/h/direction on the 2nd trunk at Laim, Hbf, Marienhof and Ostbahnhof, and 11 at Leuchtenbergring. Peak is set equal to off-peak because the concept is all-day and no peak extras are published.

**Modelling caveats:**
- These lines are *re-routed*: S1 and S6 leave the old trunk, so the old routings must be removed.
- The 20→15-min change applies network-wide on most lines. That is outside this station list, but it is the biggest supply effect.
- **Newer conflicting detail [verified, bahnblogstelle on the BEG tender, 2025]:** for the contract starting Dec 2034, S2 and S3 swap their eastern branches. The expansion for the 2nd trunk is a contract option, and the award is planned for 2029. The 2017 line numbers may therefore change.
- Express stop pattern in Munich [unverified snippet, Landtag 17/7918]: Pasing, Laim, Hbf, Marienhof, Ostbahnhof, Leuchtenbergring.

#### 6. Laim, inbound S3/S4/S6/S8 restored: 4 rows

- **Facts:** The inbound stops are cancelled from 25 Aug 2026 to "mid-2028" because of the Laim rebuild. **[verified]** notice on 2.stammstrecke-muenchen.de; muenchen.de **[unverified snippet]**.
- **How to model:** Use the outbound departures of the same line at Laim as a proxy for the restored inbound departures.

#### 7. Tram Johanneskirchen: 2 rows

- **Route:** About 1 km, branching from the St. Emmeram line at Cosimastraße.
- **Stops [verified, MVG FAQ]:** Ringofenweg and Johanneskirchner Straße, the loop at S8 Johanneskirchen, elsewhere called "Johanneskirchen Bf".
- **Status:** Plan approval has been running since end 2022. No construction date. The targets of end 2025, then Q2/2025 approval, were missed.
- **Funding conflict:** The coalition agreement says "only with funding commitments", while MVG says it is financed from grants plus city budget. I set funded = 0.
- **Line and headway:** not published; analog 16.

#### 8. U9-Spange: 7 rows

- **Stations [verified, ubahnbau-muenchen.de]:** Münchner Freiheit, Elisabethplatz, Pinakotheken, Theresienstraße (U29 branch to U2), Hauptbahnhof, Esperantoplatz, and a new joint Impler-/Poccistraße station (Billigungsbeschluss Sep 2024). 10.5 km.
- **New vs existing:** New are Elisabethplatz, Pinakotheken and Esperantoplatz. Existing nodes are Münchner Freiheit, Theresienstraße, Hbf and Impler-/Poccistraße.
- **Status:** Preliminary planning, not financed, €3.5–4 bn+. The Hbf box is being pre-built with the 2nd trunk (city > €500 m).
- **Staging proposal:** The Grüne motion of 29 Jan 2026 proposes staging Theresienstraße–Hbf–Implerstraße and questions Esperantoplatz.
- **Date:** "2040s" comes from secondary sources only, so 2040 is a placeholder.

#### 9. Tram Lerchenauer Feld (ex Y-Nord): 1 row, "unknown"

- **No stop list published.** Only the corridor is known: Hbf–Hochschule München–Nordbad–Petuelring–northern Schleißheimer Straße, then a Y split to the Lerchenauer Feld market square and to Am Hart. **[verified]** MOR letter of 24 Jul 2026: "zu einem späteren Zeitpunkt".
- **System comparison:** The comparison of tram against U-Bahn (including U1 north) was not yet presented in Feb 2026 (CSU-FW question). I set status on_hold.

#### 10. Tram-Nordtangente PFA 1 (Elisabethplatz–Englischer Garten–Tivolistraße): 6 rows

- **Route [verified]:** Route decision 20 Dec 2023 (V 10202): Elisabethplatz–Franz-Joseph-Str.–Martiusstr.–Thiemestr.–Englischer Garten–Tivolistraße.
- **Stops [secondary]:** Elisabethplatz (existing), a new westbound platform in Franz-Joseph-Straße, Giselastraße, Thiemestraße, Chinesischer Turm, Tivolistraße (existing, new loop). Sources are tramreport and muenchenwiki; the stop list is not from the council paper, so verified = 0.
- **Status: blocked.** The Freistaat refused in 2024 and SWM froze the planning (MOR letter of 6 Feb 2025) **[verified]**. MOR, Aug 2025: the city sticks with the surface route and does not pursue a tunnel. Not in the coalition agreement.
- **Planned lines:** tram 23 extended toward Karlsplatz, plus a new line Schwabing Nord–Lehel–Max-Weber-Platz–Giesing.

#### 11. Augsburg–Munich express: 1 row, "unknown"

- **No Munich stops are named** beyond Pasing and the 2nd trunk stations. It is the hourly Augsburg part of S23X. It is already in the stammstrecke2 rows, so **do not add it twice**.

#### Other projects with stations inside Munich (included)

- **S-Bahn shuttle on the DB-Nordring (Moosach or Karlsfeld to BMW FIZ, optionally Euro-Industriepark): 3 rows.**
  - New halts Knorrstraße/FIZ and Europark.
  - Every 20 min in the morning and afternoon peaks (3 hours each), otherwise hourly.
  - DB InfraGO preliminary planning; the council asked for operation before 2029, with no binding date. **[verified]** MOR letter of 18 Aug 2025 (muenchen-transparent 9252439). Exact sites are not published.
- **S-Bahn halt Berduxstraße on the S2 (Laim–Obermenzing): 1 row.**
  - Financing agreement Sep 2023 (about €14 m); planning agreement Jul 2024; tenders Dec 2025.
  - No date and no fixed site. **[verified]** MOR letter of 27 Apr 2026.
- **U4 Ost (Arabellapark–Cosimapark/Fideliopark–Englschalking–Pellegrinistraße): 4 rows.**
  - Very early planning; depends on the S8 four-track expansion. **[verified]** ubahnbau-muenchen.de
- **U26 (Am Hart–Kieferngarten): 1 row, "unknown".**
  - Two unnamed stations; only after the U9. **[verified]**
- **Regional-train halt Poccistraße: 1 row.**
  - Needs the Daglfing–Johanneskirchen expansions before all trains can stop. The 2026 target was missed. **[verified]** MOR letter of 4 Feb 2026.

#### Not included (and why)

- **U6 Martinsried:** in Planegg, outside the city. Planned 2027.
- **Tram depot access track Ständlerstraße:** no passenger stops. Plan approval 13 Feb 2026; target H2 2028, but work is suspended.
- **U1 Nord and U1 Süd (Klinikum Harlaching, 2 unnamed stations):** studies only.
- **S-Bahn halt Menterschwaige:** under study, with the experts recommending it. No plan.
- **Kolumbusplatz / S-Bahn Südring (S13X):** not pursued.
- **S8 four-track Daglfing–Johanneskirchen:** existing stations only.
- **Tram Amalienburgstraße–Freiham and Tram Parkstadt Solln:** dropped Jul 2025.
- **Tram Daglfing:** 2028 at the earliest; no stop list found.

#### Main uncertainties

1. **2nd trunk line table:** the 2017 concept is secondary-sourced, and the BEG tender signals line changes. The 15-min network-wide upgrade is not in this file.
2. **Placeholder opening years:** U5 Freiham, U9 and TMN PFA 2 (2040, 2040, 2031). TWT 2028 is official but carries funding risk.
3. **Approximated coordinates (verified = 0 sites):** Neufreimann, Rothpletzstraße, Rathenaustraße, U5 Freiham stations, Ostbahnhof tief, Hbf tief, Nordring halts, Berduxstraße, Johanneskirchner Straße loop.

#### Sources

**Verified (opened):**
- https://www.swm.de/unternehmen/presse/pressemitteilungen/2026/08-2026/mvg-planfeststellung-twt
- https://www.swm.de/unternehmen/presse/pressemitteilungen/2026/09-2026/mvg-beschluesse-tramneubaustrecken
- https://www.muenchen.de/verkehr/aktuell/neue-tram-linie-14-westtangente-zwischen-pasing-gondrellplatz
- https://www.uvp-verbund.de/documents-ige-ng/igc_by/a809852e-50cc-4489-a875-b17fa62bfc9e/1.2%20Erl%C3%A4uterungsbericht%20Tektur%20A.pdf
- https://www.uvp-verbund.de/documents-ige-ng/igc_by/a809852e-50cc-4489-a875-b17fa62bfc9e/Tektur%20C%20Bekanntmachung%20UVP.pdf
- https://www.muenchenwiki.de/wiki/Trambahnlinie_14 (secondary)
- https://www.regierung.oberbayern.bayern.de/mam/dokumente/bereich2/pfb/u-bahn_tram/2024-11-04_pfb_schwabing-_nord_kieferngarten.pdf
- https://www.muenchen-transparent.de/dokumente/9175388/datei (TMN PFA 2, V 15807)
- https://risi.muenchen.de/risi/dokument/v/9847142 (TMN and Lerchenauer Feld, 24 Jul 2026)
- https://tram-muenchner-norden.mvg.de/projekt.html
- https://www.tramreport.de/2025/07/23/tmn-202507-trassierungsbeschluss-mo/
- https://www.tramreport.de/2026/09/18/finanzierungsregelung-baustopp-tmn/
- https://www.ubahnbau-muenchen.de/projekte/pasing
- https://www.ubahnbau-muenchen.de/projekte/freiham
- https://www.ubahnbau-muenchen.de/projekte/u9-entlastungsspange
- https://www.ubahnbau-muenchen.de/projekte/u4-ost
- https://www.ubahnbau-muenchen.de/projekte/u26-verbindungsspange
- https://www.ubahnbau-muenchen.de/projekte/u6-martinsried
- https://www.ubahnbau-muenchen.de/projekte/u1-nord
- https://www.ubahnbau-muenchen.de/projekte/u1-sued
- https://www.2.stammstrecke-muenchen.de/
- https://de.wikipedia.org/wiki/Zweite_Stammstrecke (secondary)
- https://www.bayern.landtag.de/www/ElanTextAblage_WP17/Drucksachen/Schriftliche%20Anfragen/17_0007917.pdf
- https://www.bayern.landtag.de/www/ElanTextAblage_WP17/Drucksachen/Schriftliche%20Anfragen/17_0017196.pdf
- https://sma-partner.com/storage/app/media/Dokumente/Veranstaltungen%20und%20Publikationen/ETR-Die-2.-Stammstrecke_de.pdf
- https://www.bayern.de/1-muenchner-s-bahn-vertrag/
- https://bahnblogstelle.com/263471/beg-startet-vergabe-fuer-muenchner-s-bahn-betrieb-ab-ende-2034/
- https://tram-johanneskirchen.mvg.de/projekt.html
- https://tram-johanneskirchen.mvg.de/kontakt-faq/faq-tjo/tjo7.html
- https://tram-johanneskirchen.mvg.de/kontakt-faq/faq-tjo/tjo8.html
- https://www.muenchen-transparent.de/dokumente/9490929/datei (Tram Johanneskirchen, BA 13, Feb 2026)
- https://www.muenchen-transparent.de/dokumente/8135927/datei (Nordtangente route decision, V 10202)
- https://www.muenchen-transparent.de/dokumente/8902736/datei (Nordtangente frozen, Feb 2025)
- https://www.muenchen-transparent.de/dokumente/9262805/datei (Nordtangente tunnel, Aug 2025)
- https://www.tramreport.de/2023/12/13/trassierungsbeschluss-tnt/
- https://www.muenchen-transparent.de/dokumente/9530505/datei (U9 Grüne motion)
- https://www.muenchen-transparent.de/dokumente/9550336/datei (Y-Nord system comparison)
- https://www.muenchen-transparent.de/dokumente/9252439/datei (Nordring shuttle)
- https://risi.muenchen.de/risi/dokument/v/9682315 (Berduxstraße)
- https://risi.muenchen.de/risi/dokument/v/9539994 (Menterschwaige, Kolumbusplatz, Poccistraße)
- https://www.muenchen-transparent.de/dokumente/8871200/datei (Ständlerstraße)
- OpenStreetMap (Overpass and Nominatim) for coordinates

**Unverified (search snippets only):**
- https://www.abendzeitung-muenchen.de/muenchen/u5-verlaengerung-licht-im-u-bahn-tunnel-art-1138356 (U5 2036)
- https://www.mvv-muenchen.de/mvv-im-ueberblick/die-gesellschaft/planungen-und-projekte/u-bahn-planungstand/ ("Anfang der 2030er")
- https://www.bayern.landtag.de/www/ElanTextAblage_WP17/Drucksachen/Schriftliche%20Anfragen/17_0007918.pdf (express stop pattern)
- https://www.bayern.landtag.de/www/ElanTextAblage_WP17/Drucksachen/Schriftliche%20Anfragen/17_0016419.pdf (hourly Augsburg regional S-Bahn)
- https://www.muenchen.de/verkehr/aktuell/s-bahn-muenchen-grossbaustellen-und-sperrungen-juni-juli-2026 (Laim cancellations)
- https://stmb.bayern.de/med/pressemitteilungen/pressearchiv/2023/173/index.php (Berduxstraße, about €14 m, 5,200 riders/day)
- https://www.muenchenwiki.de/wiki/Tram-Nordtangente (Nordtangente stops)
- Caller background: "U5 Freiham vote postponed Oct 2026; 2040s"; "U9 2040s"

## Appendix: ranking.sql (v5 copy)

The query from `dashboards/munich-mobility-planning-v4/queries/ranking.sql`, plus the v5 what-if change: the `ex_raw` and `ex` CTEs and `+ COALESCE(ex.add_places, 0)` in `m`.

```sql
WITH feed AS (
    SELECT MIN("start_date") AS f_start, MAX("end_date") AS f_end FROM MUNICH_DATASET.MVV_CALENDAR
),
base AS (SELECT LEAST(GREATEST(DATE '2026-10-21', f_start), ADD_DAYS(f_end, -6)) AS b FROM feed),  -- reference weekday pinned: Wed 21 Oct 2026
rd AS (SELECT ADD_DAYS(b, MOD(7 - MOD(DAYS_BETWEEN(b, DATE '1970-01-07'), 7), 7)) AS ref_date FROM base),
svc AS (
    SELECT c."service_id" FROM MUNICH_DATASET.MVV_CALENDAR c CROSS JOIN rd
    WHERE c."wednesday" = 1 AND rd.ref_date BETWEEN c."start_date" AND c."end_date"
      AND c."service_id" NOT IN (SELECT x."service_id" FROM MUNICH_DATASET.MVV_CALENDAR_DATES x CROSS JOIN rd r2
                                 WHERE x."date" = r2.ref_date AND x."exception_type" = 2)
    UNION
    SELECT x."service_id" FROM MUNICH_DATASET.MVV_CALENDAR_DATES x CROSS JOIN rd
    WHERE x."date" = rd.ref_date AND x."exception_type" = 1
),
lines AS (
    SELECT r."route_id", r."route_short_name" AS line, COALESCE(lc."capacity_per_trip", v."capacity_per_trip") AS capacity
    FROM MUNICH_DATASET.MVV_ROUTES r
    JOIN MUNICH_DATASET.VEHICLE_CAPACITY v ON v."line_mode" = r."line_mode"
    LEFT JOIN MUNICH_DATASET.LINE_CAPACITY lc ON lc."line" = r."route_short_name" AND lc."line_mode" = r."line_mode"
),
wt AS (
    SELECT t."trip_id", l.line, l.capacity
    FROM MUNICH_DATASET.MVV_TRIPS t JOIN svc ON svc."service_id" = t."service_id"
    JOIN lines l ON l."route_id" = t."route_id"
),
need AS (
    -- lines whose current service is used: analog lines, plus every S-Bahn line (2nd trunk 15-minute basic interval, Laim restore)
    SELECT DISTINCT "mode" AS line_mode, "analog_line" AS line FROM MUNICH_DATASET.PT_PROJECT_STATIONS
    WHERE "analog_line" IS NOT NULL AND INSTR("analog_line", ',') = 0
    UNION SELECT DISTINCT "line_mode", "route_short_name" FROM MUNICH_DATASET.MVV_ROUTES WHERE "line_mode" = 'S-Bahn'
),
pl AS (
    SELECT r."route_id", r."line_mode" AS line_mode, r."route_short_name" AS line,
           COALESCE(lc."capacity_per_trip", v."capacity_per_trip") AS capacity
    FROM MUNICH_DATASET.MVV_ROUTES r
    JOIN need ON need.line_mode = r."line_mode" AND need.line = r."route_short_name"
    JOIN MUNICH_DATASET.VEHICLE_CAPACITY v ON v."line_mode" = r."line_mode"
    LEFT JOIN MUNICH_DATASET.LINE_CAPACITY lc ON lc."line" = r."route_short_name" AND lc."line_mode" = r."line_mode"
),
ev_sel AS (
    SELECT pl.line_mode, pl.line, pl.capacity, t."direction_id" AS dir, s."district_no" AS district_no, s."in_munich" AS in_munich,
           COALESCE(s."parent_station", s."stop_id") AS station_id
    FROM MUNICH_DATASET.MVV_TRIPS t
    JOIN svc ON svc."service_id" = t."service_id"
    JOIN pl ON pl."route_id" = t."route_id"
    JOIN MUNICH_DATASET.MVV_STOP_TIMES st ON st."trip_id" = t."trip_id"
    JOIN MUNICH_DATASET.MVV_STOPS s ON s."stop_id" = st."stop_id"
),
ana AS (
    -- rule 1b: the analog line's mean weekday departures per station inside Munich on the reference Wednesday
    SELECT line_mode, line, 1.0 * COUNT(*) / COUNT(DISTINCT station_id) AS dep_per_station
    FROM ev_sel WHERE in_munich = 1 GROUP BY line_mode, line
),
laim AS (
    -- rule 3: restored inbound departures at Laim = current outbound minus current inbound, per line
    SELECT line, SUM(CASE WHEN dir = 1 THEN 1 ELSE 0 END) - SUM(CASE WHEN dir = 0 THEN 1 ELSE 0 END) AS restored_dep
    FROM ev_sel WHERE station_id = 'de:09162:9' AND line_mode = 'S-Bahn' GROUP BY line
),
sb AS (
    -- 2nd trunk, 15-minute basic interval: today's departures per S-Bahn line and station inside Munich,
    -- all lines except S2, S7 and S20 (Landtag 17/17196, 2017) and S5 (later reinforcement line, not in that concept)
    SELECT line, station_id, MIN(district_no) AS district_no, MIN(capacity) AS capacity, COUNT(*) AS dep_today
    FROM ev_sel WHERE line_mode = 'S-Bahn' AND in_munich = 1 AND line NOT IN ('S2', 'S5', 'S7', 'S20')
    GROUP BY line, station_id
),
ps AS (
    -- rule 2: capacity per trip of the project line (LINE_CAPACITY override, else VEHICLE_CAPACITY by mode)
    SELECT p.*, COALESCE(lc."capacity_per_trip", v."capacity_per_trip") AS capacity
    FROM MUNICH_DATASET.PT_PROJECT_STATIONS p
    JOIN MUNICH_DATASET.VEHICLE_CAPACITY v ON v."line_mode" = p."mode"
    LEFT JOIN MUNICH_DATASET.LINE_CAPACITY lc ON lc."line" = p."line" AND lc."line_mode" = p."mode"
    WHERE p."district_no" IS NOT NULL AND p."station_name" <> 'unknown'
),
pmeta AS (
    SELECT "project_id" AS project_id, MIN("opening_year_model") AS oy_model, MIN("opening_year_risk") AS oy_risk
    FROM MUNICH_DATASET.PT_PROJECT_STATIONS GROUP BY "project_id"
),
comps AS (
    -- rule 1a: published frequency: (tph_peak x 6 + tph_offpeak x 13) x 2 directions, peak falls back to off-peak
    SELECT ps."project_id" AS project_id, 'added' AS comp_kind, ps."district_no" AS district_no, ps."station_name" AS station_name,
           ps."lat" AS lat, ps."lon" AS lon, ps."station_is_new" AS station_is_new, ps."mode" AS line_mode, ps."line" AS line,
           CASE WHEN ps."project_id" = 'laim_inbound_restore' THEN 'proxy: outbound departures at Laim'
                WHEN COALESCE(ps."trains_per_hour_peak", ps."trains_per_hour_offpeak") IS NOT NULL THEN 'frequency'
                WHEN ana.dep_per_station IS NOT NULL THEN 'analog ' || ps."analog_line"
                ELSE 'none (no frequency or analog)' END AS calc_method,
           COALESCE(CASE WHEN ps."project_id" = 'laim_inbound_restore' THEN laim.restored_dep
                         WHEN COALESCE(ps."trains_per_hour_peak", ps."trains_per_hour_offpeak") IS NOT NULL
                           THEN (COALESCE(ps."trains_per_hour_peak", ps."trains_per_hour_offpeak") * 6
                                 + COALESCE(ps."trains_per_hour_offpeak", ps."trains_per_hour_peak") * 13) * 2
                         ELSE ana.dep_per_station END, 0) AS departures,
           ps.capacity AS capacity, CAST(NULL AS VARCHAR(100)) AS requires_project
    FROM ps
    LEFT JOIN laim ON ps."project_id" = 'laim_inbound_restore' AND laim.line = ps."line"
    LEFT JOIN ana ON ana.line_mode = ps."mode" AND ana.line = ps."analog_line"
    UNION ALL
    -- rule 4: 2nd trunk = new-tunnel trains (above) plus a 15-minute basic interval; nothing removed from the existing trunk (slots reused).
    -- every station a non-excluded S-Bahn line serves today: departures_new = GREATEST(departures_today, 152) = 4/h x 19 h x 2 directions
    SELECT 'stammstrecke2', 'upgraded: 15-minute basic interval', sb.district_no, sb.station_id, NULL, NULL, NULL, 'S-Bahn', sb.line,
           '15-min basic interval: GREATEST(today, 152)', GREATEST(sb.dep_today, 152) - sb.dep_today, sb.capacity, NULL
    FROM sb WHERE sb.dep_today < 152
    UNION ALL
    -- with the Laim restore active, the 15-minute rule applies to the restored numbers (no double count at Laim)
    SELECT 'stammstrecke2', 'adjusted: 15-minute rule on restored Laim', sb.district_no, sb.station_id, NULL, NULL, NULL, 'S-Bahn', sb.line,
           '15-min basic interval after Laim restore',
           (GREATEST(sb.dep_today + laim.restored_dep, 152) - sb.dep_today - laim.restored_dep) - (GREATEST(sb.dep_today, 152) - sb.dep_today),
           sb.capacity, 'laim_inbound_restore'
    FROM sb JOIN laim ON laim.line = sb.line
    WHERE sb.station_id = 'de:09162:9'
      AND sb.line IN (SELECT "line" FROM MUNICH_DATASET.PT_PROJECT_STATIONS WHERE "project_id" = 'laim_inbound_restore')
),
sel AS (
    -- rule 5: a project counts only if switched on and the year has reached its opening year (risk year when pessimistic)
    SELECT c.district_no, SUM(c.departures) AS add_dep, SUM(c.departures * c.capacity) AS add_places,
           GROUP_CONCAT(DISTINCT c.project_id ORDER BY c.project_id SEPARATOR ',') AS active_projects
    FROM comps c
    JOIN pmeta m ON m.project_id = c.project_id
    LEFT JOIN pmeta rq ON rq.project_id = c.requires_project
    WHERE INSTR(',' || {projects!s} || ',', ',' || c.project_id || ',') > 0
      AND {year!d} >= CASE WHEN {pessimistic!d} = 1 THEN COALESCE(m.oy_risk, m.oy_model) ELSE m.oy_model END
      AND (c.requires_project IS NULL
           OR (INSTR(',' || {projects!s} || ',', ',' || c.requires_project || ',') > 0
               AND {year!d} >= CASE WHEN {pessimistic!d} = 1 THEN COALESCE(rq.oy_risk, rq.oy_model) ELSE rq.oy_model END))
    GROUP BY c.district_no
),
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
dep AS (
    SELECT s."district_no" AS dno, COUNT(*) AS departures, SUM(wt.capacity) AS places, COUNT(DISTINCT wt.line) AS n_lines
    FROM MUNICH_DATASET.MVV_STOP_TIMES st
    JOIN wt ON wt."trip_id" = st."trip_id"
    JOIN MUNICH_DATASET.MVV_STOPS s ON s."stop_id" = st."stop_id"
    WHERE s."in_munich" = 1
    GROUP BY s."district_no"
),
stp AS (
    SELECT "district_no" AS dno, COUNT(*) AS stops,
           COUNT(DISTINCT COALESCE("parent_station", "stop_id")) AS stations,
           SUM(CASE WHEN "stop_mode" = 'Bus' THEN 1 ELSE 0 END) AS bus_stops,
           SUM(CASE WHEN "stop_mode" = 'Tram' THEN 1 ELSE 0 END) AS tram_stops,
           SUM(CASE WHEN "stop_mode" = 'U-Bahn' THEN 1 ELSE 0 END) AS ubahn_stops,
           SUM(CASE WHEN "stop_mode" = 'S-Bahn' THEN 1 ELSE 0 END) AS sbahn_stops,
           SUM(CASE WHEN "stop_mode" = 'Regional rail' THEN 1 ELSE 0 END) AS rail_stops
    FROM MUNICH_DATASET.MVV_STOPS WHERE "in_munich" = 1 GROUP BY "district_no"
),
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
m AS (
    SELECT dem.district_no, dem.district, dem.area_km2, dem.pop_y AS population, dem.jobs_y AS jobs,
           dem.pop_y / dem.area_km2 AS residents_per_km2,
           dem.pop_y + {w_jobs!f} * dem.jobs_y AS activity,
           dem.pop_24 + {w_jobs!f} * dem.jobs_24 AS activity_24,
           (dem.pop_y + {w_jobs!f} * dem.jobs_y) / dem.area_km2 AS activity_per_km2,
           (dem.pop_24 + {w_jobs!f} * dem.jobs_24) / dem.area_km2 AS activity_per_km2_24,
           COALESCE(stp.stations, 0) AS stations, COALESCE(stp.bus_stops, 0) AS bus_stops, COALESCE(stp.tram_stops, 0) AS tram_stops,
           COALESCE(stp.ubahn_stops, 0) AS ubahn_stops, COALESCE(stp.sbahn_stops, 0) AS sbahn_stops, COALESCE(stp.rail_stops, 0) AS rail_stops,
           COALESCE(dep.n_lines, 0) AS n_lines, COALESCE(dep.departures, 0) + COALESCE(sel.add_dep, 0) AS departures,
           COALESCE(dep.places, 0) + COALESCE(sel.add_places, 0) + COALESCE(ex.add_places, 0) AS places, COALESCE(dep.places, 0) AS places_today,
           COALESCE(sel.add_places, 0) + COALESCE(ex.add_places, 0) AS add_places, COALESCE(sel.add_dep, 0) AS add_dep, sel.active_projects AS active_projects,
           1000.0 * (COALESCE(dep.places, 0) + COALESCE(sel.add_places, 0) + COALESCE(ex.add_places, 0)) / (dem.pop_y + {w_jobs!f} * dem.jobs_y) AS places_per_1k_act,
           1000.0 * COALESCE(dep.places, 0) / (dem.pop_24 + {w_jobs!f} * dem.jobs_24) AS places_per_1k_act_24,
           1000.0 * (COALESCE(dep.departures, 0) + COALESCE(sel.add_dep, 0)) / (dem.pop_y + {w_jobs!f} * dem.jobs_y) AS dep_per_1k_act,
           1000.0 * (COALESCE(dep.places, 0) + COALESCE(sel.add_places, 0) + COALESCE(ex.add_places, 0)) / dem.pop_y AS places_per_1k_res,
           dem.pop_y / NULLIF(stp.stations, 0) AS residents_per_station
    FROM dem
    LEFT JOIN stp ON stp.dno = dem.district_no
    LEFT JOIN dep ON dep.dno = dem.district_no
    LEFT JOIN sel ON sel.district_no = dem.district_no
    LEFT JOIN ex ON ex.district_no = dem.district_no
),
r AS (
    SELECT district_no, district, population, jobs, area_km2, residents_per_km2, activity, activity_per_km2,
           stations, bus_stops, tram_stops, ubahn_stops, sbahn_stops, rail_stops, n_lines, departures, places,
           add_places, add_dep, active_projects, activity_24,
           places_per_1k_act, places_per_1k_act_24, dep_per_1k_act, places_per_1k_res, residents_per_station,
           1000.0 * SUM(places) OVER () / SUM(activity) OVER () AS city_places_per_1k_act,
           1000.0 * SUM(places_today) OVER () / SUM(activity_24) OVER () AS city_places_per_1k_act_24,
           1000.0 * SUM(departures) OVER () / SUM(activity) OVER () AS city_dep_per_1k_act,
           SUM(add_places) OVER () AS city_added_places,
           RANK() OVER (ORDER BY activity_per_km2 DESC) AS act_density_rank,
           RANK() OVER (ORDER BY places_per_1k_act DESC) AS places_rank,
           RANK() OVER (ORDER BY dep_per_1k_act DESC) AS dep_rank,
           NTILE(3) OVER (ORDER BY activity_per_km2 DESC, population DESC) AS act_t,
           NTILE(3) OVER (ORDER BY places_per_1k_act DESC) AS places_t,
           NTILE(3) OVER (ORDER BY residents_per_km2 DESC, population DESC) AS res_t0,
           NTILE(3) OVER (ORDER BY places_per_1k_res DESC) AS places_t0,
           NTILE(3) OVER (ORDER BY activity_per_km2_24 DESC, population DESC) AS act_t24,
           NTILE(3) OVER (ORDER BY places_per_1k_act_24 DESC) AS places_t24
    FROM m
)
SELECT district_no, district, ROUND(population) AS population, ROUND(jobs) AS jobs, ROUND(area_km2, 1) AS area_km2,
       ROUND(residents_per_km2) AS density_per_km2, ROUND(activity) AS activity, ROUND(activity_per_km2) AS activity_per_km2,
       stations, bus_stops, tram_stops, ubahn_stops, sbahn_stops, rail_stops, n_lines, departures, places,
       ROUND(add_places) AS add_places, ROUND(add_dep) AS add_dep, active_projects,
       ROUND(city_dep_per_1k_act, 1) AS city_dep_per_1k_act, ROUND(city_added_places) AS city_added_places,
       ROUND(places_per_1k_act) AS places_per_1k_act, ROUND(places_per_1k_act_24) AS places_per_1k_act_2024,
       ROUND(dep_per_1k_act, 1) AS dep_per_1k_act,
       ROUND(places_per_1k_res) AS places_per_1k_res, ROUND(residents_per_station) AS residents_per_station,
       act_density_rank, places_rank, dep_rank, places_rank - act_density_rank AS gap,
       CASE WHEN act_t = 1 AND places_t = 3 THEN 1 ELSE 0 END AS flagged,
       CASE WHEN res_t0 = 1 AND places_t0 = 3 THEN 1 ELSE 0 END AS flagged_w0,
       CASE WHEN act_t24 = 1 AND places_t24 = 3 THEN 1 ELSE 0 END AS flagged_2024,
       CASE WHEN (act_t = 1 AND places_t = 3) AND NOT (res_t0 = 1 AND places_t0 = 3) THEN 'newly flagged'
            WHEN NOT (act_t = 1 AND places_t = 3) AND (res_t0 = 1 AND places_t0 = 3) THEN 'no longer flagged'
            ELSE '' END AS flag_change,
       CASE WHEN (act_t = 1 AND places_t = 3) AND NOT (act_t24 = 1 AND places_t24 = 3) THEN 'newly flagged'
            WHEN NOT (act_t = 1 AND places_t = 3) AND (act_t24 = 1 AND places_t24 = 3) THEN 'no longer flagged'
            ELSE '' END AS flag_change_2024,
       CASE WHEN places_rank - dep_rank > 5 THEN 'mostly bus'
            WHEN dep_rank - places_rank > 5 THEN 'mostly rail' ELSE '' END AS mode_note,
       ROUND(places_per_1k_act / city_places_per_1k_act_24, 3) AS service_ratio,
       ROUND(places_per_1k_act / city_places_per_1k_act, 3) AS ratio_own_year,
       ROUND(places_per_1k_act_24 / city_places_per_1k_act_24, 3) AS ratio_2024,
       ROUND(100 * (places_per_1k_act - places_per_1k_act_24) / city_places_per_1k_act_24, 1) AS ratio_change_pp,
       ROUND(100 * (places_per_1k_act / places_per_1k_act_24 - 1), 1) AS pct_change_places,
       ROUND(city_places_per_1k_act) AS city_places_per_1k_act,
       ROUND(city_places_per_1k_act_24) AS city_places_per_1k_act_2024,
       CASE WHEN act_t = 1 THEN 1 ELSE 0 END AS is_dense,
       {year!d} AS year_n,
       (SELECT ref_date FROM rd) AS ref_weekday
FROM r
ORDER BY gap DESC, act_density_rank
```
