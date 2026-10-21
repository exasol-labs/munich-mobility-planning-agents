"""Munich Mobility Planning v1 – Today, per resident: scheduled public transport supply (places offered on a typical
weekday) per 1,000 residents in each district, relative to the Munich average. One view: the service map.
Fixed parameters for ranking.sql: w_jobs = 0, year = 2024, projects = 'none', pessimistic = 0. Metric units (km²)."""
import json
import math
import re
import time

from dash import Dash, Input, Output, dcc, html
import plotly.graph_objects as go

from dash_server_exasol import load_rows
import munich_ui as ui
import sql_log

ACCENT = ui.PERSONA["planning"]
CACHE_TTL_S = 3600
PARAMS = {"w_jobs": 0.0, "year": 2024, "projects": "none", "pessimistic": 0}
RATIO_LO, RATIO_HI = 0.4, 2.5
Z_HALF = math.log2(RATIO_HI)  # log2(0.4) is about -log2(2.5), so the scale is symmetric around 1.0
RATIO_SCALE = [[0.0, ui.RAMP_ORANGE[5]], [0.22, ui.RAMP_ORANGE[3]], [0.42, ui.RAMP_ORANGE[1]], [0.5, "#dedcd6"],
               [0.58, ui.RAMP_BLUE[1]], [0.78, ui.RAMP_BLUE[3]], [1.0, ui.RAMP_BLUE[5]]]
RATIO_TICKS = (0.5, 0.75, 1, 1.5, 2)
DENSE_LABEL = "dense (top third by residents per km²)"
COORD = re.compile(r"(-?\d+(?:\.\d+)?(?:[eE]-?\d+)?)\s+(-?\d+(?:\.\d+)?(?:[eE]-?\d+)?)")
MAP_TITLE = "How well served is each district? – today"
CAVEAT = "Scheduled service (MVV timetable, reference Wednesday 21 Oct 2026), not passengers or delays. Residents: end of 2024."


def wkt_to_geometry(wkt):
    """WGS84 POLYGON / MULTIPOLYGON WKT (lon lat) to a GeoJSON geometry, no extra dependency."""
    text = (wkt or "").strip()
    kind = "MultiPolygon" if text.upper().startswith("MULTIPOLYGON") else "Polygon"
    body = COORD.sub(r"[\1,\2]", text[text.index("("):]).replace("(", "[").replace(")", "]")
    return {"type": kind, "coordinates": json.loads(body)}


def short_name(name):
    name = str(name or "")
    return name if len(name) <= 22 else name.split("-")[0] + "-…"


def service_map(rows, geo):
    """Choropleth of service_ratio (places per 1,000 residents / city average, w = 0, 2024) on a log scale
    centred on 1.0 and clamped at 0.4–2.5, with the densest third outlined and name + ratio labels."""
    gj = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "id": str(int(ui.num(g["district_no"]))), "properties": {"name": g["district"]},
         "geometry": wkt_to_geometry(g["polygon_wkt"])} for g in geo]}
    cent = {str(int(ui.num(g["district_no"]))): g for g in geo}
    ids = [str(int(ui.num(r["district_no"]))) for r in rows]
    ratio = [ui.num(r.get("service_ratio"), 1.0) for r in rows]
    z = [math.log2(min(max(v, RATIO_LO), RATIO_HI)) for v in ratio]
    hover = [(f"<b>{r['district']}</b><br>{v:.2f}× the city average<br>"
              f"{ui.fmt(r['population'])} residents<br>"
              f"{ui.fmt(r['density_per_km2'])} residents per km²<br>"
              f"{ui.fmt(r['places_per_1k_res'])} places, {ui.fmt(r['dep_per_1k_act'], 1)} departures per 1,000 residents<br>"
              f"{ui.fmt(r['residents_per_station'])} residents per station<br>"
              f"mode: {r.get('mode_note') or 'mixed'}")
             for r, v in zip(rows, ratio)]
    fig = go.Figure()
    fig.add_trace(go.Choroplethmap(
        geojson=gj, locations=ids, z=z, featureidkey="id", colorscale=RATIO_SCALE, zmin=-Z_HALF, zmax=Z_HALF, zmid=0,
        marker={"opacity": 0.85, "line": {"color": ui.SURFACE, "width": 1}}, hovertext=hover, hoverinfo="text",
        name="places vs city average", showlegend=False,
        colorbar={"title": {"text": "× city average", "font": {"size": 12}}, "thickness": 12, "len": 0.7,
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
    return ui.map_layout(fig, {"lat": 48.152, "lon": 11.548}, 9.85)


def create_dash_app(server, url_base_pathname, metadata):
    app = Dash(__name__, server=server, routes_pathname_prefix="/",
               requests_pathname_prefix=url_base_pathname.rstrip("/") + "/",
               title=metadata.get("title", "Munich Mobility Planning"), external_stylesheets=ui.STYLESHEETS)
    cache = {}

    def cached(name, params=None, log=None, purpose=""):
        hit = cache.get(name)
        if hit and time.time() - hit[0] < CACHE_TTL_S:
            if log is not None:
                log.append(sql_log.as_cached(hit[2]))
            return hit[1], None
        rows, err, entry = sql_log.run(
            lambda: ui.rows_or_error(load_rows(server, metadata, __file__, f"queries/{name}.sql", params=params)),
            name, params, purpose)
        if log is not None:
            log.append(entry)
        if not err:
            cache[name] = (time.time(), rows, entry)
        return rows, err

    intro = dcc.Markdown(
        "**How well is each district served by public transport today?**  \n"
        "The map compares the scheduled capacity of buses, trams, U-Bahn and S-Bahn (the places offered on a typical weekday) "
        "with the number of people living in each district. 1.0× is the Munich average. Red districts get fewer places per "
        "resident than average, blue ones more. The outlined districts are the densest third.",
        style={**ui.CARD, "marginBottom": "12px", "fontSize": "14px", "color": ui.INK2, "lineHeight": 1.5})

    app.layout = ui.page([
        dcc.Interval(id="boot", max_intervals=1, interval=200),
        intro,
        html.Div(ui.card(MAP_TITLE,
                         html.Div([ui.graph("svcmap", 640),
                                   html.Div(CAVEAT, style={"fontSize": "12px", "color": ui.MUTED, "marginTop": "8px", "lineHeight": 1.45}),
                                   html.Div(id="err")]),
                         flex="1 1 560px"),
                 style={"display": "flex"}),
        sql_log.foldout(),
    ], eyebrow="Urban planning", title="Munich Mobility Planning", accent=ACCENT,
        subtitle=[html.Div("v1 – Today, per resident",
                           style={"fontSize": "15px", "fontWeight": 600, "color": ui.INK, "marginBottom": "4px"})])

    @app.callback(Output("svcmap", "figure"), Output("err", "children"),
                  Output("sql-dash", "children"), Output("sql-sum-dash", "children"), Input("boot", "n_intervals"))
    def draw(_):
        log = []
        rows, err = cached("ranking", PARAMS, log, "district ranking for the map")
        if err:
            return (ui.empty(""), err, sql_log.entries(log), sql_log.summary(log))
        geo, gerr = cached("geo", None, log, "district polygons and label points for the map")
        if gerr:
            return (ui.empty(""), gerr, sql_log.entries(log), sql_log.summary(log))
        return (service_map(rows, geo), None, sql_log.entries(log), sql_log.summary(log))

    return app
