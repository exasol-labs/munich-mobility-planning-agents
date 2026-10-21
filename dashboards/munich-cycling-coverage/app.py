"""Munich Cycling Coverage: weighted cycle-network km per district, per 1,000 residents + w x jobs (2024-2045)
or per km2, against the city average, with the bicycle counters as measured context. Supply only. Metric units."""
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
NOW_YEAR = 2026
YEARS = (2024, 2045)
RATIO_LO, RATIO_HI = 0.4, 2.5
Z_HALF = math.log2(RATIO_HI)  # log2(0.4) is about -log2(2.5): symmetric around 1.0
RATIO_SCALE = [[0.0, ui.RAMP_ORANGE[5]], [0.22, ui.RAMP_ORANGE[3]], [0.42, ui.RAMP_ORANGE[1]], [0.5, "#dedcd6"],
               [0.58, ui.RAMP_BLUE[1]], [0.78, ui.RAMP_BLUE[3]], [1.0, ui.RAMP_BLUE[5]]]
RATIO_TICKS = (0.5, 0.75, 1, 1.5, 2)
DENSE_LABEL = "dense (top third by activity/km²)"
COORD = re.compile(r"(-?\d+(?:\.\d+)?(?:[eE]-?\d+)?)\s+(-?\d+(?:\.\d+)?(?:[eE]-?\d+)?)")
LENSES = [("person", "per person"), ("area", "per km²")]
# (placeholder, path_type base as in the data, label, default weight)
WEIGHTS = [("w_radweg", "Radweg", "Radweg (cycle track)", 1.0),
           ("w_fahrradstrasse", "Fahrradstraße", "Fahrradstraße (cycle street)", 1.0),
           ("w_getrennt", "Getrennter Rad- und Gehweg", "Getrennter Rad- und Gehweg (separated cycle and footpath)", 0.8),
           ("w_streifen", "Radfahr-/Schutzstreifen", "Radfahr-/Schutzstreifen (painted lane)", 0.6),
           ("w_gemeinsam", "Gemeinsamer Geh- und Radweg", "Gemeinsamer Geh- und Radweg (shared footpath)", 0.5),
           ("w_gehweg", "Gehweg Radverkehr frei", "Gehweg Radverkehr frei (footway, cycling allowed)", 0.3)]
CLASSES = {"Cycle track and cycle street": ui.SLOTS[0], "Separated cycle and footpath": ui.SLOTS[2],
           "Painted lane": ui.SLOTS[3], "Shared footpath": ui.SLOTS[1]}
COUNTER_COLOR = ui.RAMP_GREEN[5]
CAVEAT = ("Supply only: network length and path type, not width, surface, continuity, safety or traffic. "
          "Counters measure at 5 points only (Jan–Jul 2026; Arnulfstraße to April; Margaretenstraße no data). "
          "Residents interpolated to the 2045 forecast. Jobs: the 2022 estimate as the 2024 baseline, rising to the 2040 forecast, held after. "
          "Path weights are assumptions. Two-way paths count twice; connectors (Übergang, Anschlussabschnitt) and Dummy segments are excluded.")


def wkt_to_geometry(wkt):
    """WGS84 POLYGON / MULTIPOLYGON WKT (lon lat) to a GeoJSON geometry, no extra dependency."""
    text = (wkt or "").strip()
    kind = "MultiPolygon" if text.upper().startswith("MULTIPOLYGON") else "Polygon"
    body = COORD.sub(r"[\1,\2]", text[text.index("("):]).replace("(", "[").replace(")", "]")
    return {"type": kind, "coordinates": json.loads(body)}


def short_name(name):
    name = str(name or "")
    return name if len(name) <= 22 else name.split("-")[0] + "-…"


def clean_weight(v, default):
    """Path weights are numeric placeholders: anything outside 0-1 or not a number falls back to the default."""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return default
    if math.isnan(f) or not (0.0 <= f <= 1.0):
        return default
    return round(f, 2)


def w_text(w):
    return f"{w:.1f}" if abs(w * 10 - round(w * 10)) < 1e-9 else f"{w:.2f}"


def ratio_col(lens):
    return "ratio_area" if lens == "area" else "ratio_person"


