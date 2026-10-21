#!/usr/bin/env python3
"""Install the Munich Mobility tutorial into Claude Code: the urban-planning agent and its skills, the Dash Server
rule for every AI client found on this machine, and the link from secrets/openai_api_key to the place where the
v5 dashboard reads it (~/.exasol-starter-kit/credentials/openai_api_key).

    python3 install.py              install, then show what is ready and what is not
    python3 install.py --uninstall  remove what this installed
    python3 install.py --no-hook    skip the hook that blocks chat artifacts
    python3 install.py --check      only show what is ready and what is not; installs and changes nothing
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PERSONAS = ["urban-planning"]
SKILLS = ["munich-mobility-agents", *PERSONAS]
# installed by earlier versions of this repo; removed on install so no stale persona lingers
RETIRED = ["mobility-operations", "sustainability", "city-leadership", "persona-metrics"]
KEY_SRC = HERE / "secrets" / "openai_api_key"
KEY_DST = Path.home() / ".exasol-starter-kit" / "credentials" / "openai_api_key"
START, END = "<!-- munich-mobility-agents:start -->", "<!-- munich-mobility-agents:end -->"
HOOK_MARK = "block_artifacts.py"


def claude_home() -> Path:
    return Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")


def copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))


def install_skills(step) -> None:
    for name in SKILLS:
        src = HERE / "skill" / name
        for root in (claude_home() / "skills", Path.home() / ".agents" / "skills"):
            dst = root / name
            step(f"skill {name} -> {dst}")
            dst.parent.mkdir(parents=True, exist_ok=True)
            copy_tree(src, dst)
            for md in dst.rglob("*.md"):  # point the installed skill at this checkout
                text = md.read_text(encoding="utf-8")
                if "{{REPO}}" in text:
                    md.write_text(text.replace("{{REPO}}", str(HERE)), encoding="utf-8")
            if name in PERSONAS:
                # one shared look for the four dashboards; a single source in the repo, a copy per skill when installed
                (dst / "assets").mkdir(exist_ok=True)
                for shared in ("munich_ui.py", "app_skeleton.py"):
                    shutil.copy2(HERE / "skill" / "_shared" / shared, dst / "assets" / shared)
            if name == "munich-mobility-agents":
                (dst / "assets").mkdir(exist_ok=True)
                shutil.copy2(HERE / "scripts" / "prepare_dataset.py", dst / "assets" / "prepare_dataset.py")
                shutil.copy2(HERE / "AGENTS.md", dst / "AGENTS.md")


def install_agents(step) -> int:
    dst = claude_home() / "agents"
    dst.mkdir(parents=True, exist_ok=True)
    n = 0
    for f in sorted((HERE / "agents").glob("*.md")):
        step(f"agent -> {dst / f.name}")
        shutil.copy2(f, dst / f.name)
        n += 1
    return n


# Where each AI client reads its always-on instructions. The rule is appended between markers
# (idempotent) to the shared files, or written as its own rule file where the client has a rules folder.
# A client gets the rule only when its config folder exists, i.e. it is installed on this machine.
def client_rule_targets() -> list[tuple[str, Path, str]]:
    home = Path.home()
    return [
        ("Claude Code", claude_home() / "CLAUDE.md", "append"),
        ("Codex", home / ".codex" / "AGENTS.md", "append"),
        ("Gemini CLI", home / ".gemini" / "GEMINI.md", "append"),
        ("OpenCode", home / ".config" / "opencode" / "AGENTS.md", "append"),
        ("Cursor", home / ".cursor" / "rules" / "munich-mobility-agents.mdc", "cursor"),
        ("Continue", home / ".continue" / "rules" / "munich-mobility-agents.md", "continue"),
    ]


def _client_present(name: str, path: Path) -> bool:
    if name == "Claude Code":
        return True
    root = path.parent.parent if path.parent.name == "rules" else path.parent
    return root.is_dir()


def remove_legacy_commands(step) -> None:
    """Earlier versions installed /mobility-operations etc. as commands. The persona skills replace them
    (a skill is also a slash command), so drop the old files to avoid two entries with one name."""
    for name in PERSONAS:
        f = claude_home() / "commands" / f"{name}.md"
        if f.exists():
            step(f"remove legacy command {f}")
            f.unlink()


def install_rules(step) -> list[str]:
    block = (HERE / "claude-rules.md").read_text(encoding="utf-8").strip()
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    done = []
    for name, path, kind in client_rule_targets():
        if not _client_present(name, path):
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        if kind == "append":
            existing = path.read_text(encoding="utf-8") if path.exists() else ""
            new = pattern.sub(lambda _m: block, existing) if pattern.search(existing) else \
                (existing.rstrip() + "\n\n" if existing.strip() else "") + block + "\n"
        elif kind == "cursor":
            new = "---\ndescription: Dashboards on Exasol data are built on Dash Server (Munich demo)\nalwaysApply: true\n---\n" + block + "\n"
        else:  # continue
            new = "---\nname: munich-mobility-agents\nalwaysApply: true\n---\n" + block + "\n"
        step(f"rule for {name} -> {path}")
        path.write_text(new, encoding="utf-8")
        done.append(name)
    return done


def remove_rules() -> None:
    for name, path, kind in client_rule_targets():
        if not path.exists():
            continue
        if kind == "append":
            text = path.read_text(encoding="utf-8")
            new = re.sub(r"\n?" + re.escape(START) + r".*?" + re.escape(END) + r"\n?", "\n", text, flags=re.S).strip()
            path.write_text(new + ("\n" if new else ""), encoding="utf-8")
        else:
            path.unlink()


def install_hook(step, enable: bool) -> None:
    settings = claude_home() / "settings.json"
    data = {}
    if settings.exists():
        try:
            data = json.loads(settings.read_text(encoding="utf-8") or "{}")
        except json.JSONDecodeError:
            raise SystemExit(f"{settings} is not valid JSON; fix or remove it, then re-run.")
    hooks = data.setdefault("hooks", {})
    pre = hooks.setdefault("PreToolUse", [])
    pre[:] = [h for h in pre if HOOK_MARK not in json.dumps(h)]
    if enable:
        script = claude_home() / "skills" / "munich-mobility-agents" / "assets" / HOOK_MARK
        pre.append({"matcher": "Artifact|.*show_widget",
                    "hooks": [{"type": "command", "command": f'"{sys.executable}" "{script}"'}]})
        step(f"PreToolUse hook -> {settings}")
    if not pre:
        hooks.pop("PreToolUse", None)
    if not hooks:
        data.pop("hooks", None)
    settings.parent.mkdir(parents=True, exist_ok=True)
    settings.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def remove_retired(step) -> None:
    for name in RETIRED:
        for root in (claude_home() / "skills", Path.home() / ".agents" / "skills"):
            if (root / name).exists():
                step(f"remove retired skill {root / name}")
                shutil.rmtree(root / name, ignore_errors=True)
        f = claude_home() / "agents" / f"{name}.md"
        if f.exists():
            step(f"remove retired agent {f}")
            f.unlink()


def link_secret(step) -> str:
    """Point the kit's credentials path at secrets/openai_api_key. Never reads or prints the key."""
    if not KEY_SRC.exists():
        return "no key yet: put your OpenAI key in secrets/openai_api_key (only needed for v5)"
    if os.name != "nt":
        os.chmod(KEY_SRC, 0o600)
    KEY_DST.parent.mkdir(parents=True, exist_ok=True)
    if KEY_DST.is_symlink() and KEY_DST.resolve() == KEY_SRC.resolve():
        return f"key linked: {KEY_DST} -> {KEY_SRC}"
    if KEY_DST.exists() or KEY_DST.is_symlink():
        backup = KEY_DST.with_name(KEY_DST.name + ".before-tutorial")
        KEY_DST.replace(backup)
        step(f"kept the previous key file as {backup}")
    try:
        KEY_DST.symlink_to(KEY_SRC)
    except OSError:  # Windows without symlink rights: copy instead
        shutil.copy2(KEY_SRC, KEY_DST)
        return f"key copied to {KEY_DST} (re-run install.py after changing secrets/openai_api_key)"
    return f"key linked: {KEY_DST} -> {KEY_SRC}"


