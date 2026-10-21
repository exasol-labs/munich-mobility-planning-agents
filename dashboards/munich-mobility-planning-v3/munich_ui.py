"""Shared look for the Munich dashboards: tokens, header, stat tiles, cards, chart theme, tables.

Copied unchanged into every app workspace next to app.py. Colours follow a validated
categorical order (CVD-safe adjacent pairs); never cycle a new hue, never a dual axis.
"""
from dash import dash_table, dcc, html
import plotly.graph_objects as go

FONT = "Inter, -apple-system, 'Segoe UI', Roboto, sans-serif"
STYLESHEETS = ["https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"]

# surfaces and ink
PAGE, SURFACE, LINE, GRID = "#f4f4f1", "#ffffff", "#e7e6e1", "#eeede9"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#8a8984"

# categorical slots in the validated order (light mode)
SLOTS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
# accent colour of the urban-planning dashboards
PERSONA = {"planning": "#2a78d6"}
# transit modes in stack order; night lines (<1 % of departures) are folded out of the charts
MODES = {"Bus": SLOTS[0], "Tram": SLOTS[1], "U-Bahn": SLOTS[2], "S-Bahn": SLOTS[3], "Regional rail": SLOTS[4]}
# sequential ramps, one hue each
RAMP_BLUE = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
RAMP_ORANGE = ["#fde4d8", "#f9bda3", "#f4956f", "#eb6834", "#c8502a", "#9f3d1f", "#742b15"]
RAMP_GREEN = ["#d7f3e6", "#a6e4c8", "#6fd1a8", "#1baf7a", "#15915f", "#0f6f49", "#0a4e33"]
RAMP_VIOLET = ["#e7e4f6", "#c8c1ea", "#a69bdc", "#7f71ce", "#5e4fb6", "#4a3aa7", "#342775"]
TEXTURE = "/"  # plotly marker pattern for the print / forced-colours case


def ramp_scale(ramp):
    n = len(ramp) - 1
    return [[i / n, c] for i, c in enumerate(ramp)]


def lower(rows):
    """Exasol returns upper-case keys; the apps address columns in lower case."""
    return [{str(k).lower(): v for k, v in r.items()} for r in rows]


