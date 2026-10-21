"""v5 Ask-the-assistant: an OpenAI Responses API tool loop over the Munich planning data.

Key lookup:
  1. OPENAI_API_KEY in the process environment.
  2. ~/.exasol-starter-kit/credentials/openai_api_key, owner-readable only (mode 600).
The key is read at runtime only. It is never logged, never returned to the page and never in source.

Tools: run_sql (one guarded, read-only SELECT through the app's profile, user mcp_readonly), dashboard_scenario (the dashboard's own ranking.sql),
what_if (hypothetical extra places per district, fed to ranking.sql through {extra!s}), set_view (what this viewer's
map and change chart show), plus OpenAI's built-in web search.

Jobs run in a background thread per browser session; the page polls snapshot() once a second.
"""
import json
import math
import os
import re
import stat
import threading
import time
import uuid
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

MODEL = "gpt-6-astra"
REASONING_EFFORT = "medium"
MAX_OUTPUT_TOKENS = 32000
MAX_TOOL_ROUNDS = 12
JOB_TIMEOUT_S = 600
REQUEST_TIMEOUT_S = 300
HISTORY_TOKEN_CAP = 150_000
SESSION_IDLE_S = 4 * 3600
ROW_CAP = 200
SCHEMA = "MUNICH_DATASET"
PRICES = {"input": 10.00, "cached": 1.00, "output": 50.00}  # US$ per 1M tokens, gpt-6-astra standard

CRED_DIR = Path.home() / ".exasol-starter-kit" / "credentials"
KEY_FILE = str(CRED_DIR / "openai_api_key")
CONTEXT_FILE = Path(__file__).resolve().parent / "context.md"

SETUP_LINE = ("The assistant needs an OpenAI API key. Put it in secrets/openai_api_key in the tutorial repo "
              "(see secrets/README.md), run python3 install.py, then reload this page.")
NO_CREDITS = "The OpenAI account has no credits. Add credits at platform.openai.com → Billing."
DECLINED = "The assistant declined or gave no answer."

CLIENT_FACTORY = None  # tests may set a callable(key) -> client; default builds openai.OpenAI

YEARS = (2024, 2045)
PRESET_NAMES = ("none", "funded", "funded_planned", "everything")
MODES = ("Bus", "Tram", "U-Bahn", "S-Bahn", "Regional rail")


# ------------------------------------------------------------------ key lookup
def read_key():
    """(key, error). Never returns the key in the error, and never logs it."""
    key = os.environ.get("OPENAI_API_KEY")
    if key:
        return key.strip(), None
    try:
        info = os.stat(KEY_FILE)
    except OSError:
        return None, None                      # not configured; not an error
    if os.name != "nt" and info.st_mode & (stat.S_IRGRP | stat.S_IROTH):
        return None, f"{KEY_FILE} is readable by other users. Run: chmod 600 {KEY_FILE}"
    try:
        with open(KEY_FILE, encoding="utf-8") as handle:
            key = handle.read().strip()
    except OSError as exc:
        return None, f"could not read the key file: {exc.strerror}"
    return (key, None) if key else (None, "the key file is empty")


def key_status():
    """(configured: bool, message or None) for the panel. Never exposes the key."""
    key, err = read_key()
    if err:
        return False, err
    return (True, None) if key else (False, SETUP_LINE)


# ------------------------------------------------------------------ SQL guard
# One bounded, read-only SELECT on the schema. This dataset's documented style writes MUNICH_DATASET.TABLE unquoted
# and analysts use CTEs, so (1) the schema/table pair may be quoted or unquoted, and (2) names defined as CTEs in the
# statement, and DUAL, count as known sources. The row cap is enforced by fetching at most ROW_CAP rows, so ORDER BY in the query keeps its meaning.
FORBIDDEN = re.compile(
    r"\b(insert|update|delete|merge|drop|create|alter|truncate|grant|revoke|"
    r"commit|rollback|call|execute|import|export)\b", re.I)
SYSTEM_OBJECTS = re.compile(r'\b(?:"?SYS"?\s*\.|EXA_[A-Z_]+)', re.I)


def guard(sql, schema=SCHEMA):
    """Return (safe_sql, error). Rejects anything that is not one bounded SELECT on the schema."""
    if not sql or not sql.strip():
        return None, "empty query"
    text = sql.strip().rstrip(";").strip()
    if ";" in text:
        return None, "rejected: more than one statement"
    if "--" in text or "/*" in text:
        return None, "rejected: comments can hide a second statement"
    if not re.match(r"^(select|with)\b", text, re.I):
        return None, "rejected: only SELECT is allowed"
    if FORBIDDEN.search(text):
        return None, "rejected: contains a data- or schema-modifying keyword"
    if SYSTEM_OBJECTS.search(text):
        return None, "rejected: system tables are outside this dashboard"
    scan = re.sub(r'\b(?:EXTRACT|SUBSTRING|TRIM|OVERLAY|POSITION)\s*\((?:[^()]|\([^()]*\))*\)',
                  lambda m: re.sub(r'\bFROM\b', '____', m.group(0), flags=re.I),
                  text, flags=re.I | re.S)
    ctes = {n.upper() for n in re.findall(r'(?:\bwith|,)\s*"?([A-Za-z0-9_]+)"?\s+as\s*\(', scan, re.I)}
    sources = re.findall(r'\b(?:from|join)\s+"?([A-Za-z0-9_]+)"?\s*\.\s*"?([A-Za-z0-9_ ]+?)"?(?=[\s,)]|$)', scan, re.I)
    plain = re.findall(r'\b(?:from|join)\s+(?!\()("?)([A-Za-z0-9_]+)\1(?![A-Za-z0-9_])(?!\s*\.)', scan, re.I)
    unqualified = [n for _, n in plain if n.upper() not in ctes and n.upper() != "DUAL"]
    if not sources:
        return None, f"rejected: every table must be written as {schema}.TABLE"
    for ref_schema, _ in sources:
        if ref_schema.upper() != schema.upper():
            return None, f"rejected: reads from schema {ref_schema}, outside this dashboard"
    if unqualified:
        return None, f"rejected: unqualified table reference {unqualified[0]}; every table must name its schema"
    return text, None


