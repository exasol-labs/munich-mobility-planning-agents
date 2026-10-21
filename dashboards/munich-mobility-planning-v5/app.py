"""Munich Mobility Planning v5 – Ask the assistant. The service map and the change since 2024 (as in v4), managed entirely
through an Ask chat (OpenAI, assistant.py). One view-store (year, w, projects, pessimistic, what-if) drives both views.
Scheduled public transport supply per 1,000 residents + w x jobs per district, 2024-2045. Metric units (km2)."""
import json
import math
import re
import threading
import time
from pathlib import Path
from types import SimpleNamespace

from dash import Dash, Input, Output, State, ctx, dcc, html, no_update
import plotly.graph_objects as go

from dash_server_exasol import load_rows
import munich_ui as ui
import assistant

ACCENT = ui.PERSONA["planning"]
CACHE_TTL_S = 3600
RATIO_LO, RATIO_HI = 0.4, 2.5
Z_HALF = math.log2(RATIO_HI)  # log2(0.4) is about -log2(2.5), so the scale is symmetric around 1.0
RATIO_SCALE = [[0.0, ui.RAMP_ORANGE[5]], [0.22, ui.RAMP_ORANGE[3]], [0.42, ui.RAMP_ORANGE[1]], [0.5, "#dedcd6"],
               [0.58, ui.RAMP_BLUE[1]], [0.78, ui.RAMP_BLUE[3]], [1.0, ui.RAMP_BLUE[5]]]
RATIO_TICKS = (0.5, 0.75, 1, 1.5, 2)
DENSE_LABEL = "dense (top third by activity/km²)"
COORD = re.compile(r"(-?\d+(?:\.\d+)?(?:[eE]-?\d+)?)\s+(-?\d+(?:\.\d+)?(?:[eE]-?\d+)?)")
YEARS = (2024, 2045)
STATUS_GROUPS = [("Under construction", ("under_construction", "in_operation")), ("Approved", ("approved",)),
                 ("Planning", ("planning",)), ("On hold or blocked", ("on_hold", "blocked"))]
PRESETS = [("none", "None (today's timetable)"), ("funded", "Funded only"), ("funded_planned", "Funded + planned"),
           ("everything", "Everything discussed")]
SHORT = {"stammstrecke2": "2. Stammstrecke", "laim_inbound_restore": "Laim inbound restored",
         "tram_muenchner_norden_1": "Tram Münchner Norden PFA 1", "tram_muenchner_norden_2": "Tram Münchner Norden PFA 2",
         "u5_pasing": "U5 Laimer Platz–Pasing", "u5_freiham": "U5 Pasing–Freiham", "tram_westtangente_2": "Tram-Westtangente (14)",
         "u9_spange": "U9-Spange", "u4_ost": "U4 Ost", "u26_spange": "U26 Am Hart–Kieferngarten", "tram_nordtangente": "Tram-Nordtangente",
         "tram_y_nord": "Tram Lerchenauer Feld", "tram_johanneskirchen": "Tram Johanneskirchen",
         "sbahn_nordring_shuttle": "S-Bahn Nordring shuttle", "sbahn_berduxstrasse": "S-Bahn halt Berduxstraße",
         "sbahn_augsburg_express": "Augsburg express (part of the 2nd trunk)", "regional_halt_poccistrasse": "Regional halt Poccistraße"}
CAVEAT = ("Scheduled service only (capacity offered, not passengers or delays); residents between 2024 and 2045 interpolated to the 2045 forecast; "
          "jobs a modelled estimate (2022 as the 2024 baseline, to 2040, held after); projects per Scenarios, their dates and frequencies are assumptions. "
          "2nd Stammstrecke: new-tunnel trains plus a 15-minute basic service on all S-Bahn lines except S2, S5, S7 and S20 "
          "(2017 concept, unverified line table; S5 is a later reinforcement line not in that concept); "
          "old-trunk slots assumed reused.")


def wkt_to_geometry(wkt):
    """WGS84 POLYGON / MULTIPOLYGON WKT (lon lat) to a GeoJSON geometry, no extra dependency."""
    text = (wkt or "").strip()
    kind = "MultiPolygon" if text.upper().startswith("MULTIPOLYGON") else "Polygon"
    body = COORD.sub(r"[\1,\2]", text[text.index("("):]).replace("(", "[").replace(")", "]")
    return {"type": kind, "coordinates": json.loads(body)}


def short_name(name):
    name = str(name or "")
    return name if len(name) <= 22 else name.split("-")[0] + "-…"


def pshort(pid):
    return SHORT.get(pid, pid)


def opening_text(p, pessimistic=False):
    if int(ui.num(p.get("opening_year_assumed"))) == 1:
        return "no date published, assumed 2040"
    oy = int(ui.num(p.get("opening_year_model")))
    risk = p.get("opening_year_risk")
    if risk not in (None, "", "-"):
        return f"opens {oy} (risk {int(ui.num(risk))}{', used' if pessimistic else ''})"
    return f"opens {oy}"


def project_note(p):
    pid = p["project_id"]
    if pid == "stammstrecke2":
        return "new-tunnel trains + 15-min basic interval (all S-Bahn lines except S2/S5/S7/S20); line table unverified (2017 concept)"
    if pid == "sbahn_augsburg_express":
        return "already in the 2nd trunk as S23X, not counted twice"
    if int(ui.num(p.get("unknown_rows"))) >= int(ui.num(p.get("n_rows"))):
        return "no stations published, adds nothing"
    if ui.num(p.get("net_places")) == 0:
        return "no frequency or analog, adds nothing"
    return ""


def badge(text, bg, fg):
    return html.Span(text, style={"fontSize": "10px", "fontWeight": 600, "padding": "1px 6px", "borderRadius": "8px", "background": bg,
                                  "color": fg, "marginLeft": "6px", "whiteSpace": "nowrap"})


def project_label(p):
    funded = int(ui.num(p.get("funded"))) == 1
    verified = ui.num(p.get("verified_share")) >= 0.999
    note = project_note(p)
    return html.Span([
        html.Span(pshort(p["project_id"]), style={"fontWeight": 600}),
        html.Span(f" · {opening_text(p)}", style={"color": ui.INK2}),
        badge("funded" if funded else "not funded", "#e3f3ea" if funded else "#eeede9", "#0f6f49" if funded else ui.INK2),
        badge("verified" if verified else "partly unverified", "#e7f0fb" if verified else "#fdf0e9", "#184f95" if verified else "#9f3d1f"),
        html.Span(f" · {note}" if note else "", style={"color": ui.MUTED, "fontSize": "11px"}),
    ], style={"fontSize": "12px"})


