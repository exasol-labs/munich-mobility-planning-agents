# What Munich is doing about the gaps (as of 15 Oct 2026)

I compared the gaps found with SQL on `MUNICH_DATASET` (scheduled transport and cycle-path supply per district, roadworks near stops, the bike counters) with current city plans. The research was done in German across official sources and local media. One limit on coverage: BR, SZ, tz and Merkur block the research crawler. Their reporting is included only where the ADFC München media reviews (Radfahren in den Medien) carry it. The other media sources are Abendzeitung, t-online München, tramreport.de, VCD and Pro Bahn. Items marked (unverified) were seen only in search results, not on the source page.

## Summary

- **Schwabing-West, the densest district with the weakest transport, gets no funded rail improvement.** U9 via Elisabethplatz, Tram Y-Nord via Nordbad and the Tram-Nordtangente through the Englischer Garten are all unfunded, on hold or blocked by the Freistaat. The concrete projects there are small: Karl-Theodor-Straße (protected cycle paths, under construction until about May 2027) and Belgradstraße stop upgrades.
- **Laim, Sendling-Westpark and Neuhausen are being addressed.** Tram-Westtangente: tram 14 has run since 28 Feb 2026, and Aidenbachstraße is due end 2028, with a risk of 2030/31 if the funding condition bites. U5 to Pasing is due 2036.
- **The December 2026 timetable cuts go the other way in the flagged inner districts.** From 13 Dec 2026 the CityRing 58/68 is abolished, line 153 is shortened and tram 25 runs less often off-peak. The new line 64 (Sendling–Giesing) and line 133 help Sendling and Obergiesing.
- **There will be more roadworks, not fewer.** The Fernwärme steam-to-hot-water conversion reaches Schwabing-West, Maxvorstadt and Schwabing-Freimann from 2030. The 2. Stammstrecke opens 2035–37 and costs over €11 bn; the first tunnel boring machine started on 17 Sep 2026 (rescue tunnel), and the machines for the running tunnels start in 2028. About 65 % of building-site permits are private and cannot be forced into the city's coordination. The coalition's answers are a Baustellenfonds and "Baustellen nutzen" (redesign a street when it is dug up anyway).
- **Cycling: the dense districts with the least cycle path get mostly small and late projects.** Au-Haidhausen, the lowest per resident, gets Gebsattelberg in 2027, while Rosenheimer Platz is deferred for budget reasons. Ludwigsvorstadt-Isarvorstadt: Lindwurmstraße section 2 waits for the U-Bahn work at Poccistraße, which end Aug 2027. Schwanthalerstraße is decided but has no start date, and 170 m of Lindwurmstraße was temporarily given to replacement buses in Jul 2026. Erhardtstraße/Isar is the busiest counter and the most rain-sensitive, but it is still only in planning, with nothing weather-resilient.
- **Politics and money.** OB Krause (Grüne) has led since 1 May 2026, in a coalition of Grüne/Rosa Liste, SPD and FDP/FW (the "Mango-Koalition"). The coalition must save at least €0.5 bn a year. Under the SWM financing rule (Dec 2025), a project gets no planning beyond the approval stage without a Bund/Land funding commitment. The U-Bahn only goes ahead with early Bund/Freistaat funding commitments. The Olympia 2036 bid (DOSB nomination 26 Sep 2026) is the one political accelerator.

## Gap by gap

