# Reidar Chat Agent - Product Requirements Document

## Overview

Add Reidar as an interactive chat persona to the existing FPL MCP server. When a user loads Reidar's prompt in Claude Desktop/Code, Claude adopts the Reidar persona — a sharp-witted Norwegian FPL columnist — and can query live league data and persistent memory to answer questions in character. Phase 1 only: MCP integration. Phase 2 (future, out of scope): Teams bot.

## Target Users

League members using Claude Desktop or Claude Code who want to chat with Reidar about the league. "Reidar, how's Torkel doing this season?", "What happened in GW15?", "Who should I be worried about in the title race?"

## Core Requirements

1. Reidar persona exposed as an MCP prompt on the existing FPL MCP server
2. Memory query tools: search memory, get manager context, get season overview
3. Memory write tool: save noteworthy facts from conversation for future recall
4. Persona prompt that loads Reidar's character + relevant memory context automatically
5. Works alongside existing FPL data tools — Reidar can pull live data mid-conversation

## Tech Stack

- **Existing**: FastMCP server (`mcp_server/`), `fpl/` package, `memory/` package
- **No new dependencies** — builds on top of the MCP server and memory system from PRDs 1 and 2

## Architecture

This PRD adds to the existing `mcp_server/` package:

```
mcp_server/
  server.py              # (existing) FastMCP server instance
  tools_api.py           # (existing) Low-level API wrappers
  tools_composite.py     # (existing) Composite tools
  tools_memory.py        # (NEW) Memory query/write tools for chat
  prompts.py             # (NEW) Reidar persona prompt
```

### How It Works

1. User selects the "reidar" prompt in Claude Desktop/Code
2. Claude loads Reidar's persona (from `docs/REIDAR_PERSONA.md`) + memory context (recent facts, season arcs)
3. User asks a question: "How's the title race looking?"
4. Claude (as Reidar) uses existing FPL tools (`league_summary`, `gameweek_report`) to get live data
5. Claude uses memory tools (`search_memory`) to recall relevant history
6. Claude responds in Reidar's voice, weaving data and memory together
7. If the conversation produces noteworthy observations, Claude uses `remember_fact` to store them

### New MCP Components

**Prompt:**

| Prompt | Description |
|--------|-------------|
| `reidar` | Loads Reidar's full persona + relevant memory context. Accepts optional `topic` parameter to pre-load topic-specific memory. |

**Tools (memory):**

| Tool | Description |
|------|-------------|
| `search_memory` | FTS5 search across all facts. Returns relevant memories matching a query. |
| `get_manager_profile` | Get all known facts about a specific manager — form, history, Reidar's opinions. |
| `get_season_overview` | Get season arcs, records, active storylines, evergreen facts. |
| `remember_fact` | Store a new fact from conversation. Allows Reidar to build memory during chat. |

### Memory Integration

The chat agent uses the same `MemoryStore` from the `memory/` package. The `reidar` prompt dynamically loads memory context when invoked. Memory tools allow on-demand retrieval during conversation and fact storage for continuity.

**Prompt assembly:**
```
[Reidar persona from REIDAR_PERSONA.md]

## Your Memory (what you know so far this season)
[build_context() output with season arcs, manager profiles, recent events]

## Instructions
- You ARE Reidar. Stay in character at all times.
- Use the FPL data tools to look up live data when needed.
- Use memory tools to recall specific facts or search for context.
- Use remember_fact to store important observations for future conversations.
- Always respond in Norwegian.
- Never acknowledge being an AI or break character.
```

## Dependencies

- **PRD 1 (fpl-mcp-server)**: MCP server must exist with FPL data tools
- **PRD 2 (reidar-memory)**: Memory system must exist with MemoryStore and build_context()

## Success Criteria