def preset_ids(projects, preset):
    if preset == "funded":
        return [p["project_id"] for p in projects if int(ui.num(p.get("funded"))) == 1]
    if preset == "funded_planned":
        return [p["project_id"] for p in projects
                if int(ui.num(p.get("funded"))) == 1 or p.get("status") in ("under_construction", "in_operation", "approved", "planning")]
    if preset == "everything":
        return [p["project_id"] for p in projects]
    return []


def scen_name(projs, selected):
    chosen = set(selected)
    if not chosen:
        return "None (today's timetable)"
    for value, title in PRESETS:
        if value != "none" and chosen == set(preset_ids(projs, value)):
            return title
    return f"Custom ({len(chosen)} selected)"


def pct(a, b):
    return (b / a - 1) * 100 if a else 0.0


def w_text(w):
    return f"{w:.1f}" if abs(w * 10 - round(w * 10)) < 1e-9 else f"{w:.2f}"


def status_line(scen, w, n_active, year, added):
    added_txt = f"{added / 1e6:+.1f} M" if abs(added) >= 1e5 else f"{added:+,.0f}"
    return f"Scenario: {scen} · w = {w_text(w)} · {n_active} project(s) active in {year} · {added_txt} places/day net"


def service_map(rows, geo, year, stations):
    """Choropleth of service_ratio (year Y against the fixed 2024 city average) on a log scale centred on 1.0,
    plus the active projects' stations (circle = new station, ring = existing station gaining a line)."""
    gj = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "id": str(int(ui.num(g["district_no"]))), "properties": {"name": g["district"]},
         "geometry": wkt_to_geometry(g["polygon_wkt"])} for g in geo]}
    cent = {str(int(ui.num(g["district_no"]))): g for g in geo}
    ids = [str(int(ui.num(r["district_no"]))) for r in rows]
    ratio = [ui.num(r.get("service_ratio"), 1.0) for r in rows]
    z = [math.log2(min(max(v, RATIO_LO), RATIO_HI)) for v in ratio]

    def proj_line(r):
        act = [p for p in str(r.get("active_projects") or "").split(",") if p]
        if not act:
            return "projects: none active here"
        return f"projects: {', '.join(pshort(p) for p in act)} ({ui.num(r.get('add_places')):+,.0f} places/weekday)"

    hover = [(f"<b>{r['district']}</b> ({year})<br>{v:.2f}× the 2024 city average"
              f" · {ui.num(r.get('ratio_own_year')):.2f}× the {year} city average<br>"
              f"2024: {ui.num(r.get('ratio_2024')):.2f}× · change {ui.num(r.get('ratio_change_pp')):+.1f} pp"
              f" ({ui.num(r.get('pct_change_places')):+.1f} % places per 1,000 activity)<br>"
              f"{proj_line(r)}<br>"
              f"{ui.fmt(r['population'])} residents, {ui.fmt(r['jobs'])} jobs<br>"
              f"{ui.fmt(r['activity_per_km2'])} activity per km²<br>"
              f"{ui.fmt(r['places_per_1k_act'])} places, {ui.fmt(r['dep_per_1k_act'], 1)} departures per 1,000 activity<br>"
              f"{ui.fmt(r['residents_per_station'])} residents per station<br>"
              f"mode: {r.get('mode_note') or 'mixed'} · flag: {'yes' if int(ui.num(r.get('flagged'))) else 'no'}")
             for r, v in zip(rows, ratio)]
    fig = go.Figure()
    fig.add_trace(go.Choroplethmap(
        geojson=gj, locations=ids, z=z, featureidkey="id", colorscale=RATIO_SCALE, zmin=-Z_HALF, zmax=Z_HALF, zmid=0,
        marker={"opacity": 0.85, "line": {"color": ui.SURFACE, "width": 1}}, hovertext=hover, hoverinfo="text",
        name="places vs 2024 city average", showlegend=False,
        colorbar={"title": {"text": "× city average (2024)", "font": {"size": 12}}, "thickness": 12, "len": 0.7,
                  "tickvals": [math.log2(t) for t in RATIO_TICKS], "ticktext": [f"{t:g}" for t in RATIO_TICKS]}))
    dense = [i for i, r in zip(ids, rows) if int(ui.num(r.get("is_dense"))) == 1]
    fig.add_trace(go.Choroplethmap(
        geojson=gj, locations=dense, z=[0] * len(dense), featureidkey="id", showscale=False,
        colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]], marker={"line": {"color": ui.INK, "width": 3}},
        hoverinfo="skip", name=DENSE_LABEL, showlegend=True))
    fig.add_trace(go.Scattermap(
        lat=[ui.num(cent[i]["centroid_lat"]) for i in ids], lon=[ui.num(cent[i]["centroid_lon"]) for i in ids], mode="text",
        text=[f"{short_name(r['district'])} {v:.2f}×" for r, v in zip(rows, ratio)],
        textfont={"size": 10, "color": ui.INK}, hoverinfo="skip", showlegend=False))
    new = [s for s in stations if int(ui.num(s.get("station_is_new"))) == 1]
    old = [s for s in stations if int(ui.num(s.get("station_is_new"))) != 1]
    shover = lambda s: f"<b>{s['station_name']}</b><br>{pshort(s['project_id'])} · {s.get('line') or ''}<br>{s.get('calc_method') or ''}"
    if new:
        fig.add_trace(go.Scattermap(lat=[ui.num(s["lat"]) for s in new], lon=[ui.num(s["lon"]) for s in new], mode="markers",
                                    marker={"size": 8, "color": ui.INK}, name="project: new station", showlegend=True,
                                    text=[shover(s) for s in new], hoverinfo="text"))
    if old:
        fig.add_trace(go.Scattermap(lat=[ui.num(s["lat"]) for s in old], lon=[ui.num(s["lon"]) for s in old], mode="markers",
                                    marker={"size": 12, "color": ui.INK}, name="project: existing station gaining a line", showlegend=True,
                                    text=[shover(s) for s in old], hoverinfo="text"))
        fig.add_trace(go.Scattermap(lat=[ui.num(s["lat"]) for s in old], lon=[ui.num(s["lon"]) for s in old], mode="markers",
                                    marker={"size": 6, "color": ui.SURFACE}, hoverinfo="skip", showlegend=False))
    return ui.map_layout(fig, {"lat": 48.152, "lon": 11.548}, 9.85)


