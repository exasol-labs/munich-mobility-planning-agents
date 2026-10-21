"""Shared helpers for the check scripts in scripts/: running SQL through exapump, the pyexasol-compatible
placeholder formatter, tests/expected.json, the Dash Server URL and the human / --json output.

Standard library only. Nothing here prints credentials: exapump reads them from its own profile.
"""
from __future__ import annotations

import json
import re
import shutil
import string
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EXPECTED = REPO / "tests" / "expected.json"
SCHEMA = "MUNICH_DATASET"
PROFILE = "starter-kit"
DEFAULT_DASH_URL = "http://127.0.0.1:5100"


class CheckError(Exception):
    """A failure the scripts report as a clean message (no traceback)."""


# ---------------------------------------------------------------------------------------------
# expected.json
# ---------------------------------------------------------------------------------------------

def load_expected(path: Path | None = None) -> dict:
    p = Path(path) if path else EXPECTED
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise CheckError(f"{p} not found")
    except json.JSONDecodeError as exc:
        raise CheckError(f"{p} is not valid JSON: {exc}")


# ---------------------------------------------------------------------------------------------
# SQL through exapump
# ---------------------------------------------------------------------------------------------

_LEADING_COMMENTS = re.compile(r"^\s*(?:--[^\n]*\n\s*|/\*.*?\*/\s*)*", re.S)


def is_read_only(sql: str) -> bool:
    """True when the statement is a single SELECT / WITH query (comments ignored)."""
    body = _LEADING_COMMENTS.sub("", sql, count=1).lstrip("(").lstrip().upper()
    return body.startswith("SELECT") or body.startswith("WITH")


def exapump_bin() -> str:
    exe = shutil.which("exapump")
    if not exe:
        raise CheckError("exapump not found on PATH (install the starter kit, tutorial chapter 1)")
    return exe


def run_sql(sql: str, *, profile: str = PROFILE, allow_write: bool = False, timeout: int = 600) -> list[dict]:
    """Run one statement with `exapump sql -f json`, SQL on stdin. Returns rows with lower-case keys
    (columns that are NULL are absent in exapump's JSON and come back as None only if you .get() them).

    The starter-kit profile has write rights, so this refuses anything but a SELECT / WITH query unless
    allow_write=True (used only by load_data.py --replace for DROP TABLE)."""
    if not allow_write and not is_read_only(sql):
        raise CheckError("refusing to run a non-SELECT statement in read-only mode")
    try:
        proc = subprocess.run([exapump_bin(), "sql", "-p", profile, "-f", "json", "-"], input=sql,
                              capture_output=True, text=True, encoding="utf-8", timeout=timeout)
    except subprocess.TimeoutExpired:
        raise CheckError(f"exapump timed out after {timeout} s")
    if proc.returncode != 0:
        msg = [ln.strip() for ln in (proc.stderr or proc.stdout).splitlines() if ln.strip().startswith(("Error", "Query"))]
        raise CheckError("exapump failed: " + (msg[-1] if msg else (proc.stderr or "").strip()[-400:]))
    out = proc.stdout.strip()
    if not out:
        return []
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        # statements without a result set (DROP ...) print nothing useful
        return []
    if not isinstance(data, list):
        return []
    return [{str(k).lower(): v for k, v in row.items()} for row in data]


def table_counts(schema: str = SCHEMA, profile: str = PROFILE) -> dict[str, int]:
    """Exact COUNT(*) per table of the schema ({} when the schema does not exist)."""
    rows = run_sql(f"SELECT TABLE_NAME FROM SYS.EXA_ALL_TABLES WHERE TABLE_SCHEMA = '{schema}' ORDER BY TABLE_NAME", profile=profile)
    names = [r["table_name"] for r in rows]
    if not names:
        return {}
    union = "\nUNION ALL\n".join(f"SELECT '{n}' AS t, COUNT(*) AS n FROM \"{schema}\".\"{n}\"" for n in names)
    return {r["t"]: int(r["n"]) for r in run_sql(union, profile=profile)}


# ---------------------------------------------------------------------------------------------
# pyexasol-compatible placeholder formatter (same rules as pyexasol.ExaFormatter)
# ---------------------------------------------------------------------------------------------