def _jsonable(v):
    if isinstance(v, Decimal):
        return int(v) if v == v.to_integral_value() else float(v)
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    return v


def execute_readonly(sql, backend):
    """Run one statement through the dashboard's server-side Exasol profile (starter-kit = the read-only MCP user
    mcp_readonly, 30 s statement timeout). No guard here: the database is the floor (run_sql calls it after guard(),
    and calling it directly with a CREATE shows that the database itself rejects writes)."""
    res = backend.execute_sql(sql.replace("{", "{{").replace("}", "}}"))   # pyexasol formats the text; keep braces literal
    if res.get("status") != "ok":
        raise RuntimeError(str(res.get("error") or "query failed"))
    cols = [str(c) for c in (res.get("columns") or [])]
    rows = res.get("rows") or []
    rows = [[r.get(c) for c in cols] if isinstance(r, dict) else list(r) for r in rows]
    return {"columns": cols, "rows": [[_jsonable(v) for v in r] for r in rows[:ROW_CAP]],
            "row_count": len(rows), "returned": min(len(rows), ROW_CAP),
            "truncated": len(rows) > ROW_CAP or bool(res.get("truncated"))}


def run_sql(sql, purpose="", backend=None):
    safe, err = guard(sql)
    if err:
        return {"error": err}
    try:
        return execute_readonly(safe, backend)
    except Exception as exc:  # database message only, never credentials
        return {"error": f"query failed: {str(exc).splitlines()[0][:400] if str(exc) else type(exc).__name__}"}


# ------------------------------------------------------------------ tool schemas (strict)
def _n(t):
    return [t, "null"]


STATION = {"type": "object", "additionalProperties": False, "required": ["name", "lat", "lon"],
           "properties": {"name": {"type": "string", "description": "Existing MVV station name inside Munich, or the name of a new station"},
                          "lat": {"type": _n("number"), "description": "WGS84 latitude for a new station, else null"},
                          "lon": {"type": _n("number"), "description": "WGS84 longitude for a new station, else null"}}}
CHANGE = {"type": "object", "additionalProperties": False,
          "required": ["kind", "lines", "min_trains_per_hour", "hours", "mode", "stations", "trains_per_hour_peak", "trains_per_hour_offpeak"],
          "properties": {
              "kind": {"type": "string", "enum": ["frequency", "new_line"]},
              "lines": {"type": _n("array"), "items": {"type": "string"},
                        "description": "frequency: existing line names, e.g. S1..S8, U3, 17"},
              "min_trains_per_hour": {"type": _n("number"), "description": "frequency: minimum trains per hour and direction"},
              "hours": {"type": _n("number"), "description": "frequency: service hours per weekday (null = 19)"},
              "mode": {"type": _n("string"), "enum": [*MODES, None], "description": "new_line: mode, sets capacity per trip"},
              "stations": {"type": _n("array"), "items": STATION, "description": "new_line: the stations"},
              "trains_per_hour_peak": {"type": _n("number"), "description": "new_line: trains per hour and direction, 6 peak hours"},
              "trains_per_hour_offpeak": {"type": _n("number"), "description": "new_line: trains per hour and direction, 13 off-peak hours"}}}

