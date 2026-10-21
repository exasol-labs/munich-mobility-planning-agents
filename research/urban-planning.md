# Urban planning: where activity outruns public transport (MUNICH_DATASET, reference weekday 2026-10-21)

**Dashboard: http://127.0.0.1:5100/apps/munich-mobility-planning** ("Munich Mobility Planning", app `munich-mobility-planning`, revision 5, healthcheck healthy). Revision 2 was a byte-identical copy of revision 15 of the former app `munich-urban-planning`; revision 3 keeps only the year slider, the Scenarios foldout, the service map and the change-since-2024 chart, with one caveat line under the map; revisions 4 and 5 (2026-10-19) remodel the 2nd Stammstrecke (option 2, below; revision 5 also excludes S5). The revision numbers quoted in the older sections below are the former app's history. Workspace: `~/.exasol-starter-kit/dash-server/instance/workspaces/_git_worktrees/munich-mobility-planning/apps/munich-mobility-planning/`; the same source is in this repo under `dashboards/munich-mobility-planning-v4/` (plus intro text).

## Rail and tram project scenarios (dashboard revision 5 of `munich-mobility-planning`, 2nd Stammstrecke option 2, 2026-10-19)

**Answer.** By 2045 at w = 1, with no project switched on, city-wide supply falls from 34,425 to 29,822 places per 1,000 activity (−13.37 %). The six funded projects lift that to 32,069 (−6.84 %), which offsets 49 % of the decline. Everything discussed lifts it to 33,593 (−2.42 %), which offsets 82 %.

The largest single contributor is the 2nd Stammstrecke, modelled as the new-tunnel trains plus a 15-minute basic interval on the existing S-Bahn network. It adds +5,272,800 places per weekday net: +3,237,600 from the five tunnel stations and +2,035,200 from lifting 53 Munich S-Bahn stations on S3, S4, S6 and S8 to at least 152 departures. S1 is already above 152; S2, S5, S7 and S20 are excluded. Nothing is removed from the old trunk, so no central district loses supply: Schwanthalerhöhe (1.564 vs 1.523), Neuhausen-Nymphenburg (0.792 vs 0.776) and Maxvorstadt (0.777 = 0.777) end at or above their "none" values.

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

**15-minute basic interval by line** (S-Bahn stations inside Munich served today / lifted to 152 / places added per weekday): S1 14 / 0 / 0 · S3 16 / 4 / +88,800 · S4 16 / 16 / +729,600 · S6 15 / 15 / +655,200 · S8 18 / 18 / +561,600. Excluded: S2, S7 and S20 (2017 concept) and S5 (a later reinforcement line not in that concept; including it would add another +2,166,000, revision 4).

**Method.**
- **Rule 1:** departures = (trains per hour peak × 6 + off-peak × 13) × 2. Where no frequency is published, the analog line's mean weekday departures per Munich station on the reference Wednesday.
- **Rule 2:** places = departures × the line's capacity per trip (LINE_CAPACITY override, else VEHICLE_CAPACITY; 1,200 per S-Bahn trip).
- **Rule 3:** Laim inbound restored = today's outbound departures minus today's inbound ones, per line.
- **Rule 4 (option 2):** the 2nd trunk adds its 2017 start-concept tunnel lines at the 5 tunnel stations (Rule 1), removes nothing from the old trunk (freed slots assumed reused), and applies a 15-minute basic interval: for every S-Bahn line except S2, S5, S7 and S20, at every station inside Munich it serves today, departures = GREATEST(today, 152), where 152 = 4 trains/h × 19 h × 2 directions. With Laim restored also on, the rule is applied after the restore. Station markers stay on the 5 tunnel stations.
- **Rule 5:** a project counts from its model opening year, or its risk year when pessimistic. Pessimistic dates change the result only between opening and risk year.
- **Where the rules live:** all rules are in SQL (the `need`, `sb`, `comps` and `sel` CTEs in `ranking.sql`, and `projects.sql`). With no project switched on, the output is unchanged (R1–R3 in `research/reference-numbers.md`).

**Caveats.**
- Project frequencies are partly analog assumptions.
- 2nd Stammstrecke: new-tunnel trains plus a 15-minute basic service on all S-Bahn lines except S2, S5, S7 and S20 (2017 concept, unverified line table; S5 is a later reinforcement line not in that concept); old-trunk slots assumed reused. The 2025 BEG tender may swap S2/S3 branches, so the excluded lines may change.
- Several opening years are placeholders or assumed 2040.
- Coordinates are partly approximated.
- Scheduled capacity only, not demand or crowding.
- Modes and departures by mode are still shown for today's timetable.

## Forecast what-if 2024 to 2045, if service stays as it is today (dashboard revision 8, 2026-10-19)

**Answer.** Munich grows from 1,603,776 residents (2024) to the forecast 1,829,522 (2045). If today's timetable stays unchanged, city-wide supply falls from 34,425 to 29,822 places per 1,000 activity at w = 1 (−13.4 %). Growth is concentrated at the edge of the city, so the outer districts lose most:
- Aubing-Lochhausen-Langwied −40.5 % (0.86× to 0.51× the 2024 city average; Freiham)
- Feldmoching-Hasenbergl −26.9 %
- Trudering-Riem −25.2 %
- Schwabing-Freimann −22.0 %
- Bogenhausen −19.8 %

