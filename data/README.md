# Data

The dataset is published as a **GitHub release asset**, not in git: `munich-dataset.zip`, 18 MB. [dataset.json](dataset.json) has the URL (release `data-v1`), the size and the SHA-256 checksum. `python3 scripts/load_data.py` downloads, checks and loads it. The zip holds one folder, `munich-dataset/`, with 20 load-ready CSVs: one table each in schema `MUNICH_DATASET`. They are cleaned, converted to WGS84 coordinates, and tagged with `district_no` (1–25) by point-in-polygon, so every district join is a plain equality join. Loading is described in [tutorial chapter 2](../tutorial/02-load-data.md). Column-level documentation is in [skill/munich-mobility-agents/references/data-model.md](../skill/munich-mobility-agents/references/data-model.md).

| Table | Rows | Content | Source |
|---|---:|---|---|
| DISTRICTS | 25 | The 25 Stadtbezirke: population (end 2024), `area_km2`, `density_per_km2`, centroid, polygon (WKT) | Munich open data: population by district, district boundaries |
| DISTRICT_POPULATION | 25 | Residents counted 2015 / 2024 / 2025, and the **official forecast for 2045** | Counts: Indikatorenatlas Bevölkerung (opendata.muenchen.de). Forecast: Demografiebericht München Teil 2, Kleinräumige Bevölkerungsprognose 2025–2045 |
| DISTRICT_EMPLOYMENT | 25 | Workers at place of work, 2022, and the forecast for 2040 (a **modelled estimate**) | LHM Referat für Stadtplanung, Erwerbstätigenprognose 2025 (empirica 2024), Tabelle 3. No licence stated: internal analysis |
| MVV_STOPS, MVV_ROUTES, MVV_TRIPS, MVV_STOP_TIMES, MVV_CALENDAR, MVV_CALENDAR_DATES, MVV_AGENCY, MVV_FEED_INFO, MVV_TICKETING_DEEP_LINKS | 28,330 · 906 · 112,882 · 2,176,946 · 1,734 · 9,638 · 99 · 1 · 1 | The MVV **scheduled** timetable (GTFS, 1 Sep–30 Nov 2026), enriched with `line_mode`, `stop_mode`, `in_munich` and `district_no` | MVV open data (GTFS) |
| VEHICLE_CAPACITY | 5 | Planning capacity of one scheduled trip per mode (S-Bahn 1,200, U-Bahn 900, regional 500, tram 205, bus 90), with sources | Researched for this project; sources in the table |
| LINE_CAPACITY | 23 | Per-line overrides where the formation differs (e.g. U4/U7 580, MetroBus 100) | Same |
| PT_PROJECT_STATIONS | 88 | 17 planned rail and tram projects, one row per station and line: opening year, status, funding, frequency or analog line, district | Curated from official sources in `source/pt_projects.csv`; every row has a source URL and a verified flag |
| CYCLING_INFRASTRUCTURE | 21,172 | Cycle-path segments with type, length and midpoint | Munich open data: Radverkehrsnetz |
| BIKE_COUNT_STATIONS, BIKE_COUNTS_DAILY, BIKE_COUNTS_15MIN | 6 · 972 · 93,312 | The permanent bicycle counters, Jan–Jul 2026, daily with weather and in 15-minute intervals | Munich open data: Raddauerzählstellen |
| ROADWORKS | 5,702 | Current and planned roadworks with dates, impact and centroid | Munich open data: Baustellen |

**What the data can't answer:** passenger numbers, crowding, delays or live traffic. MVV GTFS is the schedule only, and no open dataset of passengers per stop exists for Munich (see `research/`). Cycle traffic is known only at five counters.

## Publishing a new data version (maintainers)
The zip stays out of git because GitHub rejects files over 100 MB (`mvv_stop_times.csv` is 258 MB) and Git LFS has small free quotas. A release asset can be up to 2 GB and doesn't count against either. To publish a new version:
```bash
cd data/munich-dataset/.. && zip -qr -9 munich-dataset.zip munich-dataset   # the zip must contain the folder munich-dataset/
shasum -a 256 munich-dataset.zip && stat -f %z munich-dataset.zip            # Linux: sha256sum / stat -c %s
gh release create data-vN munich-dataset.zip --title "Munich dataset vN" --notes "…"
```
Then update `url`, `release_tag`, `bytes` and `sha256` in `dataset.json`, and the row counts in `tests/expected.json` if they changed.

## Rebuilding the CSVs yourself (optional)
`scripts/prepare_dataset.py` turns the portal download (`munich-open-data.zip`) into this folder. It also writes the curated tables (capacities, employment, population forecast, project stations from `source/pt_projects.csv`).
```bash
python3 scripts/prepare_dataset.py ~/Downloads/munich-open-data.zip --out data/munich-dataset
```