TOOLS = [
    {"type": "function", "name": "run_sql", "strict": True,
     "description": ("Run one read-only SELECT (or WITH) on schema MUNICH_DATASET. Qualify every table as MUNICH_DATASET.TABLE and "
                     "double-quote the lowercase column names. No comments, one statement. At most 200 rows are returned; 30 s timeout."),
     "parameters": {"type": "object", "additionalProperties": False, "required": ["sql", "purpose"],
                    "properties": {"sql": {"type": "string"}, "purpose": {"type": "string", "description": "One line: what this query answers"}}}},
    {"type": "function", "name": "dashboard_scenario", "strict": True,
     "description": ("Run the dashboard's own model (ranking.sql) for a year, job weight w, projects and pessimistic dates, optionally "
                     "with a stored what-if. Returns the city figure, the % change since 2024 and all 25 districts. Does not change the view."),
     "parameters": {"type": "object", "additionalProperties": False,
                    "required": ["year", "w", "projects", "preset", "pessimistic", "extra"],
                    "properties": {"year": {"type": "integer", "description": "2024 to 2045"},
                                   "w": {"type": "number", "description": "job weight 0 to 1.5, steps of 0.25"},
                                   "projects": {"type": "array", "items": {"type": "string"}, "description": "project ids; [] when preset is used"},
                                   "preset": {"type": _n("string"), "enum": [*PRESET_NAMES, None],
                                              "description": "instead of projects: none, funded, funded_planned, everything"},
                                   "pessimistic": {"type": "boolean"},
                                   "extra": {"type": _n("string"), "description": "name of a what-if computed earlier with what_if, or null"}}}},
    {"type": "function", "name": "what_if", "strict": True,
     "description": ("Compute a hypothetical as extra scheduled places per weekday per district and store it under name. frequency: for "
                     "each listed line and Munich station, departures become GREATEST(today, tph x hours x 2) x capacity per trip. "
                     "new_line: per station (peak x 6 + offpeak x 13) x 2 departures x the mode's capacity. Returns the dashboard model "
                     "for the current view with the what-if added. Does not change the view; use set_view to put it on the map."),
     "parameters": {"type": "object", "additionalProperties": False, "required": ["name", "changes"],
                    "properties": {"name": {"type": "string", "description": "short label, e.g. 'S-Bahn every 10 min'"},
                                   "changes": {"type": "array", "items": CHANGE}}}},
    {"type": "function", "name": "set_view", "strict": True,
     "description": ("Change what this viewer's map, change chart and view line show. null keeps a field as it is. what_if: a stored "
                     "what-if name, or 'none' to clear it. Give projects or preset, not both. Returns the new view and its city figure."),
     "parameters": {"type": "object", "additionalProperties": False,
                    "required": ["year", "w", "projects", "preset", "pessimistic", "what_if"],
                    "properties": {"year": {"type": _n("integer")}, "w": {"type": _n("number")},
                                   "projects": {"type": _n("array"), "items": {"type": "string"}},
                                   "preset": {"type": _n("string"), "enum": [*PRESET_NAMES, None]},
                                   "pessimistic": {"type": _n("boolean")},
                                   "what_if": {"type": _n("string")}}}},
    {"type": "web_search"},
]


# ------------------------------------------------------------------ sessions and jobs
DEFAULT_VIEW = {"year": 2024, "w": 1.0, "projects": [], "pessimistic": 0, "what_if": None, "extra": ""}  # keys; year via default_view()


def current_year():
    """The calendar year now, clamped to the model's range. The default view shows this year (\"now\")."""
    return min(max(date.today().year, YEARS[0]), YEARS[1])


def default_view():
    return dict(DEFAULT_VIEW, year=current_year())
_SESSIONS = {}
_LOCK = threading.Lock()


class Session:
    def __init__(self, sid):
        self.sid = sid
        self.lock = threading.RLock()
        self.turn_items = []        # completed turns: list of lists of Responses input items
        self.turns = []             # display: dicts with question, answer, trace, sources, badges, usage, error
        self.view = default_view()
        self.view_ver = 0
        self.whatifs = {}
        self.sql_log = []           # every statement the assistant's tools ran (or tried), for the "SQL executed" foldout
        self.job = None             # dict: status, started, cancel(Event), thread
        self.rev = 0
        self.touched = time.time()

    def bump(self):
        self.rev += 1
        self.touched = time.time()


def get_session(sid):
    now = time.time()
    with _LOCK:
        for k in [k for k, s in _SESSIONS.items() if now - s.touched > SESSION_IDLE_S and not running(s)]:
            _SESSIONS.pop(k, None)
        s = _SESSIONS.get(sid)
        if s is None:
            s = _SESSIONS[sid] = Session(sid)
        return s


def running(s):
    return bool(s.job and s.job["thread"].is_alive() and not s.job.get("done"))


def new_session_id():
    return uuid.uuid4().hex


def reset(sid):
    s = get_session(sid)
    with s.lock:
        if s.job:
            s.job["cancel"].set()
            s.job["done"] = True
        s.turn_items, s.turns, s.whatifs, s.sql_log = [], [], {}, []
        s.view = default_view()
        s.view_ver += 1
        s.job = None
        s.bump()
        return dict(s.view, ver=s.view_ver)


def snapshot(sid):
    s = get_session(sid)
    with s.lock:
        job = s.job
        if job and not job.get("done") and time.time() - job["started"] > JOB_TIMEOUT_S:
            job["cancel"].set()
        busy = running(s)
        return {"rev": s.rev, "running": busy, "status": (job or {}).get("status", "") if busy else "",
                "turns": json.loads(json.dumps(s.turns, default=str)), "view": dict(s.view, ver=s.view_ver),
                "sql_log": json.loads(json.dumps(s.sql_log, default=str))}


def start(sid, question, view, backend):
    """Start a job. Returns (ok, message)."""
    question = (question or "").strip()
    if not question:
        return False, "Type a question first."
    configured, msg = key_status()
    if not configured:
        return False, msg
    s = get_session(sid)
    with s.lock:
        if running(s):
            return False, "Still answering the previous question. Wait for that answer first."
        v = default_view()
        v.update({k: view[k] for k in DEFAULT_VIEW if view and k in view})
        s.view = v
        turn = {"question": question, "answer": "", "trace": [], "sources": [], "badges": [], "usage": None,
                "error": None, "started": time.time(), "elapsed": None}
        s.turns.append(turn)
        job = {"status": "Thinking…", "started": time.time(), "cancel": threading.Event(), "done": False}
        th = threading.Thread(target=_run_job, args=(s, turn, job, question, backend), daemon=True, name=f"v5-ask-{sid[:8]}")
        job["thread"] = th
        s.job = job
        s.bump()
        th.start()
    return True, None