| Gap (from our SQL) | Built / under construction | Decided | Under discussion only |
|---|---|---|---|
| Schwabing-West: 172 departures and 476 cycle-path m per 1,000 residents | Karl-Theodor-Str. cycle paths (to ~May 2027); tram 12 extension (2025, district edge) | — | U9 Elisabethplatz, Tram Y-Nord, Tram-Nordtangente, protected lanes on Schleißheimer Str., Belgradstr./Hohenzollernstr. |
| Sendling-Westpark: 153 departures | Tram-Westtangente section 1 | Section 2 to Aidenbachstr., end 2028 | — |
| Laim: 219 departures, 543 m | Tram 14 (Feb 2026); U5 tunnel | U5 Pasing 2036; Stammstrecke Laim station | Pronnerplatz cycle bridge, Von-der-Pfordten-Str. cycle street |
| Neuhausen-Nymphenburg: 202 departures | Tram-Westtangente (Romanplatz) | — | Tram Amalienburgstr.–Freiham **dropped** 2025 |
| Au-Haidhausen: 384 m (lowest) | Franziskanerstr. renewal | Gebsattelberg path (2027) | Rosenheimer Str./Platz (deferred), more cycle streets |
| Ludwigsvorstadt-Isarvorstadt: 485 m | Lindwurmstr. section 1 (Sep 2025), Stachus crossing | Lindwurmstr. section 2, Schwanthalerstr. (no date) | Paul-Heyse-Str., Tram-Cityring |
| Maxvorstadt: 567 m, high disruption | Augustenstr. (cycle path **removed**, Tempo 20) | Elisenstr. (no date); Ludwigstraße redesign (competition May 2026) | Stiglmaierplatz, Nymphenburger Str. |
| Schwanthalerhöhe: 493 m | — | Bergmannstr. cycle street | Westend Nachbarschaftsviertel (first one, 2027+) |
| Obergiesing-Fasangarten: 239 departures, 576 m | Giesinger Berg | Martin-Luther-Str. permanent; line 64 (Dec 2026) | — |
| Erhardtstr./Isar counter | — | — | Erhardt–Steinsdorf–Widenmayerstr. (planning only) |

## Top disruption zones: what is behind them

| Zone | Work and owner | End date | Note |
|---|---|---|---|
| Frankfurter Ring 149 | SWM Leitungsbau, at least one lane each way | City says **June 2027**; our data says 30 Apr 2027 | ADAC criticizes poor coordination with the Föhringer Ring work (to 2031) |
| Nordbad (Winzerer-/Schleißheimer Str.) | MVG switch renewal, 9 Mar–31 May 2026 (finished) | 2027 dates probably cover the Fernwärme and track work on Schleißheimer Str. (inference) | Grüne motion: build protected cycle lanes at the same time |
| Stiglmaierplatz / Nymphenburger Str. | Switch work 21–22 Oct 2026 (N20 replaced by buses); SWM gas and 110 kV lines | Not found | — |
| Mariahilfplatz / Ohlmüllerstr. | Baureferat sidewalk work, **delayed** to 30 Nov 2026; SWM Fernwärme conversion in the Au | 2027/28 (inference) | The Mobilitätsreferat dropped or postponed some 2026 projects in the Au as not compatible with each other |
| Laimer Platz | U5 extension (Baureferat) | Gotthardstr. surface until end 2031 | On schedule |
| Odeonsplatz | U4 cut to Max-Weber-Platz, 5 Oct–27 Nov 2026 | 27 Nov 2026 | Trams 16/17 are the replacement, which adds load to the lines our data flags most |
| Rosenheimer Str. 145, Görresstr., Winzererstr. 68, Elsenheimerstr. 50 | **Nothing found** | — | — |

## Proposals still under discussion, ranked by impact

Impact means how severe the gap is, how many residents and departures it affects, and how directly the proposal fixes it. Likelihood is listed separately, so a high-impact proposal can still be a long shot. The ranking is my judgment from the research, not a calculation.