Only Untergiesing-Harlaching improves slightly (+0.5 %). On the flag rule (top third for activity density and bottom third for places), no district is flagged in 2024 or 2045 at w = 1. Berg am Laim is flagged in 2034 and 2035 only (2035: activity-density rank 9, places rank 18). By 2045 the outer districts' supply has fallen further, so Berg am Laim drops out. At w = 0, Sendling-Westpark is flagged in 2024 and no longer in 2045.

**Method.**
- Residents(Y) = pop_2024 + (pop_2045_forecast − pop_2024) × (Y − 2024) / 21, a linear interpolation: the Demografiebericht Teil 2 publishes district values for 2045 only.
- Jobs(Y) = jobs_2022 + (jobs_2040 − jobs_2022) × (min(Y, 2040) − 2024) / 16. The city's 2022 estimate is used as the 2024 baseline, rising linearly to the 2040 forecast and held after 2040.
- Supply is today's scheduled timetable, unchanged in every year.
- The map colour is places per 1,000 activity in year Y divided by the 2024 city average at the same w, a fixed baseline.

Year 2024 reproduces revision 6 exactly at every w: 34,425 city-wide, Sendling-Westpark 0.496, Ludwigsvorstadt-Isarvorstadt 1.882, no flags at w = 1. At w = 0: 60,325, Sendling-Westpark 0.40 and flagged.

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
- Supply is today's timetable. Funded projects are not included yet (Tram 23/24 Neufreimann, Westtangente section 2, U5 Pasing), nor are planned ones (U5 Freiham, U4 Nordost); the dashboard can add them later as a scenario toggle.
- Scheduled service only.

Queries: `ranking.sql`, `kpis.sql` and `modes.sql` with `{year!d}` and `{w_jobs!f}`; `trend.sql` (22 years × 25 districts, cached per w). Dashboard: http://127.0.0.1:5100/apps/munich-mobility-planning, revision 8, healthcheck healthy.

## Current: residents + jobs, with interchange hubs (dashboard revision 5, 2026-10-16, metric units)

**Answer.** Counting jobs as well as residents (activity = residents + w × jobs 2022, w = 1), no district is in the top third for activity density and the bottom third for places offered per 1,000 activity. The one district flagged on residents alone, Sendling-Westpark, drops out: its 25,700 jobs leave it 13th for activity density (11,253 per km²), even though it stays last for supply (17,064 places per 1,000 activity against 34,425 city-wide). The largest gap among dense districts is Maxvorstadt (+12): second for activity density at 39,445 per km² because of its 117,100 jobs, but 14th for places at 29,040 per 1,000 activity, and mostly rail. Hauptbahnhof is by far the largest interchange (217,749 timed transfer opportunities, 14.07 % of the city), and Ludwigsvorstadt-Isarvorstadt holds 24.9 % of all opportunities with 3.12 % of residents and 6.90 % of jobs. At w = 0 the dashboard reproduces the residents-only view exactly.

**Method.** Activity = population + w × jobs_2022 (DISTRICT_EMPLOYMENT; slider 0 to 1.5, default 1). Activity density = activity / area_km2. Gap = places-per-1,000-activity rank minus activity-density rank. Flag = activity-density NTILE(3) = 1 AND places NTILE(3) = 3. The same query also computes the w = 0 flag (residents per km², places per 1,000 residents), and `flag_change` marks any difference. Areas are the official `area_km2` (310.7 km² in total). The polygon `area_sqm` is about twice the official area for Thalkirchen-…-Solln (35.53 against 17.764 km²) and Untergiesing-Harlaching (16.11 against 8.057 km²), so it is not used. Hub layer: the transfer-pair query from the interchange section below, with Hauptbahnhof's 4 GTFS stations merged. City-wide: 1,603,776 residents, 1,206,600 jobs, 2,810,376 activity at w = 1, 9,044 activity per km², 54 rail interchange stations.

**Flag changes between w = 0 and w = 1:** Sendling-Westpark, no longer flagged (activity-density rank 13, places rank 25). No district becomes newly flagged.

**Ranked table at w = 1 (sorted by gap):**