def _status(s, job, text):
    with s.lock:
        job["status"] = text
        s.bump()


class _Cancelled(Exception):
    pass


def _client(key):
    if CLIENT_FACTORY:
        return CLIENT_FACTORY(key)
    from openai import OpenAI
    return OpenAI(api_key=key, timeout=REQUEST_TIMEOUT_S, max_retries=2)


def _context():
    return CONTEXT_FILE.read_text(encoding="utf-8")


def view_text(view, backend):
    projs = view.get("projects") or []
    scen = backend.scen_name(projs) if backend else ("none" if not projs else f"{len(projs)} projects")
    return (f"[Current view on the page] year {view.get('year')} · w = {view.get('w')} · scenario: {scen}"
            f" · projects: {', '.join(projs) or 'none'} · pessimistic dates: {'on' if view.get('pessimistic') else 'off'}"
            f" · what-if on the map: {view.get('what_if') or 'none'}")


def _estimate_tokens(items):
    return len(json.dumps(items, default=str)) // 4


def _history(s):
    """Previous complete turns, oldest dropped (whole turns only) while the estimate exceeds the cap."""
    fixed = len(_context()) // 3          # the context pack, about 44k tokens (bytes / 3.2 measured)
    turns = list(s.turn_items)
    while turns and fixed + sum(_estimate_tokens(t) for t in turns) > HISTORY_TOKEN_CAP:
        turns.pop(0)
    s.turn_items = turns
    return [item for t in turns for item in t]


def _api_error_text(exc):
    import openai
    if isinstance(exc, openai.AuthenticationError):
        return "OpenAI rejected the API key. Check ~/.exasol-starter-kit/credentials/openai_api_key."
    if isinstance(exc, openai.RateLimitError):
        code = getattr(exc, "code", None) or ""
        etype = getattr(exc, "type", None) or ""
        if code in ("insufficient_quota", "credit_balance_exhausted") or etype == "insufficient_quota":
            return NO_CREDITS
        return "OpenAI rate limit reached. Try again in a minute."
    if isinstance(exc, openai.APIStatusError):
        return f"OpenAI returned an error (HTTP {exc.status_code}). Try again, or rephrase the question."
    if isinstance(exc, openai.APIConnectionError):
        return "Could not reach OpenAI (network problem or timeout). Try again."
    if isinstance(exc, openai.APIError):
        # With stream=True the SDK raises a plain APIError carrying the error body (e.g. a 429 for no credits).
        code = getattr(exc, "code", None) or ""
        etype = getattr(exc, "type", None) or ""
        if code in ("insufficient_quota", "credit_balance_exhausted") or etype == "insufficient_quota":
            return NO_CREDITS
        if code == "rate_limit_exceeded":
            return "OpenAI rate limit reached. Try again in a minute."
        return f"OpenAI returned an error: {str(getattr(exc, 'message', '') or exc).splitlines()[0][:200]}"
    return None


def _dump(o):
    return o.model_dump(exclude_none=True) if hasattr(o, "model_dump") else dict(o)


def _request(client, s, job, items, final_round):
    kw = dict(model=MODEL, instructions=_context(), input=items, tools=TOOLS, store=False,
              reasoning={"effort": REASONING_EFFORT}, max_output_tokens=MAX_OUTPUT_TOKENS,
              include=["web_search_call.action.sources"], stream=True)
    if final_round:
        kw["tool_choice"] = "none"
    stream = client.responses.create(**kw)
    final = None
    try:
        for ev in stream:
            if job["cancel"].is_set():
                raise _Cancelled()
            t = getattr(ev, "type", "")
            if t in ("response.web_search_call.in_progress", "response.web_search_call.searching"):
                _status(s, job, "Searching the web…")
            elif t == "response.output_text.delta" and job["status"] != "Writing the answer…":
                _status(s, job, "Writing the answer…")
            elif t in ("response.completed", "response.incomplete", "response.failed"):
                final = ev.response
            elif t == "error":
                raise RuntimeError(f"OpenAI stream error: {getattr(ev, 'message', '')[:200]}")
    finally:
        close = getattr(stream, "close", None)
        if close:
            close()
    if final is None:
        raise RuntimeError("OpenAI stream ended without a response")
    return final


def _add_usage(acc, usage):
    if not usage:
        return
    acc["requests"] += 1
    acc["input"] += int(getattr(usage, "input_tokens", 0) or 0)
    acc["output"] += int(getattr(usage, "output_tokens", 0) or 0)
    det = getattr(usage, "input_tokens_details", None)
    acc["cached"] += int(getattr(det, "cached_tokens", 0) or 0) if det else 0


def _cost(u):
    fresh = max(u["input"] - u["cached"], 0)
    return round((fresh * PRICES["input"] + u["cached"] * PRICES["cached"] + u["output"] * PRICES["output"]) / 1e6, 3)


def _run_job(s, turn, job, question, backend):
    """Never lets the thread die silently: any unexpected failure still finishes the turn with a visible error line."""
    try:
        _run_job_inner(s, turn, job, question, backend)
    except BaseException as exc:  # noqa: BLE001 - last-resort guard for the background thread
        with s.lock:
            if s.job is job and not job.get("done"):
                turn["error"] = f"Something went wrong: {str(exc).splitlines()[0][:300] if str(exc) else type(exc).__name__}"
                turn["elapsed"] = round(time.time() - turn["started"], 1)
                job["done"] = True
                job["status"] = ""
                s.bump()


