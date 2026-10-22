# Planned rail and tram projects in Munich: stations for scenario modeling (as of 19 Oct 2026)

Companion to `pt_projects.csv`: 88 rows, 17 project_ids. The research was done in German, mostly from official sources. Each source is marked **[verified]** (I opened it and saw the fact) or **[unverified]** (seen only in search snippets or in secondary sources).

## Conventions used in the CSV

- **station_is_new is mode-specific.** 1 means no station of this mode exists at this place today. A bus stop, or a station of another mode, may already be there. Examples: a new tram stop at U-Bahn Holzapfelkreuth is 1, and the new U5 station under Pasing DB is 1. 0 means an existing station of the same mode gains a new line or platform: Laim and Leuchtenbergring for the S-Bahn, Münchner Freiheit and Hbf for the U9, Tivolistraße for the tram. Hbf and Ostbahnhof on the 2nd trunk get new deep platforms but are coded 0, so they map onto the existing hub stop. Marienhof is 1.
- **trains_per_hour** is per direction and per line. "Off-peak" means daytime off-peak, not evening. It is empty where no headway is published; then use `analog_line`.
- **opening_year** is empty when no year exists. Three values are my placeholders and are flagged in the note: U5 Freiham 2040, U9 2040 and TMN PFA 2 2031.
- **funded = 1** means the money is committed: Bund/Land grants, a signed financing agreement, or the city's explicit decision to build despite missing grants (TMN PFA 1, TWT).
- **verified** concerns the station's existence and name in the cited source. Coordinates are from OSM or Nominatim. Where the stop site is not published, I used the nearest named intersection, and the note says so.
- **Several rows per station** occur only for the 2nd trunk (one row per line) and for the Laim restoration (one row per line).

## 1. Tram-Westtangente, remaining section (tram 14): 9 rows

- **What is open:** Since 28 Feb 2026 line 14 runs Pasing Bf–…–Ammerseestraße–Senftenauerstraße–Gondrellplatz. It runs every 10 min by day and every 20 min from 22:00. **[verified]** muenchen.de
- **Not yet open, and in the CSV:** Andreas-Vöst-Straße, Holzapfelkreuth, Waldfriedhof and Waldfriedhof Haupteingang. Legally these are in PFA 1, which was approved 4 Sep 2023 and is under construction, but they open with the 2028 stage. **This is wider than the brief's "section 2 = Waldfriedhof–Aidenbachstraße"**: they are not in today's timetable, so leaving them out would undercount the stage. PFA 2, approved Aug 2026, adds Drygalski-Allee, Machtlfinger Straße, Geisenhausenerstraße and Aidenbachstraße, plus a temporary stop with loop at Ratzingerplatz. **[verified]** Erläuterungsbericht Tektur A, UVP notice Tektur C, muenchenwiki.
- **Dates:** SWM, 30 Sep 2026: opening to Aidenbachstraße "weiterhin Ende 2028". Council paper V 18994: without a city funding exemption, end 2030 or early 2031, so risk year 2031. muenchenwiki says mid-2028 to Ratzingerplatz first, because the Aidenbachstraße terminus is only finished from 2028. That conflicts mildly with SWM. Tracks from Jul 2027.
- **Headway:** 6 trains/h (10 min), the same as today's line 14. The headway for the extended line is not published separately.

## 2. Tram Münchner Norden: 6 + 6 rows

