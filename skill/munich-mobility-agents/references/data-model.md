# MUNICH_DATASET data model

Schema `MUNICH_DATASET`, loaded by `EXAKIT_SCHEMA=MUNICH_DATASET exakit data-load ~/munich-open-data` from the flat folder that `prepare_dataset.py` writes. One table per file, table name = file name upper-cased. Column names below are the CSV headers; confirm their types with `describe_exasol_tables_and_views` because a CSV load may leave dates and decimals as VARCHAR.

**Column names are lowercase and case-sensitive.** exapump creates them exactly as in the CSV header, so every column must be double-quoted in SQL: `SELECT "district_no", "population" FROM MUNICH_DATASET.DISTRICTS`. Unquoted `district_no` fails with "object DISTRICT_NO not found". Table and schema names are upper case and need no quotes.

**Types as loaded (verified):** dates are `DATE` (`count_date`, `start_date`, `end_date`, calendar dates), counts are `DECIMAL(36,0)`, measurements are `DOUBLE`, text is `VARCHAR`. GTFS `arrival_time` / `departure_time` are text `HH:MM:SS` (can exceed 24:00). Roadworks with a non-date start in the source (e.g. "Beginn vor mehr als einem Jahr") have `start_date` NULL and the original text in `start_raw`.

All coordinates are **WGS84** (`lat`, `lon` in degrees). Every point table carries `district_no` (1–25) computed by point-in-polygon against the district boundaries, so district joins are plain equality joins. Polygons are WKT in WGS84 with `lon lat` order.

## Tables

### DISTRICTS (25 rows) — Munich's 25 Stadtbezirke
| column | meaning |
|---|---|
| district_no | 1–25, the join key everywhere |
| district_name | e.g. Altstadt-Lehel |
| population, population_pct | residents and share of city |
| area_km2, area_pct, area_sqm | area in km², share of city, m² from the boundary polygon |
| density_per_km2 | residents per km² |
| centroid_lat, centroid_lon | centroid for maps |
| polygon_wkt | POLYGON/MULTIPOLYGON in WGS84 |

### DISTRICT_EMPLOYMENT (25 rows) — workers at place of work per district
| column | meaning |
|---|---|
| district_no, district_name | join key, name |
| jobs_2022 | Erwerbstätige am Arbeitsort 2022 (all workers incl. civil servants and self-employed), rounded to 100 |
| jobs_2040_forecast | the city's forecast for 2040 |
| basis, source | LHM Referat für Stadtplanung, Erwerbstätigenprognose 2025 (empirica 2024), Tabelle 3 |

A modelled city estimate, not a count: no open per-district employment count exists. No licence stated, so internal analysis only. Activity density = (`population` + `jobs_2022`) / `area_km2`.

### DISTRICT_POPULATION (25 rows) — residents per district, past and forecast
| column | meaning |
|---|---|
| district_no, district_name | join key, name |
| pop_2015, pop_2024, pop_2025 | Hauptwohnsitz counts at 31 Dec (Indikatorenatlas Bevölkerung). `pop_2024` equals `DISTRICTS.population` |
| pop_2045_forecast | official forecast, Demografiebericht München Teil 2 (Bevölkerungsprognose 2025–2045) |
| new_homes_2025_2045 | assumed new-build band (text, e.g. `>10,000`) |
| source | sources of counts and forecast |

### PT_PROJECT_STATIONS (88 rows, 17 projects) — planned rail and tram projects, one row per station and line
Curated in `scripts/data/pt_projects.csv` (sources and notes per row). Columns: `project_id`, `project_name`, `mode` (a `line_mode` value), `line`, `station_name`, `lat`, `lon`, `district_no` (point-in-polygon), `station_is_new` (per mode), `opening_year`, `opening_year_risk`, `opening_year_model` (= `opening_year`, or 2040 when none is published; then `opening_year_assumed` = 1), `status` (in_operation / under_construction / approved / planning / on_hold / blocked), `funded`, `trains_per_hour_peak`, `trains_per_hour_offpeak` (per direction and line), `analog_line` (an existing line whose weekday service is the proxy when no frequency is published), `source_url`, `verified`, `note`. Rows with `station_name = 'unknown'` have no stops published and add no supply. The 2. Stammstrecke line table (2017 start concept) is unverified; its lines are re-routed, not purely added.

The forecast gives district values for 2045 only; any year in between is an interpolation (state it as such). Jobs are forecast for 2040 (`DISTRICT_EMPLOYMENT.jobs_2040_forecast`).

### ROADWORKS (~5,700 rows) — current and planned roadworks, four-week horizon
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

### MVV_STOPS (~28,000 rows; ~4,100 inside Munich) — GTFS stops
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

### MVV_ROUTES (~900), MVV_TRIPS (~113,000), MVV_STOP_TIMES (~2.2M), MVV_CALENDAR (~1,700), MVV_CALENDAR_DATES (~9,600), MVV_AGENCY (~100) — GTFS
- `MVV_ROUTES`: route_id, agency_id, route_short_name, route_long_name, route_type (GTFS code), route_mode (raw decode of route_type; stores S-Bahn as Tram), route_color, **line_mode** (use this one: S-Bahn, U-Bahn, Regional rail, Tram, Bus), **is_night** (1 for N-lines). `line_mode` is the join key to VEHICLE_CAPACITY.
- `MVV_TRIPS`: route_id, service_id, trip_id, trip_headsign, direction_id.
- `MVV_STOP_TIMES`: trip_id, arrival_time, departure_time (text HH:MM:SS, may exceed 24:00), stop_id, stop_sequence.
- `MVV_CALENDAR`: service_id, monday..sunday (1/0), start_date, end_date (YYYY-MM-DD). `MVV_CALENDAR_DATES`: service_id, date, exception_type (1 added, 2 removed).
- Feed covers 2026-09-01 to 2026-11-30. **Scheduled service only: no passengers, delays, crowding or live positions.**

