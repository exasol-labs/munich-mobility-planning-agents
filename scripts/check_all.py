#!/usr/bin/env python3
"""Run every tutorial check and print one summary table. Read-only.

1. readiness: `python3 install.py --check` (kit, database, dash-server, skills, agent, key present)
2. data:      scripts/verify_data.py (20 row counts plus data checks)
3. numbers:   scripts/verify_numbers.py --case all (R1-R6)
4. dashboards: scripts/check_dashboard.py for each app in tests/expected.json; an app that is not deployed
   is reported as "not deployed" and does not fail the run (use --require-all to make it fail).

    python3 scripts/check_all.py
    python3 scripts/check_all.py --json
    python3 scripts/check_all.py --skip-dashboards --base http://127.0.0.1:5100

Exit code: 0 everything passed, 1 something failed.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys

import _common as c

SCRIPTS = c.REPO / "scripts"


def sub(cmd: list[str], timeout: int = 900) -> tuple[int, str, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=str(c.REPO))
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return 2, "", f"timed out after {timeout} s"


def step_readiness() -> dict:
    rc, out, err = sub([sys.executable, str(c.REPO / "install.py"), "--check"], timeout=120)
    lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
    fails = [ln[4:].strip() for ln in lines if ln.startswith("FAIL")]
    warns = [ln[4:].strip() for ln in lines if ln.startswith("WARN")]
    n_ok = sum(1 for ln in lines if ln.startswith("OK"))
    detail = f"{n_ok} ok" + (f", {len(warns)} warn ({'; '.join(warns)})" if warns else "") + \
             (f", FAIL: {'; '.join(fails)}" if fails else "") + (f" {err.strip()[-200:]}" if rc and not fails else "")
    return {"step": "readiness (install.py --check)", "status": "pass" if rc == 0 else "fail", "detail": detail, "lines": lines}


def step_json(name: str, cmd: list[str], summarize) -> dict:
    rc, out, err = sub(cmd)
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return {"step": name, "status": "fail", "detail": (err or out).strip()[-300:] or f"exit {rc}"}
    if data.get("error"):
        return {"step": name, "status": "fail", "detail": data["error"], "result": data}
    return {"step": name, "status": "pass" if rc == 0 and data.get("ok") else "fail", "detail": summarize(data), "result": data}


def sum_data(d: dict) -> str:
    s = d["summary"]
    bad = [t["table"] for t in d["tables"] if t["status"] in ("mismatch", "missing")]
    checks = sum(1 for k in d["checks"] if k["status"] == "ok")
    return (f"{s['ok']}/{len(d['tables']) - s['extra']} tables match, {checks}/{len(d['checks'])} data checks ok"
            + (f"; differ: {', '.join(bad)}" if bad else ""))


def sum_numbers(d: dict) -> str:
    good = [x["case"] for x in d["cases"] if x["ok"]]
    bad = [x["case"] for x in d["cases"] if not x["ok"]]
    return f"{len(good)}/{len(d['cases'])} cases match ({d['ref_date_mode']})" + (f"; failed: {', '.join(bad)}" if bad else "")


def sum_dash(d: dict) -> str:
    if d.get("status") == "not_deployed":
        return "not deployed"
    failed = [k["check"] for k in d.get("checks", []) if not k["ok"]]
    poly = next((k["detail"] for k in d.get("checks", []) if "polygons" in k["check"]), "")
    extra = f", title '{d['map_title']}'" if d.get("map_title") and "(now)" in d["map_title"] else ""
    return (f"{d.get('map_output', '?')}, {poly}{extra}, {d.get('callback_secs', '?')} s"
            + (f"; FAILED: {'; '.join(failed)}" if failed else ""))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], epilog="Exit 0 = everything passed, 1 = something failed.")
    ap.add_argument("--json", action="store_true", help="print the result as JSON")
    ap.add_argument("--base", help="Dash Server URL (default: from `exakit status --json`)")
    ap.add_argument("--skip-dashboards", action="store_true", help="skip the dashboard smoke tests")
    ap.add_argument("--require-all", action="store_true", help="fail when an app is not deployed")
    args = ap.parse_args()

    py = sys.executable
    steps = [step_readiness(),
             step_json("data (verify_data)", [py, str(SCRIPTS / "verify_data.py"), "--json"], sum_data),
             step_json("numbers (verify_numbers R1-R6)", [py, str(SCRIPTS / "verify_numbers.py"), "--case", "all", "--json"], sum_numbers)]
    if not args.skip_dashboards:
        base = args.base or c.dash_base_url()
        apps = [k for k in (c.load_expected().get("dashboards") or {}) if not k.startswith("_")]
        for app in apps:
            st = step_json(f"dashboard {app}", [py, str(SCRIPTS / "check_dashboard.py"), app, "--base", base, "--json"], sum_dash)
            if (st.get("result") or {}).get("status") == "not_deployed":
                st["status"] = "fail" if args.require_all else "not deployed"
            steps.append(st)
    ok = all(s["status"] in ("pass", "not deployed") for s in steps)
    res = {"ok": ok, "steps": steps}

    def human(r):
        rows = [[s["step"], s["status"].upper() if s["status"] == "fail" else s["status"], s["detail"]] for s in r["steps"]]
        print(c.table(rows, ["check", "status", "detail"]))
        n = {k: sum(1 for s in r["steps"] if s["status"] == k) for k in ("pass", "fail", "not deployed")}
        print(f"\n{'PASS' if r['ok'] else 'FAIL'}: {n['pass']} passed, {n['fail']} failed, {n['not deployed']} not deployed")

    return c.emit(res, args.json, human)


if __name__ == "__main__":
    c.run_main(main)