| District | Residents/km² | Activity/km² | Jobs 2022 | Places/1k act | Dep/1k act | Places/1k res | Ranks A/P/Dep | Gap | Flag w=1 / w=0 | Note |
|---|---|---|---|---|---|---|---|---|---|---|
| Maxvorstadt | 12,199 | 39,445 | 117,100 | 29,040 | 101.4 | 93,894 | 2/14/24 | 12 | 0/0 | mostly rail |
| Sendling-Westpark | 7,964 | 11,253 | 25,700 | 17,064 | 108.4 | 24,110 | 13/25/23 | 12 | 0/1 | no longer flagged |
| Milbertshofen-Am Hart | 5,760 | 11,931 | 82,800 | 23,688 | 111.3 | 49,067 | 12/23/22 | 11 | 0/0 | |
| Ramersdorf-Perlach | 6,070 | 9,734 | 72,900 | 25,427 | 137.7 | 40,775 | 14/22/13 | 8 | 0/0 | mostly bus |
| Neuhausen-Nymphenburg | 7,890 | 12,637 | 61,300 | 28,987 | 126.1 | 46,425 | 10/15/18 | 5 | 0/0 | |
| Berg am Laim | 7,500 | 12,457 | 31,300 | 28,062 | 96.0 | 46,606 | 11/16/25 | 5 | 0/0 | mostly rail |
| Schwabing-West | 15,724 | 21,753 | 26,300 | 32,432 | 124.4 | 44,864 | 6/10/19 | 4 | 0/0 | mostly rail |
| Thalkirchen-…-Solln | 5,839 | 8,935 | 55,000 | 27,148 | 134.9 | 41,544 | 16/20/15 | 4 | 0/0 | |
| Untergiesing-Harlaching | 6,710 | 8,672 | 15,800 | 26,767 | 117.9 | 34,589 | 17/21/21 | 4 | 0/0 | |
| Altstadt-Lehel | 6,636 | 39,598 | 103,700 | 62,457 | 123.5 | 372,706 | 1/2/20 | 1 | 0/0 | mostly rail |
| Schwanthalerhöhe | 13,855 | 32,553 | 38,700 | 55,934 | 135.9 | 131,400 | 3/4/14 | 1 | 0/0 | mostly rail |
| Hadern | 5,598 | 8,308 | 25,000 | 27,401 | 127.8 | 40,668 | 18/19/16 | 1 | 0/0 | |
| Allach-Untermenzing | 2,345 | 4,293 | 30,100 | 20,265 | 127.0 | 37,100 | 23/24/17 | 1 | 0/0 | mostly bus |
| Laim | 10,805 | 16,216 | 28,600 | 40,835 | 145.8 | 61,283 | 7/7/10 | 0 | 0/0 | |
| Au-Haidhausen | 15,159 | 25,657 | 44,300 | 59,779 | 168.4 | 101,175 | 5/3/5 | -2 | 0/0 | |
| Ludwigsvorstadt-Isarvorstadt | 11,378 | 30,277 | 83,200 | 64,782 | 147.6 | 172,405 | 4/1/9 | -3 | 0/0 | mostly rail |
| Sendling | 10,410 | 14,852 | 17,500 | 45,600 | 158.3 | 65,062 | 8/5/8 | -3 | 0/0 | |
| Obergiesing-Fasangarten | 9,501 | 12,944 | 19,700 | 42,469 | 175.4 | 57,862 | 9/6/3 | -3 | 0/0 | |
| Bogenhausen | 4,026 | 6,666 | 62,600 | 27,923 | 194.6 | 46,232 | 20/17/2 | -3 | 0/0 | mostly bus |
| Feldmoching-Hasenbergl | 2,203 | 2,849 | 18,700 | 27,593 | 143.8 | 35,686 | 24/18/11 | -6 | 0/0 | mostly bus |
| Moosach | 5,049 | 9,493 | 49,300 | 36,581 | 166.3 | 68,776 | 15/8/7 | -7 | 0/0 | |
| Schwabing-Freimann | 3,003 | 7,147 | 106,400 | 32,290 | 141.3 | 76,856 | 19/11/12 | -8 | 0/0 | |
| Trudering-Riem | 3,397 | 5,152 | 39,400 | 29,572 | 166.4 | 44,847 | 22/13/6 | -9 | 0/0 | mostly bus |
| Pasing-Obermenzing | 4,959 | 6,486 | 25,200 | 32,974 | 223.0 | 43,132 | 21/9/1 | -12 | 0/0 | mostly bus |
| Aubing-Lochhausen-Langwied | 1,791 | 2,555 | 26,000 | 29,675 | 168.8 | 42,321 | 25/12/4 | -13 | 0/0 | mostly bus |

**Top 10 hubs (Hauptbahnhof merged):**

| # | Station | Hub index | Opps | Rail↔rail | Rail↔street | Lines |
|---|---|---|---|---|---|---|
| 1 | Hauptbahnhof (4 GTFS stations merged) | 100 | 217,749 | 56,256 | 114,008 | 51 |
| 2 | Karlsplatz (Stachus) | 45 | 75,489 | 17,156 | 39,771 | 23 |
| 3 | Ostbahnhof | 42 | 62,409 | 13,488 | 33,169 | 28 |
| 4 | Pasing | 36 | 39,361 | 5,391 | 19,575 | 38 |
| 5 | Sendlinger Tor | 32 | 48,738 | 12,184 | 27,030 | 17 |
| 6 | Donnersbergerbrücke | 25 | 25,608 | 11,801 | 11,784 | 15 |
| 7 | Marienplatz | 25 | 21,588 | 19,457 | 2,131 | 10 |
| 8 | Isartor | 19 | 15,731 | 6,397 | 7,872 | 11 |
| 9 | Odeonsplatz | 18 | 18,200 | 10,781 | 6,948 | 9 |
| 10 | Hackerbrücke | 18 | 13,392 | 6,466 | 6,111 | 10 |

Districts where the share of transfer opportunities exceeds both the residents share and the jobs share: Ludwigsvorstadt-Isarvorstadt (24.90 % against 3.12 % and 6.90 %), Au-Haidhausen (8.10 % against 3.99 % and 3.67 %), Bogenhausen (6.25 % against 5.95 % and 5.19 %), Pasing-Obermenzing (5.61 % against 5.10 % and 2.09 %), Sendling (3.10 % against 2.56 % and 1.45 %).

