#!/usr/bin/env python3
"""HTTP first-render smoke test for one Dash Server app, the way a browser loads it.

1. GET /apps/<app-id>/_dash-layout and /_dash-dependencies.
2. Find the map callback generically: every callback with a `.figure` output is called (map-like ids first)
   until one returns a figure with a choroplethmap trace.
3. Call it through /_dash-update-component with the layout's default values for all inputs and state,
   which is what the browser sends on first load.
4. Assert: HTTP 200, no error text in the response, at least N district polygons (tests/expected.json),
   the "SQL executed" foldout id (sql-dash) in the layout, and the title text where expected.json sets one
   (v5: "2026 (now)").

Read-only: GET requests plus one callback POST per candidate, which runs the dashboard's own SELECTs.

    python3 scripts/check_dashboard.py munich-mobility-planning-v4
    python3 scripts/check_dashboard.py munich-cycling-coverage --base http://127.0.0.1:5100 --json

Exit code: 0 pass, 1 a check failed, 2 could not run (server down), 3 app not deployed.
"""
from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
import urllib.request

import _common as c

EXIT_NOT_DEPLOYED = 3
ERROR_MARKERS = ("Exasol query failed", "Traceback (most recent call last)", "failed: ", "Internal Server Error")
CHORO_TYPES = ("choroplethmap", "choroplethmapbox", "choropleth")


class NotDeployed(Exception):
    pass


def http(method: str, url: str, body=None, timeout: float = 180.0):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", "replace")
            return resp.status, raw
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")
    except (urllib.error.URLError, OSError) as exc:
        raise c.CheckError(f"cannot reach {url}: {getattr(exc, 'reason', exc)}")


def id_key(cid) -> str:
    """Dash's string form of a component id (dict ids: sorted keys, no spaces)."""
    return json.dumps(cid, sort_keys=True, separators=(",", ":")) if isinstance(cid, dict) else str(cid)


def walk_layout(node, out: dict) -> None:
    """Collect {id_key: props} for every component with an id."""
    if isinstance(node, list):
        for x in node:
            walk_layout(x, out)
        return
    if not isinstance(node, dict):
        return
    props = node.get("props")
    if isinstance(props, dict) and "type" in node:
        if props.get("id") is not None:
            out[id_key(props["id"])] = props
        for v in props.values():
            if isinstance(v, (dict, list)):
                walk_layout(v, out)
    else:
        for v in node.values():
            if isinstance(v, (dict, list)):
                walk_layout(v, out)


def parse_output(spec: str) -> list[tuple[str, str]]:
    """'a.b' or '..a.b...c.d..' -> [(id, prop)], prop without an allow_duplicate '@hash' suffix."""
    parts = spec[2:-2].split("...") if spec.startswith("..") and spec.endswith("..") else [spec]
    out = []
    for p in parts:
        i = p.rfind(".")
        cid, prop = p[:i], p[i + 1:]
        out.append((cid, prop.split("@")[0]))
    return out


def id_value(cid: str):
    if cid.startswith("{"):
        try:
            return json.loads(cid)
        except json.JSONDecodeError:
            return cid
    return cid


def is_wildcard(cid: str) -> bool:
    return cid.startswith("{") and any(w in cid for w in ('["ALL"]', '["MATCH"]', '["ALLSMALLER"]'))


def dep_list(items, defaults: dict) -> list[dict]:
    """[{id, property, value}] with the layout default; value omitted when the layout does not set the prop,
    as the browser does (JSON.stringify drops undefined)."""
    out = []
    for it in items:
        cid = id_key(it["id"])
        entry = {"id": it["id"], "property": it["property"]}
        props = defaults.get(cid, {})
        if it["property"] in props:
            entry["value"] = props[it["property"]]
        out.append(entry)
    return out


def text_of(node) -> str:
    if node is None:
        return ""
    if isinstance(node, (str, int, float)):
        return str(node)
    if isinstance(node, list):
        return "".join(text_of(x) for x in node)
    if isinstance(node, dict):
        return text_of((node.get("props") or {}).get("children"))
    return ""


