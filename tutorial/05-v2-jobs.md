# 5. v2: Residents and jobs

About 15 minutes. You need v1 from [04-v1-residents.md](04-v1-residents.md).

## What you'll build

The v1 map with one control, the **job weight w**. Each district is now compared on places per 1,000 **activity**, where activity = residents + w × jobs. At w = 0 you get v1 back. At w = 1 a job counts as much as a resident.

**URL:** http://127.0.0.1:5100/apps/munich-mobility-planning-v2

## The idea: residents aren't the whole demand

The old town has few residents but many offices, shops and universities. Measured per resident, Altstadt-Lehel looks six times better served than the city, but much of that capacity carries people who work there. Adding jobs gives a fairer picture of how many people a district's transport has to serve.

The jobs come from `DISTRICT_EMPLOYMENT`: workers at place of work per district, from the city's Erwerbstätigenprognose 2025, base year 2022. This is a **modelled estimate**, not a count, and no licence is stated for it. Munich publishes no open per-district employment count.

How much should a job weigh against a resident? That's a judgement, which is why w is a control and not a constant.

## Build it with Claude (the main path)

```text
Use the urban-planning agent. Build the Dash Server app munich-mobility-planning-v2 following the spec in
dashboards/munich-mobility-planning-v2/README.md. Start from your v1 app (munich-mobility-planning-v1): copy it
to the new app id and add only what the spec adds (the job weight input, activity = residents + w x jobs, the
new hover and texts).
Rules: Dash Server only, through the dash-server MCP tools (no artifact, HTML file or inline chart). All SQL
read-only through the exasol MCP. Show me each SQL statement before you run it and before you interpret its
result. Check the numbers at w = 1 and w = 0 against the "Reference checks" in the spec, then deploy, run the
healthcheck and give me the URL.
```

## Shortcut: deploy the finished version

```text
Deploy the app in dashboards/munich-mobility-planning-v2 to Dash Server as munich-mobility-planning-v2 (app_create_exasol_dashboard, copy all files, app_deploy_draft, app_run_healthcheck) and give me the URL.
```

## Look at it

- **The default is w = 1.** Compare with v1: Altstadt-Lehel drops from 6.18× to 1.81×, and the city centre evens out.
- **Set w to 0.** The map is exactly v1 again.
- **Try 0.5 and 1.5.** Values snap to steps of 0.25: type 0.6 and it becomes 0.5. Type "abc" and the input goes back to the last valid value.
- **The outlines change.** "Dense" now means the top third by activity per km², so districts with many jobs join the outlined group.
- **Hover** shows residents and jobs, activity per km², and a flag: "yes" if the district is in the densest third and in the bottom third for places.
- **The meta line** under the title shows the current city average.
- **"SQL executed":** change w and watch `w_jobs` change in the `ranking.sql` entry.

> **Check**
> - w = 1: city **34,425** places per 1,000 activity
> - w = 1: **Sendling-Westpark 0.496×** (still the lowest), then Allach-Untermenzing 0.589× and Milbertshofen-Am Hart 0.688×
> - w = 1: **Ludwigsvorstadt-Isarvorstadt 1.882×** is now the highest, ahead of Altstadt-Lehel 1.814×
> - w = 1: no district flagged (at w = 0, Sendling-Westpark is)
> - w = 0: identical to v1 (60,325; 0.40×; 6.18×)
>
> ```bash
> python3 scripts/check_dashboard.py munich-mobility-planning-v2
> python3 scripts/verify_numbers.py --case R2
> ```

## What the data can't tell you

- Jobs are a modelled 2022 estimate of all workers at their place of work (including civil servants and the self-employed), rounded to 100. They are not a count.
- Nothing here tells you how many residents or workers actually use public transport, or when they travel. There are no passenger data.
- w = 1 doesn't mean "a worker makes as many trips as a resident". It's a weighting you choose.

## How it works

Only the denominator changes. The `dem` CTE in `ranking.sql` takes jobs from `DISTRICT_EMPLOYMENT`:

```sql
           e."jobs_2022" + (e."jobs_2040_forecast" - e."jobs_2022") * (LEAST({year!d}, 2040) - 2024) / 16.0 AS jobs_y,
```

At `year = 2024` this is simply `jobs_2022`. The 2022 estimate serves as the 2024 baseline. v3 uses the rest of the formula.

The activity formula, with w as a float placeholder:

```sql
           dem.pop_y + {w_jobs!f} * dem.jobs_y AS activity,
```

and the measure the map divides:

```sql
           1000.0 * (COALESCE(dep.places, 0) + COALESCE(sel.add_places, 0)) / (dem.pop_y + {w_jobs!f} * dem.jobs_y) AS places_per_1k_act,
```

The city average uses the same w, so 1.0× always means "average for this weighting".

In `app.py`, a `dcc.Store` keeps the last valid w and the input snaps to 0.25:

```python
        v = round(v * 4) / 4
```

That's the whole change from v1. `ranking.sql` is byte-identical. The full spec is in [dashboards/munich-mobility-planning-v2/README.md](../dashboards/munich-mobility-planning-v2/README.md).

Next: [06-v3-forecast.md](06-v3-forecast.md), the forecast to 2045.
