# munich-mobility-planning-v4: Forecast with rail and tram scenarios

**Question:** which planned rail and tram projects make up for Munich's growth to 2045, and where?

**URL once deployed:** http://127.0.0.1:5100/apps/munich-mobility-planning-v4 · tutorial chapter: [07-v4-scenarios.md](../../tutorial/07-v4-scenarios.md) · builds on [v3](../munich-mobility-planning-v3/README.md)

v4 adds a **Scenarios** foldout. You can switch on 17 planned projects from `PT_PROJECT_STATIONS`, one by one or with presets. A project adds places offered from its opening year onward. Station markers show where.

## What it shows (top to bottom)

1. **Header:** "Munich Mobility Planning", subtitle "v4 – Forecast with rail and tram scenarios", then the line "Which districts, counting residents and jobs, have lower scheduled public transport supply today and as the city grows to 2045, with or without the planned rail and tram projects? Scheduled service only, not passengers." Meta line, e.g. "Year 2045 · jobs weight w = 1 · projects: … · source: MUNICH_DATASET on Exasol, read-only".
2. **Intro card** (verbatim):
   > **Which planned rail and tram projects make up for the growth, and where?**
   > As in v3, the year slider moves through Munich's growth to 2045. Open **Scenarios** to switch on planned projects: funded ones such as Tram-Westtangente, Tram 23/24, U5 to Pasing and the 2nd Stammstrecke (with 15-minute S-Bahn service), or projects that are only under discussion, such as U5 to Freiham and U9. A project counts from its planned opening year, and "pessimistic dates" uses the published risk years. Station markers show where each project adds service.
3. **Year slider** in its own card: 2024–2045, step 1, default 2024.
4. **Scenarios foldout** (folded by default). Its summary line shows a status, e.g. "Scenario: Funded only · w = 1.0 · 6 project(s) active in 2045 · +7.3 M places/day net". Inside:
   - the hint "A project adds supply from its opening year onward. Preset first, then switch single projects on or off."
   - **Presets** (radio): "None (today's timetable)", "Funded only", "Funded + planned", "Everything discussed".
   - **Job weight (w)**: the v2 input.
   - **Pessimistic dates**: a checkbox, "use the risk year where one is published".
   - **Four project checklists** by status: "Under construction" (`under_construction`, `in_operation`), "Approved", "Planning", "On hold or blocked" (`on_hold`, `blocked`). Each is sorted by opening year. Each label shows the short name, "opens 2035 (risk 2037)" or "no date published, assumed 2040", a **funded / not funded** badge, a **verified / partly unverified** badge and a note where it matters. For example: "no stations published, adds nothing".
5. **Map and change chart** side by side, as in v3, with these additions:
   - **Map title:** "How well served is each district? — <year> (<n> of <m> selected projects open)", or "(if service stays as it is today)" when nothing is selected.
   - **Station markers** of the active projects: a filled dot for a new station ("project: new station"), a ring for an existing station gaining a line ("project: existing station gaining a line"). Hover a marker for the station, project, line and calculation method.
   - **District hover** adds "projects: … (+N places/weekday)" for the projects active in that district.
   - **Chart subtitle:** "% change in places per 1,000 activity between 2024 and the selected year, with the active projects."
6. **Caveat line** under the map: "Scheduled service only (capacity offered, not passengers or delays); residents between 2024 and 2045 interpolated to the 2045 forecast; jobs a modelled estimate (2022 as the 2024 baseline, to 2040, held after); projects per Scenarios, their dates and frequencies are assumptions. 2nd Stammstrecke: new-tunnel trains plus a 15-minute basic service on all S-Bahn lines except S2, S5, S7 and S20 (2017 concept, unverified line table; S5 is a later reinforcement line not in that concept); old-trunk slots assumed reused."
7. **"SQL executed" foldout** at the bottom: `ranking.sql`, `projects.sql`, `geo.sql`.

## Files

