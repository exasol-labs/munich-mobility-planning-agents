# Urban planning: how well each district is served by scheduled public transport

Findings for the dashboards `munich-mobility-planning-v1` to `-v5` on `MUNICH_DATASET`, reference weekday Wednesday 2026-10-21. All figures are scheduled service (places offered = departures × capacity per trip), not passengers. The reference cases R1–R6 that the dashboards must reproduce are in [reference-numbers.md](reference-numbers.md).

## v1: today, per resident

**Answer.** Of the 9 densest districts, only Sendling-Westpark (7,964 residents/km², 62,240 residents) is flagged. It has 24,110 places offered per 1,000 residents, the lowest of all 25 districts, against 60,325 city-wide, and 153.2 departures per 1,000 against 249.4 city-wide. Its gap is +16 (density rank 9, places rank 25). Buses carry 54.6 % of its places (8,541 departures carry 819,560 places); U-Bahn carries 40.8 % (658 departures, 611,940 places). Schwabing-West, the densest district (15,724 residents/km²), has the next-largest gap among the dense districts (+14: places rank 15). It is not flagged only because it sits in the middle tercile, and it has the most residents per station (2,450). Untergiesing-Harlaching (+12, places rank 24) is under-served but only mid-density (6,710 residents/km²).

**Service map.** The map shows service_ratio = places per 1,000 residents / city-wide places per 1,000 residents. It runs from Sendling-Westpark 0.40× (24,110 / 60,325) to Altstadt-Lehel 6.18×. Colors are clamped at 0.4 and 2.5 on a log scale centered on 1.0. The 9 densest districts are outlined.

**Method.** Gap = places_rank − density_rank, with rank 1 = highest, so a positive gap means denser than it is served. Flag = density NTILE(3) = 1 (9 districts) AND places-per-1,000 NTILE(3) = 3 (8 districts). The thresholds are a choice. Departures per 1,000 is shown as frequency. "Mostly bus" or "mostly rail" means the places and departures ranks differ by more than five places. Validation: stops by mode sum to 4,112 (equal to in_munich = 1); city totals 400,058 departures and 96,747,005 places.

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
| Allach-Untermenzing | 2,345 | 710 | 37,100 | 232.5 | 23/22/13 | -1 | mostly bus |
| Feldmoching-Hasenbergl | 2,203 | 1,250 | 35,686 | 186.0 | 24/23/21 | -1 | |
| Pasing-Obermenzing | 4,959 | 1,076 | 43,132 | 291.7 | 19/17/8 | -2 | mostly bus |
| Ludwigsvorstadt-Isarvorstadt | 11,378 | 1,391 | 172,405 | 392.7 | 5/2/2 | -3 | |
| Milbertshofen-Am Hart | 5,760 | 1,267 | 49,067 | 230.5 | 16/11/14 | -5 | |
| Trudering-Riem | 3,397 | 1,059 | 44,847 | 252.3 | 21/16/10 | -5 | mostly bus |
| Bogenhausen | 4,026 | 1,038 | 46,232 | 322.1 | 20/14/5 | -6 | mostly bus |
| Aubing-Lochhausen-Langwied | 1,791 | 911 | 42,321 | 240.7 | 25/18/11 | -7 | mostly bus |
| Moosach | 5,049 | 1,167 | 68,776 | 312.6 | 18/7/7 | -11 | |
| Altstadt-Lehel | 6,636 | 696 | 372,706 | 737.1 | 13/1/1 | -12 | |
| Schwabing-Freimann | 3,003 | 1,056 | 76,856 | 336.3 | 22/6/3 | -16 | |

## v2: today, residents and jobs

**Answer.** Counting jobs as well as residents (activity = residents + w × jobs 2022, w = 1), no district is in the top third for activity density and the bottom third for places offered per 1,000 activity. The one district flagged on residents alone, Sendling-Westpark, drops out: its 25,700 jobs leave it 13th for activity density (11,253 per km²), even though it stays last for supply (17,064 places per 1,000 activity against 34,425 city-wide). The largest gap among dense districts is Maxvorstadt (+12): second for activity density at 39,445 per km² because of its 117,100 jobs, but 14th for places at 29,040 per 1,000 activity, and mostly rail. At w = 0 the dashboard reproduces v1 exactly.

**Service map.** At w = 1 the ratio runs from Sendling-Westpark 0.50× to Ludwigsvorstadt-Isarvorstadt 1.88× (Altstadt-Lehel 1.81×, Au-Haidhausen 1.74×, Schwanthalerhöhe 1.62×). Only 8 of the 25 districts are above the city average at w = 1, because the inner rail districts pull the average up.

**Method.** Activity = population + w × jobs_2022 (DISTRICT_EMPLOYMENT; input 0 to 1.5, default 1). Activity density = activity / area_km2. Gap = places-per-1,000-activity rank minus activity-density rank. Flag = activity-density NTILE(3) = 1 AND places NTILE(3) = 3. The same query also computes the w = 0 flag (residents per km², places per 1,000 residents), and `flag_change` marks any difference. City-wide: 1,603,776 residents, 1,206,600 jobs, 2,810,376 activity at w = 1, 9,044 activity per km².

**Flag changes between w = 0 and w = 1:** Sendling-Westpark is flagged at w = 0 and not at w = 1 (activity-density rank 13, places rank 25). No district is flagged at w = 1 only.

**Ranked table at w = 1 (sorted by gap):**

