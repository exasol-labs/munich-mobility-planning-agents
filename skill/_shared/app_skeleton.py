"""Skeleton for a Munich tutorial dashboard on Dash Server (about 80 lines when filled in).

Put it in the app with app_put_files as app.py, next to munich_ui.py and your queries/*.sql.
Replace every TODO; delete the parts the persona does not need. The helpers in munich_ui.py
only render: what each query computes and what each chart says is your design.

Host rules: a create_dash_app factory, callbacks on `app`, no query at import time,
every query in queries/*.sql through load_rows, pyexasol placeholders ({horizon!d}).
"""
from dash import Dash, Input, Output, dcc, html

from dash_server_exasol import load_rows
import munich_ui as ui

ACCENT = ui.PERSONA["planning"]

TABLE = [  # TODO: (header, column, kind) with kind text | int | num1 | num2
    ("Name", "name", "text"), ("Value", "value", "int"), ("Score", "score", "num2"),
]


def create_dash_app(server, url_base_pathname, metadata):
    app = Dash(__name__, server=server, routes_pathname_prefix="/",
               requests_pathname_prefix=url_base_pathname.rstrip("/") + "/",
               title=metadata.get("title", "Munich dashboard"), external_stylesheets=ui.STYLESHEETS)

    def q(name, params=None):
        return ui.rows_or_error(load_rows(server, metadata, __file__, f"queries/{name}.sql", params=params))

    app.layout = ui.page([
        # TODO: a control if the persona needs one, else dcc.Interval(id="boot", max_intervals=1, interval=200)
        dcc.RadioItems(id="horizon", options=[{"label": f" {d} days", "value": d} for d in (7, 14, 28)], value=28, inline=True,
                       inputStyle={"marginLeft": "12px"}, style={"fontSize": "13px", "marginBottom": "14px"}),
        html.Div(id="kpis"),
        ui.row([
            ui.card("TODO map or main chart", ui.graph("main", 520), "TODO one line on how to read it", flex="2 1 560px"),
            ui.card("TODO second chart", ui.graph("side", 520), "TODO one line", flex="1 1 360px"),
        ]),
        ui.block(ui.card("TODO ranked table", html.Div([ui.ranked_table("ranking", TABLE, ACCENT, highlight="score"), html.Div(id="err")]),
                         "TODO the score formula in one sentence", flex="1 1 100%")),
        ui.notes("Method and data gaps", ["TODO method in one line", "TODO what the data cannot answer"]),
    ], eyebrow="TODO persona", title="TODO title", accent=ACCENT, subtitle="TODO the question, plus the main caveat.")

    @app.callback(Output("kpis", "children"), Output("main", "figure"), Output("side", "figure"),
                  Output("ranking", "data"), Output("err", "children"), Output("page-meta", "children"),
                  Input("horizon", "value"))
    def refresh(horizon):
        p = {"horizon": int(horizon or 28)}
        k, err = q("kpis", p)
        if err:
            return err, ui.empty(""), ui.empty(""), [], err, ""
        kpis = ui.kpi_tiles(k[0], [  # TODO: (label, column, note with {column} placeholders)
            ("TODO label", "todo_column", "TODO note"),
        ], ACCENT)

        rows, err = q("ranking", p)  # TODO: ranked rows with lat/lon if mapped
        if err:
            return kpis, ui.empty(""), ui.empty(""), [], err, ""
        main = ui.points_map(rows, "lat", "lon", "score", lambda r: f"<b>{r['name']}</b><br>score {ui.num(r['score']):.2f}", ui.RAMP_ORANGE)
        side = ui.hbar(rows, "name", "score", ACCENT, "TODO axis title", top=15)
        meta = f"Reference weekday {k[0].get('ref_weekday', '')} · source: MUNICH_DATASET on Exasol, read-only"
        return kpis, main, side, ui.table_data(rows, TABLE), None, meta

    return app