| File | Role |
|---|---|
| `app.py` | Layout, presets (`preset_ids`), project labels, the status line, the map with station markers, the change chart. Three callbacks: project options on load, preset → checklists, and `refresh` (w, year, pessimistic, the four checklists → map, chart, titles, status, SQL list). Plus `set_w` as in v2. |
| `queries/ranking.sql` | Unchanged from v1 (byte-identical). Called with the selected project ids as a comma-separated string (`'none'` if empty) and `pessimistic` 0/1. |
| `queries/projects.sql` | One row per project (`kind = 'project'`: status, funded, opening years, verified share, gross/removed/net places, stations by district) and one row per added station (`kind = 'station'`: name, lat, lon, new or existing, line, method). Shares its CTEs with `ranking.sql`. Cached for an hour. |
| `queries/geo.sql` | As in v1. |
| `queries/sql_smoke.json` | `ranking.sql` at `year = 2045`, `w_jobs = 1.0`, `projects = "stammstrecke2,laim_inbound_restore,u5_pasing"`; `projects.sql` and `geo.sql` without parameters. |
| `sql_log.py`, `munich_ui.py`, `dash_server_exasol.py`, `requirements.txt` | As in v1. |

`queries/business/` and `queries/system/` are empty folders left by the scaffold.

## The projects

`PT_PROJECT_STATIONS` has 17 projects and 88 station rows, curated from official sources in `data/source/pt_projects.csv`. `opening_year_model` is the published opening year, or 2040 where none is published (then `opening_year_assumed = 1`). Net places per weekday once open, from `research/urban-planning.md`:

| Project (short name) | Status | Funded | Opens (risk) | Net places per weekday | Method |
|---|---|---|---|---|---|
| 2. Stammstrecke | under construction | yes | 2035 (2037) | +5,272,800 | new tunnel +3,237,600; 15-minute interval +2,035,200 |
| U9-Spange | planning | no | 2040 placeholder | +2,185,838 | analog U6 |
| U5 Pasing–Freiham | planning | no | 2040 placeholder | +1,473,120 | analog U5 |
| U5 Laimer Platz–Pasing | under construction | yes | 2036 | +1,104,840 | analog U5 |
| U4 Ost | planning | no | assumed 2040 | +424,917 | analog U4 |
| Tram-Westtangente (14) | under construction | yes | 2028 (2031) | +420,660 | frequency |
| Laim inbound restored | under construction | yes | 2028 | +312,000 | outbound departures at Laim as proxy |
| Tram Münchner Norden PFA 1 | under construction | yes | 2031 | +280,440 | frequency |
| Tram Münchner Norden PFA 2 | planning | no | 2031 placeholder | +280,440 | frequency |
| Tram-Nordtangente | blocked | no | assumed 2040 | +270,293 | analog 23 |
| S-Bahn Nordring shuttle | planning | no | assumed 2040 | +223,200 | frequency |
| S-Bahn halt Berduxstraße | planning | yes | assumed 2040 | +199,482 | analog S2 |
| Tram Johanneskirchen | planning | no | assumed 2040 | +84,589 | analog 16 |
| Regional halt Poccistraße, Tram Lerchenauer Feld, U26, Augsburg express | – | no | – | 0 | no stations published, or already in the 2nd trunk |

With both the 2nd Stammstrecke and the Laim restore on, the 15-minute rule at Laim is applied to the restored numbers, which corrects the total by −300,000 places (−250 departures), so nothing is counted twice.

**Presets** (`preset_ids` in `app.py`):
- **Funded only:** `funded = 1`. These are laim_inbound_restore, sbahn_berduxstrasse, stammstrecke2, tram_muenchner_norden_1, tram_westtangente_2 and u5_pasing.
- **Funded + planned:** funded, or status `under_construction`, `in_operation`, `approved` or `planning`.
- **Everything discussed:** all 17.

## How it computes

Everything from v3 stays the same: supply = weekday departures × capacity per trip at stops inside Munich, activity = residents + w × jobs for year Y, colours against the 2024 city average. The project logic lives in `ranking.sql` (and the same CTEs in `projects.sql`). The rules are numbered in the SQL comments.