- **PFA 1 (Schwabing Nord–Kieferngarten), under construction, 6 new stops:** Maria-Probst-Straße, Neufreimann, Werner-Egk-Bogen, Paul-Hindemith-Allee, Bernsteinweg, Kieferngarten. **[verified]** Regierung von Oberbayern plan approval of 31 Oct 2024.
- **PFA 2 (Neufreimann–Am Hart), 7 stops including Werner-Egk-Bogen, which is shared:** Grusonstraße, Paracelsusstraße, Heidemannstraße, Rothpletzstraße, Rathenaustraße, Am Hart. The names are working titles. **[verified]** council paper V 15807 (Jul 2025). The project counts 12 stops in total.
- **Line concept [verified, V 15807]:** First, tram 23 runs to Kieferngarten. After PFA 2, tram 23 runs Münchner Freiheit–Schwabing Nord–Am Hart, and the new tram 24 shuttles Am Hart–Kieferngarten. Each runs every 10 min by day, so Neufreimann–Am Hart gets a 5-min combined service.
- **Dates (conflict):** The original target was end 2027, then 2029 (summer 2025). SWM, Sep 2026: Schwabing Nord–Kieferngarten "Ende 2031" **[verified]**. For PFA 2, V 15807 (Jul 2025) targeted end 2029. Since Sep 2026 SWM says only that plan approval starts from Oct 2026, with no date. **I set 2031 (assumption).**
- **Funding:** BCR 2.61 and a GVFG application exist, but there is no binding Bund/Land commitment. Under the Dec 2025 financing rule, work was held at LP4. On 30 Sep 2026 the council decided case by case to continue past the Nordring bridge. **[verified]** SWM press release; tramreport article of 18 Sep 2026.

## 3. U5 Laimer Platz–Pasing: 3 rows

- **Stations [verified, ubahnbau-muenchen.de]:** Baumschule Laim (under Gotthardstraße between Willibald- and Reutterstraße, formerly "Willibaldstraße"), Am Knie, Pasing (under the DB station). 3.8 km, about €1.3 bn, €645.2 m in grants.
- **Dates:** 2036 per Abendzeitung (18 Jun 2026) **[verified article; press-reported, no official year]**. MVV's older page says "Anfang der 2030er" (outdated). Construction is "im Plan".
- **Headway:** not published; analog U5.

## 4. U5 Pasing–Freiham: 4 rows

- **Stations [verified, ubahnbau-muenchen.de]:** Westkreuz (S-Bahn interchange), Radolfzeller Straße, Riesenburgstraße, Freiham-Zentrum (terminus with sidings for 11 trains). 4.7 km.
- **Status:** Only the Freiham-Zentrum shell is funded and being built (Dec 2023, €94.1 m; main work to Oct 2027). The rest is unfunded.
- **Not verified:** "council planning vote postponed Oct 2026" and "2040s at the earliest" came from the brief; I could not confirm them. opening_year = 2040 is a placeholder.

## 5. 2. S-Bahn-Stammstrecke: 29 rows

- **Stations [verified, 2.stammstrecke-muenchen.de]:** Laim and Leuchtenbergring (existing, rebuilt as changeover stations), plus new underground stations Hauptbahnhof, Marienhof and Ostbahnhof. About 11 km, with a 7 km tunnel.
- **Opening:** DB plan 2035; other estimates 2037 or later; BEG tender: "Mitte oder Ende der 2030er". So 2035, with risk 2037. Cost: DB forecast over €11 bn (Apr 2025).

### Operating concept (best-sourced version, verified = 0 in the CSV)

There is no final timetable. Bavaria (Landtag 17/17196) says the detailed timetable will be worked out only close to opening. The official building blocks are:

1. **Landtag 17/7917 (2015) [verified]:** S1 (Freising/Flughafen) and S6 (Tutzing) use the 2nd trunk at an all-day 15-min headway. The express and regional S-Bahns also use the 2nd trunk.
2. **Landtag 17/17196 (2017) [verified]:** The basic headway changes from 10/20 to 15 min, except S2, S7 and S20. Express S-Bahns run every 30 min on several outer branches. S1 stations (Freising…Moosach), S6 stations (Tutzing…Gräfelfing) and Ebersberg/Grafing Stadt lose their direct link to the old trunk, which shows which branches move.
3. **SMA/OBB article, ETR 11/2017 [verified]:**
   - 15 min all day on 5 of 7 western and 3 of 5 eastern branches.
   - Express services on 4 western and 2 eastern branches, saving up to 14 min.
   - 6 instead of 3 trains/h on the S8 corridor to the airport (15-min S-Bahn plus 30-min express).
   - Regional S-Bahns from Buchloe (every 30 min), Landshut and Augsburg (hourly).
   - Trunk capacity rises from 30 to 54 trains/h/direction; the start concept uses 36.
   - Train-km rise from about 21 to about 30 million a year.