def _run_job_inner(s, turn, job, question, backend):
    usage = {"requests": 0, "input": 0, "cached": 0, "output": 0}
    with s.lock:
        view = dict(s.view)
    items = []
    error = None
    answer = ""
    try:
        items.append({"role": "user", "content": f"{question}\n\n{view_text(view, backend)}"})
        key, kerr = read_key()
        if not key:
            raise RuntimeError(kerr or SETUP_LINE)
        client = _client(key)
        key = None
        history = _history(s)
        for rnd in range(MAX_TOOL_ROUNDS + 1):
            if job["cancel"].is_set():
                raise _Cancelled()
            _status(s, job, "Thinking…")
            resp = _request(client, s, job, history + items, final_round=(rnd == MAX_TOOL_ROUNDS))
            _add_usage(usage, getattr(resp, "usage", None))
            output = list(getattr(resp, "output", None) or [])
            items += [_dump(o) for o in output]
            _collect_web(turn, output, s)
            status = getattr(resp, "status", None)
            if status == "failed":
                e = getattr(resp, "error", None)
                raise RuntimeError(f"OpenAI could not complete the answer: {getattr(e, 'message', '') or 'failed'}"[:300])
            calls = [o for o in output if getattr(o, "type", "") == "function_call"]
            if status == "incomplete":
                reason = getattr(getattr(resp, "incomplete_details", None), "reason", "") or "incomplete"
                answer = _text(output)
                error = f"The answer was cut off ({reason}). Ask a narrower question."
                break
            if not calls:
                answer = _text(output)
                if not answer:
                    error = DECLINED
                break
            for c in calls:
                if job["cancel"].is_set():
                    raise _Cancelled()
                result = _call_tool(s, turn, job, c.name, c.arguments, backend)
                items.append({"type": "function_call_output", "call_id": c.call_id,
                              "output": json.dumps(result, default=str, ensure_ascii=False)})
    except _Cancelled:
        error = "Cancelled."
    except Exception as exc:  # typed SDK exceptions first, then anything else as one plain line
        error = None
        try:
            error = _api_error_text(exc)
        except ImportError:
            pass
        error = error or f"Something went wrong: {str(exc).splitlines()[0][:300] if str(exc) else type(exc).__name__}"
    with s.lock:
        if s.job is not job:
            return  # New conversation (reset) replaced this job; drop its result
        turn["answer"] = answer
        turn["error"] = error
        turn["elapsed"] = round(time.time() - turn["started"], 1)
        turn["usage"] = dict(usage, cost_usd=_cost(usage), model=MODEL, effort=REASONING_EFFORT)
        turn["badges"] = _badges(turn)
        if not error or answer:
            s.turn_items.append(items)          # keep only complete turns (every call has its output)
        job["done"] = True
        job["status"] = ""
        s.bump()


def _text(output):
    parts, refused = [], False
    for o in output:
        if getattr(o, "type", "") != "message":
            continue
        for c in getattr(o, "content", None) or []:
            ct = getattr(c, "type", "")
            if ct == "output_text":
                parts.append(getattr(c, "text", "") or "")
            elif ct == "refusal":
                refused = True
    text = "\n\n".join(p for p in parts if p.strip())
    return "" if refused and not text else text


def _collect_web(turn, output, s):
    with s.lock:
        seen = {x["url"] for x in turn["sources"]}
        for o in output:
            t = getattr(o, "type", "")
            if t == "web_search_call":
                act = getattr(o, "action", None)
                q = getattr(act, "query", None) or getattr(act, "url", None) or ""
                srcs = [getattr(x, "url", "") for x in (getattr(act, "sources", None) or [])]
                turn["trace"].append({"kind": "web", "query": q, "consulted": [u for u in srcs if u][:8]})
            elif t == "message":
                for c in getattr(o, "content", None) or []:
                    for a in getattr(c, "annotations", None) or []:
                        if getattr(a, "type", "") == "url_citation" and a.url not in seen:
                            seen.add(a.url)
                            turn["sources"].append({"title": getattr(a, "title", "") or a.url, "url": a.url})


PLAN_WORDS = re.compile(r"Stammstrecke|U5|U9|U4|U26|Westtangente|Nordtangente|Münchner Norden|Johanneskirchen|Lerchenauer|"
                        r"Berduxstra|Poccistra|Nordring|Laim inbound|Freiham|funded|planned project", re.I)


def _badges(turn):
    kinds = {t["kind"] for t in turn["trace"]}
    b = []
    if kinds & {"sql", "model", "view"}:
        b.append("Data")
    if any(t.get("projects") for t in turn["trace"]) or PLAN_WORDS.search(turn.get("answer") or ""):
        b.append("Plans")
    if "web" in kinds or turn["sources"]:
        b.append("Web")
    if "whatif" in kinds:
        b.append("Assumption")
    return b


# ------------------------------------------------------------------ tools
def _call_tool(s, turn, job, name, arguments, backend):
    question = turn.get("question", "")

    def sink(entry):
        with s.lock:
            s.sql_log.append(dict(entry, tool=name, question=question))
            s.bump()

    set_sink = getattr(backend, "set_sink", None)
    if set_sink:
        set_sink(sink)
    try:
        return _call_tool_inner(s, turn, job, name, arguments, backend, sink)
    finally:
        if set_sink:
            set_sink(None)


