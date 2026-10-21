#!/usr/bin/env python3
"""Load data/munich-dataset.zip into schema MUNICH_DATASET, safely and repeatably, then verify.

0. If data/munich-dataset.zip is missing, downloads it from the GitHub release named in data/dataset.json
   and checks its size and SHA-256 (the zip is not in git; GitHub rejects files over 100 MB).
1. Unzips the archive to data/munich-dataset/ (skipped when the files are already there with the same size).
2. For every CSV, table = upper-case file name:
   - table missing                    -> loaded with unattended `exakit data-load` (EXAKIT_ON_EXISTING=skip)
   - table present, count as expected -> left alone
   - table present, count differs     -> reported; only with --replace: DROP TABLE, then `exapump upload`
                                         of that one CSV (never an append, which corrupts the table)
3. Runs scripts/verify_data.py.

Only MUNICH_DATASET is touched. Without --replace nothing is ever dropped.

    python3 scripts/load_data.py                       load what is missing, then verify
    python3 scripts/load_data.py --replace             also reload tables whose row count is wrong
    python3 scripts/load_data.py --dry-run             show what would happen, change nothing
    python3 scripts/load_data.py --zip other.zip --json

Exit code: 0 everything loaded and verified, 1 a table still differs or a load failed, 2 could not run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import urllib.request
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import _common as c
import verify_data

DEFAULT_ZIP = c.REPO / "data" / "munich-dataset.zip"
OUT_DIR = c.REPO / "data"
FOLDER = "munich-dataset"


DATASET_JSON = c.REPO / "data" / "dataset.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_zip(zpath: Path, url: str | None = None) -> str:
    """Download the dataset zip from the release in data/dataset.json if it is not there; verify it. Returns a note."""
    meta = json.loads(DATASET_JSON.read_text(encoding="utf-8"))
    url = url or meta["url"]
    if not zpath.exists():
        if zpath != DEFAULT_ZIP and url == meta["url"]:
            raise c.CheckError(f"{zpath} not found")
        print(f"Downloading {url} ...", file=sys.stderr)
        tmp = zpath.with_suffix(".zip.part")
        zpath.parent.mkdir(parents=True, exist_ok=True)
        try:
            with urllib.request.urlopen(url, timeout=120) as r, tmp.open("wb") as out:
                shutil.copyfileobj(r, out)
        except OSError as exc:
            tmp.unlink(missing_ok=True)
            raise c.CheckError(f"download failed ({exc}). Download it by hand from {url} into {zpath}")
        tmp.replace(zpath)
        note = "downloaded"
    else:
        note = "present"
    if zpath == DEFAULT_ZIP:
        size, digest = zpath.stat().st_size, sha256(zpath)
        if size != meta["bytes"] or digest != meta["sha256"]:
            raise c.CheckError(f"{zpath} does not match data/dataset.json (size {size}, sha256 {digest[:12]}…); "
                               f"delete it and run again to re-download")
        note += ", checksum ok"
    return note


def unzip(zpath: Path, out_dir: Path) -> tuple[Path, list[Path], int]:
    """Extract the CSVs of munich-dataset/ to out_dir/munich-dataset/; returns (folder, csvs, files written)."""
    if not zpath.exists():
        raise c.CheckError(f"{zpath} not found")
    dest = (out_dir / FOLDER).resolve()
    written = 0
    csvs = []
    with zipfile.ZipFile(zpath) as zf:
        for info in zf.infolist():
            name = info.filename
            if info.is_dir() or not name.lower().endswith(".csv"):
                continue
            target = (out_dir / name).resolve()
            if dest not in target.parents:  # no path traversal, only munich-dataset/*.csv
                raise c.CheckError(f"unexpected path in zip: {name}")
            csvs.append(target)
            if target.exists() and target.stat().st_size == info.file_size:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as src, open(target, "wb") as dst:
                shutil.copyfileobj(src, dst, 1 << 20)
            written += 1
    if not csvs:
        raise c.CheckError(f"{zpath} holds no CSVs under {FOLDER}/")
    return dest, sorted(csvs), written


def exakit_load(csv: Path, schema: str, table: str) -> tuple[bool, str]:
    exe = shutil.which("exakit")
    if not exe:
        return False, "exakit not found on PATH"
    env = dict(os.environ, EXAKIT_SCHEMA=schema, EXAKIT_DATA_FILE=str(csv), EXAKIT_DATA_TABLE=f"{schema}.{table}",
               EXAKIT_ON_EXISTING="skip")
    proc = subprocess.run([exe, "data-load"], env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True)
    tail = (proc.stdout + proc.stderr).strip().splitlines()[-3:]
    return proc.returncode == 0, " | ".join(tail)


def exapump_upload(csv: Path, schema: str, table: str, profile: str) -> tuple[bool, str]:
    proc = subprocess.run([c.exapump_bin(), "upload", "-p", profile, "-t", f"{schema}.{table}", str(csv)],
                          stdin=subprocess.DEVNULL, capture_output=True, text=True)
    tail = (proc.stdout + proc.stderr).strip().splitlines()[-2:]
    return proc.returncode == 0, " | ".join(tail)


def plan_and_load(args, expected: dict) -> dict:
    schema = expected.get("schema", c.SCHEMA)
    if schema != c.SCHEMA:
        raise c.CheckError(f"expected.json names schema {schema}; this script only loads {c.SCHEMA}")
    want = expected["tables"]
    zip_note = ensure_zip(Path(args.zip), args.url)
    folder, csvs, written = unzip(Path(args.zip), OUT_DIR)
    have = c.table_counts(schema, args.profile)
    actions, paths = [], {}
    for csv in csvs:
        table = csv.stem.upper()
        exp, act = want.get(table), have.get(table)
        paths[table] = csv
        a = {"table": table, "csv": csv.name, "expected": exp, "before": act}
        if act is None:
            a["action"] = "load"
        elif exp is None or act == exp:
            a["action"] = "keep"
        else:
            a["action"] = "replace" if args.replace else "differs"
        actions.append(a)
    for a in actions:
        if args.dry_run or a["action"] in ("keep", "differs"):
            a["result"] = "dry-run" if args.dry_run and a["action"] in ("load", "replace") else a["action"]
            continue
        csv = paths[a["table"]]
        if not args.json:
            print(f"  {a['action']:8} {a['table']} ...", flush=True)
        if a["action"] == "load":
            ok, msg = exakit_load(csv, schema, a["table"])
        else:
            c.run_sql(f'DROP TABLE "{schema}"."{a["table"]}"', profile=args.profile, allow_write=True)
            ok, msg = exapump_upload(csv, schema, a["table"], args.profile)
        a["result"] = "loaded" if ok else "failed"
        a["message"] = msg
    missing_csv = sorted(set(want) - {a["table"] for a in actions})
    verify = None if args.dry_run else verify_data.verify(expected, args.profile)
    ok = (not any(a.get("result") in ("failed", "differs") for a in actions) and not missing_csv
          and (verify is None or verify["ok"]))
    return {"ok": ok, "schema": schema, "zip": str(args.zip), "zip_status": zip_note, "folder": str(folder), "files_extracted": written,
            "dry_run": args.dry_run, "replace": args.replace, "tables": actions,
            "expected_without_csv": missing_csv, "verify": verify}


def human(res: dict) -> None:
    print(f"Zip {res['zip']} ({res.get('zip_status', '')}) -> {res['folder']} ({res['files_extracted']} file(s) extracted, the rest already there)")
    rows = [[a["table"], c.fmt_num(a["expected"]), c.fmt_num(a["before"]), a["action"], a.get("result", "")]
            for a in res["tables"]]
    print(c.table(rows, ["table", "expected", "rows before", "action", "result"]))
    for a in res["tables"]:
        if a.get("result") == "failed":
            print(f"  {a['table']} failed: {a.get('message')}")
    differs = [a["table"] for a in res["tables"] if a.get("result") == "differs"]
    if differs:
        print(f"\nRow counts differ: {', '.join(differs)}. Re-run with --replace to drop and reload just these tables.")
    if res["expected_without_csv"]:
        print(f"Expected tables with no CSV in the zip: {', '.join(res['expected_without_csv'])}")
    if res["verify"] is not None:
        print()
        verify_data.human(res["verify"])
    print(f"\n{'PASS' if res['ok'] else 'FAIL'}: load_data" + (" (dry run, nothing changed)" if res["dry_run"] else ""))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0],
                                 epilog="Exit 0 = loaded and verified, 1 = a table differs or a load failed, 2 = could not run.")
    ap.add_argument("--zip", default=str(DEFAULT_ZIP), help="the dataset zip (default data/munich-dataset.zip)")
    ap.add_argument("--url", help="download URL for the zip (default: the release in data/dataset.json)")
    ap.add_argument("--replace", action="store_true", help="drop and reload tables whose row count differs from expected.json")
    ap.add_argument("--dry-run", action="store_true", help="unzip and show the plan, load or drop nothing")
    ap.add_argument("--json", action="store_true", help="print the result as JSON")
    ap.add_argument("--expected", help="path to expected.json (default tests/expected.json)")
    ap.add_argument("--profile", default=c.PROFILE, help="exapump profile with write rights (default starter-kit)")
    args = ap.parse_args()
    return c.emit(plan_and_load(args, c.load_expected(args.expected)), args.json, human)


if __name__ == "__main__":
    c.run_main(main)