CITY_LABEL = "<b>Munich overall</b>"


def change_bars(rows, year, city_pct):
    """% change in places per 1,000 activity between 2024 and the selected year: the city-wide bar on top,
    a spacer row and a separator line, then the 25 districts."""
    rs = sorted(rows, key=lambda r: ui.num(r.get("pct_change_places")), reverse=True)
    vals = [ui.num(r.get("pct_change_places")) for r in rs]
    cats = [short_name(r["district"]) for r in rs] + ["  ", CITY_LABEL]
    fig = go.Figure(go.Bar(
        x=vals, y=[short_name(r["district"]) for r in rs], orientation="h",
        marker={"color": [ui.RAMP_ORANGE[4] if v < -0.05 else (ui.RAMP_BLUE[3] if v > 0.05 else "#bdbbb5") for v in vals]},
        hovertext=[f"<b>{r['district']}</b><br>{ui.num(r.get('pct_change_places')):+.1f} % places per 1,000 activity, 2024 to {year}<br>"
                   f"ratio {ui.num(r.get('ratio_2024')):.2f}× → {ui.num(r.get('service_ratio')):.2f}× "
                   f"({ui.num(r.get('ratio_change_pp')):+.1f} pp)" for r in rs], hoverinfo="text"))
    fig.add_bar(x=[city_pct], y=[CITY_LABEL], orientation="h", marker={"color": ui.INK2, "line": {"color": ui.INK, "width": 1}},
                text=[f"{city_pct:+.1f} %"], textposition="outside", textfont={"size": 11, "color": ui.INK},
                hovertext=[f"<b>Munich overall</b><br>{city_pct:+.1f} % places per 1,000 activity, 2024 to {year} (city-wide)"],
                hoverinfo="text")
    fig.add_shape(type="line", xref="paper", x0=0, x1=1, yref="y", y0=len(rs), y1=len(rs), line={"color": ui.LINE, "width": 1.5})
    lo = min(vals + [city_pct, -1.0])
    hi = max(vals + [city_pct, 1.0])
    return ui.theme(fig, showlegend=False, barmode="overlay",
                    xaxis={"title": f"% change in places per 1,000 activity, 2024 to {year}", "range": [lo * 1.15, max(hi * 1.15, 4)],
                           "zeroline": True, "zerolinecolor": ui.INK2},
                    yaxis={"automargin": True, "tickfont": {"size": 10}, "categoryorder": "array", "categoryarray": cats}, bargap=0.25)




EXAMPLES = ["Show 2045 with the funded projects", "What if the S-Bahn ran every 10 minutes?",
            "Which district is worst served today, counting jobs?"]
BADGE_COLORS = {"Data": ("#e7f0fb", "#184f95"), "Plans": ("#e3f3ea", "#0f6f49"), "Web": ("#efeafb", "#4a3aa7"),
                "Assumption": ("#fdf0e9", "#9f3d1f")}
DEFAULT_VIEW = dict(assistant.DEFAULT_VIEW, ver=0)  # keys only; the page uses default_view_store() (current year)


def default_view_store():
    return dict(assistant.default_view(), ver=0)


def year_label(year):
    """'2026 (now)' for the current year, plain otherwise."""
    return f"{year} (now)" if year == assistant.current_year() else str(year)


def norm_view(v):
    """view-store -> validated (year, w, projects, pessimistic, what_if, extra). Anything odd falls back to the default."""
    v = v or {}
    try:
        year = min(max(int(v.get("year", assistant.current_year())), YEARS[0]), YEARS[1])
    except (TypeError, ValueError):
        year = assistant.current_year()
    try:
        w = float(v.get("w", 1.0))
        w = round(w * 4) / 4 if 0 <= w <= 1.5 else 1.0
    except (TypeError, ValueError):
        w = 1.0
    projects = sorted({str(p) for p in (v.get("projects") or [])})
    extra = str(v.get("extra") or "")
    if extra and not re.fullmatch(r"(\d{1,2}:\d+)(;\d{1,2}:\d+)*", extra):
        extra = ""
    return year, w, projects, 1 if v.get("pessimistic") else 0, (v.get("what_if") or None) if extra else None, extra


# ---- "SQL executed" foldout: what ran, rendered exactly as sent
QUERY_DIR = Path(__file__).resolve().parent / "queries"
PURPOSE = {"ranking": "district ranking for the map and change chart", "geo": "district boundaries for the map",
           "projects": "project list and station markers", "stops": "Munich stop names for what-if stations",
           "capacity": "capacity per trip by mode", "whatif_line_stations": "today's departures per line and station for a frequency what-if"}
try:  # pyexasol's own formatter: the server's connection renders the placeholders with exactly this class
    from pyexasol.formatter import ExaFormatter
    _FMT = ExaFormatter(SimpleNamespace(options={"quote_ident": False}))
except Exception:  # pragma: no cover
    _FMT = None


def render_sql(name, params):
    """The statement as sent: the server calls connection.execute(sql_text, params or {}), which formats with ExaFormatter."""
    text = (QUERY_DIR / f"{name}.sql").read_text()
    if _FMT is None:
        return text + "\n-- placeholders are formatted by the database driver"
    try:
        return _FMT.format(text, **(params or {}))
    except Exception:
        return text


def fmt_params(params):
    def one(v):
        if isinstance(v, str):
            v = v if len(v) <= 60 else v[:57] + "…"
            return "'" + v.replace("'", "''") + "'"
        return f"{v}"
    return ", ".join(f"{k} = {one(v)}" for k, v in (params or {}).items())