def counter_traces(fig, counters):
    have = [c for c in counters if ui.num(c.get("n_days")) > 0]
    none = [c for c in counters if ui.num(c.get("n_days")) <= 0]
    top = max((ui.num(c.get("avg_per_day")) for c in have), default=1) or 1
    sizes = [10 + 18 * math.sqrt(ui.num(c.get("avg_per_day")) / top) for c in have]

    def hover(c):
        return (f"<b>Counter {c['station_name']}</b><br>{ui.fmt(c.get('avg_per_day'))} bikes per day on average<br>"
                f"rain penalty {ui.num(c.get('rain_penalty_pct')):.0f} % (days with more than 1 mm rain vs dry days)<br>"
                f"data {c.get('first_day')} to {c.get('last_day')} ({int(ui.num(c.get('n_days')))} days)")
    if have:
        lat = [ui.num(c["lat"]) for c in have]
        lon = [ui.num(c["lon"]) for c in have]
        fig.add_trace(go.Scattermap(lat=lat, lon=lon, mode="markers", marker={"size": [s + 4 for s in sizes], "color": ui.SURFACE},
                                    hoverinfo="skip", showlegend=False))
        fig.add_trace(go.Scattermap(lat=lat, lon=lon, mode="markers", marker={"size": sizes, "color": COUNTER_COLOR},
                                    name="bicycle counter, sized by bikes/day (measured at 5 points only)",
                                    text=[hover(c) for c in have], hoverinfo="text"))
    if none:
        lat = [ui.num(c["lat"]) for c in none]
        lon = [ui.num(c["lon"]) for c in none]
        fig.add_trace(go.Scattermap(lat=lat, lon=lon, mode="markers", marker={"size": 14, "color": COUNTER_COLOR},
                                    name="counter without data", text=[f"<b>Counter {c['station_name']}</b><br>no data" for c in none],
                                    hoverinfo="text"))
        fig.add_trace(go.Scattermap(lat=lat, lon=lon, mode="markers", marker={"size": 8, "color": ui.SURFACE},
                                    hoverinfo="skip", showlegend=False))


