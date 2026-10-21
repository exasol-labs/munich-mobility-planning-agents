"""'SQL executed' foldout (same look as v5): every statement the current view ran, or still depends on from the cache.

run() times one query and returns an entry; the app's main callback collects the entries of one render in a local list
and returns entries() and summary() as two extra outputs. The SQL text is formatted with pyexasol's own ExaFormatter:
dash-server calls connection.execute(sql_text, params or {}), which formats with exactly this class before sending, so
the text shown is the text sent. No credentials are part of it."""
import time
from pathlib import Path
from types import SimpleNamespace

from dash import html

import munich_ui as ui

QUERY_DIR = Path(__file__).resolve().parent / "queries"
try:  # pyexasol's own formatter, the one the server's connection uses
    from pyexasol.formatter import ExaFormatter
    _FMT = ExaFormatter(SimpleNamespace(options={"quote_ident": False}))
except Exception:  # pragma: no cover
    _FMT = None

CODE = {"whiteSpace": "pre", "fontSize": "11px", "fontFamily": "ui-monospace, SFMono-Regular, Menlo, monospace", "background": "#f4f3ef",
        "padding": "8px 10px", "borderRadius": "6px", "margin": "4px 0 2px", "maxHeight": "320px", "overflow": "auto", "userSelect": "text"}


def render_sql(name, params):
    """The statement as sent: placeholders substituted exactly as pyexasol does ({x!d}, {x!f}, {x!s} with quotes doubled)."""
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


def run(fn, name, params, purpose):
    """Time fn() -> (rows, err); return (rows, err, entry)."""
    t0 = time.time()
    rows, err = fn()
    secs = time.time() - t0
    entry = {"file": f"{name}.sql", "purpose": purpose, "params": fmt_params(params), "sql": render_sql(name, params),
             "rows": None if err else len(rows or []), "secs": secs, "cached": False, "ran_at": time.strftime("%H:%M:%S", time.localtime(t0)),
             "error": "the query returned an error (see the panel above)" if err else None}
    return rows, err, entry


def as_cached(entry, purpose=None):
    """The same statement, served from the cache for this view."""
    return {**entry, "secs": 0.0, "cached": True, "purpose": purpose or entry["purpose"]}


def foldout():
    """Very bottom of the page, folded by default. Native <details>: opening it never scrolls by code."""
    return html.Details([
        html.Summary([html.Span("SQL executed", style={"fontSize": "15px", "fontWeight": 600, "color": ui.INK}),
                      html.Span(id="sql-sum-dash", style={"fontSize": "13px", "color": ui.INK2})],
                     style={"cursor": "pointer"}),
        html.Div("Every statement as sent to Exasol (read-only user), placeholders substituted with pyexasol's formatter, the same "
                 "code the server uses. Cached statements show when they ran.", style={"fontSize": "12px", "color": ui.MUTED, "margin": "6px 0"}),
        html.H4("Dashboard queries for the current view", style={"margin": "10px 0 2px", "fontSize": "13px", "color": ui.INK}),
        html.Div(id="sql-dash"),
    ], id="sql-details", open=False, style={**ui.CARD, "marginTop": "12px"})


def sql_entry(e):
    meta = []
    if e.get("params"):
        meta.append(e["params"])
    if e.get("rows") is not None:
        meta.append(f"{e['rows']:,} row(s)")
    meta.append(f"cached, ran at {e.get('ran_at')}" if e.get("cached") else f"{e.get('secs', 0):.2f} s")
    head = [html.Code(e.get("file", ""), style={"fontWeight": 600}), html.Span(f" — {e.get('purpose') or ''}", style={"color": ui.INK2})]
    lines = [html.Div(head, style={"fontSize": "12px"}), html.Div(" · ".join(meta), style={"fontSize": "11px", "color": ui.MUTED})]
    if e.get("error"):
        lines.append(html.Div(f"failed: {e['error']}", style={"fontSize": "12px", "color": "#9f3d1f"}))
    lines.append(html.Details([html.Summary("SQL as sent to Exasol", style={"cursor": "pointer", "fontSize": "11px", "color": ui.INK2}),
                               html.Pre(e.get("sql") or "", style=CODE)]))
    return html.Div(lines, style={"padding": "6px 0", "borderTop": f"1px solid {ui.LINE}"})


def entries(log):
    return [sql_entry(e) for e in log]


def summary(log):
    secs = sum(e.get("secs") or 0 for e in log)
    return f" · {len(log)} statement{'s' if len(log) != 1 else ''} for this view · {secs:.1f} s"