def num(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def fmt(v, nd=0):
    return f"{num(v):,.{nd}f}"


CARD = {"background": SURFACE, "border": f"1px solid {LINE}", "borderRadius": "12px", "padding": "16px 18px",
        "boxShadow": "0 1px 2px rgba(11,11,11,.04)"}


def page(children, *, eyebrow, title, subtitle, accent, meta=None):
    """Page shell: coloured eyebrow + title band, then the children."""
    header = html.Div([
        html.Div([
            html.Div(eyebrow, style={"fontSize": "12px", "fontWeight": 600, "letterSpacing": ".08em", "textTransform": "uppercase", "color": accent}),
            html.H1(title, style={"margin": "4px 0 6px", "fontSize": "28px", "fontWeight": 700, "letterSpacing": "-.01em", "color": INK}),
            html.Div(subtitle, style={"fontSize": "14px", "color": INK2, "maxWidth": "820px", "lineHeight": 1.5}),
            html.Div(meta or "", id="page-meta", style={"fontSize": "12px", "color": MUTED, "marginTop": "8px"}),
        ], style={"borderLeft": f"4px solid {accent}", "paddingLeft": "16px"}),
    ], style={"padding": "4px 0 18px"})
    return html.Div([header, *children],
                    style={"fontFamily": FONT, "background": PAGE, "padding": "22px 28px 40px", "minHeight": "100vh", "color": INK,
                           "maxWidth": "1480px", "margin": "0 auto"})


def tile(label, value, note=None, accent=None):
    return html.Div([
        html.Div(label, style={"fontSize": "12px", "fontWeight": 500, "color": INK2, "letterSpacing": ".02em"}),
        html.Div(value, style={"fontSize": "30px", "fontWeight": 700, "color": INK, "marginTop": "6px", "letterSpacing": "-.02em",
                               "fontVariantNumeric": "tabular-nums", "lineHeight": 1.1}),
        html.Div(note or " ", style={"fontSize": "12px", "color": MUTED, "marginTop": "6px"}),
    ], style={**CARD, "flex": "1 1 190px", "minWidth": "180px", "borderTop": f"3px solid {accent or LINE}"})


def tiles(children):
    return html.Div(children, style={"display": "flex", "gap": "12px", "flexWrap": "wrap"})


def card(title, body, subtitle=None, flex="1 1 480px", min_width="320px"):
    kids = [html.H3(title, style={"margin": "0 0 2px", "fontSize": "15px", "fontWeight": 600, "color": INK})]
    if subtitle:
        kids.append(html.Div(subtitle, style={"fontSize": "12px", "color": MUTED, "marginBottom": "8px", "lineHeight": 1.45}))
    kids.append(html.Div(body, style={"marginTop": "6px"}))
    return html.Div(kids, style={**CARD, "flex": flex, "minWidth": min_width})


def row(children):
    return html.Div(children, style={"display": "flex", "gap": "12px", "flexWrap": "wrap", "marginTop": "12px"})


def block(child):
    return html.Div(child, style={"marginTop": "12px"})


def notes(title, items):
    return html.Details([
        html.Summary(title, style={"cursor": "pointer", "fontWeight": 600, "fontSize": "14px"}),
        html.Ul([html.Li(i) for i in items], style={"color": INK2, "fontSize": "13px", "lineHeight": 1.55, "margin": "8px 0 0"}),
    ], style={**CARD, "marginTop": "12px"})


def graph(id_, height=380, **kw):
    cfg = {"displayModeBar": False, "responsive": True}
    cfg.update(kw.pop("config", {}))
    return dcc.Loading(dcc.Graph(id=id_, config=cfg, style={"height": f"{height}px", "width": "100%"}), type="dot", color=MUTED)


def theme(fig, **kw):
    """Recessive axes and grid, legend on top, consistent hover card, thin rounded bars."""
    layout = {
        "paper_bgcolor": SURFACE, "plot_bgcolor": SURFACE,
        "font": {"family": FONT, "size": 12, "color": INK2},
        "margin": {"l": 8, "r": 8, "t": 8, "b": 36},
        "hoverlabel": {"bgcolor": INK, "bordercolor": INK, "font": {"family": FONT, "size": 12, "color": "#ffffff"}},
        "legend": {"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0, "font": {"size": 12}, "itemwidth": 30},
        "xaxis": {"gridcolor": GRID, "zerolinecolor": LINE, "linecolor": LINE, "tickfont": {"size": 11}, "title": {"font": {"size": 12, "color": MUTED}}},
        "yaxis": {"gridcolor": GRID, "zerolinecolor": LINE, "linecolor": LINE, "tickfont": {"size": 11}, "title": {"font": {"size": 12, "color": MUTED}}},
        "bargap": 0.28, "bargroupgap": 0.08, "barcornerradius": 4,
    }
    for k, v in kw.items():
        if isinstance(v, dict) and isinstance(layout.get(k), dict):
            layout[k] = {**layout[k], **v}
        else:
            layout[k] = v
    fig.update_layout(**layout)
    return fig


def empty(msg):
    fig = go.Figure()
    fig.add_annotation(text=msg, showarrow=False, font={"color": MUTED, "size": 13})
    return theme(fig, xaxis={"visible": False}, yaxis={"visible": False})


def map_layout(fig, center, zoom):
    fig.update_layout(map={"style": "carto-positron", "center": center, "zoom": zoom},
                      margin={"l": 0, "r": 0, "t": 0, "b": 0}, paper_bgcolor=SURFACE, font={"family": FONT, "size": 12},
                      hoverlabel={"bgcolor": INK, "bordercolor": INK, "font": {"family": FONT, "size": 12, "color": "#ffffff"}},
                      legend={"x": 0.01, "y": 0.99, "bgcolor": "rgba(255,255,255,.92)", "bordercolor": LINE, "borderwidth": 1, "font": {"size": 12}})
    return fig


def table(id_, columns, numeric_ids=(), highlight=None, page_size=25, accent=None):
    """DataTable with the shared type: left text, right numbers, zebra-free, accent on the key column."""
    cond = [{"if": {"column_id": list(numeric_ids)}, "textAlign": "right"}]
    if highlight:
        cond.append({"if": {"column_id": highlight}, "fontWeight": 700, "color": accent or INK})
    return dash_table.DataTable(
        id=id_, columns=columns, page_size=page_size, sort_action="native",
        style_table={"overflowX": "auto"},
        style_cell={"fontFamily": FONT, "fontSize": "13px", "padding": "7px 10px", "textAlign": "left", "whiteSpace": "normal",
                    "height": "auto", "maxWidth": "280px", "border": "none", "borderBottom": f"1px solid {GRID}", "color": INK},
        style_header={"fontWeight": 600, "fontSize": "12px", "color": INK2, "backgroundColor": SURFACE, "borderBottom": f"2px solid {LINE}",
                      "textTransform": "uppercase", "letterSpacing": ".03em"},
        style_data_conditional=cond,
        css=[{"selector": ".dash-table-container .previous-next-container", "rule": f"font-family: {FONT}; color: {INK2};"}],
    )


def error_panel(message):
    return html.Div([html.Strong("Exasol query failed"), html.Pre(message or "Unknown Exasol error", style={"whiteSpace": "pre-wrap"})],
                    style={"backgroundColor": "#fff4ec", "border": "1px solid #f4b48e", "borderRadius": "10px", "padding": "12px 14px", "fontSize": "13px"})


# ---------------------------------------------------------------------------------------------
# High-level helpers: one call per tile row, chart or table, so an app is ~80 lines, not 300.
# They only render; the queries and the choice of what to show are the app author's.
# ---------------------------------------------------------------------------------------------

def rows_or_error(result):
    """(rows, None) with lower-case keys, or ([], error_panel) when load_rows returned an error envelope."""
    if result and isinstance(result, list) and isinstance(result[0], dict) and result[0].get("_error"):
        return [], error_panel(result[0]["_error"])
    return lower(result or []), None


def kpi_tiles(row, specs, accent):
    """specs: [(label, column, note), ...]; note may use {column} placeholders from the same row.
    Numbers are formatted with thousands separators; a column ending in _pct is shown as a percentage."""
    out = []
    for label, col, note in specs:
        v = row.get(col)
        if col.endswith("_pct"):
            value = f"{num(v) * (100 if num(v) <= 1 else 1):.0f} %"
        elif isinstance(v, str) and not v.replace(".", "", 1).replace("-", "", 1).isdigit():
            value = v
        else:
            value = fmt(v, 1 if (num(v) % 1 and abs(num(v)) < 1000) else 0)
        try:
            note_txt = (note or "").format(**{k: fmt(x) if isinstance(x, (int, float)) or str(x).replace(".", "", 1).isdigit() else x
                                               for k, x in row.items()})
        except (KeyError, ValueError):
            note_txt = note or ""
        out.append(tile(label, value, note_txt, accent))
    return tiles(out)


def table_columns(spec):
    """spec: [(header, column, kind)], kind in {"text", "int", "num1", "num2"}."""
    return [{"name": h, "id": c, **({"type": "numeric"} if k != "text" else {})} for h, c, k in spec]


def table_data(rows, spec, limit=25):
    """Rows for a DataTable built from table_columns(spec); adds nothing, only formats numbers."""
    out = []
    for r in rows[:limit]:
        d = {}
        for _, c, k in spec:
            v = r.get(c)
            d[c] = (v if v is not None else "-") if k == "text" else (int(round(num(v))) if k == "int" else round(num(v), 1 if k == "num1" else 2))
        out.append(d)
    return out


def ranked_table(id_, spec, accent, highlight=None, page_size=25):
    numeric = tuple(c for _, c, k in spec if k != "text")
    return table(id_, table_columns(spec), numeric_ids=numeric, highlight=highlight, accent=accent, page_size=page_size)


def hbar(rows, label, value, color, x_title, hover=None, top=None):
    """Horizontal bar, largest on top. hover: optional extra hover text per row (callable row -> str)."""
    rs = sorted(rows, key=lambda r: num(r.get(value)))[-(top or len(rows)):]
    fig = go.Figure(go.Bar(
        x=[num(r.get(value)) for r in rs], y=[str(r.get(label) or "-") for r in rs], orientation="h", marker={"color": color},
        hovertext=[f"<b>{r.get(label)}</b><br>{fmt(r.get(value), 1)}" + (f"<br>{hover(r)}" if hover else "") for r in rs], hoverinfo="text"))
    return theme(fig, showlegend=False, xaxis={"title": x_title}, yaxis={"automargin": True, "tickfont": {"size": 10}}, bargap=0.3)


def series_bar(rows, x, series, value, colors, y_title, stacked=True, horizontal=False, order=None):
    """Bars per category x, one trace per series value, colours by series name (fixed, never cycled)."""
    fig = go.Figure()
    cats = order or list(dict.fromkeys(str(r.get(x)) for r in rows))
    for s, color in colors.items():
        sub = {str(r.get(x)): num(r.get(value)) for r in rows if r.get(series) == s}
        if not sub:
            continue
        vals = [sub.get(c, 0) for c in cats]
        kw = {"y": cats, "x": vals, "orientation": "h"} if horizontal else {"x": cats, "y": vals}
        fig.add_bar(name=s, marker={"color": color, "line": {"width": 1, "color": SURFACE}},
                    hovertemplate=f"<b>%{{{'y' if horizontal else 'x'}}}</b><br>{s}: %{{{'x' if horizontal else 'y'}:,.1f}}<extra></extra>", **kw)
    axis = {"categoryorder": "array", "categoryarray": cats[::-1] if horizontal else cats, "automargin": True, "tickfont": {"size": 10}}
    return theme(fig, barmode="stack" if stacked else "group",
                 **({"yaxis": axis, "xaxis": {"title": y_title}} if horizontal else {"xaxis": {**axis, "tickangle": -30}, "yaxis": {"title": y_title}}))


def lines(rows, x, series, value, colors, y_title, markers=False):
    """One line per series on one y-axis (never a second axis); unified hover."""
    fig = go.Figure()
    for s, color in colors.items():
        sub = [r for r in rows if r.get(series) == s]
        if sub:
            fig.add_scatter(x=[r.get(x) for r in sub], y=[num(r.get(value)) for r in sub], name=str(s),
                            mode="lines+markers" if markers else "lines", line={"color": color, "width": 2 if markers else 1.6},
                            marker={"size": 7}, hovertemplate=f"{s}: %{{y:,.0f}}<extra></extra>")
    return theme(fig, hovermode="x unified", yaxis={"title": y_title})


def points_map(rows, lat, lon, color_col, hover, ramp, cmax=None, size_col=None, context=None, center=None, zoom=11, name=""):
    """Points coloured by a magnitude on a one-hue ramp, optional grey context layer
    (context = (rows, lat, lon, hover_fn)). hover: callable row -> str."""
    fig = go.Figure()
    if context:
        crows, clat, clon, chover = context
        fig.add_trace(go.Scattermap(lat=[num(r.get(clat)) for r in crows], lon=[num(r.get(clon)) for r in crows], mode="markers",
                                    name="context", marker={"size": 5, "color": INK2, "opacity": 0.28},
                                    text=[chover(r) for r in crows], hoverinfo="text", showlegend=False))
    rs = sorted(rows, key=lambda r: num(r.get(color_col)))
    vals = [num(r.get(color_col)) for r in rs]
    top = cmax or (max(vals) if vals else 1)
    sizes = [6 + 14 * num(r.get(size_col or color_col)) / (max(num(x.get(size_col or color_col)) for x in rs) or 1) for r in rs] if rs else []
    fig.add_trace(go.Scattermap(lat=[num(r.get(lat)) for r in rs], lon=[num(r.get(lon)) for r in rs], mode="markers", name=name,
                                marker={"size": sizes, "color": vals, "colorscale": ramp_scale(ramp), "cmin": 0, "cmax": top, "opacity": 0.9,
                                        "colorbar": {"thickness": 10, "len": 0.5, "x": 0.99}},
                                text=[hover(r) for r in rs], hoverinfo="text", showlegend=False))
    return map_layout(fig, center or {"lat": 48.139, "lon": 11.575}, zoom)


def scatter(rows, x, y, size_col, label, flag_col, colors, x_title, y_title, hover):
    """Scatter: x, y, marker size from size_col; colour split by a 0/1 flag column; flagged points labelled directly."""
    fig = go.Figure()
    for flag, (name, color) in enumerate(colors):
        sub = [r for r in rows if int(num(r.get(flag_col))) == flag]
        top = max((num(r.get(size_col)) for r in rows), default=1) or 1
        fig.add_trace(go.Scatter(x=[num(r.get(x)) for r in sub], y=[num(r.get(y)) for r in sub], mode="markers+text" if flag else "markers",
                                 name=name, text=[str(r.get(label))[:18] for r in sub] if flag else None, textposition="top center",
                                 textfont={"size": 10, "color": INK2},
                                 marker={"size": [10 + 24 * num(r.get(size_col)) / top for r in sub], "color": color, "opacity": 0.85,
                                         "line": {"width": 2, "color": SURFACE}},
                                 hovertext=[hover(r) for r in sub], hoverinfo="text"))
    return theme(fig, xaxis={"title": x_title}, yaxis={"title": y_title})


def heatmap(rows, x, y, value, ramp, x_labels, y_labels, x_title=""):
    """Grid heatmap, ramp from near-zero to max; gaps between cells."""
    grid = {(str(r.get(y)), str(r.get(x))): num(r.get(value)) for r in rows}
    z = [[grid.get((str(yy), str(xx)), 0) for xx in x_labels] for yy in y_labels]
    fig = go.Figure(go.Heatmap(z=z, x=[str(v) for v in x_labels], y=[str(v) for v in y_labels], colorscale=ramp_scale(ramp), xgap=2, ygap=2,
                               colorbar={"thickness": 10}, hovertemplate="%{y} %{x}: %{z:,.0f}<extra></extra>"))
    return theme(fig, xaxis={"title": x_title, "gridcolor": SURFACE}, yaxis={"autorange": "reversed", "gridcolor": SURFACE})
