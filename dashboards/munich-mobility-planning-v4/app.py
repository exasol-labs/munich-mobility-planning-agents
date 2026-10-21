"""Munich Mobility Planning: scheduled public transport supply per 1,000 residents + w x jobs per district,
for a forecast year 2024-2045, with switchable rail and tram project scenarios. Two views: the service map and
the change since 2024. Metric units (km2)."""
import json
import math
import re
import time

from dash import Dash, Input, Output, State, dcc, html, no_update
import plotly.graph_objects as go

from dash_server_exasol import load_rows
import munich_ui as ui
import sql_log

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


def create_dash_app(server, url_base_pathname, metadata):
    app = Dash(__name__, server=server, routes_pathname_prefix="/",
               requests_pathname_prefix=url_base_pathname.rstrip("/") + "/",
               title=metadata.get("title", "Munich Mobility Planning"), external_stylesheets=ui.STYLESHEETS)
    cache = {}

    def q_logged(name, params, purpose):
        return sql_log.run(lambda: ui.rows_or_error(load_rows(server, metadata, __file__, f"queries/{name}.sql", params=params)),
                           name, params, purpose)

    def q(name, params=None, log=None, purpose=""):
        rows, err, entry = q_logged(name, params, purpose)
        if log is not None:
            log.append(entry)
        return rows, err

    def cached(name, log=None, purpose=""):
        hit = cache.get(name)
        if hit and time.time() - hit[0] < CACHE_TTL_S:
            if log is not None:
                log.append(sql_log.as_cached(hit[2], purpose))
            return hit[1], None
        rows, err, entry = q_logged(name, None, purpose)
        if log is not None:
            log.append(entry)
        if not err:
            cache[name] = (time.time(), rows, entry)
        return rows, err

    def projects(log=None):
        rows, err = cached("projects", log, "project list and station markers")
        return [r for r in rows if r.get("kind") == "project"], [r for r in rows if r.get("kind") == "station"], err

    label = {"fontSize": "13px", "fontWeight": 600, "color": ui.INK}
    group_cols = [html.Div([html.Div(title, style={**label, "marginBottom": "4px"}),
                            dcc.Checklist(id=f"proj-{i}", options=[], value=[], labelStyle={"display": "block", "marginBottom": "4px"},
                                          inputStyle={"marginRight": "6px"})],
                           style={"flex": "1 1 300px", "minWidth": "260px"}) for i, (title, _) in enumerate(STATUS_GROUPS)]
    app.layout = ui.page([
        dcc.Interval(id="boot", max_intervals=1, interval=200),
        dcc.Store(id="w-store", data=1.0),
        dcc.Markdown(
            "**Which planned rail and tram projects make up for the growth, and where?**  \n"
            "As in v3, the year slider moves through Munich's growth to 2045. Open **Scenarios** to switch on planned projects: "
            "funded ones such as Tram-Westtangente, Tram 23/24, U5 to Pasing and the 2nd Stammstrecke (with 15-minute S-Bahn service), "
            "or projects that are only under discussion, such as U5 to Freiham and U9. A project counts from its planned opening year, "
            "and \"pessimistic dates\" uses the published risk years. Station markers show where each project adds service.",
            style={**ui.CARD, "marginBottom": "12px", "fontSize": "14px", "color": ui.INK2, "lineHeight": 1.5}),
        html.Div([
            html.Div("Year", style=label),
            dcc.Slider(id="year", min=YEARS[0], max=YEARS[1], step=1, value=2024,
                       marks={y: str(y) for y in (2024, 2025, 2030, 2035, 2040, 2045)}),
        ], style={**ui.CARD, "marginBottom": "12px"}),
        html.Details([
            html.Summary([html.Span("Scenarios", style={"fontSize": "15px", "fontWeight": 600, "color": ui.INK}),
                          html.Span(id="scen-status", style={"fontSize": "13px", "color": ui.INK2, "marginLeft": "10px"})],
                         style={"cursor": "pointer", "marginBottom": "8px"}),
            html.Div("A project adds supply from its opening year onward. Preset first, then switch single projects on or off.",
                     style={"fontSize": "12px", "color": ui.MUTED, "marginBottom": "8px"}),
            dcc.RadioItems(id="preset", options=[{"label": f" {t}", "value": v} for v, t in PRESETS], value="none", inline=True,
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
                    "% change in places per 1,000 activity between 2024 and the selected year, with the active projects.",
                    flex="2 1 360px"),
        ], style={"display": "flex", "gap": "12px", "flexWrap": "wrap", "alignItems": "stretch"}),
        sql_log.foldout(),
    ], eyebrow="Urban planning", title="Munich Mobility Planning", accent=ACCENT,
        subtitle=[html.Div("v4 – Forecast with rail and tram scenarios",
                           style={"fontSize": "15px", "fontWeight": 600, "color": ui.INK, "marginBottom": "4px"}),
                  "Which districts, counting residents and jobs, have lower scheduled public transport supply today and as the city grows to 2045, with or without the planned rail and tram projects? Scheduled service only, not passengers."])

    @app.callback([Output(f"proj-{i}", "options") for i in range(len(STATUS_GROUPS))], Input("boot", "n_intervals"))
    def project_options(_):
        projs, _stations, err = projects()
        if err:
            return [[] for _ in STATUS_GROUPS]
        opts = []
        for _, statuses in STATUS_GROUPS:
            group = sorted([p for p in projs if p.get("status") in statuses], key=lambda p: (int(ui.num(p.get("opening_year_model"))), pshort(p["project_id"])))
            opts.append([{"label": project_label(p), "value": p["project_id"]} for p in group])
        return opts

    @app.callback([Output(f"proj-{i}", "value") for i in range(len(STATUS_GROUPS))], Input("preset", "value"), Input("boot", "n_intervals"))
    def apply_preset(preset, _):
        projs, _stations, err = projects()
        chosen = set(preset_ids(projs, preset or "none")) if not err else set()
        return [[p["project_id"] for p in projs if p.get("status") in statuses and p["project_id"] in chosen] for _, statuses in STATUS_GROUPS]

    @app.callback(Output("svcmap", "figure"), Output("svcmap-title", "children"), Output("change", "figure"), Output("change-title", "children"),
                  Output("err", "children"), Output("page-meta", "children"), Output("scen-status", "children"), Output("sql-dash", "children"), Output("sql-sum-dash", "children"),
                  Input("w-store", "data"), Input("year", "value"), Input("pess", "value"),
                  *[Input(f"proj-{i}", "value") for i in range(len(STATUS_GROUPS))])
    def refresh(w, year, pess, *groups):
        w = float(w if w is not None else 1.0)
        log = []
        year = int(year if year is not None else 2024)
        year = min(max(year, YEARS[0]), YEARS[1])
        pessimistic = 1 if pess else 0
        selected = sorted({pid for g in groups for pid in (g or [])})
        proj_param = ",".join(selected) if selected else "none"
        blank = ui.empty("")
        rows, err = q("ranking", {"w_jobs": w, "year": year, "projects": proj_param, "pessimistic": pessimistic}, log, "district ranking for the map and change chart")
        change_title = f"Change since 2024 — {year}"
        if err:
            return (blank, f"How well served is each district? — {year}", blank, change_title, err, "", "", sql_log.entries(log), sql_log.summary(log))
        active = {p for r in rows for p in str(r.get("active_projects") or "").split(",") if p}
        scen = "if service stays as it is today" if not selected else f"{len(active)} of {len(selected)} selected projects open"
        map_title = f"How well served is each district? — {year} ({scen})"
        projs, stations, perr = projects(log)
        act_stations = [s for s in stations if s.get("project_id") in active]
        geo, gerr = cached("geo", log, "district polygons and label points for the map")
        svcmap = blank if gerr else service_map(rows, geo, year, act_stations)
        r0 = rows[0] if rows else {}
        city_pct = pct(ui.num(r0.get("city_places_per_1k_act_2024")), ui.num(r0.get("city_places_per_1k_act")))
        status = status_line(scen_name(projs, selected), w, len(active), year, ui.num(r0.get("city_added_places")))
        meta = (f"Year {year} · jobs weight w = {w:g} · projects: {', '.join(pshort(p) for p in selected) or 'none'}"
                f"{' (pessimistic dates)' if pessimistic and selected else ''} · source: MUNICH_DATASET on Exasol, read-only")
        return (svcmap, map_title, change_bars(rows, year, city_pct), change_title, gerr or perr, meta, status, sql_log.entries(log), sql_log.summary(log))

    @app.callback(Output("w-store", "data"), Output("w-input", "value"), Input("w-input", "value"), State("w-store", "data"),
                  prevent_initial_call=True)
    def set_w(input_w, last_w):
        """The number input is the single source of truth for w; the store keeps the last valid value.
        Valid input snaps to 0.25; invalid, empty or out-of-range input falls back to the last valid value."""
        last = 1.0 if last_w is None else float(last_w)
        try:
            v = float(input_w)
        except (TypeError, ValueError):
            return no_update, last
        if not (0 <= v <= 1.5):
            return no_update, last
        v = round(v * 4) / 4
        return (no_update if v == last else v), v

    return app
