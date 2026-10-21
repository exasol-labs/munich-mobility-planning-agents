#!/usr/bin/env python3
"""Recompute the reference numbers R1-R6 (research/reference-numbers.md) with the v4 dashboard's own query.

Renders dashboards/munich-mobility-planning-v4/queries/ranking.sql with each case's parameters (year, w_jobs,
projects as the sorted comma list the dashboard passes, pessimistic) using pyexasol's placeholder rules,
runs it read-only through exapump, derives the city figures the way app.py does and compares them with
tests/expected.json.

The query picks its reference Wednesday from CURRENT_DATE. To keep results reproducible the script pins it
to the reference weekday in expected.json (2026-10-21) by substituting CURRENT_DATE with that date;
--live-date runs the query exactly as the dashboard does today.

    python3 scripts/verify_numbers.py                 all cases
    python3 scripts/verify_numbers.py --case R4 R6    selected cases
    python3 scripts/verify_numbers.py --json          machine-readable result
    python3 scripts/verify_numbers.py --show-sql R1   print the rendered SQL for one case and exit

Exit code: 0 all match, 1 a mismatch, 2 could not run.
"""
from __future__ import annotations

import argparse
import re

import _common as c


def resolve_projects(value: str, presets: dict) -> str:
    """'@funded' -> the preset list from expected.json; anything else is passed as given."""
    if isinstance(value, str) and value.startswith("@"):
        key = value[1:]
        if key not in presets:
            raise c.CheckError(f"unknown project preset {value}")
        return presets[key]
    return value


def case_params(case: dict, presets: dict) -> dict:
    p = dict(case["params"])
    p["projects"] = resolve_projects(p["projects"], presets)
    p["year"] = int(p["year"])
    p["w_jobs"] = float(p["w_jobs"])
    p["pessimistic"] = int(p.get("pessimistic", 0))
    p.setdefault("extra", "")  # v5's ranking.sql has {extra!s}; v4's ignores it
    return p


def render(template: str, params: dict, pin_date: str | None) -> str:
    sql = c.render_sql(template, params)
    if pin_date:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", pin_date):
            raise c.CheckError(f"bad reference date {pin_date!r}")
        sql = re.sub(r"\bCURRENT_DATE\b", f"DATE '{pin_date}'", sql)
    return sql


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def derive(rows: list[dict]) -> dict:
    """City figures as app.py reads them: from the first row; city % = pct(city_2024, city)."""
    r0 = rows[0] if rows else {}
    city = num(r0.get("city_places_per_1k_act"))
    city24 = num(r0.get("city_places_per_1k_act_2024"))
    return {
        "city_places_per_1k_act": city,
        "city_places_per_1k_act_2024": city24,
        "city_added_places": num(r0.get("city_added_places")),
        "city_pct_change": (city / city24 - 1) * 100 if city is not None and city24 else None,
        "ref_weekday": str(r0.get("ref_weekday") or "")[:10],
    }


def run_case(name: str, case: dict, template: str, presets: dict, pin_date: str | None, profile: str) -> dict:
    params = case_params(case, presets)
    out = {"case": name, "title": case.get("title", ""), "params": {k: v for k, v in params.items() if k != "extra"},
           "checks": [], "ok": False}
    try:
        rows = c.run_sql(render(template, params, pin_date), profile=profile)
    except (c.CheckError, ValueError) as exc:
        out["error"] = str(exc)
        return out
    city = derive(rows)
    out["rows"] = len(rows)
    out["ref_weekday"] = city["ref_weekday"]
    by_name = {r.get("district"): r for r in rows}
    for chk in case["checks"]:
        district = chk.get("district")
        if district:
            row = by_name.get(district)
            actual = num(row.get(chk["metric"])) if row else None
            if row is not None and actual is None and chk["metric"] in ("add_places", "add_dep"):
                actual = 0.0
        else:
            actual = city.get(chk["metric"])
        ok = actual is not None and abs(actual - chk["value"]) <= chk.get("tol", 0) + 1e-9
        out["checks"].append({"district": district, "metric": chk["metric"], "expected": chk["value"], "actual": actual,
                              "tol": chk.get("tol", 0), "ok": ok})
    problems = []
    if len(rows) != 25:
        problems.append(f"expected 25 district rows, got {len(rows)}")
    if pin_date and city["ref_weekday"] != pin_date:
        problems.append(f"reference weekday {city['ref_weekday']} != {pin_date}")
    out["problems"] = problems
    out["ok"] = not problems and all(k["ok"] for k in out["checks"])
    return out