def polygons(fig) -> tuple[int, str | None]:
    """(largest number of distinct locations in a choropleth trace, its type)."""
    best, kind = 0, None
    for tr in (fig or {}).get("data") or []:
        if isinstance(tr, dict) and tr.get("type") in CHORO_TYPES:
            n = len(set(map(str, tr.get("locations") or [])))
            if n > best:
                best, kind = n, tr["type"]
    return best, kind


def error_texts(response: dict, outputs: list[tuple[str, str]]) -> list[str]:
    found = []
    blob = json.dumps(response, ensure_ascii=False)
    for marker in ERROR_MARKERS:
        if marker in blob:
            i = blob.index(marker)
            found.append(blob[max(0, i - 40): i + 160])
    for cid, prop in outputs:
        if re.search(r"(^|[-_])err(or)?s?($|[-_])", cid) and prop == "children":
            val = (response.get(cid) or {}).get(prop)
            if text_of(val).strip():
                found.append(f"{cid}: {text_of(val).strip()[:200]}")
    return found


def candidate_callbacks(deps: list[dict], map_output: str | None) -> list[dict]:
    cands = []
    for cb in deps:
        outs = parse_output(cb["output"])
        figs = [cid for cid, prop in outs if prop == "figure"]
        if not figs or cb.get("clientside_function"):
            continue
        ids = [x["id"] for x in cb.get("inputs", []) + cb.get("state", [])]
        if any(is_wildcard(id_key(i)) for i in ids) or any(is_wildcard(cid) for cid, _ in outs):
            continue
        hint = 0 if map_output and map_output in [f"{a}.{b}" for a, b in outs] else (1 if any("map" in f for f in figs) else 2)
        cands.append((hint, len(cands), cb))
    return [cb for _, _, cb in sorted(cands, key=lambda t: (t[0], t[1]))]


