# 7. v4: Rail and tram projects as scenarios

About 20 minutes. You need v3 from [06-v3-forecast.md](06-v3-forecast.md).

## What you'll build

v3 plus a **Scenarios** foldout, where you switch on Munich's planned rail and tram projects, one at a time or with presets. A project adds places from its opening year onward, and markers show its stations on the map. Now you can ask: how much of the decline to 2045 do the funded projects make up, and where?

**URL:** http://127.0.0.1:5100/apps/munich-mobility-planning-v4

## The idea: projects as switchable supply

`PT_PROJECT_STATIONS` holds **17 projects in 88 station rows**, curated from official sources in `data/source/pt_projects.csv`. Each row has a station, a district, a mode and line, an opening year (and a risk year where one is published), a status, a funding flag, and either a published frequency or an analog line. Four rules turn a project into places:

1. **When it counts:** once the year ≥ its opening year. With "pessimistic dates" ticked, it counts from its risk year instead. Projects without a published year are assumed to open in 2040.
2. **Added departures per station** = (trains per hour peak × 6 + trains per hour off-peak × 13) × 2 directions. Where no frequency is published, the project uses the mean weekday departures per station of an **analog line** (e.g. U5 for the U5 extensions).
3. **Places** = departures × the line's capacity per trip, as everywhere else.
4. **The 2nd Stammstrecke** gets its own rule:
   - The new-tunnel trains are added at the 5 tunnel stations.
   - Nothing is removed from the old trunk, because the freed slots are assumed to be reused.
   - Every S-Bahn line except **S2, S5, S7 and S20** gets at least 15-minute service: ≥ 152 departures per Munich station and weekday (4 trains/h × 19 h × 2 directions).

   The sources are the 2017 start concept (its line table is unverified) and Landtag paper 17/17196. S5 is excluded because it is a later reinforcement line that isn't in that concept.

The **funded** projects ("Funded only" preset) are:
- Tram-Westtangente section 2
- Tram Münchner Norden (tram 23)
- U5 to Pasing
- the 2nd Stammstrecke
- the Laim inbound S-Bahn stops restored
- the S-Bahn halt Berduxstraße

## Build it with Claude (the main path)

```text
Use the urban-planning agent. Build the Dash Server app munich-mobility-planning-v4 following the spec in
dashboards/munich-mobility-planning-v4/README.md. Start from your v3 app (munich-mobility-planning-v3) and add
only what the spec adds: the project rules in the SQL (frequency or analog line, Laim restore, the 2nd
Stammstrecke 15-minute rule, opening and risk years), projects.sql, the Scenarios foldout with presets,
checklists and pessimistic dates, the status line and the station markers.
Rules: Dash Server only, through the dash-server MCP tools (no artifact, HTML file or inline chart). All SQL
read-only through the exasol MCP. Show me each SQL statement before you run it and before you interpret its
result. Check None, Funded only, Everything discussed and 2nd Stammstrecke only at 2045, w = 1 against the
"Reference checks" in the spec, then deploy, run the healthcheck and give me the URL.
```

This is the biggest step in the series. If Claude's numbers differ, ask it to diff its SQL against `dashboards/munich-mobility-planning-v4/queries/ranking.sql`.

## Shortcut: deploy the finished version

```text
Deploy the app in dashboards/munich-mobility-planning-v4 to Dash Server as munich-mobility-planning-v4 (app_create_exasol_dashboard, copy all files, app_deploy_draft, app_run_healthcheck) and give me the URL.
```

## Look at it