**Rule 1a, published frequency:** departures per station = (trains per hour peak × 6 + off-peak × 13) × 2 directions. Peak falls back to off-peak and the other way round.
**Rule 1b, analog line:** where no frequency is published, the departures are the analog line's mean weekday departures per station inside Munich on the reference Wednesday.
**Rule 2:** places = departures × the project line's capacity per trip (`LINE_CAPACITY` override, else `VEHICLE_CAPACITY` by mode).
**Rule 3, Laim inbound restored:** restored departures = today's outbound minus today's inbound departures at Laim, per line.

```sql
           COALESCE(CASE WHEN ps."project_id" = 'laim_inbound_restore' THEN laim.restored_dep
                         WHEN COALESCE(ps."trains_per_hour_peak", ps."trains_per_hour_offpeak") IS NOT NULL
                           THEN (COALESCE(ps."trains_per_hour_peak", ps."trains_per_hour_offpeak") * 6
                                 + COALESCE(ps."trains_per_hour_offpeak", ps."trains_per_hour_peak") * 13) * 2
                         ELSE ana.dep_per_station END, 0) AS departures,
```
```sql
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
```

**Rule 4, the 2nd Stammstrecke (option 2):**
- The new-tunnel trains at the 5 tunnel stations count by rule 1a.
- Nothing is removed from the old trunk; the freed slots are assumed to be reused.
- Every S-Bahn line except S2, S5, S7 and S20 gets at least 15-minute service at each station inside Munich it serves today. 152 = 4 trains/h × 19 h × 2 directions.

The exclusions follow Landtag 17/17196 (2017) for S2, S7 and S20; S5 is a later reinforcement line that is not in the 2017 concept. The line table of the 2017 start concept is unverified.

```sql
sb AS (
    -- 2nd trunk, 15-minute basic interval: today's departures per S-Bahn line and station inside Munich,
    -- all lines except S2, S7 and S20 (Landtag 17/17196, 2017) and S5 (later reinforcement line, not in that concept)
    SELECT line, station_id, MIN(district_no) AS district_no, MIN(capacity) AS capacity, COUNT(*) AS dep_today
    FROM ev_sel WHERE line_mode = 'S-Bahn' AND in_munich = 1 AND line NOT IN ('S2', 'S5', 'S7', 'S20')
    GROUP BY line, station_id
),
```
```sql
    -- rule 4: 2nd trunk = new-tunnel trains (above) plus a 15-minute basic interval; nothing removed from the old trunk (slots reused).
    -- every station a non-excluded S-Bahn line serves today: departures_new = GREATEST(departures_today, 152) = 4/h x 19 h x 2 directions
    SELECT 'stammstrecke2', 'upgraded: 15-minute basic interval', sb.district_no, sb.station_id, NULL, NULL, NULL, 'S-Bahn', sb.line,
           '15-min basic interval: GREATEST(today, 152)', GREATEST(sb.dep_today, 152) - sb.dep_today, sb.capacity, NULL
    FROM sb WHERE sb.dep_today < 152
```

The lines lifted (stations inside Munich served today / lifted to 152 / places added per weekday) are S1 14 / 0 / 0, S3 16 / 4 / +88,800, S4 16 / 16 / +729,600, S6 15 / 15 / +655,200 and S8 18 / 18 / +561,600. In total 53 stations are lifted, adding +2,035,200 places.

**Rule 5, when a project counts:** only if it is switched on and the year has reached its opening year, or its risk year with pessimistic dates. The selected ids arrive as one string, `{projects!s}`.

```sql
sel AS (
    -- rule 5: a project counts only if switched on and the year has reached its opening year (risk year when pessimistic)
    SELECT c.district_no, SUM(c.departures) AS add_dep, SUM(c.departures * c.capacity) AS add_places,
           GROUP_CONCAT(DISTINCT c.project_id ORDER BY c.project_id SEPARATOR ',') AS active_projects
    FROM comps c
    JOIN pmeta m ON m.project_id = c.project_id
    LEFT JOIN pmeta rq ON rq.project_id = c.requires_project
    WHERE INSTR(',' || {projects!s} || ',', ',' || c.project_id || ',') > 0
      AND {year!d} >= CASE WHEN {pessimistic!d} = 1 THEN COALESCE(m.oy_risk, m.oy_model) ELSE m.oy_model END
```