def readiness() -> int:
    """What is ready for the tutorial, and what is not. Changes nothing."""
    rows = []
    exakit = shutil.which("exakit")
    rows.append(("OK  " if exakit else "FAIL", "exakit on PATH", "" if exakit else "install the starter kit (tutorial step 1)"))
    if exakit:
        out = subprocess.run([exakit, "status"], capture_output=True, text=True).stdout
        db = "reachable" in out
        dash = "dash-server       running" in out
        rows.append(("OK  " if db else "FAIL", "database running", "" if db else "exakit start"))
        rows.append(("OK  " if dash else "FAIL", "dash-server running", "" if dash else "exakit marketplace dash-server, then exakit start"))
    for name in SKILLS:
        ok = (claude_home() / "skills" / name).is_dir()
        rows.append(("OK  " if ok else "FAIL", f"skill {name}", ""))
    ok = (claude_home() / "agents" / "urban-planning.md").exists()
    rows.append(("OK  " if ok else "FAIL", "agent urban-planning", ""))
    ok = KEY_SRC.exists()
    rows.append(("OK  " if ok else "WARN", "OpenAI key in secrets/openai_api_key", "" if ok else "only needed for v5"))
    for flag, what, fix in rows:
        print(f"  {flag}  {what}" + (f"  ->  {fix}" if fix else ""))
    return 1 if any(r[0] == "FAIL" for r in rows) else 0


def uninstall() -> int:
    for name in SKILLS:
        for root in (claude_home() / "skills", Path.home() / ".agents" / "skills"):
            shutil.rmtree(root / name, ignore_errors=True)
    for f in (HERE / "agents").glob("*.md"):
        (claude_home() / "agents" / f.name).unlink(missing_ok=True)
    remove_legacy_commands(lambda m: None)
    remove_rules()
    install_hook(lambda m: None, enable=False)
    if KEY_DST.is_symlink():
        KEY_DST.unlink()
    print("Removed: the skills, the agent, the Dash Server rule from every AI client, the PreToolUse hook "
          "and the key link. secrets/openai_api_key itself is left alone.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--uninstall", action="store_true")
    ap.add_argument("--no-hook", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--check", action="store_true", help="only run the readiness check; changes nothing")
    args = ap.parse_args()
    if args.check:
        return readiness()
    if args.uninstall:
        return uninstall()
    say = (lambda *a: None) if args.quiet else print
    step = (lambda m: print(f"==> {m}")) if args.verbose else (lambda m: None)

    remove_retired(step)
    install_skills(step)
    n = install_agents(step)
    remove_legacy_commands(step)
    clients = install_rules(step)
    install_hook(step, enable=not args.no_hook)

    key = link_secret(step)
    say(f"Installed: {n} agent, skills {', '.join(SKILLS)}, "
        f"Dash Server rule for {', '.join(clients)}{', hook' if not args.no_hook else ''}")
    say(key)
    say("")
    sys.stdout.flush()
    return readiness()

if __name__ == "__main__":
    sys.exit(main())