def _call_tool_inner(s, turn, job, name, arguments, backend, sink):
    try:
        args = json.loads(arguments or "{}")
    except ValueError:
        return {"error": "arguments are not valid JSON"}
    try:
        if name == "run_sql":
            _status(s, job, "Running SQL…")
            t0 = time.time()
            res = run_sql(args.get("sql", ""), args.get("purpose", ""), backend)
            err = res.get("error") or ""
            sink({"file": "ad-hoc SQL", "purpose": args.get("purpose", ""), "params": "", "sql": args.get("sql", ""),
                  "rows": res.get("row_count"), "secs": round(time.time() - t0, 3), "cached": False,
                  "rejected": err[len("rejected: "):] if err.startswith("rejected") else (err if err == "empty query" else ""),
                  "error": err if err and not err.startswith("rejected") and err != "empty query" else "",
                  "ran_at": time.strftime("%H:%M:%S")})
            with s.lock:
                turn["trace"].append({"kind": "sql", "purpose": args.get("purpose", ""), "sql": args.get("sql", ""),
                                      "rows": res.get("row_count"), "error": res.get("error")})
            return res
        if name == "dashboard_scenario":
            _status(s, job, "Running the dashboard model…")
            res = dashboard_scenario(s, backend, **{k: args.get(k) for k in ("year", "w", "projects", "preset", "pessimistic", "extra")})
            with s.lock:
                turn["trace"].append({"kind": "model", "args": args, "projects": res.get("projects"),
                                      "summary": res.get("summary") or res.get("error")})
            return res
        if name == "what_if":
            _status(s, job, "Computing what-if…")
            res = what_if(s, backend, args.get("name"), args.get("changes") or [])
            with s.lock:
                turn["trace"].append({"kind": "whatif", "name": args.get("name"), "assumptions": res.get("assumptions"),
                                      "places_by_district": res.get("places_by_district"), "error": res.get("error"),
                                      "summary": res.get("summary")})
            return res
        if name == "set_view":
            _status(s, job, "Updating the map…")
            res = set_view(s, backend, **{k: args.get(k) for k in ("year", "w", "projects", "preset", "pessimistic", "what_if")})
            with s.lock:
                turn["trace"].append({"kind": "view", "text": res.get("change") or res.get("error"),
                                      "projects": (res.get("view") or {}).get("projects"), "error": res.get("error")})
            return res
        return {"error": f"unknown tool {name}"}
    except Exception as exc:
        return {"error": f"{name} failed: {str(exc).splitlines()[0][:300] if str(exc) else type(exc).__name__}"}


def _valid_year(year):
    if year is None or isinstance(year, bool):
        return None, "year is required"
    try:
        y = int(year)
    except (TypeError, ValueError):
        return None, "year must be an integer"
    if y != float(year) or not (YEARS[0] <= y <= YEARS[1]):
        return None, f"year must be between {YEARS[0]} and {YEARS[1]}"
    return y, None


def _valid_w(w):
    try:
        v = float(w)
    except (TypeError, ValueError):
        return None, "w must be a number"
    if not (0 <= v <= 1.5):
        return None, "w must be between 0 and 1.5"
    return round(v * 4) / 4, None


def _resolve_projects(backend, projects, preset):
    if projects and preset:
        return None, "give projects or preset, not both"
    known = backend.project_ids()
    if preset:
        if preset not in PRESET_NAMES:
            return None, f"unknown preset {preset}; use one of {', '.join(PRESET_NAMES)}"
        return sorted(backend.preset_ids(preset)), None
    bad = [p for p in (projects or []) if p not in known]
    if bad:
        return None, f"unknown project id(s) {', '.join(bad)}; valid ids: {', '.join(sorted(known))}"
    return sorted(set(projects or [])), None


def _scenario(backend, year, w, projs, pessimistic, extra):
    rows, err = backend.ranking({"w_jobs": w, "year": year, "projects": ",".join(projs) if projs else "none",
                                 "pessimistic": 1 if pessimistic else 0, "extra": extra or ""})
    if err:
        return {"error": f"dashboard model failed: {err}"}
    r0 = rows[0] if rows else {}
    c24, cy = float(r0.get("city_places_per_1k_act_2024") or 0), float(r0.get("city_places_per_1k_act") or 0)
    pct = (cy / c24 - 1) * 100 if c24 else 0.0
    active = sorted({p for r in rows for p in str(r.get("active_projects") or "").split(",") if p})
    districts = [{"district_no": int(r["district_no"]), "district": r["district"], "service_ratio": _jsonable(r.get("service_ratio")),
                  "ratio_2024": _jsonable(r.get("ratio_2024")), "pct_change_since_2024": _jsonable(r.get("pct_change_places")),
                  "places_per_1k_activity": _jsonable(r.get("places_per_1k_act")), "places_added": _jsonable(r.get("add_places")),
                  "flagged": _jsonable(r.get("flagged"))} for r in rows]
    districts.sort(key=lambda d: d["district_no"])
    added = _jsonable(r0.get("city_added_places"))
    summary = (f"{year}, w = {w}, {len(projs)} project(s) switched on, {len(active)} active: city {cy:,.0f} places per 1,000 activity "
               f"vs {c24:,.0f} in 2024 ({pct:+.2f} %), {added:+,.0f} places/weekday added")
    return {"year": year, "w": w, "projects": projs, "active_projects": active, "pessimistic": bool(pessimistic),
            "city_places_per_1k_activity": cy, "city_2024_places_per_1k_activity": c24, "city_pct_change_since_2024": round(pct, 2),
            "city_places_added_per_weekday": added, "districts": districts, "summary": summary,
            "note": "ratio = district places per 1,000 activity / 2024 city average at the same w; scheduled service only"}


