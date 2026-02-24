# FPL MCP Server - Product Requirements Document

## Overview

Build an MCP (Model Context Protocol) server that wraps the existing `fpl/` package, exposing FPL league data as tools queryable by Claude Desktop and Claude Code. The server provides both low-level API wrappers (1:1 with `FPL_API` methods) and higher-level composite tools that combine multiple API calls into rich, contextualized responses. Read-only — no write/action tools.

## Target Users

Anyone using Claude Desktop or Claude Code who wants to query FPL league data conversationally — "How is the league looking this week?", "Who had the best captain pick in GW15?", "Show me Salah's stats".

## Core Requirements

1. Stdio-based MCP server using FastMCP that Claude Desktop/Code can launch as a subprocess
2. Low-level tools wrapping each `FPL_API` method (standings, team, history, picks, transfers, live events, bootstrap)
3. Composite tool: league summary — combines standings, stats, and current GW overview into one rich response
4. Composite tool: gameweek report — combines picks, transfers, live data, and awards for a specific GW
5. Composite tool: player search — searches bootstrap data by player name with stats and ownership info
6. Dev mode support — `--dev` flag uses sample data, no live API calls needed
7. Configuration documentation for Claude Desktop and Claude Code setup

## Tech Stack

- **Language**: Python 3.13
- **MCP SDK**: FastMCP (`fastmcp` package — decorator-based, stdio transport)
- **Data layer**: Existing `fpl/` package (`FPL_API`, `FPLLeague`, `PlayerRegistry`, `WeeklyReport`, stats functions)
- **Testing**: pytest (existing)
- **Linting**: ruff, mypy (existing)

## Architecture

```
mcp_server/
  __init__.py
  server.py          # FastMCP server instance + tool definitions
  tools_api.py       # Low-level API wrapper tools
  tools_composite.py # Higher-level composite tools
  __main__.py        # Entry point (python -m mcp_server)
```

The MCP server imports from `fpl/` directly (same repo). A shared `FPL_API` instance is created at server startup and passed to all tools. Dev mode is controlled by a `--dev` CLI flag.

### Tool Inventory

**Low-level tools** (direct API wrappers):

| Tool | Wraps | Description |
|------|-------|-------------|
| `get_league_standings` | `FPL_API.get_league_standings()` | Current league table with ranks and points |
| `get_team_info` | `FPL_API.get_team()` | Basic team info for a manager |
| `get_team_history` | `FPL_API.get_team_history()` | Full GW-by-GW history for a team |
| `get_team_picks` | `FPL_API.get_team_picks()` | Squad picks for a specific GW |
| `get_transfers` | `FPL_API.get_transfers()` | Transfer history for a team |
| `get_event_live` | `FPL_API.get_event_live()` | Live player points for a GW |
| `get_bootstrap` | `FPL_API.get_bootstrap_static()` | Global data: players, teams, events |

**Composite tools** (multi-call, enriched):

| Tool | Description |
|------|-------------|
| `league_summary` | Standings + season stats + current GW status. Uses `FPLLeague` + `statistics.py`. |
| `gameweek_report` | Full GW breakdown: picks, captains, transfers, bench points, awards. Uses `WeeklyReport` + `weekly_report_stats.py`. |
| `player_search` | Find players by name. Returns stats, ownership, recent form. Uses `PlayerRegistry` + bootstrap data. |

### Default League ID

The server uses league ID `1639886` (Sinkaberg Superliga) as the default. All tools accept an optional `league_id` parameter to override this.

## Success Criteria

- `python -m mcp_server` starts a working stdio MCP server
- `python -m mcp_server --dev` starts with sample data
- All 10 tools are discoverable and callable from Claude Desktop/Code
- Composite tools return rich, well-structured data suitable for conversational responses
- Configuration docs enable setup in under 5 minutes
- All tests pass, ruff clean, mypy clean

---

## Tasks