- **Set the year to 2045 and open Scenarios.** Pick "Funded only". The status line reads "Scenario: Funded only · w = 1.0 · 6 project(s) active in 2045 · +7.3 M places/day net".
- **Step the slider back.** Projects switch on in their opening years: Tram-Westtangente and the Laim restore in 2028, Tram 23 in 2031, the 2nd Stammstrecke in 2035, U5 Pasing in 2036.
- **Tick "Pessimistic dates".** At 2035 the 2nd Stammstrecke drops out (risk year 2037). At 2045 nothing changes, because every funded project is open by then even at its risk year.
- **Untick one project.** The selection matches no preset, so the status line says "Custom".
- **Read the badges** on each project: funded or not, verified or partly unverified, and notes such as "no stations published, adds nothing".
- **Hover a station marker** to see its project, line and calculation method. A filled dot is a new station; a ring is an existing station gaining a line.
- **Hover a district** to see which projects are active there and how many places they add.
- **Try "Everything discussed"** and look at Aubing-Lochhausen-Langwied. It recovers mostly through the unfunded U5 to Freiham, whose year is a placeholder.
- **"SQL executed"** now lists `ranking.sql` (with the project ids in `projects`), `projects.sql` and `geo.sql`.

> **Check** (2045, w = 1)
> - None: **−13.37 %** (as v3)
> - Funded only: **−6.84 %**, **+7.3 M** places per weekday, which offsets **49 %** of the decline
> - Everything discussed: **−2.42 %**, **+12.2 M**, which offsets **82 %**; 14 of 17 projects open
> - 2nd Stammstrecke only: **−8.65 %**, **+5.27 M** (+3,237,600 from the tunnel, +2,035,200 from the 15-minute interval)
> - Funded only, by district: Laim +32.0 %, Au-Haidhausen +16.6 %, Pasing-Obermenzing +15.2 %; Aubing-Lochhausen-Langwied still −35.3 %; Feldmoching-Hasenbergl and Allach-Untermenzing get nothing
>
> ```bash
> python3 scripts/check_dashboard.py munich-mobility-planning-v4
> python3 scripts/verify_numbers.py --case R4
> python3 scripts/verify_numbers.py --case R5
> ```

## What the data can't tell you

- Opening years, frequencies and analog lines are assumptions from public sources. `research/pt-projects-notes.md` gives the source and status of each one. Placeholder years (2040) are marked in the labels.
- The 2nd Stammstrecke line table is unverified, and the 2025 tender may swap branches.
- The model adds capacity where the stations are. It doesn't know whether people would use it, how travel times change, or whether a project gets built on time or at all.
- Still scheduled service only: no passengers, crowding or delays.

## How it works

The analog line is a real line's average weekday departures per Munich station:

```sql
ana AS (
    -- rule 1b: the analog line's mean weekday departures per station inside Munich on the reference Wednesday
    SELECT line_mode, line, 1.0 * COUNT(*) / COUNT(DISTINCT station_id) AS dep_per_station
    FROM ev_sel WHERE in_munich = 1 GROUP BY line_mode, line
),
```

The published frequency formula, inside the `comps` CTE:

```sql
                           THEN (COALESCE(ps."trains_per_hour_peak", ps."trains_per_hour_offpeak") * 6
                                 + COALESCE(ps."trains_per_hour_offpeak", ps."trains_per_hour_peak") * 13) * 2
```

The 15-minute rule of the 2nd Stammstrecke lifts each eligible line and station to at least 152 departures. Stations that already have more keep their number, so nothing is counted twice:

```sql
    FROM ev_sel WHERE line_mode = 'S-Bahn' AND in_munich = 1 AND line NOT IN ('S2', 'S5', 'S7', 'S20')
```
```sql
           '15-min basic interval: GREATEST(today, 152)', GREATEST(sb.dep_today, 152) - sb.dep_today, sb.capacity, NULL
```

A project counts only if it is selected and open in the chosen year:

```sql
    WHERE INSTR(',' || {projects!s} || ',', ',' || c.project_id || ',') > 0
      AND {year!d} >= CASE WHEN {pessimistic!d} = 1 THEN COALESCE(m.oy_risk, m.oy_model) ELSE m.oy_model END
```

The added places go only into the selected year's supply. The 2024 baseline stays today's timetable, so the colours remain comparable. The full rules, the project table and the presets are in [dashboards/munich-mobility-planning-v4/README.md](../dashboards/munich-mobility-planning-v4/README.md).

Next: [08-v5-assistant.md](08-v5-assistant.md), an assistant that drives this view.