The added places go into the year-Y supply only. The 2024 baseline stays today's timetable:

```sql
           COALESCE(dep.places, 0) + COALESCE(sel.add_places, 0) AS places, COALESCE(dep.places, 0) AS places_today,
```

Project rows with `station_name = 'unknown'` or without a district are skipped (`ps` CTE), so they add nothing.

**The status line,** from `app.py`. The net places are `city_added_places` (the sum of `add_places` over all districts):

```python
def status_line(scen, w, n_active, year, added):
    added_txt = f"{added / 1e6:+.1f} M" if abs(added) >= 1e5 else f"{added:+,.0f}"
    return f"Scenario: {scen} · w = {w_text(w)} · {n_active} project(s) active in {year} · {added_txt} places/day net"
```

## Controls

| Control | Effect |
|---|---|
| Year slider (2024–2045) | As in v3; also decides which selected projects are open. |
| Preset | Ticks the matching projects in the four checklists. |
| Project checklists | The selection that is sent as `projects`. |
| Job weight (w) | As in v2. |
| Pessimistic dates | Uses `opening_year_risk` where one is published. |

## Reference checks

From `research/reference-numbers.md`, all at w = 1 (`pessimistic = 0` unless stated):

| Case | Expected |
|---|---|
| 2024, None (R2) | Munich overall +0.0 % |
| 2045, None (R3) | −13.37 % (29,822 vs 34,425) |
| 2045, Funded only (R4) | −6.84 % (32,069); status "6 project(s) active in 2045 · +7.3 M places/day net" (+7,290,222). Offsets 49 % of the decline. |
| 2045, Everything discussed (R5) | −2.42 % (33,593); 14 of 17 projects open; +12.2 M places/day net (+12,232,618). Offsets 82 %. |
| 2045, 2. Stammstrecke only (R6) | −8.65 % (31,448); +5,272,800 places (+3,237,600 tunnel, +2,035,200 15-minute interval). Schwanthalerhöhe 1.564, Neuhausen-Nymphenburg 0.792, Maxvorstadt 0.777: none below its "None" ratio (1.523, 0.776, 0.777). |
| 2045, Funded, districts | Laim 1.566 (+32.0 %), Au-Haidhausen 2.025 (+16.6 %), Pasing-Obermenzing 1.103 (+15.2 %); Aubing-Lochhausen-Langwied 0.558 (−35.3 %), Feldmoching-Hasenbergl and Allach-Untermenzing unchanged (−26.9 %, −17.2 %) |
| 2045, Everything, Aubing | 0.851 (−1.3 %), mainly from the unfunded U5 Freiham |
| 2045, Funded, pessimistic dates | still −6.84 %: all six funded projects open by 2045 even at their risk years |
| Healthcheck | healthy (SQL smoke on all three query files) |

## Deploy

```text
Deploy the app in dashboards/munich-mobility-planning-v4 to Dash Server as munich-mobility-planning-v4 (app_create_exasol_dashboard, copy all files, app_deploy_draft, app_run_healthcheck) and give me the URL.
```

The steps are as in [v1](../munich-mobility-planning-v1/README.md#deploy).

**Verify:** `python3 scripts/check_dashboard.py munich-mobility-planning-v4` (run from the repo root after deploying).

## What it can't tell you

Opening years, frequencies and analog lines are assumptions taken from public sources (see `research/pt-projects-notes.md`); placeholder years are marked as such. The 2nd Stammstrecke line table is unverified, and the 2025 BEG tender may swap branches. The model adds capacity. It does not model where people would actually travel, crowding, travel times, transfers, cost or whether a project gets built. Scheduled service only.