The task list below drives autonomous agent execution. Each task must be:
- **Atomic**: Completable in one agent session without context overflow
- **Verifiable**: Has clear acceptance criteria an agent can test
- **Ordered**: Respects dependencies (earlier tasks don't depend on later ones)

```json
[
  {
    "id": 1,
    "category": "setup",
    "title": "Scaffold MCP server package with FastMCP",
    "description": "Create the mcp_server/ package directory with __init__.py, server.py, and __main__.py. Install fastmcp (add to requirements.txt). In server.py, create a FastMCP instance named 'FPL League' with a brief instruction string. In __main__.py, parse --dev and --league-id CLI flags (argparse), create a shared FPL_API instance, store it on the server (mcp.settings or module-level), and call mcp.run() for stdio transport. Verify the server starts without errors: python -m mcp_server. Follow existing project patterns (see generate_html.py for argparse patterns).",
    "acceptance_criteria": [
      "mcp_server/ directory exists with __init__.py, server.py, __main__.py",
      "fastmcp added to requirements.txt",
      "server.py creates FastMCP('FPL League') instance",
      "__main__.py parses --dev and --league-id (default: 1639886) flags",
      "__main__.py creates FPL_API(dev_mode=args.dev) and stores it accessibly",
      "python -m mcp_server starts without errors (stdio transport)",
      "python -m mcp_server --dev starts with dev mode enabled",
      "Ruff clean, mypy clean, all existing tests pass"
    ],
    "passes": false
  },
  {
    "id": 2,
    "category": "feature",
    "title": "Implement low-level API wrapper tools",
    "description": "Create mcp_server/tools_api.py with 7 MCP tools that wrap FPL_API methods 1:1. Each tool should use the @mcp.tool decorator, accept the same parameters as the underlying API method (with clear docstrings), call the shared FPL_API instance, and return the raw API response. Tools: get_league_standings(league_id), get_team_info(team_id), get_team_history(team_id), get_team_picks(team_id, event_id), get_transfers(team_id), get_event_live(event_id), get_bootstrap(). Import and register tools in server.py. The league_id parameter should default to the configured league ID where applicable (get_league_standings). All other ID parameters are required strings.",
    "acceptance_criteria": [
      "mcp_server/tools_api.py exists with 7 tool functions",
      "Each tool uses @mcp.tool decorator with descriptive docstring",
      "get_league_standings defaults league_id to the configured default",
      "get_team_info, get_team_history, get_transfers accept team_id: str",
      "get_team_picks accepts team_id: str and event_id: str",
      "get_event_live accepts event_id: str",
      "get_bootstrap takes no parameters",
      "All tools call the shared FPL_API instance and return raw response",
      "Tools are registered on the FastMCP server (importable and discoverable)",
      "Ruff clean, mypy clean"
    ],
    "passes": false
  },
  {
    "id": 3,
    "category": "feature",
    "title": "Implement composite tool: league_summary",
    "description": "Create mcp_server/tools_composite.py and implement the league_summary tool. This tool combines multiple API calls into a rich league overview. Steps: (1) Create FPLLeague instance from the shared API and league_id. (2) Call get_summary() to get participants with stats. (3) Use statistics.py functions to add: highest team value, in-form players, closest overall rank gap, biggest rank loss. (4) Include league info (name, current GW, next deadline). (5) Return a well-structured dict with sections: league_info, standings (with rank, points, GW points, form), season_stats, current_gameweek_status. Accept optional league_id parameter (defaults to configured ID).",
    "acceptance_criteria": [
      "mcp_server/tools_composite.py exists",
      "league_summary tool registered with @mcp.tool and clear docstring",
      "Creates FPLLeague to get standings and participant data",
      "Includes statistics: highest team value, in-form players, closest rank gap, biggest rank loss",
      "Response includes league_info section (name, current GW, next deadline)",
      "Response includes standings list with rank, total_points, event_total, team_name, manager_name",
      "Response includes season_stats section with computed statistics",
      "Accepts optional league_id parameter with default",
      "Ruff clean, mypy clean"
    ],
    "passes": false
  },
  {
    "id": 4,
    "category": "feature",
    "title": "Implement composite tool: gameweek_report",
    "description": "Add the gameweek_report tool to mcp_server/tools_composite.py. This tool provides a detailed breakdown of a specific gameweek. Steps: (1) Create WeeklyReport instance with the shared API, league_id, and event_id. (2) Call build() to get the full report dict (standings, awards, league_summary, meta). (3) Return the report dict directly — it already has the right structure (see docs/WEEKLY_REPORT_PLAN.md for schema). Accept league_id (optional, default) and event_id (required int). If event_id is not provided, auto-detect the latest finished GW from bootstrap data (same logic as generate_weekly_report.py). Import WeeklyReport from fpl.weekly_report.",
    "acceptance_criteria": [
      "gameweek_report tool added to tools_composite.py",
      "Registered with @mcp.tool and clear docstring explaining what it returns",
      "Creates WeeklyReport and calls build() to generate full report",
      "Returns complete report dict with meta, standings, awards, league_summary",
      "Accepts optional league_id (default) and optional event_id",
      "Auto-detects latest finished GW when event_id is omitted",
      "Ruff clean, mypy clean"
    ],
    "passes": false
  },
  {
    "id": 5,
    "category": "feature",
    "title": "Implement composite tool: player_search",
    "description": "Add the player_search tool to mcp_server/tools_composite.py. This tool searches for FPL players by name and returns enriched info. Steps: (1) Get bootstrap data from shared API. (2) Create PlayerRegistry. (3) Search bootstrap elements[] for players whose first_name or second_name or web_name contains the query string (case-insensitive). (4) For each match (limit to 10 results), return: full name, team, position, total_points, event_points (current GW), now_cost (divide by 10 for display), selected_by_percent, form, minutes. (5) Sort results by total_points descending. Accept query (required str) and max_results (optional int, default 10).",
    "acceptance_criteria": [
      "player_search tool added to tools_composite.py",
      "Registered with @mcp.tool and clear docstring",
      "Accepts query: str (required) and max_results: int (optional, default 10)",
      "Searches elements by first_name, second_name, and web_name (case-insensitive substring match)",
      "Returns list of player dicts with: name, team, position, total_points, event_points, price, selected_by_percent, form, minutes",
      "Results sorted by total_points descending",
      "Results limited to max_results",
      "Uses PlayerRegistry for team name resolution",
      "Returns empty list with message when no matches found",
      "Ruff clean, mypy clean"
    ],
    "passes": false
  },
  {
    "id": 6,
    "category": "test",
    "title": "Tests for MCP server tools",
    "description": "Create tests/test_mcp_server/ directory with test files for the MCP server tools. Use DummyAPI pattern from existing tests — create a DummyAPI that implements FPLAPIProtocol with sample data from tests/fpl_tests/data_samples/. Test low-level tools: verify each tool calls the correct API method and returns the expected response type. Test composite tools: verify league_summary returns expected structure, verify gameweek_report returns report with awards, verify player_search finds players and returns correct fields. Test edge cases: player_search with no matches, player_search case insensitivity. Do NOT test the MCP transport layer — test the tool functions directly by calling them.",
    "acceptance_criteria": [
      "tests/test_mcp_server/ directory exists with __init__.py",
      "Test file(s) for API tools and composite tools",
      "Uses DummyAPI or existing test fixtures for sample data",
      "Tests verify low-level tools return correct response types",
      "Tests verify league_summary response structure (league_info, standings, season_stats)",
      "Tests verify gameweek_report response structure (meta, standings, awards)",
      "Tests verify player_search finds players by name substring",
      "Tests verify player_search case insensitivity",
      "Tests verify player_search empty result handling",
      "All tests pass: python -m pytest tests/test_mcp_server/"
    ],
    "passes": false
  },
  {
    "id": 7,
    "category": "setup",
    "title": "Configuration docs and project updates",
    "description": "Create docs/MCP_SERVER_SETUP.md with setup instructions for Claude Desktop and Claude Code. For Claude Desktop: show the claude_desktop_config.json snippet with command/args pointing to python -m mcp_server (and --dev variant). For Claude Code: show the .mcp.json project config or settings.json snippet. Include: prerequisites (Python 3.13, pip install -r requirements.txt), available tools list with descriptions, example queries ('Ask Claude: How is the league doing?'). Update root AGENTS.md to document the MCP server module (brief entry in Module Documentation and Directory Structure sections). Add mcp_server/AGENTS.md with module documentation for the MCP server package. Verify end-to-end: python -m mcp_server --dev starts and tools are listed.",
    "acceptance_criteria": [
      "docs/MCP_SERVER_SETUP.md exists with setup instructions",
      "Claude Desktop config example: claude_desktop_config.json snippet with correct command/args",
      "Claude Code config example: .mcp.json or settings.json snippet",
      "Prerequisites section: Python 3.13, dependencies installation",
      "Available tools table with name and description for all 10 tools",
      "Example queries section showing what users can ask",
      "Root AGENTS.md updated with MCP server entry in Module Documentation and Directory Structure",
      "mcp_server/AGENTS.md exists with module documentation",
      "Ruff clean, mypy clean, all tests pass"
    ],
    "passes": false
  }
]
```

---

## Agent Instructions

1. Read `prd/fpl-mcp-server-activity.md` to understand current state
2. Find the next task where `"passes": false`
3. Complete all acceptance criteria for that task
4. Verify the feature works (run tests, check manually)
5. Update the task to `"passes": true`
6. Log completion in `prd/fpl-mcp-server-activity.md`
7. Commit changes with descriptive message

**Critical:** Only modify the `passes` field. Never remove, edit, or reorder tasks.

**Before committing any task**, follow the workflow from AGENTS.md:
```bash
source venv/Scripts/activate
python -m ruff check --fix .
python -m mypy fpl/ --ignore-missing-imports
python -m pytest
```

**Reference docs:**
- `fpl/AGENTS.md` — Module documentation, DummyAPI pattern, test fixtures
- `fpl/fpl_api.py` — FPL_API class with all available methods
- `fpl/fpl_api_protocol.py` — FPLAPIProtocol for type-safe API access
- `fpl/statistics.py` — Season-level stat functions
- `fpl/weekly_report_stats.py` — Gameweek award calculations
- `fpl/weekly_report.py` — WeeklyReport orchestrator
- `fpl/player_registry.py` — Player name/metadata lookup
- `AGENTS.md` — Project conventions, testing patterns, code quality rules