def check(app_id: str, base: str, expected: dict) -> dict:
    exp = (expected.get("dashboards") or {}).get(app_id, {})
    min_poly = int(exp.get("min_polygons", 25))
    foldout_id = exp.get("sql_foldout_id", "sql-dash")
    title_contains = exp.get("title_contains")
    root = f"{base.rstrip('/')}/apps/{app_id}"
    res = {"app": app_id, "url": root + "/", "ok": False, "status": "fail", "checks": []}

    def add(name, ok, detail=""):
        res["checks"].append({"check": name, "ok": bool(ok), "detail": detail})

    code, raw = http("GET", f"{root}/_dash-layout", timeout=60)
    if code == 404:
        res["status"] = "not_deployed"
        res["detail"] = "/_dash-layout returned 404"
        return res
    if code != 200:
        add("layout", False, f"HTTP {code}: {raw[:200]}")
        return res
    layout = json.loads(raw)
    code, raw = http("GET", f"{root}/_dash-dependencies", timeout=60)
    if code != 200:
        add("dependencies", False, f"HTTP {code}: {raw[:200]}")
        return res
    deps = json.loads(raw)
    defaults: dict = {}
    walk_layout(layout, defaults)
    add("layout and dependencies load", True, f"{len(defaults)} components with an id, {len(deps)} callbacks")
    sql_ids = [k for k in defaults if k == foldout_id] or [k for k in defaults if k.startswith("sql-")]
    add("SQL executed foldout in layout", foldout_id in defaults,
        f"id {foldout_id!r} " + ("found" if foldout_id in defaults else f"missing (sql-* ids: {sql_ids})"))

    tried = []
    hit = None
    for cb in candidate_callbacks(deps, exp.get("map_output")):
        outs = parse_output(cb["output"])
        body = {"output": cb["output"],
                "outputs": ([{"id": id_value(i), "property": p} for i, p in outs] if cb["output"].startswith("..")
                            else {"id": id_value(outs[0][0]), "property": outs[0][1]}),
                "inputs": dep_list(cb.get("inputs", []), defaults),
                "state": dep_list(cb.get("state", []), defaults),
                "changedPropIds": []}
        t0 = time.time()
        code, raw = http("POST", f"{root}/_dash-update-component", body)
        secs = round(time.time() - t0, 2)
        fig_ids = [i for i, p in outs if p == "figure"]
        if code == 204:
            tried.append({"output": cb["output"][:120], "http": 204, "note": "PreventUpdate on first load"})
            continue
        if code != 200:
            tried.append({"output": cb["output"][:120], "http": code, "note": raw[:200]})
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            tried.append({"output": cb["output"][:120], "http": code, "note": "response is not JSON"})
            continue
        response = payload.get("response", payload)
        best = max(((polygons((response.get(i) or {}).get("figure")), i) for i in fig_ids), key=lambda t: t[0][0])
        (n_poly, kind), fig_id = best
        tried.append({"output": cb["output"][:120], "http": code, "secs": secs, "polygons": n_poly})
        if kind:
            hit = {"callback": cb, "outs": outs, "response": response, "fig_id": fig_id, "polygons": n_poly, "kind": kind, "secs": secs}
            break
    res["tried"] = tried
    if not hit:
        add("map callback found", False, f"no figure callback returned a choroplethmap ({len(tried)} tried)")
        res["ok"] = False
        return res

    resp, outs = hit["response"], hit["outs"]
    res["map_output"] = f"{hit['fig_id']}.figure"
    res["callback_secs"] = hit["secs"]
    add("map callback found", True, f"{hit['fig_id']}.figure ({hit['kind']}), first render {hit['secs']} s")
    add(f"at least {min_poly} district polygons", hit["polygons"] >= min_poly, f"{hit['polygons']} polygons")
    errs = error_texts(resp, outs)
    add("no error text", not errs, "; ".join(errs)[:400])
    if foldout_id in [i for i, _ in outs]:
        n = text_of((resp.get(foldout_id) or {}).get("children")).count("SQL as sent to Exasol")
        entries = (resp.get(foldout_id) or {}).get("children")
        n = n or (len(entries) if isinstance(entries, list) else 0)
        add("SQL foldout filled by the map callback", n > 0, f"{n} statement(s) listed")

    titles = [(i, text_of((resp.get(i) or {}).get(p))) for i, p in outs if "title" in i and p == "children"]
    titles.sort(key=lambda t: (not t[0].startswith(hit["fig_id"]), "map" not in t[0]))
    res["map_title"] = titles[0][1] if titles else None
    if title_contains:
        add(f"map title contains {title_contains!r}", bool(titles) and title_contains in titles[0][1],
            repr(titles[0][1]) if titles else "no title output")
    res["ok"] = all(k["ok"] for k in res["checks"])
    res["status"] = "pass" if res["ok"] else "fail"
    return res


def human(res: dict) -> None:
    print(f"{res['app']}  {res['url']}")
    if res["status"] == "not_deployed":
        print(f"  NOT DEPLOYED ({res.get('detail')})")
        return
    for k in res["checks"]:
        print(f"  {'OK  ' if k['ok'] else 'FAIL'}  {k['check']}" + (f"  ({k['detail']})" if k["detail"] else ""))
    if res.get("map_title"):
        print(f"  map title: {res['map_title']}")
    if not res["ok"] and res.get("tried"):
        for t in res["tried"]:
            print(f"  tried {t}")
    print(f"{'PASS' if res['ok'] else 'FAIL'}: {res['app']}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0],
                                 epilog="Exit 0 = pass, 1 = a check failed, 2 = could not run, 3 = app not deployed.")
    ap.add_argument("app_id", help="Dash Server app id, e.g. munich-mobility-planning-v4")
    ap.add_argument("--base", help="Dash Server URL (default: from `exakit status --json`, else http://127.0.0.1:5100)")
    ap.add_argument("--json", action="store_true", help="print the result as JSON")
    ap.add_argument("--expected", help="path to expected.json (default tests/expected.json)")
    args = ap.parse_args()
    res = check(args.app_id, args.base or c.dash_base_url(), c.load_expected(args.expected))
    rc = c.emit(res, args.json, human)
    return EXIT_NOT_DEPLOYED if res["status"] == "not_deployed" else rc


if __name__ == "__main__":
    c.run_main(main)