### VEHICLE_CAPACITY (5 rows) — how many people one scheduled trip can carry, per line_mode
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

### LINE_CAPACITY (~23 rows) — per-line overrides where the formation differs from the mode
| column | meaning |
|---|---|
| line, line_mode | join to `MVV_ROUTES.route_short_name` and `line_mode` |
| capacity_per_trip | replaces the mode value for this line: U1/U2/U3/U5/U6/U8 930 (six-car), U4/U7 580 (4-car A/B), tram 20 257 (coupled Avenio pair), MetroBus 50–63 and 68 100 (articulated) |
| basis, sources | why, and where from |

Use `COALESCE(line override, mode value)`; the snippet does it. These are planning values, not measured loads. A departure weighted by `capacity_per_trip` is **places offered**. Use places for supply questions (a U-Bahn train is not a bus), departures for frequency questions, and `runs_on_street = 1` for what surface roadworks can disrupt.

### BIKE_COUNTS_DAILY (~970 rows) — permanent bicycle counters, one row per counter per day, with weather
| column | meaning |
|---|---|
| count_date | YYYY-MM-DD, Jan–Jul 2026 |
| station | Arnulf, Erhardt, Hirsch, Kreuther, Margareten, Olympia |
| dir_1, dir_2, total | counts per direction and total |
| temp_min_c, temp_max_c | °C |
| rain_mm, cloud_cover_pct, sunshine_hours | weather that day |

### BIKE_COUNTS_15MIN (~93,000 rows) — same counters, 15-minute resolution
count_date, time_start, time_end (HH:MM), station, dir_1, dir_2, total.

### BIKE_COUNT_STATIONS (6 rows)
station, station_name, lat, lon, direction_1, direction_2, district_no. (Arnulf is missing in May–July 2026.)

### CYCLING_INFRASTRUCTURE (~21,000 rows) — cycle-path segments maintained by the city
segment_id, street, length_m, path_type (e.g. Getrennter Rad- und Gehweg, Radfahrstreifen, Fahrradstraße …), start_lat/lon, end_lat/lon, mid_lat/lon, district_no.

### MVG_BIKE_TRIPS (optional, only if prepared with --with-mvg-bikes)
trip_no, start_time, end_time, start_lat/lon, end_lat/lon, rental_is_station, rental_station_name, return_is_station, return_station_name, year. **Historical only: the MVG Rad service ended in September 2025.**

## Joins
- District rollups: `X.district_no = DISTRICTS.district_no` for stops, roadworks, cycle segments, counters.
- Departures per stop: `MVV_STOP_TIMES st JOIN MVV_TRIPS t ON st."trip_id" = t."trip_id" JOIN MVV_ROUTES r ON t."route_id" = r."route_id" JOIN MVV_CALENDAR c ON t."service_id" = c."service_id"` — filter `c."tuesday" = 1` (or any weekday) and a date inside the feed window for a typical weekday.
- Places offered: add `JOIN VEHICLE_CAPACITY v ON v."line_mode" = r."line_mode"` and `SUM(v."capacity_per_trip")` instead of `COUNT(*)`.
- Proximity: filter both sides to the same `district_no` (or neighbouring ones) first, then apply the distance below. A full cross join of roadworks × stops is 160M pairs; the district filter cuts it to a few million, which Exasol handles in seconds.

## Haversine distance in metres (Exasol SQL)
```sql
2 * 6371000 * ASIN(SQRT(
    POWER(SIN(RADIANS(b."lat" - a."lat") / 2), 2) +
    COS(RADIANS(a."lat")) * COS(RADIANS(b."lat")) * POWER(SIN(RADIANS(b."lon" - a."lon") / 2), 2)
)) AS distance_m
```
Exasol also has GIS functions (`ST_GEOMFROMTEXT`, `ST_POINT`, `ST_CONTAINS`, `ST_DISTANCE`, `ST_INTERSECTS`) on `GEOMETRY` columns; `polygon_wkt` and `shape_wkt` can be wrapped in `ST_GEOMFROMTEXT(...)` for point-in-polygon or intersection questions. Distances from `ST_DISTANCE` on lat/lon are in degrees, so prefer the haversine above for metres.

## Example
```sql
SELECT s."station", d."district_name", AVG(b."total") AS avg_daily
FROM MUNICH_DATASET.BIKE_COUNTS_DAILY b
JOIN MUNICH_DATASET.BIKE_COUNT_STATIONS s ON s."station" = b."station"
JOIN MUNICH_DATASET.DISTRICTS d ON d."district_no" = s."district_no"
WHERE b."rain_mm" > 1
GROUP BY 1, 2 ORDER BY 3 DESC;
```

## Known gaps (say them)
- No passenger counts, delays, crowding, live traffic or event data.
- Vehicle capacities are planning values per mode, not the formation of each individual trip.
- Six counters for the whole city; Arnulf missing May–July.
- Roadworks horizon is the next four weeks from the download date (September 2026 snapshot).
- GTFS `shapes` is empty in this feed, so route geometry is not available; use stop sequences.
- Population figures are a point-in-time snapshot from the portal.