- Selecting the "reidar" prompt in Claude loads Reidar's persona with memory context
- Reidar can answer questions about the league using live FPL data tools
- Reidar can recall season history via memory tools
- Reidar can store new observations via `remember_fact`
- All responses are in Norwegian and in Reidar's distinctive voice
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
    "category": "feature",
    "title": "Implement memory tools for MCP server",
    "description": "Create mcp_server/tools_memory.py with 4 MCP tools that wrap the memory/ package. (1) search_memory(query: str, category: str | None = None, limit: int = 10) — calls MemoryStore.search(), returns list of fact dicts. (2) get_manager_profile(manager_name: str) — calls MemoryStore.get_by_entity() with the manager name, returns profile + recent performance facts. (3) get_season_overview() — calls MemoryStore.get_evergreen() + get_recent(limit=30), returns season arcs and recent storylines. (4) remember_fact(content: str, category: str, entity: str | None = None, is_evergreen: bool = False) — creates a Fact with source_type='chat' and stores it via MemoryStore.store(). All tools require a MemoryStore instance — get it from the shared server state (same pattern as FPL_API). Import and register tools in server.py. Update __main__.py to create MemoryStore alongside FPL_API (db_path from --memory-db flag or default memory_db/{league_id}/reidar.db).",
    "acceptance_criteria": [
      "mcp_server/tools_memory.py exists with 4 tool functions",
      "search_memory uses @mcp.tool, calls MemoryStore.search(), returns fact dicts",
      "get_manager_profile returns profile + performance facts for a manager",
      "get_season_overview returns evergreen facts + recent storylines",
      "remember_fact creates and stores a Fact with source_type='chat'",
      "remember_fact validates category against VALID_CATEGORIES",
      "All tools registered on the FastMCP server",
      "__main__.py creates MemoryStore with configurable db_path",
      "Ruff clean, mypy clean"
    ],
    "passes": false
  },
  {
    "id": 2,
    "category": "feature",
    "title": "Implement Reidar persona prompt",
    "description": "Create mcp_server/prompts.py with the 'reidar' MCP prompt. Use @mcp.prompt decorator. The prompt function: (1) Reads docs/REIDAR_PERSONA.md for the persona text. (2) Calls build_context() from memory/ to get current memory context (season arcs, manager profiles, recent events). (3) Assembles the full prompt: persona text + memory context section + behavioral instructions (stay in character, use FPL tools for live data, use memory tools for recall, use remember_fact for new observations, always respond in Norwegian, never break character). Accept optional topic: str parameter — if provided, also run a memory search for the topic and include results. Import and register in server.py. The persona file path should be relative to the project root (use Path(__file__).parent.parent / 'docs' / 'REIDAR_PERSONA.md').",
    "acceptance_criteria": [
      "mcp_server/prompts.py exists with reidar prompt function",
      "Uses @mcp.prompt decorator with descriptive name and description",
      "Reads REIDAR_PERSONA.md for persona text",
      "Calls build_context() to include memory context",
      "Assembles full prompt with persona + memory + behavioral instructions",
      "Behavioral instructions: stay in character, use tools, respond in Norwegian",
      "Optional topic parameter triggers additional memory search",
      "Handles missing persona file gracefully (clear error message)",
      "Handles empty memory gracefully (works on first run)",
      "Prompt registered on the FastMCP server",
      "Ruff clean, mypy clean"
    ],
    "passes": false
  },
  {
    "id": 3,
    "category": "test",
    "title": "Tests for memory tools and Reidar prompt",
    "description": "Create tests/test_mcp_server/test_tools_memory.py and tests/test_mcp_server/test_prompts.py. For memory tools: create a MemoryStore with tmp_path, pre-populate with sample facts, test each tool function directly (not via MCP transport). Verify search_memory returns matching facts, get_manager_profile returns correct manager facts, get_season_overview returns evergreen + recent facts, remember_fact stores a new fact with source_type='chat'. For prompts: test the reidar prompt function returns a string containing the persona text and memory sections. Mock the file reading if needed. Test with empty memory (first run). Test with topic parameter.",
    "acceptance_criteria": [
      "tests/test_mcp_server/test_tools_memory.py exists",
      "tests/test_mcp_server/test_prompts.py exists",
      "search_memory tested with matching and non-matching queries",
      "get_manager_profile tested with known and unknown managers",
      "get_season_overview tested with populated memory",
      "remember_fact tested: stores fact and retrieves it back",
      "remember_fact tested: rejects invalid category",
      "Reidar prompt tested: contains persona text",
      "Reidar prompt tested: contains memory context section",
      "Reidar prompt tested: works with empty memory",
      "Reidar prompt tested: topic parameter adds search results",
      "All tests pass: python -m pytest tests/test_mcp_server/"
    ],
    "passes": false
  },
  {
    "id": 4,
    "category": "setup",
    "title": "Update configuration docs and project documentation",
    "description": "Update docs/MCP_SERVER_SETUP.md to document the new Reidar chat features: how to load the 'reidar' prompt in Claude Desktop/Code, available memory tools, example conversation starters. Add a 'Chatting with Reidar' section with: (1) How to activate Reidar (select the prompt). (2) Example queries: 'Hvordan går det med ligaen?', 'Hva skjedde i runde 15?', 'Hvem har best form akkurat nå?'. (3) How memory works (Reidar remembers across conversations). (4) Note that FPL data tools are available for live data. Update mcp_server/AGENTS.md with documentation for tools_memory.py and prompts.py. Update root AGENTS.md if the MCP server section needs expanding. Verify end-to-end: python -m mcp_server --dev shows all tools and the reidar prompt.",
    "acceptance_criteria": [
      "docs/MCP_SERVER_SETUP.md has 'Chatting with Reidar' section",
      "Documents how to load the reidar prompt",
      "Includes example conversation starters in Norwegian",
      "Explains memory system (Reidar remembers across conversations)",
      "Lists memory tools with descriptions",
      "mcp_server/AGENTS.md updated with tools_memory.py and prompts.py docs",
      "python -m mcp_server --dev lists all tools including memory tools",
      "python -m mcp_server --dev lists the reidar prompt",
      "Ruff clean, mypy clean, all tests pass"
    ],
    "passes": false
  }
]
```

---

## Agent Instructions

1. Read `prd/reidar-chat-agent-activity.md` to understand current state
2. Find the next task where `"passes": false`
3. Complete all acceptance criteria for that task
4. Verify the feature works (run tests, check manually)
5. Update the task to `"passes": true`
6. Log completion in `prd/reidar-chat-agent-activity.md`
7. Commit changes with descriptive message

**Critical:** Only modify the `passes` field. Never remove, edit, or reorder tasks.

**Before committing any task**, follow the workflow from AGENTS.md:
```bash
source venv/Scripts/activate
python -m ruff check --fix .
python -m mypy fpl/ memory/ mcp_server/ --ignore-missing-imports
python -m pytest
```

**Reference docs:**
- `prd/fpl-mcp-server.md` — MCP server PRD (must be completed first)
- `prd/reidar-memory.md` — Memory system PRD (must be completed first)
- `docs/REIDAR_PERSONA.md` — Reidar character definition
- `docs/MCP_SERVER_SETUP.md` — MCP server setup docs (created in fpl-mcp-server PRD)
- `mcp_server/AGENTS.md` — MCP server module docs (created in fpl-mcp-server PRD)
- `AGENTS.md` — Project conventions, testing patterns, code quality rules

**Dependencies:**
- All tasks in `prd/fpl-mcp-server.md` must be complete before starting this PRD
- All tasks in `prd/reidar-memory.md` must be complete before starting this PRD
