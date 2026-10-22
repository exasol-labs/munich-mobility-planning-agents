# 2 · Load the Munich data

**Goal:** the 20 tables of schema `MUNICH_DATASET` loaded and checked.

The data is a zip of 20 load-ready CSVs, about 18 MB zipped and 285 MB unzipped. [data/README.md](../data/README.md) describes every table and its source.

## 2.1 Download and unzip
Download **[munich-dataset.zip](https://github.com/exasol-labs/munich-mobility-planning-agents/releases/download/data-v1/munich-dataset.zip)** and save it in the repo's `data/` folder. Then unzip it there:
```bash
unzip -o data/munich-dataset.zip -d data/
```
This creates `data/munich-dataset/` with one CSV per table. The zip and the folder are gitignored.

## 2.2 Load
```bash
exakit data-load
```
1. Choose **A local CSV / Parquet / JSON file, or a folder of them**.
2. Enter the **full path** of `data/munich-dataset`.
3. Target schema: `MUNICH_DATASET`.

Each file becomes one table named after it, e.g. `districts.csv` → `MUNICH_DATASET.DISTRICTS`. 

## 2.3 Check with your agent
Ask:
```text
What tables are in the MUNICH_DATASET schema and how many rows does each have? Show the SQL.
```
The agent shows one query on the system tables and a result like this:

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


Next: [3 · First questions](03-first-questions.md)