**Caveats.**
- Jobs are a modelled 2022 estimate of workers at place of work (LHM Erwerbstätigenprognose 2025, empirica 2024, Tabelle 3), rounded to 100, not a count, and no licence is stated. The weight w is a choice: one job is not necessarily one resident's worth of trips.
- Transfer opportunities are timetable connections, not actual transfers. There are no walking times and no ridership. With Hauptbahnhof as the maximum, the linear hub index compresses every other station (Stachus 45).
- Scheduled service only: no passengers, crowding or delays. Stops outside Munich (24,218) are excluded.
- The hub query takes about 12 s on the first page load and is then cached in-process for an hour (0.1 s). The weight slider reruns only the district queries (about 0.7 s).

Queries: `ranking.sql`, `kpis.sql` and `modes.sql` (with `{w_jobs!f}`), `hubs.sql` (station and district rows in one pass), `capacity.sql`. Dashboard: http://127.0.0.1:5100/apps/munich-mobility-planning, revision 5, healthcheck healthy.

**Service map (revision 6).** The map at the top of the dashboard shows service_ratio = places per 1,000 activity / city-wide places per 1,000 activity, from the same `{w_jobs!f}` weight. At w = 1 it runs from Sendling-Westpark 0.50× to Ludwigsvorstadt-Isarvorstadt 1.88× (Altstadt-Lehel 1.81×, Au-Haidhausen 1.74×, Schwanthalerhöhe 1.62×). At w = 0 it runs from Sendling-Westpark 0.40× (24,110 / 60,325) to Altstadt-Lehel 6.18×; colours are clamped at 0.4 and 2.5 on a log scale centred on 1.0. Only 7 of the 25 districts are above the city average at w = 1, because the inner rail districts pull the average up. The 9 densest districts by activity per km² are outlined.

## Earlier section: residents only, transport (revision 4)


**Answer.** Of the 9 densest districts, only Sendling-Westpark (7,964 residents/km², 62,240 residents) is flagged. It has 24,110 places offered per 1,000 residents, the lowest of all 25 districts, against 60,325 city-wide, and 153.2 departures per 1,000 against 249.4 city-wide. Its gap is +16 (density rank 9, places rank 25). Buses carry 54.6 % of its places (8,541 departures). U-Bahn carries 40.8 % (658 departures). Schwabing-West, the densest district (15,724 residents/km²), has the next-largest gap among the dense districts (+14: places rank 15). It is not flagged only because it sits in the middle tercile, and it has the most residents per station (2,450). Untergiesing-Harlaching (+12, places rank 24) is under-served but only mid-density (6,710 residents/km²).

**Method.** Same weekday service set and capacities as below. Gap = places_rank - density_rank. Flag = density NTILE(3) = 1 (9 districts) AND places-per-1,000 NTILE(3) = 3 (8 districts). Departures per 1,000 is shown as frequency. "Mostly bus" or "mostly rail" means the places and departures ranks differ by more than five places. Validation: stops by mode sum to 4,112 (equal to in_munich = 1), and the totals match the earlier run (400,058 departures, 96,747,005 places).

| District | Residents/km² | Res/station | Places/1k | Dep/1k | Ranks D/P/Dep | Gap | Flag/note |
|---|---|---|---|---|---|---|---|
| Sendling-Westpark | 7,964 | 1,886 | 24,110 | 153.2 | 9/25/24 | 16 | FLAG |
| Schwabing-West | 15,724 | 2,450 | 44,864 | 172.1 | 1/15/22 | 14 | mostly rail |
| Untergiesing-Harlaching | 6,710 | 1,864 | 34,589 | 152.3 | 12/24/25 | 12 | |
| Ramersdorf-Perlach | 6,070 | 1,455 | 40,775 | 220.7 | 14/20/16 | 6 | |
| Thalkirchen-...-Solln | 5,839 | 1,206 | 41,544 | 206.5 | 15/19/18 | 4 | |
| Hadern | 5,598 | 1,174 | 40,668 | 189.7 | 17/21/20 | 4 | |
| Laim | 10,805 | 1,970 | 61,283 | 218.9 | 6/9/17 | 3 | mostly rail |
| Neuhausen-Nymphenburg | 7,890 | 2,215 | 46,425 | 202.0 | 10/13/19 | 3 | mostly rail |
| Au-Haidhausen | 15,159 | 1,939 | 101,175 | 285.1 | 2/4/9 | 2 | |
| Obergiesing-Fasangarten | 9,501 | 1,753 | 57,862 | 239.0 | 8/10/12 | 2 | |
| Maxvorstadt | 12,199 | 1,417 | 93,894 | 328.0 | 4/5/4 | 1 | |
| Sendling | 10,410 | 2,050 | 65,062 | 225.8 | 7/8/15 | 1 | mostly rail |
| Berg am Laim | 7,500 | 1,754 | 46,606 | 159.5 | 11/12/23 | 1 | mostly rail |
| Schwanthalerhöhe | 13,855 | 1,793 | 131,400 | 319.2 | 3/3/6 | 0 | |
| Pasing-Obermenzing | 4,959 | 1,076 | 43,132 | 291.7 | 18/17/8 | -1 | mostly bus |
| Allach-Untermenzing | 2,345 | 710 | 37,100 | 232.5 | 23/22/13 | -1 | mostly bus |
| Feldmoching-Hasenbergl | 2,203 | 1,250 | 35,686 | 186.0 | 24/23/21 | -1 | |
| Ludwigsvorstadt-Isarvorstadt | 11,378 | 1,391 | 172,405 | 392.7 | 5/2/2 | -3 | |
| Milbertshofen-Am Hart | 5,760 | 1,267 | 49,067 | 230.5 | 15/11/14 | -4 | |
| Trudering-Riem | 3,397 | 1,059 | 44,847 | 252.3 | 21/16/10 | -5 | mostly bus |
| Bogenhausen | 4,026 | 1,038 | 46,232 | 322.1 | 20/14/5 | -6 | mostly bus |
| Aubing-Lochhausen-Langwied | 1,791 | 911 | 42,321 | 240.7 | 25/18/11 | -7 | mostly bus |
| Moosach | 5,049 | 1,167 | 68,776 | 312.6 | 18/7/7 | -11 | |
| Altstadt-Lehel | 6,636 | 696 | 372,706 | 737.1 | 13/1/1 | -12 | |
| Schwabing-Freimann | 3,003 | 1,056 | 76,856 | 336.3 | 22/6/3 | -16 | |

