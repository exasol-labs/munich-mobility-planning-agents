"""Munich Mobility Planning v3 - Forecast to 2045, if service stays as today: scheduled public transport supply
per 1,000 residents + w x jobs per district for a forecast year 2024-2045 on today's timetable (no projects).
Two views: the service map and the change since 2024. Metric units (km2)."""
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
CAVEAT = ("Scheduled service as of today, held constant. Residents between 2024 and 2045 interpolated to the official 2045 forecast "
          "(Demografiebericht Teil 2). Jobs: 2022 estimate as the 2024 baseline, to the 2040 forecast, held after.")
INTRO = ("**How does this change as Munich grows, if nothing is added?**  \n"
         "Munich is forecast to grow from 1.60 M residents (2024) to 1.83 M (2045), mostly at the edges of the city. "
         "Move the year slider: residents follow the city's official forecast, and jobs follow the 2040 forecast. "
         "The timetable stays exactly as it is today. The map compares each district with today's Munich average, "
         "and the chart on the right shows how much each district's places per 1,000 activity change since 2024.")


def wkt_to_geometry(wkt):
    """WGS84 POLYGON / MULTIPOLYGON WKT (lon lat) to a GeoJSON geometry, no extra dependency."""
    text = (wkt or "").strip()
    kind = "MultiPolygon" if text.upper().startswith("MULTIPOLYGON") else "Polygon"
    body = COORD.sub(r"[\1,\2]", text[text.index("("):]).replace("(", "[").replace(")", "]")
    return {"type": kind, "coordinates": json.loads(body)}


def short_name(name):
    name = str(name or "")
    return name if len(name) <= 22 else name.split("-")[0] + "-…"


def pct(a, b):
    return (b / a - 1) * 100 if a else 0.0


def service_map(rows, geo, year):
    """Choropleth of service_ratio (year Y against the fixed 2024 city average) on a log scale centred on 1.0."""
    gj = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "id": str(int(ui.num(g["district_no"]))), "properties": {"name": g["district"]},
         "geometry": wkt_to_geometry(g["polygon_wkt"])} for g in geo]}
    cent = {str(int(ui.num(g["district_no"]))): g for g in geo}
    ids = [str(int(ui.num(r["district_no"]))) for r in rows]
    ratio = [ui.num(r.get("service_ratio"), 1.0) for r in rows]
    z = [math.log2(min(max(v, RATIO_LO), RATIO_HI)) for v in ratio]

    hover = [(f"<b>{r['district']}</b> ({year})<br>{v:.2f}× the 2024 city average"
              f" · {ui.num(r.get('ratio_own_year')):.2f}× the {year} city average<br>"
              f"2024: {ui.num(r.get('ratio_2024')):.2f}× · change {ui.num(r.get('ratio_change_pp')):+.1f} pp"
              f" ({ui.num(r.get('pct_change_places')):+.1f} % places per 1,000 activity)<br>"
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

    label = {"fontSize": "13px", "fontWeight": 600, "color": ui.INK}
    app.layout = ui.page([
        dcc.Interval(id="boot", max_intervals=1, interval=200),
        dcc.Store(id="w-store", data=1.0),
        dcc.Markdown(INTRO, style={**ui.CARD, "marginBottom": "12px", "fontSize": "14px", "color": ui.INK2, "lineHeight": 1.5}),
        html.Div([
            html.Div([
                html.Div("Year", style=label),
                dcc.Slider(id="year", min=YEARS[0], max=YEARS[1], step=1, value=2024,
                           marks={y: str(y) for y in (2024, 2025, 2030, 2035, 2040, 2045)}),
            ], style={"flex": "3 1 420px", "minWidth": "280px"}),
            html.Div([
                html.Div([
                    html.Span("Job weight (w)", style={**label, "marginRight": "8px"}),
                    dcc.Input(id="w-input", type="number", min=0, max=1.5, step=0.25, value=1.0, debounce=True,
                              style={"width": "80px", "fontSize": "13px", "padding": "2px 6px"}),
                ]),
                html.Div("Activity = residents + w × jobs; w = 0 means residents only. 0 to 1.5 in steps of 0.25.",
                         style={"fontSize": "12px", "color": ui.MUTED, "marginTop": "4px"}),
            ], style={"flex": "1 1 260px", "minWidth": "240px"}),
        ], style={**ui.CARD, "marginBottom": "12px", "display": "flex", "gap": "16px", "flexWrap": "wrap", "alignItems": "center"}),
        html.Div([
            ui.card(html.Span("How well served is each district?", id="svcmap-title"),
                    html.Div([ui.graph("svcmap", 640),
                              html.Div(CAVEAT, style={"fontSize": "12px", "color": ui.MUTED, "marginTop": "8px", "lineHeight": 1.45}),
                              html.Div(id="err")]),
                    "Scheduled places offered per 1,000 residents + w × jobs in the selected year on today's timetable, relative to the "
                    "2024 city average at the same w (a fixed baseline, so colours compare across years).",
                    flex="3 1 560px"),
            ui.card(html.Span("Change since 2024", id="change-title"), ui.graph("change", 690),
                    "% change in places per 1,000 activity between 2024 and the selected year, if service stays as it is today.",
                    flex="2 1 360px"),
        ], style={"display": "flex", "gap": "12px", "flexWrap": "wrap", "alignItems": "stretch"}),
        sql_log.foldout(),
    ], eyebrow="Urban planning", title="Munich Mobility Planning", accent=ACCENT,
        subtitle=[html.Div("v3 – Forecast to 2045, if service stays as today",
                           style={"fontSize": "15px", "fontWeight": 600, "color": ui.INK, "marginBottom": "4px"})])

    @app.callback(Output("svcmap", "figure"), Output("svcmap-title", "children"), Output("change", "figure"), Output("change-title", "children"),
                  Output("err", "children"), Output("page-meta", "children"), Output("sql-dash", "children"), Output("sql-sum-dash", "children"),
                  Input("w-store", "data"), Input("year", "value"))
    def refresh(w, year):
        w = float(w if w is not None else 1.0)
        log = []
        year = int(year if year is not None else 2024)
        year = min(max(year, YEARS[0]), YEARS[1])
        blank = ui.empty("")
        rows, err = q("ranking", {"w_jobs": w, "year": year, "projects": "none", "pessimistic": 0}, log, "district ranking for the map and change chart")
        change_title = f"Change since 2024 – {year}"
        map_title = f"How well served is each district? – {year} (if service stays as it is today)"
        if err:
            return (blank, map_title, blank, change_title, err, "", sql_log.entries(log), sql_log.summary(log))
        geo, gerr = cached("geo", log, "district polygons and label points for the map")
        svcmap = blank if gerr else service_map(rows, geo, year)
        r0 = rows[0] if rows else {}
        city_pct = pct(ui.num(r0.get("city_places_per_1k_act_2024")), ui.num(r0.get("city_places_per_1k_act")))
        meta = f"Year {year} · jobs weight w = {w:g} · today's timetable, no projects · source: MUNICH_DATASET on Exasol, read-only"
        return (svcmap, map_title, change_bars(rows, year, city_pct), change_title, gerr, meta, sql_log.entries(log), sql_log.summary(log))

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
