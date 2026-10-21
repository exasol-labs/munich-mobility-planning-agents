#!/usr/bin/env python3
"""Turn munich-open-data.zip into a FLAT folder of analysis-ready CSVs.

`exakit data-load <folder>` reads a folder at its TOP LEVEL only and makes one
table per file, named after the file. The portal download is nested (one
sub-folder per dataset), uses German column names, mixed date formats, UTM
coordinates (EPSG:25832) in some files and WGS84 lat/lon in others. This script
fixes all of that once, so the tables join with plain SQL.

    python3 prepare_dataset.py ~/Downloads/munich-open-data.zip --out ~/munich-dataset
    EXAKIT_SCHEMA=MUNICH_DATASET exakit data-load ~/munich-dataset

Pure standard library. No pandas, no pyproj.

Output files (-> table names after load, schema MUNICH_DATASET):
  bike_counts_daily.csv        BIKE_COUNTS_DAILY       one row per station per day, with weather
  bike_counts_15min.csv        BIKE_COUNTS_15MIN       15-minute counts
  bike_count_stations.csv      BIKE_COUNT_STATIONS     the 6 permanent counters, lat/lon, district
  districts.csv                DISTRICTS               25 districts: population, area_km2, density_per_km2, centroid, polygon (WGS84 WKT)
  district_employment.csv      DISTRICT_EMPLOYMENT     workers at place of work per district, 2022 + 2040 (city estimate)
  district_population.csv      DISTRICT_POPULATION     residents per district, counts 2015/2024/2025 + forecast 2045
  pt_project_stations.csv      PT_PROJECT_STATIONS     planned rail/tram projects, one row per station, with district
  roadworks.csv                ROADWORKS               current/planned roadworks, dates, centroid, district
  cycling_infrastructure.csv   CYCLING_INFRASTRUCTURE  cycle-path segments, type, length, lat/lon, district
  mvv_agency.csv               MVV_AGENCY              GTFS
  mvv_routes.csv               MVV_ROUTES              GTFS, with route_mode decoded from route_type, line_mode
                                                       (S-Bahn by name) and is_night
  mvv_trips.csv                MVV_TRIPS               GTFS
  mvv_stops.csv                MVV_STOPS               GTFS, with district_no for stops inside Munich and the
                                                       modes that serve each stop (stop_mode, stop_modes, serves_*)
  vehicle_capacity.csv         VEHICLE_CAPACITY        planning capacity per scheduled trip for each line_mode
  line_capacity.csv            LINE_CAPACITY           per-line overrides where the formation differs (U4, U7, ...)
  mvv_stop_times.csv           MVV_STOP_TIMES          GTFS (large: ~250 MB)
  mvv_calendar.csv             MVV_CALENDAR            GTFS
  mvv_calendar_dates.csv       MVV_CALENDAR_DATES      GTFS
  mvv_feed_info.csv            MVV_FEED_INFO           GTFS
  mvv_ticketing_deep_links.csv MVV_TICKETING_DEEP_LINKS GTFS
  mvv_ticketing_identifiers.csv MVV_TICKETING_IDENTIFIERS GTFS (when present)
  mvg_bike_trips.csv           MVG_BIKE_TRIPS          optional, --with-mvg-bikes 2024 2025
"""
from __future__ import annotations

import argparse
import csv
import io
import math
import os
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

csv.field_size_limit(min(sys.maxsize, 2**31 - 1))

# --------------------------------------------------------------------------- geo
A = 6378137.0
F = 1 / 298.257223563
K0 = 0.9996
E2 = F * (2 - F)
EP2 = E2 / (1 - E2)


def utm_to_latlon(easting: float, northing: float, zone: int = 32) -> tuple[float, float]:
    """EPSG:25832 (UTM 32N, ETRS89) -> WGS84 lat/lon. ETRS89 ~ WGS84 at metre level."""
    x = easting - 500000.0
    y = northing
    lon0 = math.radians((zone - 1) * 6 - 180 + 3)
    m = y / K0
    mu = m / (A * (1 - E2 / 4 - 3 * E2**2 / 64 - 5 * E2**3 / 256))
    e1 = (1 - math.sqrt(1 - E2)) / (1 + math.sqrt(1 - E2))
    phi1 = (mu + (3 * e1 / 2 - 27 * e1**3 / 32) * math.sin(2 * mu)
            + (21 * e1**2 / 16 - 55 * e1**4 / 32) * math.sin(4 * mu)
            + (151 * e1**3 / 96) * math.sin(6 * mu)
            + (1097 * e1**4 / 512) * math.sin(8 * mu))
    n1 = A / math.sqrt(1 - E2 * math.sin(phi1) ** 2)
    t1 = math.tan(phi1) ** 2
    c1 = EP2 * math.cos(phi1) ** 2
    r1 = A * (1 - E2) / (1 - E2 * math.sin(phi1) ** 2) ** 1.5
    d = x / (n1 * K0)
    lat = phi1 - (n1 * math.tan(phi1) / r1) * (
        d**2 / 2 - (5 + 3 * t1 + 10 * c1 - 4 * c1**2 - 9 * EP2) * d**4 / 24
        + (61 + 90 * t1 + 298 * c1 + 45 * t1**2 - 252 * EP2 - 3 * c1**2) * d**6 / 720)
    lon = lon0 + (d - (1 + 2 * t1 + c1) * d**3 / 6
                  + (5 - 2 * c1 + 28 * t1 - 3 * c1**2 + 8 * EP2 + 24 * t1**2) * d**5 / 120) / math.cos(phi1)
    return round(math.degrees(lat), 6), round(math.degrees(lon), 6)


_RING = re.compile(r"\(([^()]+)\)")