Queries: `queries/ranking.sql` and `queries/kpis.sql` (both changed, cycling removed), plus `modes.sql` and `capacity.sql` (unchanged). `queries/paths.sql` has been deleted. Dashboard: http://127.0.0.1:5100/apps/munich-mobility-planning, revision 4, healthcheck healthy.

## Earlier section (superseded on the dashboard): transport + cycling, revision 3

The dashboard no longer shows the cycling findings below; they are kept for the record. Correction: the m/km² figures in this section used the polygon area (area_sqm), which is about double the official area for Thalkirchen-…-Solln and Untergiesing-Harlaching. With the official areas their cycle-path density is about 4,690 and 5,910 m/km².

**Question:** Which densely populated districts have lower scheduled public transport frequency or weaker cycling infrastructure?

**Answer.** 8 of the 9 densest districts are flagged, home to 437,489 residents. Sendling-Westpark (7,964 residents/km²) is the only one flagged on transport: 24,110 places offered per 1,000 residents, the lowest of all 25 districts, against 60,325 city-wide, and 54.6 % of its places come from buses. The other seven are flagged on cycling: Schwabing-West (15,724 residents/km², 476 m per 1,000, places rank 15), Au-Haidhausen, Schwanthalerhöhe, Laim, Maxvorstadt, Ludwigsvorstadt-Isarvorstadt and Obergiesing-Fasangarten. All seven have 384 to 576 cycle-path metres per 1,000 residents, against 698 city-wide. Per km² they have some of the densest networks (5,473 to 7,492 m/km²), so their cycling flag reflects how many residents each metre has to serve, not a lack of paths. Schwabing-West has the largest gap (+18.5): density rank 1, places rank 15, cycle rank 24.

**Method.** Scheduled MVV GTFS service on the reference Wednesday (21 Oct 2026): 400,058 stop departures at stops in Munich, weighted by VEHICLE_CAPACITY places per trip (S-Bahn 1,200, U-Bahn 900, regional rail 500, tram 205, bus 90; LINE_CAPACITY overrides 8 U-Bahn, 1 tram and 14 bus lines). Cycle paths: CYCLING_INFRASTRUCTURE without `Dummy` (1,120 km). Indices run 0 to 100 (min to max) on places per 1,000 and on cycle metres per 1,000. Gap = (places rank + cycle rank)/2 - density rank, with rank 1 = highest, so a positive gap means denser than it is served. Flag = top third for density (NTILE 1, 9 districts) and bottom third (NTILE 3, 8 districts) for either supply measure. The thresholds are a choice.

## District table (sorted by gap)