4. **BEG / bayern.de, 1st Munich S-Bahn contract, second operating stage [verified]:**
   - The basic headway on most lines changes from 20 to 15 min.
   - Express S-Bahns run every 30 min to Mammendorf, Herrsching, Ebersberg and the airport.
   - Regional S-Bahns run to Buchloe and Landshut, and via Mering to Augsburg, alternating with the Mammendorf express.
   - Train-km go from 20.9 to 29.1 million a year (+40 %), with 110 new trains.
5. **Line table, start concept "Mitfall 6+" (Apr 2017), from German Wikipedia [secondary, unverified against the primary source]:**

| Line | Route on the 2nd trunk | Headway | Trains/h used |
|---|---|---|---|
| S1 | Freising/Flughafen–Laim–Marienhof–Leuchtenbergring–Ebersberg | 15′ (30′ per branch north of Neufahrn) | 4 |
| S6 | Tutzing–Pasing–Laim–Marienhof–Ostbahnhof | 15′ | 4 (not at Leuchtenbergring) |
| S18X | Herrsching–Pasing–Laim–Marienhof–Leuchtenbergring (express) | 30′ | 2 |
| S21X | Landshut–Freising–Marienhof–Leuchtenbergring (regional S-Bahn) | 60′ | 1 |
| S23X | (Augsburg–)Mering–Mammendorf–Pasing–Laim–Marienhof–Flughafen via S8 corridor | 30′ (hourly from Augsburg) | 2 |
| S24X | Buchloe–Geltendorf–Pasing–Laim–Marienhof–Leuchtenbergring | 30′ | 2 |

That totals 15 trains/h/direction on the 2nd trunk at Laim, Hbf, Marienhof and Ostbahnhof, and 11 at Leuchtenbergring. Peak is set equal to off-peak because the concept is all-day and no peak extras are published.

**Modeling caveats:**
- These lines are *re-routed*: S1 and S6 leave the old trunk, so the old routings must be removed.
- The 20→15-min change applies network-wide on most lines. That is outside this station list, but it is the biggest supply effect.
- **Newer conflicting detail [verified, bahnblogstelle on the BEG tender, 2025]:** for the contract starting Dec 2034, S2 and S3 swap their eastern branches. The expansion for the 2nd trunk is a contract option, and the award is planned for 2029. The 2017 line numbers may therefore change.
- Express stop pattern in Munich [unverified snippet, Landtag 17/7918]: Pasing, Laim, Hbf, Marienhof, Ostbahnhof, Leuchtenbergring.

## 6. Laim, inbound S3/S4/S6/S8 restored: 4 rows

- **Facts:** The inbound stops are canceled from 25 Aug 2026 to "mid-2028" because of the Laim rebuild. **[verified]** notice on 2.stammstrecke-muenchen.de; muenchen.de **[unverified snippet]**.
- **How to model:** Use the outbound departures of the same line at Laim as a proxy for the restored inbound departures.

## 7. Tram Johanneskirchen: 2 rows

- **Route:** About 1 km, branching from the St. Emmeram line at Cosimastraße.
- **Stops [verified, MVG FAQ]:** Ringofenweg and Johanneskirchner Straße, the loop at S8 Johanneskirchen, elsewhere called "Johanneskirchen Bf".
- **Status:** Plan approval has been running since end 2022. No construction date. The targets of end 2025, then Q2/2025 approval, were missed.
- **Funding conflict:** The coalition agreement says "only with funding commitments", while MVG says it is financed from grants plus city budget. I set funded = 0.
- **Line and headway:** not published; analog 16.

