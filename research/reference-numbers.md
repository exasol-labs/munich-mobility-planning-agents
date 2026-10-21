# Reference numbers

Computed with `dashboards/munich-mobility-planning-v4/queries/ranking.sql`, reference weekday 2026-10-21 (`scripts/verify_numbers.py` pins it; expected values in `tests/expected.json`).

The query runs read-only with its placeholders substituted (`pessimistic = 0` throughout). All values are scheduled service (places offered = departures x capacity per trip), not passengers.

## Data checks

| Check | Expected |
|---|---|
| DISTRICTS rows | 25 |
| DISTRICT_EMPLOYMENT rows | 25 |
| DISTRICT_POPULATION rows | 25 |
| PT_PROJECT_STATIONS rows | 88 |
| SUM(pop_2024) | 1,603,776 |

## Reference cases

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

## R1: 2024, w = 0 (per resident), no projects. City 60,325 places per 1,000 residents

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

## R2: 2024, w = 1 (residents + jobs), no projects. City 34,425 places per 1,000 activity

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

## R3: 2045, w = 1, no projects (change since 2024, % places per 1,000 activity)

City: 29,822 (2045) vs 34,425 (2024) = -13.37 %. Lowest: Aubing-Lochhausen-Langwied -40.5 %, Feldmoching-Hasenbergl -26.9 %, Trudering-Riem -25.2 %, Schwabing-Freimann -22.0 %, Bogenhausen -19.8 %. Highest: Untergiesing-Harlaching +0.5 %, Hadern -2.4 %, Obergiesing-Fasangarten -3.1 %.

## The 2nd Stammstrecke in the model

When `stammstrecke2` is active: (1) the 5 new-tunnel stations from `PT_PROJECT_STATIONS` are added by the frequency method; (2) S1/S6 departures on the existing trunk are not removed (the slots are reused); (3) 15-minute basic interval: for every S-Bahn line except S2, S5, S7 and S20, at every station inside Munich the line serves today, `departures_new = GREATEST(departures_today, 152)`, places = difference x capacity per trip (1,200 for every S-Bahn line); (4) with `laim_inbound_restore` also active, the 15-minute rule is applied on the restored numbers at Laim (S3/S4/S6/S8: -250 departures adjustment, nothing counted twice). S5 is excluded because it is a later reinforcement line, not part of the 2017 concept. The rule sits in the `sb` CTE of `ranking.sql` and `projects.sql` (`line NOT IN ('S2', 'S5', 'S7', 'S20')`). R1-R3 do not use projects and are unaffected (0 places added; sum of the 25 ratios 30.160 / 25.413 / 22.535).

Lines in the feed: S1, S2, S20, S3, S4, S5, S6, S7, S8. Upgraded lines (S-Bahn stations inside Munich served today / lifted to 152 / places added per weekday): S1 14 / 0 / 0 (235 departures everywhere already); S3 16 / 4 / +88,800; S4 16 / 16 / +729,600; S6 15 / 15 / +655,200; S8 18 / 18 / +561,600. Total 79 stations, 53 lifted, +1,696 departures, +2,035,200 places.

## R6: 2045, w = 1, stammstrecke2 only

Net **+5,272,800** places per weekday = step 1 (new tunnel) +3,237,600 + step 3 (15-minute basic interval) +2,035,200. City 31,448 vs 34,425 = -8.65 %.

| District | R6 ratio | None ratio (R3) | R6 % since 2024 | Places added |
|---|---|---|---|---|
| Schwanthalerhöhe | 1.564 | 1.523 | -3.7 % | +100,800 |
| Neuhausen-Nymphenburg | 0.792 | 0.776 | -5.9 % | +100,800 |
| Maxvorstadt | 0.777 | 0.777 | -7.9 % | 0 |

All 25 districts (R6): Altstadt-Lehel 1.800 (-0.8 %, +885,600); Ludwigsvorstadt-Isarvorstadt 1.918 (+1.9 %, +986,400); Maxvorstadt 0.777 (-7.9 %, +0); Schwabing-West 0.906 (-3.8 %, +0); Au-Haidhausen 2.025 (+16.6 %, +1,508,400); Sendling 1.235 (-6.7 %, +0); Sendling-Westpark 0.463 (-6.5 %, +0); Schwanthalerhöhe 1.564 (-3.7 %, +100,800); Neuhausen-Nymphenburg 0.792 (-5.9 %, +100,800); Moosach 0.895 (-15.8 %, +0); Milbertshofen-Am Hart 0.644 (-6.5 %, +0); Schwabing-Freimann 0.732 (-22.0 %, +0); Bogenhausen 0.662 (-18.4 %, +75,600); Berg am Laim 0.706 (-13.4 %, +98,400); Trudering-Riem 0.661 (-23.1 %, +98,400); Ramersdorf-Perlach 0.653 (-11.6 %, +0); Obergiesing-Fasangarten 1.197 (-3.0 %, +3,600); Untergiesing-Harlaching 0.781 (+0.5 %, +0); Thalkirchen-Obersendling-Forstenried-Fürstenried-Solln 0.687 (-12.9 %, +0); Hadern 0.776 (-2.4 %, +0); Pasing-Obermenzing 0.877 (-8.4 %, +100,800); Aubing-Lochhausen-Langwied 0.558 (-35.3 %, +224,400); Allach-Untermenzing 0.488 (-17.2 %, +0); Feldmoching-Hasenbergl 0.586 (-26.9 %, +0); Laim 1.446 (+21.9 %, +1,089,600).

## R4: 2045, w = 1, Funded only

City 32,069 vs 34,425 = **-6.84 %**; net +7,290,222 places per weekday (dashboard: "+7.3 M places/day net"). Schwanthalerhöhe 1.564 vs 1.523, Neuhausen-Nymphenburg 0.792 vs 0.776, Maxvorstadt 0.777 = 0.777: no district falls below its "None" value.

## R5: 2045, w = 1, Everything discussed

City 33,593 vs 34,425 = **-2.42 %**; 14 of 17 projects open by 2045; net +12,232,618 places per weekday (dashboard: "+12.2 M places/day net").

## R4/R5: None / Funded only / Everything discussed at 2045, w = 1, all 25 districts (sorted by the Funded ratio)

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