def dashboard_scenario(s, backend, year=None, w=None, projects=None, preset=None, pessimistic=False, extra=None):
    y, err = _valid_year(year)
    if err:
        return {"error": err}
    wv, err = _valid_w(w if w is not None else 1.0)
    if err:
        return {"error": err}
    projs, err = _resolve_projects(backend, projects, preset)
    if err:
        return {"error": err}
    extra_str, wname = "", None
    if extra:
        with s.lock:
            wi = s.whatifs.get(extra)
        if not wi:
            return {"error": f"unknown what-if {extra}; stored: {', '.join(s.whatifs) or 'none'} (compute it with what_if first)"}
        extra_str, wname = wi["extra"], extra
    res = _scenario(backend, y, wv, projs, pessimistic, extra_str)
    if wname and "error" not in res:
        res["what_if"] = wname
    return res


def set_view(s, backend, year=None, w=None, projects=None, preset=None, pessimistic=None, what_if=None):
    """Validate everything first; on any error the view stays unchanged."""
    with s.lock:
        cur = dict(s.view)
    new = dict(cur)
    if year is not None:
        y, err = _valid_year(year)
        if err:
            return {"error": err, "view": cur}
        new["year"] = y
    if w is not None:
        wv, err = _valid_w(w)
        if err:
            return {"error": err, "view": cur}
        new["w"] = wv
    if projects is not None or preset is not None:
        projs, err = _resolve_projects(backend, projects, preset)
        if err:
            return {"error": err, "view": cur}
        new["projects"] = projs
    if pessimistic is not None:
        new["pessimistic"] = 1 if pessimistic else 0
    if what_if is not None:
        if str(what_if).strip().lower() in ("", "none", "null", "clear"):
            new["what_if"], new["extra"] = None, ""
        else:
            with s.lock:
                wi = s.whatifs.get(what_if)
            if not wi:
                return {"error": f"unknown what-if {what_if}; stored: {', '.join(s.whatifs) or 'none'}", "view": cur}
            new["what_if"], new["extra"] = what_if, wi["extra"]
    res = _scenario(backend, new["year"], new["w"], new["projects"], new["pessimistic"], new["extra"])
    if "error" in res:
        return {"error": res["error"], "view": cur}
    change = describe_change(cur, new, backend)
    with s.lock:
        s.view = new
        s.view_ver += 1
        s.bump()
    return {"view": new, "change": change, "city_places_per_1k_activity": res["city_places_per_1k_activity"],
            "city_pct_change_since_2024": res["city_pct_change_since_2024"],
            "city_places_added_per_weekday": res["city_places_added_per_weekday"], "active_projects": res["active_projects"]}


def describe_change(old, new, backend):
    parts = []
    if new["year"] != old["year"]:
        parts.append(f"year {new['year']}")
    if new["w"] != old["w"]:
        parts.append(f"w = {new['w']:g}")
    if new["projects"] != old["projects"]:
        parts.append(backend.scen_name(new["projects"]))
    if new["pessimistic"] != old["pessimistic"]:
        parts.append("pessimistic dates " + ("on" if new["pessimistic"] else "off"))
    if new["what_if"] != old["what_if"]:
        parts.append(f"what-if: {new['what_if']}" if new["what_if"] else "what-if cleared")
    return "set " + ", ".join(parts) if parts else "view unchanged"


# ------------------------------------------------------------------ what-if
def _norm(name):
    t = str(name or "").lower().replace("ß", "ss").replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
    t = re.sub(r"\b(muenchen|munich)\b", "", t)
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def _point_in_ring(lon, lat, ring):
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / ((yj - yi) or 1e-15) + xi:
            inside = not inside
        j = i
    return inside