def wkt_rings(wkt: str) -> list[list[tuple[float, float]]]:
    """Every coordinate ring in a POLYGON / MULTIPOLYGON WKT, as (x, y) lists."""
    rings = []
    for group in _RING.findall(wkt or ""):
        pts = []
        for pair in group.split(","):
            parts = pair.split()
            if len(parts) >= 2:
                pts.append((float(parts[0]), float(parts[1])))
        if len(pts) >= 3:
            rings.append(pts)
    return rings


def outer_rings(wkt: str) -> list[list[tuple[float, float]]]:
    """First ring of each polygon part (holes are ignored for this demo)."""
    out = []
    body = (wkt or "").strip()
    if body.upper().startswith("MULTIPOLYGON"):
        for part in re.findall(r"\(\((.*?)\)\)", body, flags=re.S):
            r = wkt_rings("((" + part + "))")
            if r:
                out.append(r[0])
    else:
        r = wkt_rings(body)
        if r:
            out.append(r[0])
    return out


def rings_to_wgs84(rings):
    return [[utm_to_latlon(x, y) for (x, y) in ring] for ring in rings]


def centroid(rings_ll):
    pts = [p for ring in rings_ll for p in ring]
    if not pts:
        return "", ""
    return (round(sum(p[0] for p in pts) / len(pts), 6),
            round(sum(p[1] for p in pts) / len(pts), 6))


def point_in_ring(lat, lon, ring):
    inside = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        yi, xi = ring[i]
        yj, xj = ring[j]
        if (yi > lat) != (yj > lat):
            x_cross = (xj - xi) * (lat - yi) / (yj - yi + 1e-18) + xi
            if lon < x_cross:
                inside = not inside
        j = i
    return inside


def polygon_wkt_wgs84(rings_ll):
    parts = []
    for ring in rings_ll:
        if ring[0] != ring[-1]:
            ring = ring + [ring[0]]
        parts.append("((" + ", ".join(f"{lon} {lat}" for lat, lon in ring) + "))")
    if len(parts) == 1:
        return "POLYGON" + parts[0]
    return "MULTIPOLYGON(" + ", ".join(parts) + ")"


class DistrictIndex:
    def __init__(self):
        self.items = []  # (district_no, rings_ll, bbox)

    def add(self, no, rings_ll):
        for ring in rings_ll:
            lats = [p[0] for p in ring]
            lons = [p[1] for p in ring]
            self.items.append((no, ring, (min(lats), max(lats), min(lons), max(lons))))

    def lookup(self, lat, lon):
        if lat == "" or lon == "":
            return ""
        for no, ring, (la0, la1, lo0, lo1) in self.items:
            if la0 <= lat <= la1 and lo0 <= lon <= lo1 and point_in_ring(lat, lon, ring):
                return no
        return ""