## 8. U9-Spange: 7 rows

- **Stations [verified, ubahnbau-muenchen.de]:** Münchner Freiheit, Elisabethplatz, Pinakotheken, Theresienstraße (U29 branch to U2), Hauptbahnhof, Esperantoplatz, and a new joint Impler-/Poccistraße station (Billigungsbeschluss Sep 2024). 10.5 km.
- **New vs existing:** New are Elisabethplatz, Pinakotheken and Esperantoplatz. Existing nodes are Münchner Freiheit, Theresienstraße, Hbf and Impler-/Poccistraße.
- **Status:** Preliminary planning, not financed, €3.5–4 bn+. The Hbf box is being pre-built with the 2nd trunk (€662.5 m including the U9 preliminary planning, of which €562.6 m for the shell structure; V 08143, Nov 2022).
- **Staging proposal:** The Grüne motion of 29 Jan 2026 proposes staging Theresienstraße–Hbf–Implerstraße and questions Esperantoplatz.
- **Date:** "2040s" comes from secondary sources only, so 2040 is a placeholder.

## 9. Tram Lerchenauer Feld (ex Y-Nord): 1 row, "unknown"

- **No stop list published.** Only the corridor is known: Hbf–Hochschule München–Nordbad–Petuelring–northern Schleißheimer Straße, then a Y split to the Lerchenauer Feld market square and to Am Hart. **[verified]** MOR letter of 24 Jul 2026: "zu einem späteren Zeitpunkt".
- **System comparison:** The comparison of tram against U-Bahn (including U1 north) was not yet presented in Feb 2026 (CSU-FW question). I set status on_hold.

## 10. Tram-Nordtangente PFA 1 (Elisabethplatz–Englischer Garten–Tivolistraße): 6 rows

- **Route [verified]:** Route decision 20 Dec 2023 (V 10202): Elisabethplatz–Franz-Joseph-Str.–Martiusstr.–Thiemestr.–Englischer Garten–Tivolistraße.
- **Stops [secondary]:** Elisabethplatz (existing), a new westbound platform in Franz-Joseph-Straße, Giselastraße, Thiemestraße, Chinesischer Turm, Tivolistraße (existing, new loop). Sources are tramreport and muenchenwiki; the stop list is not from the council paper, so verified = 0.
- **Status: blocked.** The Freistaat refused in 2024 and SWM froze the planning (MOR letter of 6 Feb 2025) **[verified]**. MOR, Aug 2025: the city sticks with the surface route and does not pursue a tunnel. Not in the coalition agreement.
- **Planned lines:** tram 23 extended toward Karlsplatz, plus a new line Schwabing Nord–Lehel–Max-Weber-Platz–Giesing.

## 11. Augsburg–Munich express: 1 row, "unknown"

- **No Munich stops are named** beyond Pasing and the 2nd trunk stations. It is the hourly Augsburg part of S23X. It is already in the stammstrecke2 rows, so **do not add it twice**.

## Other projects with stations inside Munich (included)

- **S-Bahn shuttle on the DB-Nordring (Moosach or Karlsfeld to BMW FIZ, optionally Euro-Industriepark): 3 rows.**
  - New halts Knorrstraße/FIZ and Europark.
  - Every 20 min in the morning and afternoon peaks (3 hours each), otherwise hourly.
  - DB InfraGO preliminary planning; the council asked for operation before 2029, with no binding date. **[verified]** MOR letter of 18 Aug 2025 (muenchen-transparent 9252439). Exact sites are not published.
- **S-Bahn halt Berduxstraße on the S2 (Laim–Obermenzing): 1 row.**
  - Financing agreement Sep 2023 (about €14 m); planning agreement Jul 2024; tenders Dec 2025.
  - No date and no fixed site. **[verified]** MOR letter of 27 Apr 2026.
- **U4 Ost (Arabellapark–Cosimapark/Fideliopark–Englschalking–Pellegrinistraße): 4 rows.**
  - Very early planning; depends on the S8 four-track expansion. **[verified]** ubahnbau-muenchen.de