def district_at(backend, lat, lon):
    for g in backend.geo():
        geom = g["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        for poly in polys:
            if poly and _point_in_ring(lon, lat, poly[0]) and not any(_point_in_ring(lon, lat, h) for h in poly[1:]):
                return int(g["district_no"])
    return None


def what_if(s, backend, name, changes):
    name = str(name or "").strip()[:60]
    if not name:
        return {"error": "give the what-if a short name"}
    if not changes:
        return {"error": "no changes given"}
    totals, assumptions, notes = {}, [], []
    for i, ch in enumerate(changes, 1):
        kind = ch.get("kind")
        if kind == "frequency":
            lines = [str(x).strip() for x in (ch.get("lines") or []) if str(x).strip()]
            tph = ch.get("min_trains_per_hour")
            hours = 19 if ch.get("hours") is None else ch.get("hours")
            if not lines:
                return {"error": f"change {i}: frequency needs lines"}
            if tph is None or not (0 < float(tph) <= 40):
                return {"error": f"change {i}: min_trains_per_hour must be between 0 and 40"}
            if not (1 <= float(hours) <= 24):
                return {"error": f"change {i}: hours must be between 1 and 24"}
            target = float(tph) * float(hours) * 2
            rows, err = backend.query("whatif_line_stations", {"lines": ",".join(lines)})
            if err:
                return {"error": f"change {i}: {err}"}
            found = {r["line"] for r in rows}
            missing = [l for l in lines if l not in found]
            if missing:
                return {"error": f"change {i}: no scheduled service inside Munich on the reference weekday for line(s) {', '.join(missing)}"}
            lifted, added = 0, 0.0
            for r in rows:
                dep = float(r["dep_today"])
                extra_dep = max(dep, target) - dep
                if extra_dep > 0 and r.get("district_no") is not None:
                    lifted += 1
                    p = extra_dep * float(r["capacity"])
                    added += p
                    d = int(r["district_no"])
                    totals[d] = totals.get(d, 0.0) + p
            caps = sorted({f"{r['line']} {int(float(r['capacity']))}" for r in rows})
            assumptions.append(f"{', '.join(lines)}: at least {float(tph):g} trains/h per direction for {float(hours):g} h "
                               f"(≥ {target:g} departures per station and weekday); {lifted} of {len(rows)} line-stations in Munich lifted; "
                               f"capacity per trip {', '.join(caps)}; +{added:,.0f} places/weekday")
        elif kind == "new_line":
            mode = ch.get("mode")
            if mode not in MODES:
                return {"error": f"change {i}: new_line needs mode, one of {', '.join(MODES)}"}
            peak, off = ch.get("trains_per_hour_peak"), ch.get("trains_per_hour_offpeak")
            peak = off if peak is None else peak
            off = peak if off is None else off
            if peak is None or not (0 < float(peak) <= 40) or not (0 <= float(off) <= 40):
                return {"error": f"change {i}: trains_per_hour_peak / _offpeak must be between 0 and 40"}
            stations = ch.get("stations") or []
            if not stations:
                return {"error": f"change {i}: new_line needs stations"}
            cap = backend.capacity(mode)
            dep = (float(peak) * 6 + float(off) * 13) * 2
            stops = backend.stops()
            seen, placed = set(), []
            for st in stations:
                nm = str(st.get("name") or "").strip()
                if st.get("lat") is not None and st.get("lon") is not None:
                    d = district_at(backend, float(st["lat"]), float(st["lon"]))
                    if d is None:
                        notes.append(f"{nm or 'point'} ({st['lat']}, {st['lon']}) is outside Munich: adds nothing")
                        continue
                else:
                    key = _norm(nm)
                    hits = [x for x in stops if x["norm"] == key]
                    if not hits:
                        cands = sorted({f"{x['name']} (district {x['district_no']})" for x in stops if key and key in x["norm"]})[:8]
                        return {"error": f"change {i}: station '{nm}' not found among Munich stops"
                                         + (f"; candidates: {'; '.join(cands)}" if cands else "; give lat/lon for a new station")}
                    dists = sorted({x["district_no"] for x in hits})
                    if len(dists) > 1:
                        return {"error": f"change {i}: station name '{nm}' is ambiguous; stops in districts {dists}: "
                                         + "; ".join(sorted({f"{x['name']} (district {x['district_no']}, {x['lat']:.4f}, {x['lon']:.4f})" for x in hits})[:8])
                                         + ". Pass lat/lon to choose."}
                    d = dists[0]
                if (key2 := (_norm(nm), d)) in seen:
                    continue
                seen.add(key2)
                placed.append(f"{nm} (district {d})")
                totals[d] = totals.get(d, 0.0) + dep * cap
            assumptions.append(f"new {mode} line: {float(peak):g} trains/h peak (6 h), {float(off):g} off-peak (13 h), both directions = "
                               f"{dep:g} departures per station; {cap:g} places per trip; stations inside Munich: {', '.join(placed) or 'none'}; "
                               f"+{dep * cap * len(placed):,.0f} places/weekday")
        else:
            return {"error": f"change {i}: kind must be frequency or new_line"}
    clean = {int(d): float(p) for d, p in totals.items() if 1 <= int(d) <= 25 and float(p) > 0}
    extra = ";".join(f"{int(d)}:{float(p):.0f}" for d, p in sorted(clean.items()))
    if not re.fullmatch(r"(\d{1,2}:\d+)(;\d{1,2}:\d+)*|", extra):
        return {"error": "internal: what-if string failed validation"}
    with s.lock:
        s.whatifs[name] = {"extra": extra, "assumptions": assumptions}
        view = dict(s.view)
    res = _scenario(backend, view["year"], view["w"], view["projects"], view["pessimistic"], extra)
    names = backend.district_names()
    out = {"name": name, "stored": True, "assumptions": assumptions, "notes": notes,
           "places_by_district": {names.get(d, str(d)): round(p) for d, p in sorted(clean.items())},
           "total_places_added_per_weekday": round(sum(clean.values())),
           "evaluated_for_current_view": {k: view[k] for k in ("year", "w", "projects", "pessimistic")},
           "hypothetical": "a what-if, not a plan; demand shifts, crowding, travel time, cost and feasibility are not modelled"}
    out.update({k: v for k, v in res.items() if k not in ("year", "w", "projects", "pessimistic")})
    return out