# --------------------------------------------------------------------------- helpers
def norm_date(s: str, strict: bool = False) -> str:
    """'2026.01.01' / '01.01.2026' / '2026-01-01' / with time -> 'YYYY-MM-DD'.
    strict=True returns '' for anything that is not a date (e.g. 'Beginn vor mehr als einem Jahr')."""
    s = (s or "").strip()
    m = re.match(r"^(\d{4})[.\-/](\d{2})[.\-/](\d{2})", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m = re.match(r"^(\d{2})[.\-/](\d{2})[.\-/](\d{4})", s)
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    return "" if strict else s


def norm_datetime(s: str) -> str:
    s = (s or "").strip()
    d = norm_date(s)
    m = re.search(r"(\d{1,2}):(\d{2})(?::(\d{2}))?", s[8:] if len(s) > 8 else "")
    if m and len(d) == 10:
        return f"{d} {int(m.group(1)):02d}:{m.group(2)}:{m.group(3) or '00'}"
    return d


def num(s: str) -> str:
    s = (s or "").strip().replace(",", ".")
    return s


def intnum(s: str) -> str:
    """'101 901' / '101.901' -> '101901'."""
    return re.sub(r"[^0-9-]", "", s or "")


def clean_header(h: str) -> str:
    h = h.strip().lower()
    h = (h.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss"))
    h = re.sub(r"[^a-z0-9]+", "_", h).strip("_")
    return h


def read_csv(path: Path, delimiter=None, encoding="utf-8-sig"):
    raw = path.read_text(encoding=encoding, errors="replace")
    if delimiter is None:
        first = raw.split("\n", 1)[0]
        delimiter = ";" if first.count(";") > first.count(",") else ","
    rdr = csv.reader(io.StringIO(raw), delimiter=delimiter)
    header = [clean_header(h) for h in next(rdr)]
    for row in rdr:
        if not row or all(not c.strip() for c in row):
            continue
        yield dict(zip(header, [c.strip() for c in row]))


def write_csv(path: Path, header: list[str], rows):
    n = 0
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")  # LF only: exapump passes CRLF through
        w.writerow(header)
        for r in rows:
            w.writerow([r.get(h, "") for h in header])
            n += 1
    print(f"  wrote {path.name:<30} {n:>9,} rows")
    return n


def find_dir(root: Path, startswith: str) -> Path | None:
    for p in sorted((root / "datasets").iterdir()):
        if p.is_dir() and p.name.startswith(startswith):
            return p
    return None


STATIONS = [
    # name, long name, lat, lon, direction_1, direction_2  (Munich geoportal, mor_wfs:raddauerzaehlstellen)
    ("Arnulf", "Arnulfstr. 9 - 11 Suedseite", 48.14205, 11.55534, "Ost", "West"),
    ("Kreuther", "Bad-Kreuther-Str.", 48.12194, 11.62417, "West", "Ost"),
    ("Olympia", "Rudolf-Harbig-Weg (Olympiapark)", 48.16887, 11.55005, "Nord", "Sued"),
    ("Hirsch", "Birketweg HLP (Hirschgarten)", 48.14438, 11.51794, "West", "Ost"),
    ("Margareten", "Margaretenstr. (Harras)", 48.12032, 11.53599, "West", "Ost"),
    ("Erhardt", "Erhardtstr. (Deutsches Museum)", 48.13192, 11.58469, "Sued", "Nord"),
]

ROUTE_MODES = {"0": "Tram", "1": "U-Bahn", "2": "Rail", "3": "Bus", "4": "Ferry", "5": "Cable tram",
               "6": "Aerial lift", "7": "Funicular", "11": "Trolleybus", "12": "Monorail",
               "100": "Rail", "109": "S-Bahn", "400": "U-Bahn", "700": "Bus", "900": "Tram"}

# Analysis modes, highest capacity first. A stop's stop_mode is the first of these that serves it.
LINE_MODES = ["S-Bahn", "U-Bahn", "Regional rail", "Tram", "Bus"]
MODE_FLAGS = {"S-Bahn": "serves_sbahn", "U-Bahn": "serves_ubahn", "Regional rail": "serves_regional_rail",
              "Tram": "serves_tram", "Bus": "serves_bus"}


def line_mode(route: dict) -> str:
    """The MVV feed stores S-Bahn lines as route_type 0 (tram); classify by name instead."""
    name = route.get("route_short_name", "").strip()
    mode = ROUTE_MODES.get(route.get("route_type", ""), "Other")
    if re.match(r"^S\d+$", name) or mode == "S-Bahn":
        return "S-Bahn"
    if mode == "Rail":
        return "Regional rail"
    return mode


# Planning capacity per scheduled trip (seats + standing), one row per line_mode -> table VEHICLE_CAPACITY.
# Researched 2026-10-16; see the sources column. Standing room at the VDV planning norm where available.
VEHICLE_CAPACITY_HEADER = ["line_mode", "capacity_per_trip", "capacity_low", "capacity_high", "typical_vehicle",
                           "typical_formation", "seats", "standing", "standing_standard", "runs_on_street",
                           "basis", "sources"]
_ZAHLEN = "https://www.mvg.de/dam/jcr:bc1ca7c4-a1ea-4a3b-adc9-ebdb1da8bb0b/260624_MVG_Flyer_MVG_in_Zahlen_2026_Web-RGB.pdf"
_MVG = "https://www.mvg.de/ueber-die-mvg/unsere-fahrzeuge/"
VEHICLE_CAPACITY = [
    {"line_mode": "S-Bahn", "capacity_per_trip": 1200, "capacity_low": 612, "capacity_high": 1836,
     "typical_vehicle": "DB ET 423 (modernised, 612 places per unit)", "typical_formation": "Vollzug, 2 units",
     "seats": "", "standing": "", "standing_standard": "not stated",
     "runs_on_street": 0,
     "basis": "Vollzug of two modernised ET 423 = 1,224; Kurzzug (1 unit, Sundays) and Langzug (3 units, peak on some "
              "lines) roughly cancel; the 36 ET 420 (446) and 16 ET 424 (506) pull the average slightly down",
     "sources": "https://www.bayern.landtag.de/www/ElanTextAblage_WP17/Drucksachen/Schriftliche%20Anfragen/17_0000926.pdf "
                "https://de.wikipedia.org/wiki/DB-Baureihe_423"},
    {"line_mode": "U-Bahn", "capacity_per_trip": 900, "capacity_low": 580, "capacity_high": 940,
     "typical_vehicle": "MVG C2 (220 seats + 720 standing)", "typical_formation": "Langzug, 6 cars",
     "seats": 220, "standing": 720, "standing_standard": "4 persons/m2 (Siemens C2 datasheet)",
     "runs_on_street": 0,
     "basis": "102 of 121 trains are C1/C2 (912-940) and run as 6 cars; most lines run Langzug all day. "
              "Per-line values in LINE_CAPACITY (U4, U7 run 4-car A/B trains = 580)",
     "sources": _MVG + "u-bahn.html "
                "https://assets.new.siemens.com/siemens/assets/api/uuid:d82c503e-7f68-42a4-bd2f-2afed7e12530/siemens-mobility-metro-munich-datasheet-de.pdf "
                + _ZAHLEN},
    {"line_mode": "Regional rail", "capacity_per_trip": 500, "capacity_low": 200, "capacity_high": 1000,
     "typical_vehicle": "Talent 2, LINT 54, Desiro HC", "typical_formation": "single to triple units",
     "seats": "", "standing": "", "standing_standard": "not stated",
     "runs_on_street": 0,
     "basis": "single Talent 2 / LINT about 200-380, coupled units and Desiro HC on the main RE lines 600-1,000; "
              "low confidence",
     "sources": "https://de.wikipedia.org/wiki/Bayerische_Oberlandbahn https://de.wikipedia.org/wiki/Siemens_Desiro_HC"},
    {"line_mode": "Tram", "capacity_per_trip": 205, "capacity_low": 162, "capacity_high": 257,
     "typical_vehicle": "Siemens Avenio, 4-part (69 seats + 147 standing)", "typical_formation": "single vehicle",
     "seats": 69, "standing": 147, "standing_standard": "4 persons/m2 (Siemens Avenio datasheet)",
     "runs_on_street": 1,
     "basis": "fleet-weighted over 166 trams: R2.2 164 x54, R3.3 218 x20, S1 221 x14, Avenio 4-part about 218, "
              "T2+T3 coupled 257 x9 -> about 202-204. Line 20 in LINE_CAPACITY",
     "sources": _MVG + "tram.html "
                "https://assets.new.siemens.com/siemens/assets/api/uuid:003a031b-4c1b-45ec-be0f-c25194e01320/datenblatt-avenio-muenchen-d.pdf "
                + _ZAHLEN},
    {"line_mode": "Bus", "capacity_per_trip": 90, "capacity_low": 55, "capacity_high": 133,
     "typical_vehicle": "18 m articulated bus (about 100 places)", "typical_formation": "single vehicle",
     "seats": "", "standing": "", "standing_standard": "not stated",
     "runs_on_street": 1,
     "basis": "SWM fleet-weighted (72 solo x65, 270 articulated x100, 57 bus-trailer x130) = 98; the 283 partner "
              "buses and MVV regional buses are mostly 12 m solo (about 60-65), so 90 overall",
     "sources": _MVG + "bus.html " + _ZAHLEN},
]

# Lines whose formation differs from their mode's typical value; only overrides with a published source.
LINE_CAPACITY_HEADER = ["line", "line_mode", "capacity_per_trip", "basis", "sources"]
_UBAHN = "https://www.u-bahn-muenchen.de/fahrzeuge/ https://de.wikipedia.org/wiki/U-Bahn_M%C3%BCnchen"
LINE_CAPACITY = (
    [{"line": l, "line_mode": "U-Bahn", "capacity_per_trip": 930,
      "basis": "Langzug line, mostly C1/C2 six-car trains (912-940)", "sources": _UBAHN}
     for l in ("U1", "U2", "U3", "U5", "U6", "U8")]
    + [{"line": l, "line_mode": "U-Bahn", "capacity_per_trip": 580,
        "basis": "runs as a 4-car A/B train (2 x 290) as the rule", "sources": _UBAHN} for l in ("U4", "U7")]
    + [{"line": "20", "line_mode": "Tram", "capacity_per_trip": 257,
        "basis": "Avenio T2+T3 coupled pair (about 260 places)", "sources": _MVG + "tram.html " + _ZAHLEN}]
    + [{"line": l, "line_mode": "Bus", "capacity_per_trip": 100,
        "basis": "MetroBus line, mostly articulated buses (about 100 places)",
        "sources": "https://de.wikipedia.org/wiki/Busverkehr_in_M%C3%BCnchen " + _ZAHLEN}
       for l in ("50", "51", "52", "53", "54", "55", "56", "57", "58", "59", "60", "62", "63", "68")]
)


def enrich_transit(out: Path) -> None:
    """Add line_mode / is_night to mvv_routes.csv, the modes serving each stop to mvv_stops.csv, and write
    vehicle_capacity.csv. Works on the flat folder, so it can run after a full build or on its own."""
    routes = list(read_csv(out / "mvv_routes.csv", delimiter=","))
    for r in routes:
        r["line_mode"] = line_mode(r)
        r["is_night"] = "1" if re.match(r"^N\d+", r.get("route_short_name", "").strip()) else "0"
    write_csv(out / "mvv_routes.csv", list(routes[0].keys()), routes)
    route_mode = {r["route_id"]: r["line_mode"] for r in routes}

    trip_mode = {}
    for r in read_csv(out / "mvv_trips.csv", delimiter=","):
        trip_mode[r["trip_id"]] = route_mode.get(r["route_id"], "Other")

    stop_modes: dict[str, set[str]] = {}
    st = out / "mvv_stop_times.csv"
    if st.exists():
        print(f"  scanning {st.name} for the modes serving each stop ...")
        with st.open(encoding="utf-8-sig", newline="") as fh:
            rdr = csv.reader(fh)
            header = [clean_header(h) for h in next(rdr)]
            i_trip, i_stop = header.index("trip_id"), header.index("stop_id")
            for row in rdr:
                if len(row) > max(i_trip, i_stop):
                    stop_modes.setdefault(row[i_stop], set()).add(trip_mode.get(row[i_trip], "Other"))
    else:
        print(f"  skip stop modes: {st.name} not in {out}")

    stops = list(read_csv(out / "mvv_stops.csv", delimiter=","))
    for r in stops:  # a station (parent) is served by whatever serves its platforms
        parent = r.get("parent_station", "")
        if parent and r["stop_id"] in stop_modes:
            stop_modes.setdefault(parent, set()).update(stop_modes[r["stop_id"]])
    for r in stops:
        modes = stop_modes.get(r["stop_id"], set())
        ordered = [m for m in LINE_MODES if m in modes]
        r["stop_mode"] = ordered[0] if ordered else ""
        r["stop_modes"] = "|".join(ordered)
        for m, col in MODE_FLAGS.items():
            r[col] = "1" if m in modes else "0"
    write_csv(out / "mvv_stops.csv", list(stops[0].keys()), stops)

    write_csv(out / "vehicle_capacity.csv", VEHICLE_CAPACITY_HEADER, VEHICLE_CAPACITY)
    write_csv(out / "line_capacity.csv", LINE_CAPACITY_HEADER, LINE_CAPACITY)


# --------------------------------------------------------------------------- districts (metric units)
# Areas in km², densities in residents per km², lengths in m or km. No hectares anywhere.
DISTRICTS_HEADER = ["district_no", "district_name", "population", "population_pct", "area_km2", "area_pct",
                    "density_per_km2", "area_sqm", "centroid_lat", "centroid_lon", "polygon_wkt"]


def km2(ha: str) -> str:
    v = num(ha)
    return f"{float(v) / 100:.3f}" if v else ""


def per_km2(population: str, ha: str) -> str:
    pop, area = intnum(population), num(ha)
    return str(round(float(pop) / (float(area) / 100))) if pop and area and float(area) else ""


def metric_districts(out: Path) -> None:
    """Rewrite an older districts.csv (area_ha, density_per_ha) to km² in place; a no-op when already metric."""
    rows = list(read_csv(out / "districts.csv", delimiter=","))
    if not rows or "area_ha" not in rows[0]:
        return
    for r in rows:
        r["area_km2"], r["density_per_km2"] = km2(r["area_ha"]), per_km2(r["population"], r["area_ha"])
    write_csv(out / "districts.csv", DISTRICTS_HEADER, [{k: r.get(k, "") for k in DISTRICTS_HEADER} for r in rows])


# Workers at place of work (Erwerbstätige am Arbeitsort) per district -> table DISTRICT_EMPLOYMENT.
# No open per-district dataset exists (official employee counts stop at city level). These are the city's
# modelled estimates, Tabelle 3 p. 22, typed in. No licence stated: internal analysis only.
DISTRICT_EMPLOYMENT_HEADER = ["district_no", "district_name", "jobs_2022", "jobs_2040_forecast", "basis", "source"]
_ERWERB = ("LHM Referat fuer Stadtplanung und Bauordnung, Erwerbstaetigenprognose 2025 (empirica 2024), Tabelle 3 "
           "https://stadt.muenchen.de/dam/jcr:81e9850c-c0e6-4c1a-b412-9f7c35e4abb0/LHM_Erwerbstaetigenprognose_2025_web2.pdf")
_JOBS = [  # district_no, name, 2022 and 2040 in thousands
    (1, "Altstadt-Lehel", 103.7, 119.0), (2, "Ludwigsvorstadt-Isarvorstadt", 83.2, 96.4),
    (3, "Maxvorstadt", 117.1, 130.1), (4, "Schwabing-West", 26.3, 31.6), (5, "Au-Haidhausen", 44.3, 49.8),
    (6, "Sendling", 17.5, 19.9), (7, "Sendling-Westpark", 25.7, 29.1), (8, "Schwanthalerhöhe", 38.7, 44.0),
    (9, "Neuhausen-Nymphenburg", 61.3, 72.8), (10, "Moosach", 49.3, 58.1), (11, "Milbertshofen-Am Hart", 82.8, 89.2),
    (12, "Schwabing-Freimann", 106.4, 140.5), (13, "Bogenhausen", 62.6, 75.0), (14, "Berg am Laim", 31.3, 41.4),
    (15, "Trudering-Riem", 39.4, 46.0), (16, "Ramersdorf-Perlach", 72.9, 83.3),
    (17, "Obergiesing-Fasangarten", 19.7, 22.1), (18, "Untergiesing-Harlaching", 15.8, 18.3),
    (19, "Thalkirchen-Obersendling-Forstenried-Fürstenried-Solln", 55.0, 63.3), (20, "Hadern", 25.0, 28.7),
    (21, "Pasing-Obermenzing", 25.2, 30.1), (22, "Aubing-Lochhausen-Langwied", 26.0, 33.0),
    (23, "Allach-Untermenzing", 30.1, 34.7), (24, "Feldmoching-Hasenbergl", 18.7, 25.9), (25, "Laim", 28.6, 32.3),
]


def district_employment() -> list[dict]:
    basis = ("modelled estimate, all workers at place of work incl. civil servants and self-employed, "
             "base year 2022, rounded to 100; 2040 is a forecast")
    rows = [{"district_no": n, "district_name": name, "jobs_2022": round(j22 * 1000), "jobs_2040_forecast": round(j40 * 1000),
             "basis": basis, "source": _ERWERB} for n, name, j22, j40 in _JOBS]
    # Tabelle 3 city total is 1,206.7 thousand; the rounded district values add up to within a few hundred
    assert abs(sum(r["jobs_2022"] for r in rows) - 1_206_700) <= 500, "district jobs do not add up to Tabelle 3"
    return rows


# Residents (Hauptwohnsitz) per district: counts 2015/2024/2025 and the official forecast 2045 -> DISTRICT_POPULATION.
# Counts: Indikatorenatlas Bevoelkerung (opendata.muenchen.de, 22 May 2026); forecast: Demografiebericht Muenchen
# Teil 2, Kleinraeumige Bevoelkerungsprognose 2025-2045 (PLAN, May 2025), per-district tables "Bezirk gesamt".
DISTRICT_POPULATION_HEADER = ["district_no", "district_name", "pop_2015", "pop_2024", "pop_2025", "pop_2045_forecast",
                              "new_homes_2025_2045", "source"]
_DEMOGRAFIE = ("Counts: Indikatorenatlas Bevoelkerung, opendata.muenchen.de (2026-05-22). Forecast: Demografiebericht "
               "Muenchen Teil 2, Kleinraeumige Bevoelkerungsprognose 2025-2045, Referat fuer Stadtplanung und Bauordnung")
_POP = [  # district_no, name, 2015, 2024, 2025 (counts, 31 Dec), 2045 (forecast), new-homes band 2025-2045
    (1, 'Altstadt-Lehel', 21122, 20876, 20606, 20864, '0-500'),
    (2, 'Ludwigsvorstadt-Isarvorstadt', 54049, 50081, 50048, 49296, '501-2,000'),
    (3, 'Maxvorstadt', 53743, 52434, 52501, 53895, '0-500'),
    (4, 'Schwabing-West', 68527, 68610, 69484, 67091, '501-2,000'),
    (5, 'Au-Haidhausen', 61495, 63972, 64122, 64694, '501-2,000'),
    (6, 'Sendling', 40879, 41002, 41334, 42826, '501-2,000'),
    (7, 'Sendling-Westpark', 58398, 62240, 62640, 64997, '501-2,000'),
    (8, 'Schwanthalerhöhe', 30381, 28684, 29456, 27870, '0-500'),
    (9, 'Neuhausen-Nymphenburg', 98702, 101901, 102527, 104389, '2,001-5,000'),
    (10, 'Moosach', 53261, 56015, 56150, 66975, '2,001-5,000'),
    (11, 'Milbertshofen-Am Hart', 75488, 77281, 77500, 81966, '2,001-5,000'),
    (12, 'Schwabing-Freimann', 75020, 77092, 76809, 94664, '5,001-10,000'),
    (13, 'Bogenhausen', 85947, 95475, 95540, 122034, '5,001-10,000'),
    (14, 'Berg am Laim', 45035, 47367, 47185, 53527, '2,001-5,000'),
    (15, 'Trudering-Riem', 69830, 76280, 77154, 108701, '>10,000'),
    (16, 'Ramersdorf-Perlach', 112371, 120776, 121271, 135912, '5,001-10,000'),
    (17, 'Obergiesing-Fasangarten', 54402, 54352, 54500, 54304, '2,001-5,000'),
    (18, 'Untergiesing-Harlaching', 53377, 54067, 54227, 51245, '501-2,000'),
    (19, 'Thalkirchen-Obersendling-Forstenried-Fürstenried-Solln', 93602, 103717, 104237, 118939, '2,001-5,000'),
    (20, 'Hadern', 50257, 51637, 51809, 49861, '0-500'),
    (21, 'Pasing-Obermenzing', 73320, 81804, 81783, 90118, '2,001-5,000'),
    (22, 'Aubing-Lochhausen-Langwied', 43682, 61011, 63207, 113143, '>10,000'),
    (23, 'Allach-Untermenzing', 31882, 36230, 36238, 45378, '2,001-5,000'),
    (24, 'Feldmoching-Hasenbergl', 61534, 63756, 64586, 86945, '5,001-10,000'),
    (25, 'Laim', 55374, 57116, 57515, 59888, '501-2,000'),
]


def district_population() -> list[dict]:
    rows = [dict(zip(DISTRICT_POPULATION_HEADER, (*r, _DEMOGRAFIE))) for r in _POP]
    assert sum(r["pop_2024"] for r in rows) == 1_603_776, "2024 count must equal the DISTRICTS snapshot"
    return rows


# Planned rail and tram projects -> PT_PROJECT_STATIONS. One row per new station (or existing station gaining a
# line), curated from official sources in data/source/pt_projects.csv (see the source and verified columns).
# district_no comes from the station coordinates against the district polygons, like every other point table.
PT_PROJECTS_SOURCE = Path(__file__).resolve().parent.parent / "data" / "source" / "pt_projects.csv"
ASSUMED_OPENING_YEAR = 2040  # used only when a project has no published opening year; flagged in opening_year_assumed


def pt_project_stations(out: Path) -> None:
    idx = DistrictIndex()
    for d in read_csv(out / "districts.csv", delimiter=","):
        for part in re.findall(r"\(\(([^()]+)\)", d["polygon_wkt"]):
            ring = [(float(lat), float(lon)) for lon, lat in (pt.split() for pt in part.split(","))]
            idx.add(d["district_no"], [ring])
    rows = list(read_csv(PT_PROJECTS_SOURCE, delimiter=","))
    for r in rows:
        has_xy = r["lat"] and r["lon"]
        r["district_no"] = idx.lookup(float(r["lat"]), float(r["lon"])) if has_xy else ""
        r["opening_year_assumed"] = "0" if r["opening_year"] else "1"
        r["opening_year_model"] = r["opening_year"] or str(ASSUMED_OPENING_YEAR)
    header = list(rows[0].keys())
    write_csv(out / "pt_project_stations.csv", header, rows)


# --------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("source", help="munich-open-data.zip or the extracted munich-open-data folder")
    ap.add_argument("--out", default=str(Path.home() / "munich-dataset"), help="flat output folder")
    ap.add_argument("--with-mvg-bikes", nargs="*", metavar="YEAR",
                    help="also build mvg_bike_trips.csv from these years (e.g. 2024 2025); large")
    ap.add_argument("--skip-stop-times", action="store_true", help="leave out the 250 MB GTFS stop_times file")
    ap.add_argument("--enrich-only", action="store_true",
                    help="SOURCE is an already flat folder: only add stop/line modes and the capacity tables")
    args = ap.parse_args()

    src = Path(args.source).expanduser()
    out = Path(args.out).expanduser()
    if args.enrich_only:
        print(f"Enriching {src}")
        enrich_transit(src)
        metric_districts(src)
        write_csv(src / "district_employment.csv", DISTRICT_EMPLOYMENT_HEADER, district_employment())
        write_csv(src / "district_population.csv", DISTRICT_POPULATION_HEADER, district_population())
        pt_project_stations(src)
        return 0
    tmp = None
    if src.is_file() and src.suffix == ".zip":
        tmp = Path(tempfile.mkdtemp(prefix="munich-"))
        print(f"Extracting {src.name} ...")
        with zipfile.ZipFile(src) as z:
            for m in z.namelist():
                if m.startswith("__MACOSX") or m.endswith(".DS_Store"):
                    continue
                z.extract(m, tmp)
        root = tmp / "munich-open-data"
    else:
        root = src
    if not (root / "datasets").is_dir():
        print(f"error: {root} has no datasets/ folder", file=sys.stderr)
        return 1

    out.mkdir(parents=True, exist_ok=True)
    print(f"Writing flat dataset to {out}")

    # --- 5 + 4. districts --------------------------------------------------------
    idx = DistrictIndex()
    d_bounds = find_dir(root, "5.")
    d_pop = find_dir(root, "4.")
    pop = {}
    for r in read_csv(next(d_pop.glob("*.csv"))):
        no = str(int(r["stadtbezirksnummer"]))
        pop[no] = r
    # A district split into several polygon parts (18, 19) is several rows in the
    # source; merge them into ONE row per district so joins never double count.
    parts: dict[str, dict] = {}
    for r in read_csv(next(p for p in d_bounds.glob("*.csv"))):
        no = str(int(r["sb_nummer"]))
        rings = rings_to_wgs84(outer_rings(r["shape"]))
        idx.add(no, rings)
        entry = parts.setdefault(no, {"name": r["sb_name"], "rings": [], "area_sqm": 0.0})
        entry["rings"].extend(rings)
        try:  # every part row carries the WHOLE district's area (18, 19 doubled when summed), so take it once
            entry["area_sqm"] = max(entry["area_sqm"], float(num(r.get("flaeche_qm", "0")) or 0))
        except ValueError:
            pass
    districts = []
    for no, entry in parts.items():
        clat, clon = centroid(entry["rings"])
        p = pop.get(no, {})
        districts.append({
            "district_no": no, "district_name": entry["name"],
            "population": intnum(p.get("bevoelkerung", "")), "population_pct": num(p.get("bevoelkerung_in_prozent", "")),
            "area_km2": km2(p.get("flaeche_in_ha", "")), "area_pct": num(p.get("flaeche_in_prozent", "")),
            "density_per_km2": per_km2(p.get("bevoelkerung", ""), p.get("flaeche_in_ha", "")),
            "area_sqm": round(entry["area_sqm"], 2),
            "centroid_lat": clat, "centroid_lon": clon, "polygon_wkt": polygon_wkt_wgs84(entry["rings"]),
        })
    districts.sort(key=lambda d: int(d["district_no"]))
    write_csv(out / "districts.csv",
              DISTRICTS_HEADER, districts)
    write_csv(out / "district_employment.csv", DISTRICT_EMPLOYMENT_HEADER, district_employment())
    write_csv(out / "district_population.csv", DISTRICT_POPULATION_HEADER, district_population())
    pt_project_stations(out)

    # --- 1. bike counts -------------------------------------------------------------
    d_bike = find_dir(root, "1.")
    daily, q15 = [], []
    for f in sorted(d_bike.glob("*_tage.csv")):
        for r in read_csv(f):
            daily.append({
                "count_date": norm_date(r["datum"]), "station": r["zaehlstelle"],
                "dir_1": r["richtung_1"], "dir_2": r["richtung_2"], "total": r["gesamt"],
                "temp_min_c": num(r.get("min_temp", "")), "temp_max_c": num(r.get("max_temp", "")),
                "rain_mm": num(r.get("niederschlag", "")), "cloud_cover_pct": num(r.get("bewoelkung", "")),
                "sunshine_hours": num(r.get("sonnenstunden", "")),
            })
    for f in sorted(d_bike.glob("*_15min.csv")):
        for r in read_csv(f):
            q15.append({
                "count_date": norm_date(r["datum"]), "time_start": r["uhrzeit_start"], "time_end": r["uhrzeit_ende"],
                "station": r["zaehlstelle"], "dir_1": r["richtung_1"], "dir_2": r["richtung_2"], "total": r["gesamt"],
            })
    write_csv(out / "bike_counts_daily.csv",
              ["count_date", "station", "dir_1", "dir_2", "total", "temp_min_c", "temp_max_c", "rain_mm",
               "cloud_cover_pct", "sunshine_hours"], daily)
    write_csv(out / "bike_counts_15min.csv",
              ["count_date", "time_start", "time_end", "station", "dir_1", "dir_2", "total"], q15)
    write_csv(out / "bike_count_stations.csv",
              ["station", "station_name", "lat", "lon", "direction_1", "direction_2", "district_no"],
              [{"station": s[0], "station_name": s[1], "lat": s[2], "lon": s[3], "direction_1": s[4],
                "direction_2": s[5], "district_no": idx.lookup(s[2], s[3])} for s in STATIONS])

    # --- 3. roadworks -----------------------------------------------------------------
    d_road = find_dir(root, "3.")
    roads = []
    for r in read_csv(next(d_road.glob("*.csv"))):
        rings = rings_to_wgs84(outer_rings(r.get("shape", "")))
        clat, clon = centroid(rings)
        roads.append({
            "roadwork_id": r.get("fid", ""), "street": r.get("strasse_hausnr", ""),
            "affected_areas": r.get("betroffene_bereiche", ""), "description": r.get("beschreibung", ""),
            "impact": r.get("beeintraechtigung", ""), "kind": r.get("art", ""),
            "more_info": r.get("weitere_info", ""), "contact": r.get("kontakt_oeffentlich", ""),
            "start_date": norm_date(r.get("beginn_datum_kombiniert", ""), strict=True),
            "end_date": norm_date(r.get("ende_datum_kombiniert", ""), strict=True),
            "start_raw": r.get("beginn_datum_kombiniert", ""), "end_raw": r.get("ende_datum_kombiniert", ""),
            "source_id": r.get("fachliche_id", ""), "centroid_lat": clat, "centroid_lon": clon,
            "district_no": idx.lookup(clat, clon) if clat != "" else "",
            "shape_wkt": polygon_wkt_wgs84(rings) if rings else "",
        })
    write_csv(out / "roadworks.csv",
              ["roadwork_id", "street", "affected_areas", "description", "impact", "kind", "more_info", "contact",
               "start_date", "end_date", "start_raw", "end_raw", "source_id", "centroid_lat", "centroid_lon",
               "district_no", "shape_wkt"], roads)

    # --- 6. cycling infrastructure ------------------------------------------------
    d_cyc = find_dir(root, "6.")
    cyc = []
    for r in read_csv(next(d_cyc.glob("*.csv"))):
        try:
            slat, slon = utm_to_latlon(float(r["start_x"]), float(r["start_y"]))
            elat, elon = utm_to_latlon(float(r["end_x"]), float(r["end_y"]))
        except (ValueError, KeyError):
            continue
        mlat, mlon = round((slat + elat) / 2, 6), round((slon + elon) / 2, 6)
        cyc.append({
            "segment_id": r.get("fid", ""), "street": r.get("strassenna", ""),
            "length_m": num(r.get("shape_leng", "")), "path_type": r.get("d_radwegar", ""),
            "start_lat": slat, "start_lon": slon, "end_lat": elat, "end_lon": elon,
            "mid_lat": mlat, "mid_lon": mlon, "district_no": idx.lookup(mlat, mlon),
        })
    write_csv(out / "cycling_infrastructure.csv",
              ["segment_id", "street", "length_m", "path_type", "start_lat", "start_lon", "end_lat", "end_lon",
               "mid_lat", "mid_lon", "district_no"], cyc)

    # --- 2. MVV GTFS ------------------------------------------------------------------
    d_mvv = find_dir(root, "2.")
    simple = {"agency": "mvv_agency", "trips": "mvv_trips", "calendar": "mvv_calendar",
              "calendar_dates": "mvv_calendar_dates"}
    for name, target in simple.items():
        rows = list(read_csv(d_mvv / f"{name}.csv", delimiter=","))
        if name == "calendar":
            for r in rows:
                r["start_date"] = norm_date(re.sub(r"^(\d{4})(\d{2})(\d{2})$", r"\1-\2-\3", r["start_date"]))
                r["end_date"] = norm_date(re.sub(r"^(\d{4})(\d{2})(\d{2})$", r"\1-\2-\3", r["end_date"]))
        if name == "calendar_dates":
            for r in rows:
                r["date"] = re.sub(r"^(\d{4})(\d{2})(\d{2})$", r"\1-\2-\3", r["date"])
        header = list(rows[0].keys()) if rows else []
        write_csv(out / f"{target}.csv", header, rows)

    routes = list(read_csv(d_mvv / "routes.csv", delimiter=","))
    for r in routes:
        r["route_mode"] = ROUTE_MODES.get(r.get("route_type", ""), "Other")
    write_csv(out / "mvv_routes.csv", list(routes[0].keys()), routes)

    stops = []
    for r in read_csv(d_mvv / "stops.csv", delimiter=","):
        try:
            lat, lon = float(r["stop_lat"]), float(r["stop_lon"])
        except ValueError:
            lat, lon = "", ""
        r["district_no"] = idx.lookup(lat, lon) if lat != "" else ""
        r["in_munich"] = "1" if r["district_no"] else "0"
        stops.append(r)
    write_csv(out / "mvv_stops.csv", list(stops[0].keys()), stops)

    # every other GTFS file, unchanged, so nothing in the feed is left behind
    for name in ("feed_info", "ticketing_deep_links", "ticketing_identifiers", "shapes"):
        f = d_mvv / f"{name}.csv"
        if not f.exists():
            print(f"  skip: {f.name} not in the archive")
            continue
        rows = list(read_csv(f, delimiter=","))
        if not rows:
            print(f"  skip: {f.name} has a header but no rows (exapump cannot load an empty file)")
            continue
        write_csv(out / f"mvv_{name}.csv", list(rows[0].keys()), rows)

    if not args.skip_stop_times:
        src_st = d_mvv / "stop_times.csv"
        print(f"  copying {src_st.name} ({src_st.stat().st_size / 1e6:.0f} MB) -> mvv_stop_times.csv (LF endings)")
        with src_st.open("rb") as fin, (out / "mvv_stop_times.csv").open("wb") as fout:
            for chunk in iter(lambda: fin.read(1 << 20), b""):
                fout.write(chunk.replace(b"\r\n", b"\n"))

    enrich_transit(out)

    # --- 7. optional MVG bike trips ------------------------------------------------
    if args.with_mvg_bikes:
        d_mvg = find_dir(root, "7.")
        header = ["trip_no", "start_time", "end_time", "start_lat", "start_lon", "end_lat", "end_lon",
                  "rental_is_station", "rental_station_name", "return_is_station", "return_station_name", "year"]
        rows = []
        for year in args.with_mvg_bikes:
            f = d_mvg / f"MVG_Rad_Fahrten_{year}.csv"
            if not f.exists():
                print(f"  skip: {f.name} not in the archive")
                continue
            for r in read_csv(f, delimiter=";"):
                rows.append({
                    "trip_no": r.get("row", ""), "start_time": norm_datetime(r.get("starttime", "")),
                    "end_time": norm_datetime(r.get("endtime", "")),
                    "start_lat": num(r.get("startlat", "")), "start_lon": num(r.get("startlon", "")),
                    "end_lat": num(r.get("endlat", "")), "end_lon": num(r.get("endlon", "")),
                    "rental_is_station": r.get("rental_is_station", ""),
                    "rental_station_name": r.get("rental_station_name", ""),
                    "return_is_station": r.get("return_is_station", ""),
                    "return_station_name": r.get("return_station_name", ""), "year": year,
                })
        write_csv(out / "mvg_bike_trips.csv", header, rows)

    if tmp:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\nDone. Load it with:\n"
          f"  EXAKIT_SCHEMA=MUNICH_DATASET exakit data-load {out}\n"
          "(answer the schema prompt with MUNICH_DATASET; set EXAKIT_ON_EXISTING=replace to re-run without questions)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