| District | Residents/km² | Activity/km² | Jobs 2022 | Places/1k act | Dep/1k act | Places/1k res | Ranks A/P/Dep | Gap | Flag w=1 / w=0 | Note |
|---|---|---|---|---|---|---|---|---|---|---|
| Maxvorstadt | 12,199 | 39,445 | 117,100 | 29,040 | 101.4 | 93,894 | 2/14/24 | 12 | 0/0 | mostly rail |
| Sendling-Westpark | 7,964 | 11,253 | 25,700 | 17,064 | 108.4 | 24,110 | 13/25/23 | 12 | 0/1 | flagged at w = 0 only |
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

**Caveats.**
- Jobs are a modeled 2022 estimate of workers at place of work (LHM Erwerbstätigenprognose 2025, empirica 2024, Tabelle 3), rounded to 100, not a count, and no license is stated. The weight w is a choice: one job is not necessarily one resident's worth of trips.

## v3: forecast to 2045, if service stays as it is today

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
- The map color is places per 1,000 activity in year Y divided by the 2024 city average at the same w, a fixed baseline.

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
- Jobs are a modeled estimate, with the 2022 value used as the 2024 baseline and held after 2040.
- Supply is today's timetable. Funded projects (Tram Münchner Norden part 1 with tram 23 to Kieferngarten, Westtangente section 2, U5 Pasing) and planned ones (U5 Freiham, U4 Ost) are not included; v4 adds them as scenarios.
- Scheduled service only.

## v4: forecast with rail and tram scenarios

**Answer.** By 2045 at w = 1, with no project switched on, city-wide supply falls from 34,425 to 29,822 places per 1,000 activity (−13.37 %). The six funded projects lift that to 32,069 (−6.84 %), which offsets 49 % of the decline. Everything discussed lifts it to 33,593 (−2.42 %), which offsets 82 %.

The largest single contributor is the 2nd Stammstrecke, modeled as the new-tunnel trains plus a 15-minute basic interval on the existing S-Bahn network. It adds +5,272,800 places per weekday net: +3,237,600 from the five tunnel stations and +2,035,200 from lifting 53 Munich S-Bahn stations on S3, S4, S6 and S8 to at least 152 departures. S1 is already above 152; S2, S5, S7 and S20 are excluded. Nothing is removed from the existing trunk, so no central district loses supply: Schwanthalerhöhe (1.564 vs 1.523), Neuhausen-Nymphenburg (0.792 vs 0.776) and Maxvorstadt (0.777 = 0.777) end at or above their "none" values.

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
- Laim inbound restored +312,000 (260 departures, 2028); with the 2nd trunk also on, the 15-minute rule at Laim is applied to the restored numbers, −300,000 (−250 departures)
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
- **Consistency:** with no project switched on, the output equals v3 (R1–R3 in [reference-numbers.md](reference-numbers.md)).

**Caveats.**
- Project frequencies are partly analog assumptions.
- 2nd Stammstrecke: new-tunnel trains plus a 15-minute basic service on all S-Bahn lines except S2, S5, S7 and S20 (2017 concept, unverified line table; S5 is a later reinforcement line not in that concept); existing-trunk slots assumed reused. The 2025 BEG tender may swap S2/S3 branches, so the excluded lines may change.
- Several opening years are placeholders or assumed 2040.
- Coordinates are partly approximated.
- Scheduled capacity only, not demand or crowding.
- The mode note ("mostly bus", "mostly rail") refers to today's timetable.

## v5: ask the assistant

v5 uses v4's model unchanged; its numbers are v4's. With no what-if, the model returns exactly the v4 output.

- First load is the current year with w = 1.0 and no projects: on the reference date that is 2026, Munich overall −1.66 % (33,853 vs 34,425).
- "Show 2045 with the funded projects" gives Funded only, 6 projects active, +7.3 M places per weekday net, Munich overall −6.84 % (R4).
- 2045 None −13.37 % (R3), Everything discussed −2.42 % (R5), 2nd Stammstrecke only −8.65 % (R6).
- A frequency what-if reuses the 15-minute rule with the frequency as a parameter: extra places = (GREATEST(departures today, trains per hour × hours × 2) − departures today) × capacity per trip. "S4 at least 4 trains/h for 19 h" adds +729,600 places, the same as v4's 15-minute rule for S4.
- A new-line what-if adds (peak × 6 + off-peak × 13) × 2 departures per station × the mode's capacity per trip.

**Caveats.** A what-if is capacity arithmetic, not a plan: demand shifts, crowding, travel time, cost and feasibility are not modeled. It adds to supply in every year shown; departures and the 2024 baseline don't change.

## Method common to all versions

- **Service set:** scheduled MVV GTFS service on the reference Wednesday (21 Oct 2026): 400,058 stop departures at stops in Munich.
- **Capacity:** each departure is weighted by VEHICLE_CAPACITY places per trip (S-Bahn 1,200, U-Bahn 900, regional rail 500, tram 205, bus 90); LINE_CAPACITY overrides 8 U-Bahn, 1 tram and 14 bus lines.
- **Areas:** the official `area_km2` (310.7 km² in total), which matches the polygon `area_sqm` for every district.
- **SQL:** every figure comes from one read-only model query, shared by v1–v4; v5 adds the what-if input.

## What the data cannot answer

- Ridership, crowding and delays. MVV GTFS is scheduled service only, and places offered measure capacity, not use.
- Capacities are planning values per mode, not the formation of each trip.
- 24,218 stops with `in_munich = 0` are excluded from every figure; 4,112 stops in Munich are counted (1,116 stations).
- Population is a point-in-time snapshot. Per-resident measures favor sparse outer districts.