- **U26 (Am Hart–Kieferngarten): 1 row, "unknown".**
  - Two unnamed stations; only after the U9. **[verified]**
- **Regional-train halt Poccistraße: 1 row.**
  - Needs the Daglfing–Johanneskirchen expansions before all trains can stop. The 2026 target was missed. **[verified]** MOR letter of 4 Feb 2026.

## Not included (and why)

- **U6 Martinsried:** in Planegg, outside the city. Planned 2027 (MVG and Planegg project pages; on schedule as of Aug 2026).
- **Tram depot access track Ständlerstraße:** no passenger stops. Plan approval 13 Feb 2026; target H2 2028, but work is suspended.
- **U1 Nord and U1 Süd (Klinikum Harlaching, 2 unnamed stations):** studies only.
- **S-Bahn halt Menterschwaige:** under study, with the experts recommending it. No plan.
- **Kolumbusplatz / S-Bahn Südring (S13X):** not pursued.
- **S8 four-track Daglfing–Johanneskirchen:** existing stations only.
- **Tram Amalienburgstraße–Freiham and Tram Parkstadt Solln:** dropped Jul 2025.
- **Tram Daglfing:** 2028 at the earliest; no stop list found.

## Main uncertainties

1. **2nd trunk line table:** the 2017 concept is secondary-sourced, and the BEG tender signals line changes. The 15-min network-wide upgrade is not in this file.
2. **Placeholder opening years:** U5 Freiham, U9 and TMN PFA 2 (2040, 2040, 2031). TWT 2028 is official but carries funding risk.
3. **Approximated coordinates (verified = 0 sites):** Neufreimann, Rothpletzstraße, Rathenaustraße, U5 Freiham stations, Ostbahnhof tief, Hbf tief, Nordring halts, Berduxstraße, Johanneskirchner Straße loop.

## Sources