class Backend:
    """What assistant.py may use from the dashboard: its own SQL files (through the app's Exasol profile) and v4's
    preset logic. Static lookups are cached for an hour."""

    def __init__(self, server, metadata):
        self.server, self.metadata = server, metadata
        self.cache = {}
        self._tl = threading.local()   # per-thread sink: the refresh callback's list, or the assistant job's session log

    def set_sink(self, fn):
        self._tl.sink = fn

    def _record(self, entry):
        fn = getattr(self._tl, "sink", None)
        if fn:
            fn(entry)

    def query(self, name, params=None):
        t0 = time.time()
        res = load_rows(self.server, self.metadata, __file__, f"queries/{name}.sql", params=params)
        secs = round(time.time() - t0, 3)
        failed = bool(res and isinstance(res, list) and isinstance(res[0], dict) and res[0].get("_error"))
        self._record({"file": f"{name}.sql", "purpose": PURPOSE.get(name, ""), "params": fmt_params(params), "sql": render_sql(name, params),
                      "rows": None if failed else len(res or []), "secs": secs, "cached": False, "ran_at": time.strftime("%H:%M:%S"),
                      "error": "query failed" if failed else ""})
        if failed:
            lines = [l.strip() for l in str(res[0]["_error"]).splitlines() if l.strip() and l.strip() != "("]
            msg = next((l.split("=>", 1)[1].strip() for l in lines if l.startswith("message")), lines[0] if lines else "")
            return None, (msg or "Exasol query failed")[:300]   # never empty: an empty error would read as success
        return ui.lower(res or []), None

    def cached(self, name):
        hit = self.cache.get(name)
        if hit and time.time() - hit[0] < CACHE_TTL_S:
            self._record({"file": f"{name}.sql", "purpose": PURPOSE.get(name, ""), "params": "", "sql": render_sql(name, {}),
                          "rows": len(hit[1]), "secs": 0.0, "cached": True, "ran_at": time.strftime("%H:%M:%S", time.localtime(hit[0])),
                          "error": ""})
            return hit[1], None
        rows, err = self.query(name)
        if not err:
            self.cache[name] = (time.time(), rows)
        return rows, err

    def execute_sql(self, sql_text):
        """Ad-hoc SQL for the assistant's run_sql, through the same server-side profile and service that load_rows
        uses (dash_server.exasol.runtime.execute_profile_query), so no credentials or connections live in this app."""
        service = self.server.extensions.get("exasol_dashboard_service")
        if service is None:
            return {"status": "error", "error": "Exasol dashboard service is not registered"}
        profile = ((self.metadata.get("data_sources") or {}).get("primary") or {}).get("profile")
        return service.execute_profile_query(profile, sql_text, params={})

    def ranking(self, params):
        return self.query("ranking", params)

    def projects(self):
        rows, err = self.cached("projects")
        if err:
            raise RuntimeError(err)
        return [r for r in rows if r.get("kind") == "project"]

    def project_ids(self):
        return {p["project_id"] for p in self.projects()}

    def preset_ids(self, preset):
        return preset_ids(self.projects(), preset)

    def scen_name(self, selected):
        try:
            return scen_name(self.projects(), selected)
        except RuntimeError:
            return f"{len(selected)} projects" if selected else "None (today's timetable)"

    def capacity(self, mode):
        rows, err = self.cached("capacity")
        if err:
            raise RuntimeError(err)
        return float(next(ui.num(r["capacity_per_trip"]) for r in rows if r["line_mode"] == mode))

    def stops(self):
        hit = self.cache.get("_stops")
        if hit:
            self.cached("stops")   # records the (cached) statement the what-if depends on
            return hit
        rows, err = self.cached("stops")
        if err:
            raise RuntimeError(err)
        out = [{"name": r["name"], "norm": assistant._norm(r["name"]), "district_no": int(ui.num(r["district_no"])),
                "lat": ui.num(r["lat"]), "lon": ui.num(r["lon"])} for r in rows]
        self.cache["_stops"] = out
        return out

    def geo(self):
        hit = self.cache.get("_geo")
        if hit:
            self.cached("geo")
            return hit
        rows, err = self.cached("geo")
        if err:
            raise RuntimeError(err)
        out = [{"district_no": int(ui.num(g["district_no"])), "district": g["district"], "geometry": wkt_to_geometry(g["polygon_wkt"])}
               for g in rows]
        self.cache["_geo"] = out
        return out

    def district_names(self):
        return {g["district_no"]: g["district"] for g in self.geo()}


def badge_row(names):
    return html.Div([html.Span(n, style={"fontSize": "10px", "fontWeight": 600, "padding": "1px 7px", "borderRadius": "8px",
                                         "background": BADGE_COLORS[n][0], "color": BADGE_COLORS[n][1], "marginRight": "6px"})
                     for n in names if n in BADGE_COLORS], style={"marginTop": "6px"})


def how_i_got_this(turn):
    items = []
    for t in turn.get("trace") or []:
        k = t.get("kind")
        if k == "sql":
            head = f"SQL: {t.get('purpose') or 'query'} · " + (f"error: {t['error']}" if t.get("error") else f"{t.get('rows')} row(s)")
            items.append(html.Li([html.Div(head), html.Pre(t.get("sql") or "", style=PRE)]))
        elif k == "model":
            a = t.get("args") or {}
            items.append(html.Li(f"Dashboard model (ranking.sql): year {a.get('year')}, w {a.get('w')}, "
                                 f"{a.get('preset') or (', '.join(a.get('projects') or []) or 'no projects')}"
                                 f"{', pessimistic dates' if a.get('pessimistic') else ''}{', what-if ' + a['extra'] if a.get('extra') else ''}"
                                 f" → {t.get('summary')}"))
        elif k == "whatif":
            if t.get("error"):
                items.append(html.Li(f"What-if '{t.get('name')}': error: {t['error']}"))
            else:
                pbd = t.get("places_by_district") or {}
                items.append(html.Li([html.Div(f"What-if (assumption) '{t.get('name')}':"),
                                      html.Ul([html.Li(a) for a in (t.get("assumptions") or [])]),
                                      html.Div("Places added per weekday: " + ", ".join(f"{d} {p:+,}" for d, p in pbd.items()),
                                               style={"color": ui.MUTED})]))
        elif k == "view":
            items.append(html.Li(f"View change: {t.get('text')}"))
        elif k == "web":
            items.append(html.Li(f"Web search: {t.get('query') or '(search)'}"))
    for src in turn.get("sources") or []:
        items.append(html.Li(["Web source: ", html.A(src.get("title") or src["url"], href=src["url"], target="_blank", rel="noopener")]))
    u = turn.get("usage") or {}
    foot = ""
    if u:
        foot = (f"Answers by OpenAI {u.get('model')} (reasoning {u.get('effort')}) · {u.get('requests')} request(s) · "
                f"input {u.get('input', 0):,} tokens ({u.get('cached', 0):,} cached) · output {u.get('output', 0):,} · "
                f"about US${u.get('cost_usd', 0):.2f} · {turn.get('elapsed')} s")
    return html.Details([html.Summary("How I got this", style={"cursor": "pointer", "fontSize": "12px", "color": ui.INK2}),
                         html.Ul(items or [html.Li("No tools ran." if turn.get("error") else "No tools used: answered from the context pack.")],
                                 style={"fontSize": "12px", "color": ui.INK2, "paddingLeft": "18px", "margin": "6px 0"}),
                         html.Div(foot, style={"fontSize": "11px", "color": ui.MUTED})], style={"marginTop": "6px"})


