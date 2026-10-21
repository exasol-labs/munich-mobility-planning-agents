# 1 · Set up the Exasol Personal Local Starter Kit

**Goal:** a local Exasol database, Dash Server for the dashboards, and Claude Code connected to both over MCP.
**Time:** about 15 minutes, mostly downloads.

## 1.1 Install the starter kit
Go to <https://www.exasol.com/personal/>, or run the installer for your OS in a terminal:

macOS / Linux / WSL
```bash
curl https://www.exasol.com/install/starter-kit.sh | sh
```
Windows PowerShell
```powershell
irm https://www.exasol.com/install/starter-kit.ps1 | iex
```
The installer asks two things that matter here:
- **AI clients for the MCP server:** select **Claude**. That covers both Claude Code and the Claude desktop app.
- **Marketplace add-ons:** select **dash-server**. It hosts every dashboard in this tutorial.

You can add dash-server later: `exakit marketplace dash-server`, then `exakit mcp-setup` and `exakit start`.

## 1.2 Check that everything runs
```bash
exakit status
```
You want to see:
```
Runtime     personal · running
Database    127.0.0.1:8563 · reachable
dash-server running · http://127.0.0.1:5100
```
Open <http://127.0.0.1:5100> in a browser. That's where your dashboards will appear.

## 1.3 Get this repo
```bash
git clone https://github.com/exasol-labs/munich-mobility-planning-agents.git
cd munich-mobility-planning-agents
```
All later commands run from this folder.

## 1.4 Start Claude Code
```bash
claude
```
In Claude Code, run `/mcp`. You should see two servers connected:
- **exasol:** read-only SQL on your database (its login can read everything and change nothing; the database enforces that)
- **dash-server:** the control plane Claude uses to create and deploy dashboards

If one is missing, see [Troubleshooting](10-troubleshooting.md#mcp-servers-missing).

## Check
- `exakit status` shows the database reachable and dash-server running.
- `/mcp` in Claude Code lists `exasol` and `dash-server`.

Next: [2 · Load the Munich data](02-load-data.md)