def coverage_map(rows, geo, counters, lens):
    """A fresh figure every call (no uirevision), so a control change always redraws the drawn data."""
    gj = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "id": str(int(ui.num(g["district_no"]))), "properties": {"name": g["district"]},
         "geometry": wkt_to_geometry(g["polygon_wkt"])} for g in geo]}
    cent = {str(int(ui.num(g["district_no"]))): g for g in geo}
    col = ratio_col(lens)
    ids = [str(int(ui.num(r["district_no"]))) for r in rows]
    ratio = [ui.num(r.get(col), 1.0) for r in rows]
    z = [math.log2(min(max(v, RATIO_LO), RATIO_HI)) for v in ratio]
    year = int(ui.num(rows[0].get("year_n"))) if rows else NOW_YEAR
    hover = [(f"<b>{r['district']}</b><br>"
              f"per person ({year}): {ui.num(r.get('ratio_person')):.2f}× the 2024 city average · "
              f"per km²: {ui.num(r.get('ratio_area')):.2f}× the city average<br>"
              f"{ui.fmt(r['population'])} residents, {ui.fmt(r['jobs'])} jobs, {ui.fmt(r['activity'])} activity ({year})<br>"
              f"{ui.num(r.get('weighted_km')):,.1f} km weighted network · {ui.num(r.get('raw_km')):,.1f} km raw path length<br>"
              f"{ui.num(r.get('km_per_1k_act')):.3f} km per 1,000 activity · {ui.fmt(r.get('m_per_km2'))} m per km²<br>"
              f"high-quality paths (cycle track, cycle street, separated): {ui.num(r.get('hq_share_pct')):.0f} %")
             for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Choroplethmap(
        geojson=gj, locations=ids, z=z, featureidkey="id", colorscale=RATIO_SCALE, zmin=-Z_HALF, zmax=Z_HALF, zmid=0,
        marker={"opacity": 0.85, "line": {"color": ui.SURFACE, "width": 1}}, hovertext=hover, hoverinfo="text",
        name="weighted network vs city average", showlegend=False,
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
    counter_traces(fig, counters)
    return ui.map_layout(fig, {"lat": 48.152, "lon": 11.548}, 9.85)


def pathmix_chart(mix, rows, lens):
    col = ratio_col(lens)
    order_rows = sorted(rows, key=lambda r: ui.num(r.get(col)))
    label = {int(ui.num(r["district_no"])): f"{short_name(r['district'])} {ui.num(r.get(col)):.2f}×" for r in order_rows}
    data = [{"label": label[int(ui.num(m["district_no"]))], "path_class": m["path_class"], "km": m["km"]}
            for m in mix if int(ui.num(m["district_no"])) in label]
    fig = ui.series_bar(data, "label", "path_class", "km", CLASSES, "km of cycle path (two-way counted twice)",
                        stacked=True, horizontal=True, order=[label[int(ui.num(r["district_no"]))] for r in order_rows])
    fig.update_layout(margin={"l": 8, "r": 8, "t": 40, "b": 36})
    return fig


def create_dash_app(server, url_base_pathname, metadata):
    app = Dash(__name__, server=server, routes_pathname_prefix="/",
               requests_pathname_prefix=url_base_pathname.rstrip("/") + "/",
               title=metadata.get("title", "Munich Cycling Coverage"), external_stylesheets=ui.STYLESHEETS)
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
    hint = {"fontSize": "12px", "color": ui.MUTED}
    weight_inputs = html.Div([
        html.Div([
            dcc.Input(id=f"wt-{key}", type="number", min=0, max=1, step=0.1, value=default, debounce=True,
                      style={"width": "70px", "fontSize": "13px", "padding": "2px 6px", "marginRight": "8px"}),
            html.Span(f"{text} · default {default:g}", style={"fontSize": "13px", "color": ui.INK2}),
        ], style={"marginBottom": "6px"}) for key, _, text, default in WEIGHTS])
    year_marks = {y: str(y) for y in (2024, 2030, 2035, 2040, 2045)}
    year_marks[NOW_YEAR] = {"label": "now", "style": {"fontWeight": 600, "color": ui.INK, "whiteSpace": "nowrap"}}

    app.layout = ui.page([
        dcc.Store(id="w-store", data=1.0),
        dcc.Markdown(
            "**The map shows how much cycle network each district has, weighted by path quality, against the city average.** "
            "*Per person* divides it by residents + w × jobs in the selected year and compares with the 2024 city average, so growth "
            "without new paths darkens the map. *Per km²* compares network density by area and does not change with the year. "
            "This is supply only (length and type of path from the city's network data), not use or safety. "
            "Green dots are the bicycle counters: measured demand, but at 5 points only.",
            style={**ui.CARD, "marginBottom": "12px", "fontSize": "14px", "color": ui.INK2, "lineHeight": 1.5}),
        html.Div([
            html.Div([
                html.Div("Year", style=label),
                dcc.Slider(id="year", min=YEARS[0], max=YEARS[1], step=1, value=NOW_YEAR, marks=year_marks),
            ], style={"flex": "3 1 420px", "minWidth": "300px"}),
            html.Div([
                html.Div("Lens", style=label),
                dcc.RadioItems(id="lens", options=[{"label": f" {t}", "value": v} for v, t in LENSES], value="person", inline=True,
                               inputStyle={"marginLeft": "12px"}, style={"fontSize": "13px", "marginTop": "6px"}),
            ], style={"flex": "1 1 200px"}),
            html.Div([
                html.Div("Job weight (w)", style=label),
                dcc.Input(id="w-input", type="number", min=0, max=1.5, step=0.25, value=1.0, debounce=True,
                          style={"width": "80px", "fontSize": "13px", "padding": "2px 6px", "marginTop": "4px"}),
                html.Div("Activity = residents + w × jobs, 0 to 1.5 in steps of 0.25. Per-person lens only.", style=hint),
            ], style={"flex": "1 1 240px"}),
        ], style={**ui.CARD, "marginBottom": "12px", "display": "flex", "gap": "18px", "flexWrap": "wrap", "alignItems": "flex-start"}),
        html.Details([
            html.Summary([html.Span("Path weights", style={"fontSize": "15px", "fontWeight": 600, "color": ui.INK}),
                          html.Span(id="wt-status", style={"fontSize": "13px", "color": ui.INK2, "marginLeft": "10px"})],
                         style={"cursor": "pointer", "marginBottom": "8px"}),
            html.Div("How much one km of each path type counts (0 to 1, step 0.1). These are assumptions; a value outside 0–1 falls back to the default.",
                     style={**hint, "marginBottom": "8px"}),
            weight_inputs,
            html.Button("Reset weights", id="wt-reset", n_clicks=0,
                        style={"fontSize": "13px", "padding": "4px 10px", "border": f"1px solid {ui.LINE}", "borderRadius": "6px",
                               "background": ui.SURFACE, "cursor": "pointer", "marginTop": "4px"}),
        ], id="wt-details", open=False, style={**ui.CARD, "marginBottom": "12px"}),
        ui.card(html.Span("How well is each district served for cycling?", id="map-title"),
                html.Div([ui.graph("covmap", 640), html.Div(id="err")]),
                "Weighted cycle-network km relative to the city average, log colour scale centred on 1.0× (clamped 0.4–2.5). "
                "Thick outline: dense districts. Hover a district for the raw numbers, a counter for its measured demand.",
                flex="1 1 100%"),
        ui.block(ui.card(html.Span("Path-quality mix", id="mix-title"), ui.graph("pathmix", 720),
                         "km of cycle path by class, two-way paths counted twice, connectors excluded; districts sorted by the map's ratio "
                         "(lowest on top). Cycle track and cycle street = Radweg, Fahrradstraße; painted lane = Radfahr-/Schutzstreifen; "
                         "shared footpath = Gemeinsamer Geh- und Radweg, Gehweg Radverkehr frei.",
                         flex="1 1 100%")),
        html.Div(CAVEAT, style={"fontSize": "12px", "color": ui.MUTED, "marginTop": "10px", "lineHeight": 1.45}),
        sql_log.foldout(),
    ], eyebrow="Urban planning", title="Munich Cycling Coverage", accent=ACCENT,
        subtitle="How well is each district served for cycling? Cycle-network supply per person or per km², 2024 to 2045, "
                 "with the bicycle counters as measured context.")

    @app.callback(Output("covmap", "figure"), Output("map-title", "children"), Output("pathmix", "figure"), Output("mix-title", "children"),
                  Output("err", "children"), Output("page-meta", "children"), Output("wt-status", "children"),
                  Output("sql-dash", "children"), Output("sql-sum-dash", "children"),
                  Input("year", "value"), Input("lens", "value"), Input("w-store", "data"),
                  *[Input(f"wt-{key}", "value") for key, _, _, _ in WEIGHTS])
    def refresh(year, lens, w, *weights):
        log = []
        year = min(max(int(year if year is not None else NOW_YEAR), YEARS[0]), YEARS[1])
        lens = lens if lens in ("person", "area") else "person"
        w = float(w if w is not None else 1.0)
        wts = {key: clean_weight(v, default) for (key, _, _, default), v in zip(WEIGHTS, weights)}
        params = {"year": year, "w_jobs": w, **wts}
        changed = [k for k, _, _, d in WEIGHTS if abs(wts[k] - d) > 1e-9]
        wt_status = "defaults" if not changed else f"{len(changed)} changed from the default"
        lens_txt = dict(LENSES)[lens]
        title = (f"How well is each district served for cycling? – {year} ({lens_txt})" if lens == "person"
                 else f"How well is each district served for cycling? – {lens_txt} (does not change with the year)")
        rows, err = q("cycling", params, log, "per-district weighted network, activity and both ratios for the map and the mix order")
        geo, gerr = cached("geo", log, "district polygons and label points for the map")
        counters, cerr = cached("counters", log, "counter markers: average per day, rain penalty, data period")
        mix, merr = cached("pathmix", log, "km by path class per district for the path-quality mix")
        blank = ui.empty("")
        if err:
            return (blank, title, blank, "Path-quality mix", err, "", wt_status, sql_log.entries(log), sql_log.summary(log))
        fig = blank if gerr else coverage_map(rows, geo, [] if cerr else counters, lens)
        mixfig = blank if merr else pathmix_chart(mix, rows, lens)
        r0 = rows[0] if rows else {}
        city = (f"city {ui.num(r0.get('city_weighted_km')):,.1f} weighted km of {ui.num(r0.get('city_raw_km')):,.1f} km raw path length; "
                + (f"2024 average {ui.num(r0.get('city_km_per_1k_act_2024')):.3f} km per 1,000 activity at w = {w_text(w)}"
                   if lens == "person" else f"average {ui.fmt(r0.get('city_m_per_km2'))} m per km²"))
        meta = (f"Year {year} · lens {lens_txt} · w = {w_text(w)}{' (not used in this lens)' if lens == 'area' else ''} · "
                f"path weights {wt_status} · {city} · source: MUNICH_DATASET on Exasol, read-only")
        mix_title = f"Path-quality mix – sorted by ratio ({lens_txt}{', ' + str(year) if lens == 'person' else ''})"
        return (fig, title, mixfig, mix_title, gerr or cerr or merr, meta, wt_status, sql_log.entries(log), sql_log.summary(log))

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

    @app.callback(Output("w-input", "disabled"), Input("lens", "value"), prevent_initial_call=True)
    def w_enabled(lens):
        return lens == "area"

    @app.callback([Output(f"wt-{key}", "value") for key, _, _, _ in WEIGHTS], Input("wt-reset", "n_clicks"), prevent_initial_call=True)
    def reset_weights(_):
        return [default for _, _, _, default in WEIGHTS]

    return app