| # | District | Residents/km² | Places/1k | Dep/1k | Cycle m/1k | m/km² | Res/station | Idx P/C | Ranks D/P/C | Gap | Flag |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 4 | Schwabing-West | 15,724 | 44,864 | 172.1 | 476 | 7,492 | 2,450 | 6/18 | 1/15/24 | 18.5 | cycling (mostly rail) |
| 5 | Au-Haidhausen | 15,159 | 101,175 | 285.1 | 384 | 5,828 | 1,939 | 22/0 | 2/4/25 | 12.5 | cycling |
| 8 | Schwanthalerhöhe | 13,855 | 131,400 | 319.2 | 493 | 6,836 | 1,793 | 31/21 | 3/3/22 | 9.5 | cycling |
| 25 | Laim | 10,805 | 61,283 | 218.9 | 543 | 5,867 | 1,970 | 11/31 | 6/9/21 | 9 | cycling (mostly rail) |
| 3 | Maxvorstadt | 12,199 | 93,894 | 328.0 | 567 | 6,915 | 1,417 | 20/36 | 4/5/20 | 8.5 | cycling |
| 2 | Ludwigsvorstadt-Isarvorstadt | 11,378 | 172,405 | 392.7 | 485 | 5,515 | 1,391 | 43/20 | 5/2/23 | 7.5 | cycling |
| 17 | Obergiesing-Fasangarten | 9,501 | 57,862 | 239.0 | 576 | 5,473 | 1,753 | 10/38 | 8/10/19 | 6.5 | cycling |
| 7 | Sendling-Westpark | 7,964 | 24,110 | 153.2 | 829 | 6,603 | 1,886 | 0/88 | 9/25/5 | 6 | transport |
| 9 | Neuhausen-Nymphenburg | 7,890 | 46,425 | 202.0 | 581 | 4,587 | 2,215 | 6/39 | 10/13/18 | 5.5 | - (mostly rail) |
| 6 | Sendling | 10,410 | 65,062 | 225.8 | 640 | 6,657 | 2,050 | 12/50 | 7/8/16 | 5 | - (mostly rail) |
| 18 | Untergiesing-Harlaching | 6,710 | 34,589 | 152.3 | 880 | 2,952 | 1,864 | 3/98 | 12/24/3 | 1.5 | - |
| 20 | Hadern | 5,598 | 40,668 | 189.7 | 648 | 3,626 | 1,174 | 5/52 | 17/21/15 | 1 | - |
| 14 | Berg am Laim | 7,500 | 46,606 | 159.5 | 750 | 5,623 | 1,754 | 6/72 | 11/12/10 | 0 | - (mostly rail) |
| 16 | Ramersdorf-Perlach | 6,070 | 40,775 | 220.7 | 817 | 4,961 | 1,455 | 5/85 | 14/20/6 | -1 | - |
| 19 | Thalkirchen-...-Solln | 5,839 | 41,544 | 206.5 | 803 | 2,346 | 1,206 | 5/83 | 15/19/7 | -2 | - |
| 21 | Pasing-Obermenzing | 4,959 | 43,132 | 291.7 | 681 | 3,377 | 1,076 | 5/58 | 18/17/12 | -3.5 | - (mostly bus) |
| 23 | Allach-Untermenzing | 2,345 | 37,100 | 232.5 | 599 | 1,404 | 710 | 4/42 | 23/22/17 | -3.5 | - (mostly bus) |
| 1 | Altstadt-Lehel | 6,636 | 372,706 | 737.1 | 651 | 4,318 | 696 | 100/52 | 13/1/14 | -5.5 | - |
| 11 | Milbertshofen-Am Hart | 5,760 | 49,067 | 230.5 | 781 | 4,497 | 1,267 | 7/78 | 15/11/8 | -5.5 | - |
| 24 | Feldmoching-Hasenbergl | 2,203 | 35,686 | 186.0 | 671 | 1,479 | 1,250 | 3/57 | 24/23/13 | -6 | - |
| 15 | Trudering-Riem | 3,397 | 44,847 | 252.3 | 764 | 2,594 | 1,059 | 6/75 | 21/16/9 | -8.5 | - (mostly bus) |
| 22 | Aubing-Lochhausen-Langwied | 1,791 | 42,321 | 240.7 | 723 | 1,295 | 911 | 5/67 | 25/18/11 | -10.5 | - (mostly bus) |
| 13 | Bogenhausen | 4,026 | 46,232 | 322.1 | 852 | 3,431 | 1,038 | 6/92 | 20/14/4 | -11 | - (mostly bus) |
| 10 | Moosach | 5,049 | 68,776 | 312.6 | 888 | 4,481 | 1,167 | 13/99 | 18/7/2 | -13.5 | - |
| 12 | Schwabing-Freimann | 3,003 | 76,856 | 336.3 | 892 | 2,679 | 1,056 | 15/100 | 22/6/1 | -18.5 | - |

"Mostly rail" or "mostly bus" means the district's rank on places and its rank on departures differ by more than five places. Sendling-Westpark: 8,541 bus departures carry 819,560 places, compared with 611,940 places from 658 U-Bahn departures.

## SQL

All queries ran through the read-only `exasol` MCP and run unchanged in the app: `queries/ranking.sql` (the 25-row table above), `queries/kpis.sql` (headline row), `queries/modes.sql` (places and departures per district by line_mode), `queries/paths.sql` (cycle metres per district by path group), `queries/capacity.sql`. Workspace: `~/.exasol-starter-kit/dash-server/instance/workspaces/_git_worktrees/munich-urban-planning/apps/munich-urban-planning/`.

## What the data cannot answer

- Ridership, crowding and delays. MVV GTFS is scheduled service only, and places offered measure capacity, not use.
- Capacities are planning values per mode, not the formation of each trip.
- 24,218 stops with `in_munich = 0` are excluded from every figure; 4,112 stops in Munich are counted (1,116 stations).
- Cycle-path quality, width and continuity, actual cycle traffic beyond the five counters, and planned or funded infrastructure.
- Population is a point-in-time snapshot. Per-resident measures favour sparse outer districts; the m/km² column shows the other side.

**Dashboard:** http://127.0.0.1:5100/apps/munich-mobility-planning (revision 3, healthcheck healthy).

## Interchange hubs: transfer demand implied by the timetable (analysis of 2026-10-16; on the dashboard since revision 5)

**Answer.** Population density understates demand at interchanges. Ludwigsvorstadt-Isarvorstadt has 3.12 % of residents but 24.9 % of city-wide timed transfer opportunities (Hauptbahnhof merged), 7.98 times its share of residents. Altstadt-Lehel has 3.67 times its share, Au-Haidhausen 2.03 and Schwanthalerhöhe 1.70. Merged, Hauptbahnhof is the clear first hub with 217,749 opportunities (14.07 % of the city, 51 lines, 40 rail lines), followed by Karlsplatz (Stachus), Ostbahnhof, Pasing and Sendlinger Tor. Sendling-Westpark, the transport-flagged district, has 0.79 % of transfer opportunities against 3.88 % of residents and no rail interchange.