PRE = {"whiteSpace": "pre-wrap", "fontSize": "11px", "background": "#f4f3ef", "padding": "6px 8px", "borderRadius": "6px",
       "margin": "4px 0", "maxHeight": "220px", "overflowY": "auto"}


def render_turns(turns, status):
    out = []
    for i, t in enumerate(turns):
        out.append(html.Div(t["question"], style={"alignSelf": "flex-end", "background": "#e7f0fb", "color": ui.INK, "padding": "8px 12px",
                                                   "borderRadius": "12px 12px 2px 12px", "maxWidth": "80%", "fontSize": "14px",
                                                   "whiteSpace": "pre-wrap"}))
        last = i == len(turns) - 1
        if t.get("elapsed") is None and last:
            out.append(html.Div(status or "Working…", style={"fontSize": "13px", "color": ui.MUTED, "fontStyle": "italic"}))
            if t.get("trace"):
                out.append(how_i_got_this(t))
            continue
        body = []
        if t.get("answer"):
            body.append(dcc.Markdown(t["answer"], link_target="_blank", style={"fontSize": "14px", "lineHeight": 1.5}))
        if t.get("error"):
            body.append(html.Div(t["error"], style={"fontSize": "13px", "color": "#9f3d1f"}))
        body += [badge_row(t.get("badges") or []), how_i_got_this(t)]
        out.append(html.Div(body, style={"background": ui.SURFACE, "border": f"1px solid {ui.LINE}", "padding": "8px 12px",
                                         "borderRadius": "12px 12px 12px 2px", "maxWidth": "92%"}))
    return out


def n_finished(turns):
    """Turns with an answer or an error line. The answer section shows only when this is > 0."""
    return sum(1 for t in turns if t.get("elapsed") is not None)


STATUS_ON = {"display": "block", "fontSize": "12px", "color": ui.INK2, "fontStyle": "italic", "marginTop": "6px"}
STATUS_OFF = {"display": "none"}
ANSWERS_OFF = {"display": "none"}
ANSWERS_ON = {**ui.CARD, "marginTop": "12px", "display": "block"}


CODE = {"whiteSpace": "pre", "fontSize": "11px", "fontFamily": "ui-monospace, SFMono-Regular, Menlo, monospace", "background": "#f4f3ef",
        "padding": "8px 10px", "borderRadius": "6px", "margin": "4px 0 2px", "maxHeight": "320px", "overflow": "auto", "userSelect": "text"}


def sql_entry(e, with_tool=False):
    meta = []
    if e.get("params"):
        meta.append(e["params"])
    if e.get("rows") is not None:
        meta.append(f"{e['rows']:,} row(s)")
    meta.append(f"cached, ran at {e.get('ran_at')}" if e.get("cached") else f"{e.get('secs', 0):.2f} s")
    head = [html.Code(e.get("file", ""), style={"fontWeight": 600}), html.Span(f" — {e.get('purpose') or ''}", style={"color": ui.INK2})]
    lines = [html.Div(head, style={"fontSize": "12px"})]
    if with_tool:
        q = (e.get("question") or "").strip()
        lines.append(html.Div(f"{e.get('tool', '')} · for: “{q[:90] + ('…' if len(q) > 90 else '')}”", style={"fontSize": "11px", "color": ui.MUTED}))
    lines.append(html.Div(" · ".join(meta), style={"fontSize": "11px", "color": ui.MUTED}))
    if e.get("rejected"):
        lines.append(html.Div(f"rejected by guard: {e['rejected']}", style={"fontSize": "12px", "color": "#9f3d1f", "fontWeight": 600}))
    elif e.get("error"):
        lines.append(html.Div(f"failed: {e['error']}", style={"fontSize": "12px", "color": "#9f3d1f"}))
    lines.append(html.Details([html.Summary("SQL as sent to Exasol" if not e.get("rejected") else "SQL (not sent)",
                                            style={"cursor": "pointer", "fontSize": "11px", "color": ui.INK2}),
                               html.Pre(e.get("sql") or "", style=CODE)]))
    return html.Div(lines, style={"padding": "6px 0", "borderTop": f"1px solid {ui.LINE}"})


def sql_dash_summary(entries):
    secs = sum(e.get("secs") or 0 for e in entries)
    return f" · {len(entries)} statement{'s' if len(entries) != 1 else ''} for this view · {secs:.1f} s"


def sql_assist_summary(log):
    return f" · {len(log)} assistant statement{'s' if len(log) != 1 else ''} in this conversation" if log else ""


def view_line(year, w, scen, pessimistic, wname, n_active, added):
    added_txt = f"{added / 1e6:+.1f} M" if abs(added) >= 1e5 else f"{added:+,.0f}"
    return (f"Showing {year_label(year)} · w = {w_text(w)} · Scenario: {scen}{' (pessimistic dates)' if pessimistic else ''}"
            f"{' · What-if: ' + wname if wname else ''} · {n_active} project(s) active · {added_txt} places/day net"
            f" · source: MUNICH_DATASET on Exasol, read-only")


