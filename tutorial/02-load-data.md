# 2 · Load the Munich data

**Goal:** the 20 tables of schema `MUNICH_DATASET` loaded and checked.
**Time:** about 5 minutes.

The data is published as a release asset of this repo: `munich-dataset.zip`, 20 load-ready CSVs, about 18 MB zipped and 285 MB unzipped. It's too big for git itself, since one file alone is 258 MB. It's already cleaned, converted to WGS84 coordinates and tagged with the district number. [data/README.md](../data/README.md) describes every table and its source, and `data/dataset.json` gives the download URL and checksum.

## 2.1 The quick way: one command
```bash
python3 scripts/load_data.py
```
It downloads the zip from the release (if `data/munich-dataset.zip` isn't there yet), checks its SHA-256, unzips it to `data/munich-dataset/`, loads every table that doesn't exist yet into `MUNICH_DATASET`, and verifies the row counts. It never appends to an existing table. Run it again any time; it only does what's missing. If that worked, skip to 2.3.

## 2.1b Or by hand: download and unzip
Download `munich-dataset.zip` from the URL in `data/dataset.json` (the repo's *Releases* page, tag `data-v1`) into `data/`, then:
```bash
unzip -o data/munich-dataset.zip -d data/
```
This creates `data/munich-dataset/` with one CSV per table. The zip and the folder are gitignored.

## 2.2 Load (by hand)
Interactive:
```bash
exakit data-load
```
1. Choose **A local CSV / Parquet / JSON file, or a folder of them**.
2. Paste the **full path** of `data/munich-dataset`. Run `echo "$PWD/data/munich-dataset"` in the repo folder to get it.
3. Target schema: `MUNICH_DATASET`

Or in one line, without prompts (macOS / Linux / WSL):
```bash
EXAKIT_SCHEMA=MUNICH_DATASET EXAKIT_DATA_FILE="$PWD/data/munich-dataset" exakit data-load </dev/null
```
Each file becomes one table named after it, e.g. `districts.csv` → `MUNICH_DATASET.DISTRICTS`.

> **Loading a second time:** `exakit data-load` won't replace a table that already exists. It skips it, or appends rows by column position, which corrupts the table. To reload, drop the old table first, e.g. `exapump sql -p starter-kit "DROP TABLE MUNICH_DATASET.DISTRICTS"` (that profile has write rights; the Claude MCP login doesn't). Then load that one file again. See [Troubleshooting](10-troubleshooting.md#reloading-a-table).

## 2.3 Check, in Claude Code
Ask:
```
What tables are in the MUNICH_DATASET schema and how many rows does each have? Show the SQL.
```
Claude should show one query on `SYS.EXA_ALL_TABLES` and a table like this:

| Table | Rows | | Table | Rows |
|---|---:|---|---|---:|
| BIKE_COUNTS_15MIN | 93,312 | | MVV_CALENDAR_DATES | 9,638 |
| BIKE_COUNTS_DAILY | 972 | | MVV_FEED_INFO | 1 |
| BIKE_COUNT_STATIONS | 6 | | MVV_ROUTES | 906 |
| CYCLING_INFRASTRUCTURE | 21,172 | | MVV_STOPS | 28,330 |
| DISTRICTS | 25 | | MVV_STOP_TIMES | 2,176,946 |
| DISTRICT_EMPLOYMENT | 25 | | MVV_TICKETING_DEEP_LINKS | 1 |
| DISTRICT_POPULATION | 25 | | MVV_TRIPS | 112,882 |
| LINE_CAPACITY | 23 | | PT_PROJECT_STATIONS | 88 |
| MVV_AGENCY | 99 | | ROADWORKS | 5,702 |
| MVV_CALENDAR | 1,734 | | VEHICLE_CAPACITY | 5 |

Then try the read-only guardrail:
```
Delete the roadworks that have already finished.
```
Claude refuses: the MCP login is read-only, and the database would reject the statement anyway. It offers a filtered SELECT instead.

## Check
- 20 tables with the row counts above.
- `DISTRICTS` sums to 1,603,776 residents (end of 2024).

Next: [3 · Install the planning agent](03-install-agent.md)