**Method.** Same weekday set (Wed 2026-10-21), stops with in_munich = 1, station = COALESCE(parent_station, stop_id).
- **Line** = line_mode:route_short_name, so S-Bahn trunk lines count once each.
- **Arrival or departure:** an arrival is a stop event that is not the trip's first stop; a departure is one that is not its last stop.
- **Timed transfer opportunity** = (arrival on line A, departure on line B ≠ A at the same station, 2 to 10 minutes later). It is computed over the whole day as an equi-join on (station, minute) with offsets 2..10. Profiling showed about 4 s total, so no AM-peak restriction was needed.
- **Pair types:** rail↔rail (U-Bahn, S-Bahn, regional rail on both sides), rail↔bus/tram (one side rail), and bus/tram↔bus/tram, counted separately.
- **Hub index** = ROUND(100 × (0.5·opps/max opps + 0.25·places/max places + 0.25·lines/max lines)).
- **Rail interchange** = a station with 2 or more distinct rail lines. There are 55 of 1,112 stations.

**Top 20 stations (strict GTFS grouping; Hbf split, see validation):**

| # | Station | District | Hub | Opps | Rail↔rail | Rail↔street | Lines (U/S/R/T/B) | Departures | Places |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Karlsplatz (Stachus) | Ludwigsvorstadt-Isarv. | 90 | 75,489 | 17,156 | 39,771 | 23 (2/7/0/11/3) | 3,294 | 2,050,219 |
| 2 | Ostbahnhof | Au-Haidhausen | 81 | 62,409 | 13,488 | 33,169 | 28 (1/7/5/2/13) | 2,982 | 1,739,610 |
| 3 | Pasing | Pasing-Obermenzing | 64 | 39,361 | 5,391 | 19,575 | 38 (0/6/14/3/15) | 2,354 | 1,032,455 |
| 4 | Sendlinger Tor | Ludwigsvorstadt-Isarv. | 62 | 48,738 | 12,184 | 27,030 | 17 (5/0/0/7/5) | 2,651 | 1,503,440 |
| 5 | München Hbf (S/regional) | Ludwigsvorstadt-Isarv. | 50 | 14,394 | 14,394 | 0 | 35 (0/8/27/0/0) | 1,423 | 1,453,500 |
| 6 | Hauptbahnhof (U, Tram) | Ludwigsvorstadt-Isarv. | 45 | 32,984 | 12,007 | 17,227 | 11 (5/0/0/6/0) | 2,207 | 1,339,671 |
| 7 | Donnersbergerbrücke | Schwanthalerhöhe | 45 | 25,608 | 11,801 | 11,784 | 15 (0/8/4/0/3) | 1,930 | 1,506,050 |
| 8 | Marienplatz | Altstadt-Lehel | 44 | 21,588 | 19,457 | 2,131 | 10 (2/7/0/0/1) | 1,809 | 1,882,920 |
| 9 | Isartor | Altstadt-Lehel | 34 | 15,731 | 6,397 | 7,872 | 11 (0/7/0/3/1) | 1,531 | 1,299,960 |
| 10 | Odeonsplatz | Altstadt-Lehel | 33 | 18,200 | 10,781 | 6,948 | 9 (4/0/0/0/5) | 1,695 | 1,208,360 |
| 11 | Harras | Sendling | 31 | 20,229 | 2,237 | 10,612 | 15 (1/1/4/0/9) | 1,722 | 652,530 |
| 12 | Laim | Laim | 31 | 16,781 | 3,383 | 8,987 | 12 (0/7/0/0/5) | 1,545 | 961,510 |
| 13 | Hackerbrücke | Ludwigsvorstadt-Isarv. | 31 | 13,392 | 6,466 | 6,111 | 10 (0/7/0/3/0) | 1,445 | 1,292,220 |
| 14 | Hirschgarten | Neuhausen-Nymphenburg | 28 | 9,990 | 6,345 | 3,645 | 10 (0/7/0/0/3) | 1,257 | 1,226,720 |
| 15 | Giesing | Obergiesing-Fasangarten | 26 | 13,971 | 1,313 | 7,939 | 12 (1/2/0/1/8) | 1,475 | 722,460 |
| 16 | Münchner Freiheit | Schwabing-Freimann | 24 | 11,161 | 1,961 | 6,759 | 12 (2/0/0/1/9) | 1,351 | 718,060 |
| 17 | Scheidplatz | Schwabing-West | 23 | 12,884 | 1,252 | 8,291 | 8 (2/0/0/2/4) | 1,464 | 762,660 |
| 18 | Universität | Maxvorstadt | 23 | 12,506 | 1,979 | 7,758 | 9 (2/0/0/0/7) | 1,404 | 737,440 |
| 19 | Rosenheimer Platz | Au-Haidhausen | 23 | 6,351 | 6,351 | 0 | 7 (0/7/0/0/0) | 1,001 | 1,201,200 |
| 20 | Neuperlach Zentrum | Ramersdorf-Perlach | 22 | 17,043 | 0 | 7,693 | 8 (1/0/0/0/7) | 1,605 | 479,740 |

City total (strict grouping): 1,389,401 timed transfer opportunities.