| # | Proposal | Gap addressed | Stage | Likelihood | Horizon |
|---|---|---|---|---|---|
| 1 | **U9-Spange** (Münchner Freiheit–Elisabethplatz–Hbf–Implerstr.) | Schwabing-West, Maxvorstadt, Ludwigsvorstadt, Sendling; relieves the core | Preliminary planning; Hbf shell being built with the Stammstrecke; €3.5–4 bn+ | Low–medium (needs Bund/Freistaat money). A Grüne motion of 29 Jan 2026 wants the south section first, which would **not** reach Schwabing-West | 2040s |
| 2 | **Tram Y-Nord** (Hbf–Nordbad–Petuelring) | The Nordbad corridor itself, Schwabing-West; relieves U2 | Planning on hold; the 2025 exemption from cuts was probably not adopted (unclear) | Low–medium | 2030s |
| 3 | **Tram-Nordtangente / Englischer Garten** | East–west link for Schwabing-West | Frozen since the Freistaat veto (2024); tunnel study Jan 2026 (~€240 m); not in the coalition agreement | Low–medium; Olympia raises it | ≥2030 |
| 4 | **Nahverkehrsumlage + Land funding back from 10 % to 15 %** | Enables service everywhere, unlocks 1–3 | Grüne motion Jan 2026; needs a Bavarian law | Low–medium (FDP, IHK) | Mid-term |
| 5 | **Protected cycle lanes on Schleißheimer Str. during the Fernwärme/track work** | Schwabing-West cycling plus the top disruption zone | Grüne motion 19 Dec 2025; outcome not found | Medium–high (matches the coalition's "Baustellen nutzen") | 2026–27 |
| 6 | **Bus priority at building sites** (bus lanes, signal priority) | Roadworks beside high-frequency bus lines | Grüne motion Jan 2026 (unverified) | Medium | Short |
| 7 | **Funded cycle network program IR III from 2027** | Cycle-path gap in all flagged districts | Network adopted 23 Sep 2026; ÖDP amendment for money, outcome unknown | Medium (cheap measures only) | 2027+ |
| 8 | **Tram-Cityring** (Silberhornstr.–Goetheplatz–Hbf) | Ludwigsvorstadt, Schwanthalerhöhe, Au-Haidhausen | Corridor "under study" (Pro Bahn) | Low (the bus ring is being abolished instead) | 2030s |
| 9 | **Belgradstr. redesign + Hohenzollernstr. as a cycle street** | Schwabing-West stops and cycling | District-council motions 25 Jun 2026 | Medium | 2027+ |
| 10 | **Nachbarschaftsviertel Westend, then Gärtnerplatz; Altstadt für alle** | Schwanthalerhöhe, Isarvorstadt, Altstadt-Lehel | Concept / step-by-step plans | Medium | 2027–30 |
| 11 | **Cycle and foot bridge at Pronnerplatz (Nymphenburg–Laim)** | Laim, Neuhausen | Feasibility study being updated | Low–medium | 2030s |
| 12 | **Higher parking fees** (short-stay €2.60/h; residents' permit up to €300) | Money for the above; inner districts | Savings package Jul 2026 (single source) | Medium short-stay, low residents | 2026–27 |

S-Bahn-Nordring, Tram Johanneskirchen and U26 are planned projects but do not touch the flagged districts. I found no current debate on a Citymaut, a cable car or a maglev.

## Notes on the dataset

- **Bus 68 disappears on 13 Dec 2026.** The MVV feed runs 1 Sep–30 Nov 2026 and predates the 2027 timetable, so the "bus 68: 142 roadworks" finding expires in December.
- **Frankfurter Ring 149:** the city's end date (June 2027) is later than in our data.
- **Nordbad:** the MVG switch project in our area ended May 2026. The open records with 2027 dates are probably the follow-on Fernwärme and track work.
- **Erhardtstr. counter:** the dataset assigns it to Ludwigsvorstadt-Isarvorstadt. It sits at the Au-Haidhausen border, so check the district assignment.

## Conflicts between sources

- **Co-funding of regional buses X204/X206:** one source says it continues and only X208 ends. Another reads the council paper (V 00776) as ending all of them from the Dec 2028 timetable. Follow the council paper.
- **Altstadt-Radlring progress:** the Radentscheid site says 3.2 of 10.2 km in its header and 1.3 of 10.3 km in its text.
- **Lindwurmstraße section 2 start:** there is no official date. Work follows the Goetheplatz/Poccistraße U-Bahn renovation, which ends on 1 Aug 2027 (SWM, 11 May 2026).
- **Tram Münchner Norden opening:** older pages say 2027; official since Sep 2026: end 2031.
- **Tree loss for the Englischer Garten tram:** figures range from 19 to 900 depending on the route variant.

## Key sources

- Coalition agreement 2026–2032: https://www.fdp-muenchen.de/sites/default/files/2026-05/260508_Koalitionsvertrag_Muenchen.pdf
- Timetable 2027 (council paper): https://risi.muenchen.de/risi/dokument/v/9853476 · https://www.muenchen-transparent.de/dokumente/9813547/datei
- New tram line decisions, 30 Sep 2026: https://www.swm.de/unternehmen/presse/pressemitteilungen/2026/09-2026/mvg-beschluesse-tramneubaustrecken
- Tram-Westtangente plan approval: https://www.swm.de/unternehmen/presse/pressemitteilungen/2026/08-2026/mvg-planfeststellung-twt
- Westtangente funding risk (V 18994): https://www.muenchen-transparent.de/dokumente/9518781/datei
- U9: https://www.muenchen-transparent.de/dokumente/9530505/datei · https://de.wikipedia.org/wiki/U9-Spange_(U-Bahn_M%C3%BCnchen)
- Englischer Garten tunnel study: https://www.abendzeitung-muenchen.de/muenchen/fuer-240-millionen-euro-muenchner-doppelwumms-fuer-den-englischen-garten-art-1107368
- Cuts to the public transport building program (V 17096): https://www.muenchen-transparent.de/dokumente/9214100/datei
- 2. Stammstrecke: https://www.deutschebahn.com/de/presse/presse-regional/pr-muenchen-de/aktuell/presseinformationen/Donna-Maria-startet-Erster-maschineller-Tunnelvortrieb-der-2-Stammstrecke-beginnt--14037354
- U5 tunnel breakthrough: https://www.abendzeitung-muenchen.de/muenchen/u5-verlaengerung-licht-im-u-bahn-tunnel-art-1138356
- Nordbad switches: https://www.swm.de/unternehmen/presse/pressemitteilungen/2026/03-2026/mvg-tram-12-27-n27-weichenerneuerung-nordbad
- Schleißheimer Str. motion: https://www.muenchen-transparent.de/dokumente/9478485/datei
- Building-site management (Dunkel, Apr 2026): https://www.muenchen-transparent.de/dokumente/9641968/datei
- Building-site map and closures: https://stadt.muenchen.de/infos/baustellen-verkehrseinschraenkungen · https://www.mvg.de/trambau
- ADAC on building sites 2026: https://www.adac.de/der-adac/regionalclubs/suedbayern/news/muenchens-verkehrsnetz-am-limit-baustellen-2026/
- SWM Fernwärme conversion: https://www.swm.de/geschaeftskunden/fernwaerme/modernisierung-netz
- Cycle network IR III: https://ru.muenchen.de/2026/182/Stadtrat-beschliesst-neue-Radverkehrsverbindungen-126187
- Gebsattelberg: https://ru.muenchen.de/2026/137/Stadtrat-beschliesst-kostenguenstigen-Radweg-am-Gebsattelberg-125370
- Radentscheid status: https://stadt.muenchen.de/infos/radentscheid.html · https://muenchenunterwegs.de/radentscheid/massnahmen/
- Lindwurmstraße rollback: https://www.abendzeitung-muenchen.de/muenchen/lindwurmstrasse-in-muenchen-verschwinden-die-radwege-wieder-art-1145658
- Nahverkehrsumlage motion: https://www.muenchen-transparent.de/dokumente/9530781/datei
- Olympia nomination: https://www.muenchen.de/aktuell/dosb-vergibt-nationale-olympiabewerbung-muenchen
- Tramreport on the coalition: https://www.tramreport.de/2026/05/08/koalitionsvertrag-2026-2032/
