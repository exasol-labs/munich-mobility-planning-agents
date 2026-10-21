#!/usr/bin/env python3
"""Compare the row counts of schema MUNICH_DATASET with tests/expected.json (read-only).

Counts every table with COUNT(*) through `exapump sql -p starter-kit`, reports missing, extra and
mismatched tables, and runs the extra data checks from expected.json (e.g. SUM(pop_2024) = 1,603,776).
Only SELECT statements are sent.

    python3 scripts/verify_data.py           human summary
    python3 scripts/verify_data.py --json    machine-readable result

Exit code: 0 all match, 1 a mismatch, 2 could not run (exapump missing, database down).
"""
from __future__ import annotations

import argparse

import _common as c


def verify(expected: dict, profile: str = c.PROFILE) -> dict:
    schema = expected.get("schema", c.SCHEMA)
    want = expected["tables"]
    have = c.table_counts(schema, profile)
    tables = []
    for name in sorted(set(want) | set(have)):
        exp, act = want.get(name), have.get(name)
        if exp is None:
            status = "extra"
        elif act is None:
            status = "missing"
        else:
            status = "ok" if exp == act else "mismatch"
        tables.append({"table": name, "expected": exp, "actual": act, "status": status})
    checks = []
    for chk in expected.get("data_checks", []):
        try:
            rows = c.run_sql(chk["sql"], profile=profile)
            val = rows[0].get("v") if rows else None
            val = float(val) if val is not None else None
            ok = val is not None and abs(val - chk["value"]) <= chk.get("tol", 0)
            checks.append({"label": chk["label"], "expected": chk["value"], "actual": val, "status": "ok" if ok else "mismatch"})
        except c.CheckError as exc:
            checks.append({"label": chk["label"], "expected": chk["value"], "actual": None, "status": "error", "error": str(exc)})
    # an extra table is reported but is not a failure (the schema may hold your own work)
    ok = all(t["status"] in ("ok", "extra") for t in tables) and all(k["status"] == "ok" for k in checks)
    return {"ok": ok, "schema": schema, "tables": tables, "checks": checks,
            "summary": {s: sum(1 for t in tables if t["status"] == s) for s in ("ok", "mismatch", "missing", "extra")}}


def human(res: dict) -> None:
    rows = [[t["table"], c.fmt_num(t["expected"]), c.fmt_num(t["actual"]), t["status"].upper() if t["status"] != "ok" else "ok"]
            for t in res["tables"]]
    print(f"Row counts in {res['schema']}")
    print(c.table(rows, ["table", "expected", "actual", "status"]))
    for k in res["checks"]:
        print(f"check: {k['label']}: expected {c.fmt_num(k['expected'])}, actual {c.fmt_num(k['actual'])} -> {k['status']}"
              + (f" ({k['error']})" if k.get("error") else ""))
    s = res["summary"]
    print(f"\n{'PASS' if res['ok'] else 'FAIL'}: {s['ok']} ok, {s['mismatch']} mismatch, {s['missing']} missing, {s['extra']} extra")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], epilog="Exit 0 = all match, 1 = mismatch, 2 = could not run.")
    ap.add_argument("--json", action="store_true", help="print the result as JSON")
    ap.add_argument("--expected", help="path to expected.json (default tests/expected.json)")
    ap.add_argument("--profile", default=c.PROFILE, help="exapump profile (default starter-kit)")
    args = ap.parse_args()
    return c.emit(verify(c.load_expected(args.expected), args.profile), args.json, human)


if __name__ == "__main__":
    c.run_main(main)