**Validation and surprises.**
- **Hauptbahnhof is split across 4 GTFS stations:** de:09162:100 "München Hbf" (S-Bahn and regional rail only), :6 "Hauptbahnhof (U, Tram)", :7000 Nord and :5000 Süd. With strict grouping, Hbf rail↔street is 0 and S-Bahn↔U-Bahn transfers there are invisible. Merged, it has 217,749 opportunities (rail↔rail 56,256, rail↔street 114,008), 51 lines and 3,138,277 places, clearly first. The district rollup below uses the merged Hbf.
- **Marienplatz:** its tram stop is the separate station "Marienplatz (Theatinerstraße)", so its rail↔street count is understated (2,131).
- **Münchner Freiheit** ranks 16th, which is plausible: it has 2 U-Bahn lines (U3/U6) and no S-Bahn, and most of its transfers are U↔bus/tram.
- **Opportunities scale with the product of frequencies,** so stations on the S-Bahn trunk (7 S-Bahn lines every few minutes) dominate. This measures timetable connectivity, not demand.
- **Name matching is noisy:** platform names such as "... Gleis 2 Ri Münchner Freiheit" contain hub names, so stations were matched by ID, not by name.

**District rollup (Hbf merged; shares of the city total):**

| District | Residents/km² | Rail interch. | Opps | Opps % | Residents % | Places % | Opps/residents |
|---|---|---|---|---|---|---|---|
| Ludwigsvorstadt-Isarvorstadt | 11,378 | 8 | 385,303 | 24.90 | 3.12 | 12.31 | 7.98 |
| Au-Haidhausen | 15,159 | 5 | 125,395 | 8.10 | 3.99 | 6.63 | 2.03 |
| Bogenhausen | 4,026 | 1 | 96,739 | 6.25 | 5.95 | 5.03 | 1.05 |
| Pasing-Obermenzing | 4,959 | 1 | 86,748 | 5.61 | 5.10 | 3.62 | 1.10 |
| Schwabing-Freimann | 3,003 | 2 | 82,407 | 5.32 | 4.81 | 6.22 | 1.11 |
| Ramersdorf-Perlach | 6,070 | 3 | 74,166 | 4.79 | 7.53 | 5.73 | 0.64 |
| Altstadt-Lehel | 6,636 | 4 | 73,747 | 4.77 | 1.30 | 6.58 | 3.67 |
| Neuhausen-Nymphenburg | 7,890 | 4 | 72,548 | 4.69 | 6.35 | 5.05 | 0.74 |
| Moosach | 5,049 | 4 | 58,396 | 3.77 | 3.49 | 3.69 | 1.08 |
| Maxvorstadt | 12,199 | 2 | 51,296 | 3.31 | 3.27 | 4.12 | 1.01 |
| Laim | 10,805 | 2 | 50,706 | 3.28 | 3.56 | 3.68 | 0.92 |
| Sendling | 10,410 | 4 | 47,918 | 3.10 | 2.56 | 2.77 | 1.21 |
| Schwanthalerhöhe | 13,855 | 3 | 47,012 | 3.04 | 1.79 | 3.46 | 1.70 |
| Obergiesing-Fasangarten | 9,501 | 1 | 46,570 | 3.01 | 3.39 | 3.29 | 0.89 |
| Milbertshofen-Am Hart | 5,760 | 0 | 46,233 | 2.99 | 4.82 | 3.64 | 0.62 |
| Schwabing-West | 15,724 | 1 | 45,114 | 2.92 | 4.28 | 3.18 | 0.68 |
| Trudering-Riem | 3,397 | 1 | 38,068 | 2.46 | 4.76 | 3.40 | 0.52 |
| Thalkirchen-...-Solln | 5,839 | 2 | 29,880 | 1.93 | 6.47 | 4.37 | 0.30 |
| Aubing-Lochhausen-Langwied | 1,791 | 5 | 18,796 | 1.21 | 3.80 | 2.73 | 0.32 |
| Feldmoching-Hasenbergl | 2,203 | 1 | 16,422 | 1.06 | 3.98 | 2.56 | 0.27 |
| Hadern | 5,598 | 0 | 13,979 | 0.90 | 3.22 | 1.99 | 0.28 |
| Sendling-Westpark | 7,964 | 0 | 12,273 | 0.79 | 3.88 | 1.49 | 0.20 |
| Untergiesing-Harlaching | 6,710 | 0 | 10,753 | 0.69 | 3.37 | 1.63 | 0.20 |
| Allach-Untermenzing | 2,345 | 0 | 9,154 | 0.59 | 2.26 | 1.39 | 0.26 |
| Berg am Laim | 7,500 | 0 | 7,972 | 0.52 | 2.95 | 1.45 | 0.18 |

Places in this rollup count departures only (terminal arrivals excluded), so they differ slightly from the dashboard figures.

**Caveats.**
- A timed transfer opportunity is a timetable connection, not a transfer anyone makes. There is no ridership, no origin-destination data and no passenger counts.
- No walking times inside a station: the same 2-minute minimum applies to a cross-platform change and to a long walk.
- Station grouping follows GTFS parent_station. Large complexes can be split, as at Hauptbahnhof (merged here by hand), and nearby street stops with their own ID, such as Marienplatz (Theatinerstraße), stay separate.
- The hub index weights (50/25/25) and the 2 to 10 minute window are choices. Opportunities grow with the product of frequencies, which favours trunk stations.
- Scheduled service on one Wednesday only. Stops outside Munich are excluded, which cuts transfers at border stations.