def human(res: dict) -> None:
    print(f"Reference numbers from {res['query']} (reference weekday: {res['ref_date_mode']})")
    for case in res["cases"]:
        p = case["params"]
        proj = p["projects"] if len(p["projects"]) <= 40 else f"{p['projects'].count(',') + 1} projects"
        print(f"\n{case['case']}  {case['title']}  [year={p['year']} w={p['w_jobs']:g} projects={proj} pessimistic={p['pessimistic']}]"
              f"  -> {'PASS' if case['ok'] else 'FAIL'}")
        if case.get("error"):
            print(f"  error: {case['error']}")
            continue
        rows = [[k["district"] or "Munich (city)", k["metric"], c.fmt_num(k["expected"]),
                 c.fmt_num(round(k["actual"], 4)) if k["actual"] is not None else "-", "ok" if k["ok"] else "MISMATCH"]
                for k in case["checks"]]
        print("  " + c.table(rows, ["where", "metric", "expected", "actual", "status"]).replace("\n", "\n  "))
        for prob in case.get("problems", []):
            print(f"  problem: {prob}")
    n_ok = sum(1 for x in res["cases"] if x["ok"])
    print(f"\n{'PASS' if res['ok'] else 'FAIL'}: {n_ok} of {len(res['cases'])} cases match")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], epilog="Exit 0 = all match, 1 = mismatch, 2 = could not run.")
    ap.add_argument("--case", nargs="+", default=["all"], metavar="R1", help="case ids (R1 ... R6) or 'all' (default)")
    ap.add_argument("--json", action="store_true", help="print the result as JSON")
    ap.add_argument("--live-date", action="store_true", help="use CURRENT_DATE as the dashboard does instead of the pinned reference weekday")
    ap.add_argument("--show-sql", metavar="CASE", help="print the rendered SQL for one case and exit (nothing is run)")
    ap.add_argument("--expected", help="path to expected.json (default tests/expected.json)")
    ap.add_argument("--profile", default=c.PROFILE, help="exapump profile (default starter-kit)")
    args = ap.parse_args()

    exp = c.load_expected(args.expected)
    ref = exp["reference_numbers"]
    cases, presets = ref["cases"], exp.get("project_presets", {})
    qpath = c.REPO / ref["query"]
    try:
        template = qpath.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise c.CheckError(f"{qpath} not found")
    pin = None if args.live_date else ref.get("ref_weekday")

    if args.show_sql:
        name = args.show_sql.upper()
        if name not in cases:
            raise c.CheckError(f"unknown case {args.show_sql}; known: {', '.join(cases)}")
        print(render(template, case_params(cases[name], presets), pin))
        return 0

    wanted = list(cases) if any(x.lower() == "all" for x in args.case) else [x.upper() for x in args.case]
    unknown = [x for x in wanted if x not in cases]
    if unknown:
        raise c.CheckError(f"unknown case(s) {', '.join(unknown)}; known: {', '.join(cases)}")
    results = [run_case(n, cases[n], template, presets, pin, args.profile) for n in wanted]
    res = {"ok": all(r["ok"] for r in results), "query": ref["query"],
           "ref_date_mode": "live CURRENT_DATE" if pin is None else f"pinned {pin}", "cases": results}
    return c.emit(res, args.json, human)


if __name__ == "__main__":
    c.run_main(main)