def create_dash_app(server, url_base_pathname, metadata):
    app = Dash(__name__, server=server, routes_pathname_prefix="/",
               requests_pathname_prefix=url_base_pathname.rstrip("/") + "/",
               title=metadata.get("title", "Munich Mobility Planning"), external_stylesheets=ui.STYLESHEETS)
    backend = Backend(server, metadata)

    def q(name, params=None):
        return ui.rows_or_error(load_rows(server, metadata, __file__, f"queries/{name}.sql", params=params))

    def cached(name):
        rows, err = backend.cached(name)
        return (rows, None) if not err else ([], ui.error_panel(err))

    def projects():
        rows, err = cached("projects")
        return [r for r in rows if r.get("kind") == "project"], [r for r in rows if r.get("kind") == "station"], err

    btn = {"fontSize": "13px", "padding": "6px 14px", "borderRadius": "8px", "border": f"1px solid {ui.LINE}", "cursor": "pointer",
           "background": ui.SURFACE, "color": ui.INK}
    chip = {**btn, "fontSize": "12px", "padding": "3px 10px", "borderRadius": "14px", "marginRight": "6px", "marginBottom": "4px",
            "color": ui.INK2}
    chat_panel = html.Div([
        html.Div("Ask", style={"fontSize": "15px", "fontWeight": 600, "color": ui.INK, "marginBottom": "4px"}),
        html.Div(id="setup-line", style={"display": "none", "fontSize": "13px", "color": "#9f3d1f", "marginTop": "8px"}),
        html.Div([
            html.Div([html.Button(t, id=f"chip-{i}", n_clicks=0, style=chip) for i, t in enumerate(EXAMPLES)], style={"margin": "4px 0 4px"}),
            dcc.Textarea(id="question", placeholder="Ask about the data, the plans, or a what-if…", value="",
                         style={"width": "100%", "height": "64px", "fontSize": "14px", "padding": "6px 8px", "borderRadius": "8px",
                                "border": f"1px solid {ui.LINE}", "fontFamily": ui.FONT, "boxSizing": "border-box"}),
            html.Div([html.Button("Ask", id="ask-btn", n_clicks=0, style={**btn, "background": ACCENT, "color": "#fff", "border": "none",
                                                                          "fontWeight": 600}),
                      html.Button("New conversation", id="new-btn", n_clicks=0, style={**btn, "marginLeft": "8px"}),
                      html.Span(f"Answers by OpenAI {assistant.MODEL}. Questions, the context pack and the SQL results it asks for are sent to OpenAI.",
                                style={"fontSize": "11px", "color": ui.MUTED, "marginLeft": "12px"})],
                     style={"marginTop": "6px", "display": "flex", "alignItems": "center", "flexWrap": "wrap", "gap": "4px"}),
            html.Div(id="chat-status", style=STATUS_OFF),
        ], id="chat-input", style={"display": "none"}),
    ], style={**ui.CARD, "marginBottom": "12px"})
    answers = html.Div([
        html.H3("Answers", style={"margin": "0 0 8px", "fontSize": "15px", "fontWeight": 600, "color": ui.INK}),
        html.Div(id="chat-log", style={"display": "flex", "flexDirection": "column", "gap": "8px"}),
    ], id="answers-section", style=ANSWERS_OFF)

    label = {"fontSize": "13px", "fontWeight": 600, "color": ui.INK}
    now_y = assistant.current_year()
    marks = {y: str(y) for y in (2024, 2025, 2030, 2035, 2040, 2045)}
    marks[now_y] = f"{now_y} (now)"
    group_cols = [html.Div([html.Div(title, style={**label, "marginBottom": "4px"}),
                            dcc.Checklist(id=f"proj-{i}", options=[], value=[], labelStyle={"display": "block", "marginBottom": "4px"},
                                          inputStyle={"marginRight": "6px"})],
                           style={"flex": "1 1 300px", "minWidth": "260px"}) for i, (title, _) in enumerate(STATUS_GROUPS)]
    controls = [
        html.Div([
            html.Div("Year", style=label),
            dcc.Slider(id="year", min=YEARS[0], max=YEARS[1], step=1, value=now_y, marks=marks),
        ], style={**ui.CARD, "marginBottom": "12px"}),
        html.Details([
            html.Summary([html.Span("Scenarios", style={"fontSize": "15px", "fontWeight": 600, "color": ui.INK}),
                          html.Span(id="scen-status", style={"fontSize": "13px", "color": ui.INK2, "marginLeft": "10px"})],
                         style={"cursor": "pointer", "marginBottom": "8px"}),
            html.Div("A project adds supply from its opening year onward. Preset first, then switch single projects on or off.",
                     style={"fontSize": "12px", "color": ui.MUTED, "marginBottom": "8px"}),
            dcc.RadioItems(id="preset", options=[{"label": f" {t}", "value": v} for v, t in PRESETS]
                           + [{"label": " Custom", "value": "custom", "disabled": True}], value="none", inline=True,
                           inputStyle={"marginLeft": "14px"}, style={"fontSize": "13px", "marginBottom": "6px"}),
            html.Div([
                html.Span("Job weight (w)", style={"fontSize": "13px", "fontWeight": 600, "color": ui.INK, "marginRight": "8px"}),
                dcc.Input(id="w-input", type="number", min=0, max=1.5, step=0.25, value=1.0, debounce=True,
                          style={"width": "80px", "fontSize": "13px", "padding": "2px 6px"}),
                html.Span("Activity = residents + w × jobs; w = 0 means residents only. 0 to 1.5 in steps of 0.25.",
                          style={"fontSize": "12px", "color": ui.MUTED, "marginLeft": "8px"}),
            ], style={"marginBottom": "8px"}),
            dcc.Checklist(id="pess", options=[{"label": " Pessimistic dates (use the risk year where one is published)", "value": 1}], value=[],
                          style={"fontSize": "13px", "marginBottom": "10px"}),
            html.Div(group_cols, style={"display": "flex", "gap": "16px", "flexWrap": "wrap"}),
        ], id="scen-details", open=False, style={**ui.CARD, "marginBottom": "12px"}),
    ]

    app.layout = ui.page([
        dcc.Interval(id="boot", max_intervals=1, interval=200),
        dcc.Interval(id="poll", interval=1000, disabled=True),
        dcc.Store(id="sid"),
        dcc.Store(id="chat-rev", data=-1),
        dcc.Store(id="view-store", data=default_view_store()),
        *controls,
        chat_panel,
        html.Div(id="whatif-banner", style={"display": "none"}),
        html.Div([
            ui.card(html.Span("How well served is each district?", id="svcmap-title"),
                    html.Div([ui.graph("svcmap", 640),
                              html.Div(CAVEAT, style={"fontSize": "12px", "color": ui.MUTED, "marginTop": "8px", "lineHeight": 1.45}),
                              html.Div(id="err")]),
                    "Scheduled places offered per 1,000 residents + w × jobs in the selected year, relative to the 2024 city average at the same w "
                    "(a fixed baseline on today's timetable, so colours compare across years and scenarios). Dots: active projects' stations "
                    "(filled = new station, ring = existing station gaining a line).",
                    flex="3 1 560px"),
            ui.card(html.Span("Change since 2024", id="change-title"), ui.graph("change", 690),
                    "% change in places per 1,000 activity between 2024 and the selected year, with the active projects and any what-if.",
                    flex="2 1 360px"),
        ], style={"display": "flex", "gap": "12px", "flexWrap": "wrap", "alignItems": "stretch"}),
        answers,
        html.Details([
            html.Summary([html.Span("SQL executed", style={"fontSize": "15px", "fontWeight": 600, "color": ui.INK}),
                          html.Span(id="sql-sum-dash", style={"fontSize": "13px", "color": ui.INK2}),
                          html.Span(id="sql-sum-assist", style={"fontSize": "13px", "color": ui.INK2})],
                         style={"cursor": "pointer"}),
            html.Div("Every statement as sent to Exasol (read-only user), placeholders substituted with pyexasol's formatter, the same "
                     "code the server uses. Cached statements show when they ran.", style={"fontSize": "12px", "color": ui.MUTED, "margin": "6px 0"}),
            html.H4("Dashboard queries for the current view", style={"margin": "10px 0 2px", "fontSize": "13px", "color": ui.INK}),
            html.Div(id="sql-dash"),
            html.H4("Assistant queries in this conversation", style={"margin": "14px 0 2px", "fontSize": "13px", "color": ui.INK}),
            html.Div(id="sql-assist", children=html.Div("None yet.", style={"fontSize": "12px", "color": ui.MUTED})),
        ], id="sql-details", open=False, style={**ui.CARD, "marginTop": "12px"}),
    ], eyebrow="Urban planning", title="Munich Mobility Planning", accent=ACCENT,
        subtitle=[html.Div("v5 – Ask the assistant", style={"fontSize": "15px", "fontWeight": 600, "color": ui.INK, "marginBottom": "4px"}),
                  "Ask about how well each district is served by scheduled public transport, now and to 2045, the planned projects, "
                  "or a what-if. Set the year and scenario yourself, or let the assistant set them. Scheduled service only, not passengers."])

    @app.callback(Output("svcmap", "figure"), Output("svcmap-title", "children"), Output("change", "figure"), Output("change-title", "children"),
                  Output("err", "children"), Output("page-meta", "children"), Output("whatif-banner", "children"),
                  Output("whatif-banner", "style"), Output("scen-status", "children"), Output("sql-dash", "children"),
                  Output("sql-sum-dash", "children"), Input("view-store", "data"))
    def refresh(view):
        """Map + change chart for the view, plus the list of statements that produced them (group 1 of 'SQL executed')."""
        entries = []
        backend.set_sink(entries.append)
        try:
            out = refresh_inner(view)
        finally:
            backend.set_sink(None)
        return (*out, [sql_entry(e) for e in entries], sql_dash_summary(entries))

    def refresh_inner(view):
        year, w, selected, pessimistic, wname, extra = norm_view(view)
        proj_param = ",".join(selected) if selected else "none"
        blank = ui.empty("")
        banner_off = {"display": "none"}
        banner_on = {"display": "block", "background": "#fdf3d8", "border": "1px solid #eda100", "color": "#6b4a00", "borderRadius": "8px",
                     "padding": "6px 12px", "fontSize": "13px", "marginBottom": "12px", "fontWeight": 600}
        banner = f"What-if: {wname}, a hypothetical, not a real plan" if wname else ""
        rows, err = backend.query("ranking", {"w_jobs": w, "year": year, "projects": proj_param, "pessimistic": pessimistic, "extra": extra})
        err = ui.error_panel(err) if err else None
        change_title = f"Change since 2024 — {year_label(year)}"
        if err:
            return (blank, f"How well served is each district? — {year_label(year)}", blank, change_title, err, "", banner,
                    banner_on if wname else banner_off, "")
        active = {p for r in rows for p in str(r.get("active_projects") or "").split(",") if p}
        projs, stations, perr = projects()
        scen = scen_name(projs, selected) if not perr else (f"{len(selected)} projects" if selected else "None (today's timetable)")
        is_now = year == assistant.current_year()
        if not selected and not wname:
            title_scen = "now" if is_now else "if service stays as it is today"
        else:
            title_scen = (f"{scen}, {len(active)} of {len(selected)} projects open" if selected else "today's timetable")
            title_scen += f" · What-if: {wname}" if wname else ""
            title_scen = f"now · {title_scen}" if is_now else title_scen
        map_title = f"How well served is each district? — {year} ({title_scen})"
        act_stations = [s for s in stations if s.get("project_id") in active]
        geo, gerr = cached("geo")
        svcmap = blank if gerr else service_map(rows, geo, year, act_stations)
        r0 = rows[0] if rows else {}
        city_pct = pct(ui.num(r0.get("city_places_per_1k_act_2024")), ui.num(r0.get("city_places_per_1k_act")))
        line = view_line(year, w, scen, pessimistic and selected, wname, len(active), ui.num(r0.get("city_added_places")))
        status = status_line(scen, w, len(active), year, ui.num(r0.get("city_added_places")))
        return (svcmap, map_title, change_bars(rows, year, city_pct), change_title, gerr or perr, line, banner,
                banner_on if wname else banner_off, status)

    # ---- manual controls. view-store stays the only source the map and chart read.
    @app.callback([Output(f"proj-{i}", "options") for i in range(len(STATUS_GROUPS))], Input("boot", "n_intervals"))
    def project_options(_):
        projs, _stations, err = projects()
        if err:
            return [[] for _ in STATUS_GROUPS]
        opts = []
        for _, statuses in STATUS_GROUPS:
            group = sorted([p for p in projs if p.get("status") in statuses],
                           key=lambda p: (int(ui.num(p.get("opening_year_model"))), pshort(p["project_id"])))
            opts.append([{"label": project_label(p), "value": p["project_id"]} for p in group])
        return opts

    @app.callback(Output("year", "value"), Output("preset", "value"), Output("w-input", "value"), Output("pess", "value"),
                  *[Output(f"proj-{i}", "value") for i in range(len(STATUS_GROUPS))], Input("view-store", "data"))
    def view_to_controls(view):
        """Controls always show the real state (also after the assistant's set_view or New conversation).
        Concrete values only, and no view-store output, so this can never block the first render."""
        year, w, selected, pessimistic, _wname, _extra = norm_view(view)
        projs, _stations, err = projects()
        chosen = set(selected)
        preset = "none" if not chosen else "custom"
        if chosen and not err:
            for value, _title in PRESETS:
                if value != "none" and chosen == set(preset_ids(projs, value)):
                    preset = value
                    break
        groups = [[p["project_id"] for p in projs if p.get("status") in statuses and p["project_id"] in chosen] for _, statuses in STATUS_GROUPS]
        return (year, preset, w, [1] if pessimistic else [], *groups)

    @app.callback(Output("view-store", "data", allow_duplicate=True), Output("w-input", "value", allow_duplicate=True),
                  Input("year", "value"), Input("preset", "value"), Input("w-input", "value"), Input("pess", "value"),
                  *[Input(f"proj-{i}", "value") for i in range(len(STATUS_GROUPS))], State("view-store", "data"),
                  prevent_initial_call=True)
    def controls_to_view(year_v, preset_v, w_v, pess_v, *rest):
        """Controls -> view-store, written only when the view really changes (so store -> controls -> here ends in one no-op).
        Keeps an active what-if (it is additive). prevent_initial_call: never part of the first-load chain."""
        groups, cur = rest[:-1], rest[-1] or {}
        y0, w0, p0, pess0, _wn, _ex = norm_view(cur)
        trig = {t["prop_id"].split(".")[0] for t in ctx.triggered}
        try:
            wv = float(w_v)
            w_new = round(wv * 4) / 4 if 0 <= wv <= 1.5 else None
        except (TypeError, ValueError):
            w_new = None
        w_fix = no_update
        if w_new is None:
            w_new, w_fix = w0, w0          # invalid or empty w: keep the last valid value and show it again
        if trig == {"preset"} and preset_v in {v for v, _ in PRESETS}:
            projs, _stations, err = projects()
            sel = sorted(set(preset_ids(projs, preset_v))) if not err else p0
        else:
            sel = sorted({pid for g in groups for pid in (g or [])})
        try:
            y_new = min(max(int(year_v), YEARS[0]), YEARS[1])
        except (TypeError, ValueError):
            y_new = y0
        new = {"year": y_new, "w": w_new, "projects": sel, "pessimistic": 1 if pess_v else 0}
        if (new["year"], new["w"], new["projects"], new["pessimistic"]) == (y0, w0, p0, pess0):
            return no_update, w_fix
        return dict(cur, **new), w_fix

    @app.callback(Output("chat-log", "children"), Output("chat-status", "children"), Output("chat-status", "style"),
                  Output("answers-section", "style"), Output("view-store", "data"),
                  Output("ask-btn", "disabled"), Output("poll", "disabled"), Output("question", "value"), Output("chat-rev", "data"),
                  Output("sql-assist", "children"), Output("sql-sum-assist", "children"),
                  Output("sid", "data"), Output("chat-input", "style"), Output("setup-line", "children"), Output("setup-line", "style"),
                  Input("boot", "n_intervals"), Input("ask-btn", "n_clicks"), Input("new-btn", "n_clicks"), Input("poll", "n_intervals"),
                  State("question", "value"), State("sid", "data"), State("view-store", "data"), State("chat-rev", "data"))
    def chat(_boot, _ask, _new, _poll, question, sid, view, rev):
        trig = ctx.triggered_id
        nu = no_update

        def boot_view(cur):
            """Always a concrete store on the initial call and on boot, never no_update: refresh (Input view-store.data)
            waits on this output in Dash's initial-call chain, so no_update here would leave the map and chart blank.
            The default view is the current year; the layout default is computed at app start, so correct the year here."""
            want = default_view_store()
            if not cur or not (cur.get("projects") or cur.get("what_if")):
                return dict(want, ver=(cur or {}).get("ver", 0))
            return dict(cur)

        def pack(snap, status=None, log=True, view_out=nu, ask_disabled=None, poll_disabled=None, question_out=nu,
                 sid_out=nu, input_style=nu, setup=nu, setup_style=nu):
            """One place that decides what the answer section and status line show."""
            status = snap["status"] if status is None else status
            busy = snap["running"]
            done = n_finished(snap["turns"])
            return (render_turns(snap["turns"], snap["status"]) if log else nu, status, STATUS_ON if status else STATUS_OFF,
                    ANSWERS_ON if done else ANSWERS_OFF, view_out,
                    busy if ask_disabled is None else ask_disabled, (not busy) if poll_disabled is None else poll_disabled,
                    question_out, snap["rev"] if log else rev,
                    [sql_entry(e, with_tool=True) for e in snap["sql_log"]] or html.Div("None yet.", style={"fontSize": "12px", "color": ui.MUTED}),
                    sql_assist_summary(snap["sql_log"]), sid_out, input_style, setup, setup_style)

        if trig == "boot" or not sid:
            sid = assistant.new_session_id()
            snap = assistant.snapshot(sid)
            ok, msg = assistant.key_status()
            if not ok:
                return pack(snap, status="", ask_disabled=True, poll_disabled=True, question_out="", sid_out=sid, view_out=boot_view(view),
                            input_style={"display": "none"}, setup=msg,
                            setup_style={"display": "block", "fontSize": "13px", "color": "#9f3d1f", "marginTop": "8px"})
            return pack(snap, status="", sid_out=sid, input_style={"display": "block"}, setup="", setup_style={"display": "none"},
                        view_out=boot_view(view))
        if trig == "new-btn":
            v = assistant.reset(sid)
            return pack(assistant.snapshot(sid), status="", view_out=v, question_out="")
        if trig == "ask-btn":   # only the Ask button sends; the example chips just fill the input (clientside below)
            ok, msg = assistant.start(sid, question, view, backend)
            snap = assistant.snapshot(sid)
            if not ok:
                return pack(snap, status=msg, log=False)
            return pack(snap, ask_disabled=True, poll_disabled=False, question_out="")
        # poll
        snap = assistant.snapshot(sid)
        new_view = snap["view"] if (view or {}).get("ver") != snap["view"]["ver"] else nu
        return pack(snap, log=snap["rev"] != rev, view_out=new_view)

    app.clientside_callback(
        # example chips: put the chip's text into the input (replacing it) and focus the field without scrolling; nothing is sent.
        # No view-store output and prevent_initial_call, so it cannot enter the first-load callback chain.
        "function(){var ex=" + json.dumps(EXAMPLES) + ";var t=(window.dash_clientside.callback_context.triggered||[])[0];"
        "if(!t||!t.value){return window.dash_clientside.no_update;}var i=parseInt(t.prop_id.split('.')[0].split('-')[1],10);"
        "setTimeout(function(){var el=document.getElementById('question');if(el){el.focus({preventScroll:true});var n=el.value.length;"
        "try{el.setSelectionRange(n,n);}catch(e){}}},50);return ex[i];}",
        Output("question", "value", allow_duplicate=True), [Input(f"chip-{i}", "n_clicks") for i in range(len(EXAMPLES))],
        prevent_initial_call=True)

    return app
