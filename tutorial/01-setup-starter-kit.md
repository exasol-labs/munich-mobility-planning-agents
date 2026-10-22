# 1 · Set up the Exasol Personal Local Starter Kit

**Goal:** a local Exasol database, Dash Server for the dashboards, and your coding agent (Codex or Claude Code) connected to both over MCP.

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
The installer asks two questions:
- **AI clients for the MCP server:** select the agent you'll use
- **Marketplace add-ons:** select **dash-server**. It hosts every dashboard in this tutorial.

## 1.2 Check that everything runs

```bash
exakit status
```
The output should include:
```
Runtime     personal · running
Database    127.0.0.1:8563 · reachable
dash-server running · http://127.0.0.1:5100
```
Open <http://127.0.0.1:5100> in a browser. Your dashboards will appear there.

## 1.3 Get this repo

```bash
git clone https://github.com/exasol-labs/munich-mobility-planning-agents.git
cd munich-mobility-planning-agents
```
All later commands run from this folder.

## 1.4 Start your agent in the repo folder

[AGENTS.md](../AGENTS.md) holds the standing instructions for the agent: the data, the model, the dashboard conventions and the Dash Server deploy steps. The prompts in the following chapters rely on it.

**Codex**
```bash
codex
```
Codex reads `AGENTS.md` on its own. Run `/mcp` in Codex to list the MCP servers.

**Claude Code**
```bash
claude
```
Run `/mcp` in Claude Code to list the MCP servers.

Either way, two servers should be connected:
- **exasol:** read-only SQL on your database. Its login can read everything and change nothing; the database enforces that.
- **dash-server:** the control plane the agent uses to create and deploy dashboards.

Next: [2 · Load the Munich data](02-load-data.md)