**Verified (opened):**
- https://www.swm.de/unternehmen/presse/pressemitteilungen/2026/08-2026/mvg-planfeststellung-twt
- https://www.swm.de/unternehmen/presse/pressemitteilungen/2026/09-2026/mvg-beschluesse-tramneubaustrecken
- https://www.muenchen.de/verkehr/aktuell/neue-tram-linie-14-westtangente-zwischen-pasing-gondrellplatz
- https://www.uvp-verbund.de/documents-ige-ng/igc_by/a809852e-50cc-4489-a875-b17fa62bfc9e/1.2%20Erl%C3%A4uterungsbericht%20Tektur%20A.pdf
- https://www.uvp-verbund.de/documents-ige-ng/igc_by/a809852e-50cc-4489-a875-b17fa62bfc9e/Tektur%20C%20Bekanntmachung%20UVP.pdf
- https://www.muenchenwiki.de/wiki/Trambahnlinie_14 (secondary)
- https://www.regierung.oberbayern.bayern.de/mam/dokumente/bereich2/pfb/u-bahn_tram/2024-11-04_pfb_schwabing-_nord_kieferngarten.pdf
- https://www.muenchen-transparent.de/dokumente/9175388/datei (TMN PFA 2, V 15807)
- https://risi.muenchen.de/risi/dokument/v/9847142 (TMN and Lerchenauer Feld, 24 Jul 2026)
- https://tram-muenchner-norden.mvg.de/projekt.html
- https://www.tramreport.de/2025/07/23/tmn-202507-trassierungsbeschluss-mo/
- https://www.tramreport.de/2026/09/18/finanzierungsregelung-baustopp-tmn/
- https://www.ubahnbau-muenchen.de/projekte/pasing
- https://www.ubahnbau-muenchen.de/projekte/freiham
- https://www.ubahnbau-muenchen.de/projekte/u9-entlastungsspange
- https://www.ubahnbau-muenchen.de/projekte/u4-ost
- https://www.ubahnbau-muenchen.de/projekte/u26-verbindungsspange
- https://www.ubahnbau-muenchen.de/projekte/u6-martinsried
- https://www.ubahnbau-muenchen.de/projekte/u1-nord
- https://www.ubahnbau-muenchen.de/projekte/u1-sued
- https://www.2.stammstrecke-muenchen.de/
- https://de.wikipedia.org/wiki/Zweite_Stammstrecke (secondary)
- https://www.bayern.landtag.de/www/ElanTextAblage_WP17/Drucksachen/Schriftliche%20Anfragen/17_0007917.pdf
- https://www.bayern.landtag.de/www/ElanTextAblage_WP17/Drucksachen/Schriftliche%20Anfragen/17_0017196.pdf
- https://sma-partner.com/storage/app/media/Dokumente/Veranstaltungen%20und%20Publikationen/ETR-Die-2.-Stammstrecke_de.pdf
- https://www.bayern.de/1-muenchner-s-bahn-vertrag/
- https://bahnblogstelle.com/263471/beg-startet-vergabe-fuer-muenchner-s-bahn-betrieb-ab-ende-2034/
- https://tram-johanneskirchen.mvg.de/projekt.html
- https://tram-johanneskirchen.mvg.de/kontakt-faq/faq-tjo/tjo7.html
- https://tram-johanneskirchen.mvg.de/kontakt-faq/faq-tjo/tjo8.html
- https://www.muenchen-transparent.de/dokumente/9490929/datei (Tram Johanneskirchen, V 18766, BA 13 decision of 10 Feb 2026)
- https://www.muenchen-transparent.de/dokumente/8135927/datei (Nordtangente route decision, V 10202)
- https://www.muenchen-transparent.de/dokumente/8902736/datei (Nordtangente frozen, Feb 2025)
- https://www.muenchen-transparent.de/dokumente/9262805/datei (Nordtangente, MOR letter of 26 Aug 2025: surface route, no tunnel)
- https://www.tramreport.de/2023/12/13/trassierungsbeschluss-tnt/
- https://www.muenchen-transparent.de/dokumente/9530505/datei (U9 Grüne motion)
- https://www.muenchen-transparent.de/dokumente/9550336/datei (Y-Nord system comparison)
- https://www.muenchen-transparent.de/dokumente/9252439/datei (Nordring shuttle)
- https://risi.muenchen.de/risi/dokument/v/9682315 (Berduxstraße)
- https://risi.muenchen.de/risi/dokument/v/9539994 (Menterschwaige, Kolumbusplatz, Poccistraße)
- https://www.muenchen-transparent.de/dokumente/8871200/datei (Ständlerstraße)
- OpenStreetMap (Overpass and Nominatim) for coordinates

**Unverified (search snippets only):**
- https://www.abendzeitung-muenchen.de/muenchen/u5-verlaengerung-licht-im-u-bahn-tunnel-art-1138356 (U5 2036)
- https://www.mvv-muenchen.de/mvv-im-ueberblick/die-gesellschaft/planungen-und-projekte/u-bahn-planungstand/ ("Anfang der 2030er")
- https://www.bayern.landtag.de/www/ElanTextAblage_WP17/Drucksachen/Schriftliche%20Anfragen/17_0007918.pdf (express stop pattern)
- https://www.bayern.landtag.de/www/ElanTextAblage_WP17/Drucksachen/Schriftliche%20Anfragen/17_0016419.pdf (hourly Augsburg regional S-Bahn)
- https://www.muenchen.de/verkehr/aktuell/s-bahn-muenchen-grossbaustellen-und-sperrungen-juni-juli-2026 (Laim cancellations)
- https://stmb.bayern.de/med/pressemitteilungen/pressearchiv/2023/173/index.php (Berduxstraße, about €14 m, 5,200 riders/day)
- https://www.muenchenwiki.de/wiki/Tram-Nordtangente (Nordtangente stops)
- Caller background: "U5 Freiham vote postponed Oct 2026; 2040s"; "U9 2040s"
