#!/usr/bin/env python3
"""PreToolUse hook: keep dashboards on Dash Server.

Claude Code pipes the pending tool call to stdin as JSON ({"tool_name", "tool_input", ...}).
Exit 2 blocks the call and hands stderr to the agent as the reason. Exit 0 lets it through.

Blocked: the Artifact tool publishing a page (its default action) and any *show_widget* tool.
Allowed: Artifact read/list/open/delete (no page is produced), everything else.
Override for one session: MUNICH_ALLOW_ARTIFACTS=1.
"""
import json
import os
import sys

MESSAGE = (
    "Blocked by the munich-mobility-agents skill: on this machine every dashboard, chart or visual "
    "result is built on Dash Server, not as an artifact or inline widget. Build it through the "
    "dash-server MCP control plane with the deploy recipe in the munich-mobility-agents skill "
    "(app_create_exasol_dashboard -> app_put_files -> app_deploy_draft -> app_run_healthcheck; "
    "on Windows app_build -> app_run_healthcheck -> app_promote_revision) and give the user the URL "
    "from `exakit status --json`. If the dash-server tools are missing, do NOT fall back: install the "
    "add-on with `exakit marketplace dash-server`, then `exakit mcp-setup`, then `exakit start`, check "
    "`exakit status`, and ask the user to restart Claude so the dash-server tools load. "
    "Set MUNICH_ALLOW_ARTIFACTS=1 to override for one session."
)


def main() -> int:
    if os.environ.get("MUNICH_ALLOW_ARTIFACTS") == "1":
        return 0
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    name = str(payload.get("tool_name", ""))
    tool_input = payload.get("tool_input") or {}
    block = False
    if name == "Artifact":
        action = str(tool_input.get("action") or "publish").lower()
        block = action == "publish"
    elif name.endswith("show_widget"):
        block = True
    if block:
        sys.stderr.write(MESSAGE + "\n")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