class ExaFormatter(string.Formatter):
    """{x!s} quoted string (single quotes doubled), {x!d} integer/decimal, {x!f} float, {x!r} raw,
    {x!i} safe identifier, {x!q} quoted identifier; {{ and }} are literal braces. format_spec is disabled."""
    safe_ident_regexp = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
    safe_decimal_regexp = re.compile(r"^(\+|-)?[0-9]+(\.[0-9]+)?$")
    safe_float_regexp = re.compile(r"^(\+|-)?[0-9]+(\.[0-9]+((e|E)(\+|-)[0-9]+)?)?$")

    def __init__(self):
        self.conversions = {"s": self.quote, "d": self.safe_decimal, "f": self.safe_float, "i": self.safe_ident,
                            "q": self.quote_ident, "r": str}

    def format_field(self, value, format_spec):
        if format_spec != "":
            raise ValueError("format_spec is disabled for ExaFormatter")
        return value

    def convert_field(self, value, conversion):
        conv = self.conversions.get(conversion or "s")
        if conv is None:
            raise ValueError(f"Unknown conversion {conversion}")
        if isinstance(value, list):
            if not value:
                raise ValueError("Trying to format an empty list")
            return ", ".join(conv(v) for v in value)
        return conv(value)

    @staticmethod
    def quote(val):
        return "NULL" if val is None else "'" + str(val).replace("'", "''") + "'"

    @staticmethod
    def quote_ident(val):
        if isinstance(val, tuple):
            return ".".join(ExaFormatter.quote_ident(x) for x in val)
        return '"' + str(val).replace('"', '""') + '"'

    @classmethod
    def safe_ident(cls, val):
        if isinstance(val, tuple):
            return ".".join(cls.safe_ident(x) for x in val)
        val = str(val)
        if not cls.safe_ident_regexp.match(val):
            raise ValueError(f"Value [{val}] is not a safe identifier")
        return val

    @classmethod
    def safe_float(cls, val):
        if val is None:
            return "NULL"
        val = str(val)
        if not cls.safe_float_regexp.match(val):
            raise ValueError(f"Value [{val}] is not a safe float")
        return val

    @classmethod
    def safe_decimal(cls, val):
        if val is None:
            return "NULL"
        val = str(val)
        if not cls.safe_decimal_regexp.match(val):
            raise ValueError(f"Value [{val}] is not a safe integer")
        return val


def render_sql(template: str, params: dict) -> str:
    return ExaFormatter().vformat(template, (), params)


# ---------------------------------------------------------------------------------------------
# Dash Server URL
# ---------------------------------------------------------------------------------------------

def dash_base_url() -> str:
    """The dash-server URL from `exakit status --json`, else the default http://127.0.0.1:5100."""
    exe = shutil.which("exakit")
    if exe:
        try:
            proc = subprocess.run([exe, "status", "--json"], capture_output=True, text=True, timeout=60)
            url = (json.loads(proc.stdout or "{}").get("urls") or {}).get("dash-server")
            if url:
                return url.rstrip("/")
        except (subprocess.SubprocessError, json.JSONDecodeError, OSError):
            pass
    return DEFAULT_DASH_URL


# ---------------------------------------------------------------------------------------------
# output
# ---------------------------------------------------------------------------------------------

def fmt_num(v) -> str:
    if v is None:
        return "-"
    if isinstance(v, float) and not v.is_integer():
        return f"{v:,.3f}".rstrip("0").rstrip(".") if abs(v) < 100 else f"{v:,.2f}"
    return f"{int(v):,}"


def table(rows: list[list], headers: list[str]) -> str:
    cells = [[str(c) for c in r] for r in rows]
    widths = [max(len(h), *(len(r[i]) for r in cells)) if cells else len(h) for i, h in enumerate(headers)]
    line = lambda r: "  ".join(c.ljust(w) for c, w in zip(r, widths)).rstrip()
    return "\n".join([line(headers), line(["-" * w for w in widths]), *(line(r) for r in cells)])


def emit(result: dict, as_json: bool, human) -> int:
    """Print result as JSON or via human(result); return the exit code (0 when result['ok'])."""
    if as_json:
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    else:
        human(result)
    sys.stdout.flush()
    return 0 if result.get("ok") else 1


def run_main(main) -> None:
    """Run main() -> int, turning CheckError and Ctrl-C into a clean message and exit code 2 / 130."""
    try:
        sys.exit(main())
    except CheckError as exc:
        if "--json" in sys.argv:
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)
    except KeyboardInterrupt:
        sys.exit(130)
