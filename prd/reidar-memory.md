# Reidar Memory System - Product Requirements Document

## Overview

Build a general-purpose agent memory system backed by SQLite + FTS5 that stores discrete, searchable facts. Designed as a shared foundation for both the weekly narrative pipeline (Reidar) and the future chat agent. Each fact is an atomic record with metadata (category, entity, source event, timestamp), enabling precise retrieval — only pull what's relevant, keep token usage low.

This PRD supersedes weekly-report tasks 13 and 15 (MD-file memory scaffold and memory update).

## Target Users

- **Reidar (weekly narrative)**: Needs season context when writing — manager profiles, running jokes, recent form, season arcs. Retrieves ~50-100 relevant facts per narrative generation.
- **Chat agent (future)**: Needs real-time context during conversation — "what happened to Torkel last week?", "who's on the longest green arrow streak?". Searches memory on demand.

## Core Requirements

1. SQLite database with FTS5 full-text search for fact retrieval
2. `Fact` dataclass representing a single atomic piece of knowledge with metadata
3. `MemoryStore` class with store/search/retrieve interface — general-purpose, not Reidar-specific
4. Filtered retrieval: by entity (manager), category, source event, recency
5. Context assembly: combine retrieved facts into a formatted prompt string with token budgeting
6. LLM fact extraction: after narrative generation, Claude extracts discrete facts from report JSON + narrative
7. Integration with weekly report pipeline: replaces MD-file memory system

## Tech Stack

- **Language**: Python 3.13
- **Database**: SQLite 3 (stdlib) + FTS5 virtual table
- **LLM Client**: anthropic SDK (existing dependency)
- **Testing**: pytest (existing)
- **Linting**: ruff, mypy (existing)

## Architecture

```
memory/
  __init__.py
  fact.py            # Fact dataclass
  store.py           # MemoryStore: SQLite + FTS5 storage and retrieval
  context.py         # Context assembly for prompt inclusion
  extraction.py      # LLM-based fact extraction from reports/narratives
```

The `memory/` package is a top-level module (alongside `fpl/` and `mcp_server/`). It has no dependency on `fpl/` — it's a general-purpose fact store. Reidar-specific behavior lives in the extraction prompts and how the weekly report pipeline queries memory.

### Data Model

#### Fact Dataclass

```python
@dataclass
class Fact:
    content: str                    # The fact itself: "Torkel took a -12 hit in GW15"
    category: str                   # performance | transfer | captain | chip | opinion | arc | profile | record
    entity: str | None = None       # Manager first name, or None for league-wide facts
    source_event: int | None = None # GW number, or None for season-level facts
    source_type: str = "report"     # report | narrative | chat
    created_at: datetime | None = None  # Auto-set on storage
    is_evergreen: bool = False      # True for facts that shouldn't decay (season records, running jokes)
    id: int | None = None           # Auto-assigned by database
```

#### Categories

| Category | Description | Example |
|----------|-------------|---------|
| `performance` | Scores, ranks, form | "Ola scored 87 points in GW15, highest of the season" |
| `transfer` | Transfer decisions, hits | "Lars took a -8 hit to bring in Salah and Palmer" |
| `captain` | Captain picks and outcomes | "Eva captained Isak when everyone else picked Salah — paid off with 18 points" |
| `chip` | Chip usage and results | "Per played bench boost in GW12, gained only 4 extra points" |
| `opinion` | Reidar's subjective takes | "Torkel's team selection is increasingly chaotic" |
| `arc` | Season storylines, rivalries | "The title race between Ola and Hedda has been within 10 points for 5 weeks" |
| `profile` | Manager personality, archetypes | "Simon is the league ghost — hasn't made a transfer since GW8" |
| `record` | Season records, milestones | "87 points in GW15 is the new season-high single-GW score" |

#### SQLite Schema

```sql
CREATE TABLE facts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    category TEXT NOT NULL,
    entity TEXT,
    source_event INTEGER,
    source_type TEXT NOT NULL DEFAULT 'report',
    created_at TEXT NOT NULL,
    is_evergreen INTEGER NOT NULL DEFAULT 0
);

CREATE VIRTUAL TABLE facts_fts USING fts5(
    content,
    category,
    entity,
    content=facts,
    content_rowid=id
);
```

### Interface

```python
class MemoryStore:
    def __init__(self, db_path: Path) -> None: ...
    def store(self, facts: list[Fact]) -> None: ...
    def search(self, query: str, limit: int = 20, category: str | None = None, entity: str | None = None) -> list[Fact]: ...
    def get_by_entity(self, entity: str, limit: int = 20, category: str | None = None) -> list[Fact]: ...
    def get_by_event(self, event_id: int, entity: str | None = None) -> list[Fact]: ...
    def get_recent(self, limit: int = 50, entity: str | None = None) -> list[Fact]: ...
    def count(self, category: str | None = None, entity: str | None = None) -> int: ...
```

### Context Assembly

```python
def build_context(
    store: MemoryStore,
    query: str | None = None,
    managers: list[str] | None = None,
    event_id: int | None = None,
    max_tokens: int = 4000
) -> str: ...
```

Assembles a formatted prompt string by combining:
1. Manager profiles (facts with category `profile` for each requested manager)
2. Season arcs (facts with category `arc`, `is_evergreen=True`)
3. Recent facts for the relevant GW window
4. Query-specific search results (if query provided)

Respects `max_tokens` budget by prioritizing: profiles > arcs > recent > search results. Uses approximate token counting (words * 1.3).

### LLM Fact Extraction

After each narrative is generated, a Claude API call extracts facts:

**Input**: Report JSON + generated narrative
**Output**: List of `Fact` objects with appropriate categories and metadata

The extraction prompt instructs Claude to:
- Extract objective facts from the report (scores, ranks, transfers, captains)
- Extract subjective observations from the narrative (Reidar's opinions, running jokes)
- Identify season arc developments
- Flag evergreen facts (records, milestones)
- Use the manager's first name as the `entity` field

## Success Criteria

- `MemoryStore` can store and retrieve facts via FTS5 search
- Filtered retrieval by entity, category, event, recency works correctly
- Context assembly produces well-formatted prompt text within token budget
- LLM extraction produces meaningful facts from a sample report + narrative
- Weekly report pipeline uses `MemoryStore` instead of MD files
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
    "category": "data",
    "title": "Create Fact model and SQLite schema with FTS5",
    "description": "Create the memory/ top-level package with __init__.py and fact.py. In fact.py, define a Fact dataclass with fields: content (str), category (str), entity (str | None), source_event (int | None), source_type (str, default 'report'), created_at (datetime | None), is_evergreen (bool, default False), id (int | None, default None). Define VALID_CATEGORIES as a module-level tuple: ('performance', 'transfer', 'captain', 'chip', 'opinion', 'arc', 'profile', 'record'). Add a validate() method on Fact that checks category is in VALID_CATEGORIES and content is non-empty. Add to_dict() and from_row() class methods for SQLite serialization. Ruff clean, mypy clean.",
    "acceptance_criteria": [
      "memory/ directory exists with __init__.py and fact.py",
      "Fact dataclass has all specified fields with correct types and defaults",
      "VALID_CATEGORIES tuple defined with 8 categories",
      "validate() raises ValueError for invalid category or empty content",
      "to_dict() returns a plain dict suitable for JSON serialization",
      "from_row() class method reconstructs a Fact from a SQLite row tuple",
      "Ruff clean, mypy clean, all existing tests pass"
    ],
    "passes": false
  },
  {
    "id": 2,
    "category": "feature",
    "title": "Implement MemoryStore with SQLite storage and FTS5 search",
    "description": "Create memory/store.py with MemoryStore class. Constructor takes db_path (Path), creates SQLite database with facts table and facts_fts FTS5 virtual table (see schema in PRD). Use content triggers to keep FTS5 index in sync with facts table (INSERT, DELETE, UPDATE triggers). Methods: (1) store(facts: list[Fact]) — validates each fact, auto-sets created_at if None, inserts into facts table (FTS5 updates via trigger). (2) search(query: str, limit=20, category=None, entity=None) — uses FTS5 MATCH on content, optionally filters by category and entity, returns list[Fact] ordered by FTS5 rank. (3) count(category=None, entity=None) — returns total fact count with optional filters. Database creation should be idempotent (CREATE TABLE IF NOT EXISTS). Use context managers for connections.",
    "acceptance_criteria": [
      "memory/store.py exists with MemoryStore class",
      "Constructor creates SQLite database with facts table and facts_fts FTS5 virtual table",
      "FTS5 sync triggers (INSERT, DELETE, UPDATE) keep index in sync",
      "store() validates facts, auto-sets created_at, inserts into database",
      "store() handles batch inserts efficiently",
      "search() uses FTS5 MATCH and returns Fact objects ordered by relevance",
      "search() supports optional category and entity filters",
      "count() returns correct counts with optional filters",
      "Database creation is idempotent (safe to call multiple times)",
      "Ruff clean, mypy clean"
    ],
    "passes": false
  },
  {
    "id": 3,
    "category": "feature",
    "title": "Implement filtered retrieval helpers on MemoryStore",
    "description": "Add retrieval methods to MemoryStore in memory/store.py: (1) get_by_entity(entity: str, limit=20, category=None) — returns all facts for a specific manager, optionally filtered by category, ordered by created_at descending. (2) get_by_event(event_id: int, entity=None) — returns all facts for a specific GW, optionally filtered by entity. (3) get_recent(limit=50, entity=None) — returns the most recent facts ordered by created_at descending, optionally filtered by entity. (4) get_evergreen(entity=None) — returns all facts where is_evergreen=True, optionally filtered by entity. All methods return list[Fact]. Use parameterized queries to prevent SQL injection.",
    "acceptance_criteria": [
      "get_by_entity() returns facts filtered by entity, ordered by recency",
      "get_by_entity() supports optional category filter",
      "get_by_event() returns facts for a specific source_event",
      "get_by_event() supports optional entity filter",
      "get_recent() returns N most recent facts, ordered by created_at descending",
      "get_recent() supports optional entity filter",
      "get_evergreen() returns only facts with is_evergreen=True",
      "All methods use parameterized queries (no string formatting for SQL)",
      "All methods return list[Fact]",
      "Ruff clean, mypy clean"
    ],
    "passes": false
  },
  {
    "id": 4,
    "category": "feature",
    "title": "Implement context assembly for prompt inclusion",
    "description": "Create memory/context.py with a build_context() function. Signature: build_context(store: MemoryStore, query: str | None = None, managers: list[str] | None = None, event_id: int | None = None, max_tokens: int = 4000) -> str. Assembly logic: (1) If managers specified, retrieve profile facts for each manager (category='profile'). (2) Retrieve evergreen arc facts (category='arc', is_evergreen=True). (3) If event_id specified, retrieve facts from the last 5 GWs (event_id-4 to event_id). (4) If query specified, run FTS5 search for additional context. (5) Deduplicate facts by id. (6) Format into sections: '## Manager Profiles', '## Season Arcs', '## Recent Events', '## Relevant Context'. (7) Respect max_tokens budget — use approximate token counting (len(text.split()) * 1.3), truncate lowest-priority sections first (search results > recent > arcs > profiles). Return the assembled string.",
    "acceptance_criteria": [
      "memory/context.py exists with build_context() function",
      "Retrieves profile facts for specified managers",
      "Retrieves evergreen arc facts",
      "Retrieves recent GW facts when event_id is specified (window of 5)",
      "Runs FTS5 search when query is provided",
      "Deduplicates facts by id across all sources",
      "Formats output into clearly labeled markdown sections",
      "Respects max_tokens budget with priority-based truncation",
      "Returns empty string gracefully when no facts exist",
      "Ruff clean, mypy clean"
    ],
    "passes": false
  },
  {
    "id": 5,
    "category": "feature",
    "title": "Implement LLM fact extraction prompt and parser",
    "description": "Create memory/extraction.py with fact extraction functionality. Define EXTRACTION_PROMPT as a module-level string template — this is the system prompt for Claude that instructs it to extract discrete facts from a gameweek report and narrative. The prompt should explain the Fact schema (categories, entity field, is_evergreen), provide examples of good facts for each category, and request output as a JSON array of fact objects. Implement extract_facts(report: dict, narrative: str, client, event_id: int, model: str = 'claude-sonnet-4-6') -> list[Fact] — calls the anthropic client with EXTRACTION_PROMPT as system message, report JSON + narrative as user message, parses the JSON response into Fact objects. Handle JSON parsing errors gracefully (log warning, return empty list). Implement parse_extraction_response(response_text: str, event_id: int) -> list[Fact] as a separate testable function that parses Claude's JSON output into validated Fact objects.",
    "acceptance_criteria": [
      "memory/extraction.py exists",
      "EXTRACTION_PROMPT explains all 8 categories with examples",
      "EXTRACTION_PROMPT requests JSON array output format",
      "EXTRACTION_PROMPT instructs use of first names for entity field",
      "extract_facts() calls anthropic client with correct system/user messages",
      "extract_facts() returns list[Fact] with source_event set to event_id",
      "parse_extraction_response() parses JSON string into validated Fact objects",
      "parse_extraction_response() handles malformed JSON gracefully (returns empty list)",
      "parse_extraction_response() skips facts with invalid categories",
      "Ruff clean, mypy clean"
    ],
    "passes": false
  },
  {
    "id": 6,
    "category": "test",
    "title": "Tests for MemoryStore storage and retrieval",
    "description": "Create tests/test_memory/ directory with test_store.py. Test MemoryStore using tmp_path for database files (no persistent state between tests). Tests: (1) store() inserts facts and assigns IDs. (2) store() auto-sets created_at. (3) store() validates facts (rejects invalid category). (4) search() finds facts by keyword. (5) search() filters by category and entity. (6) search() returns empty list for no matches. (7) get_by_entity() returns correct facts. (8) get_by_event() returns correct facts. (9) get_recent() returns facts in recency order. (10) get_evergreen() returns only evergreen facts. (11) count() returns correct counts with filters. (12) Database creation is idempotent. Create test fixtures with realistic FPL facts covering multiple managers, categories, and events.",
    "acceptance_criteria": [
      "tests/test_memory/ directory exists with __init__.py and test_store.py",
      "Tests use tmp_path for isolated database files",
      "store() insertion and ID assignment tested",
      "store() created_at auto-set tested",
      "store() validation tested (invalid category rejected)",
      "search() keyword matching tested",
      "search() category and entity filtering tested",
      "get_by_entity(), get_by_event(), get_recent(), get_evergreen() tested",
      "count() with filters tested",
      "Edge case: empty database returns empty results",
      "All tests pass: python -m pytest tests/test_memory/"
    ],
    "passes": false
  },
  {
    "id": 7,
    "category": "test",
    "title": "Tests for context assembly and fact extraction",
    "description": "Create tests/test_memory/test_context.py and tests/test_memory/test_extraction.py. For context assembly: test build_context() with various combinations of managers, event_id, and query. Test token budget enforcement (verify output doesn't exceed max_tokens). Test empty database returns empty string. Test section formatting (verify markdown headers present). For extraction: test parse_extraction_response() with valid JSON, malformed JSON, invalid categories, missing fields. Test extract_facts() with mocked anthropic client (mock the messages.create call, return a predetermined JSON string). Do NOT make real API calls.",
    "acceptance_criteria": [
      "tests/test_memory/test_context.py exists",
      "tests/test_memory/test_extraction.py exists",
      "build_context() tested with managers, event_id, query combinations",
      "Token budget enforcement tested (output within max_tokens)",
      "Empty database context test (returns empty string)",
      "Section formatting test (markdown headers present)",
      "parse_extraction_response() tested with valid JSON input",
      "parse_extraction_response() tested with malformed JSON (returns empty list)",
      "parse_extraction_response() tested with invalid categories (skipped)",
      "extract_facts() tested with mocked anthropic client",
      "All tests pass: python -m pytest tests/test_memory/"
    ],
    "passes": false
  },
  {
    "id": 8,
    "category": "feature",
    "title": "Integrate memory system with weekly report pipeline",
    "description": "Update generate_weekly_report.py to use the new memory system instead of the planned MD-file approach. When --narrative flag is set: (1) Create MemoryStore with db_path at memory_db/{league_id}/{season}/reidar.db (create directories as needed). (2) Call build_context(store, managers=[list of participant first names], event_id=event_id) to get memory context. (3) Pass memory context to NarrativeGenerator.generate() (when task 14 from weekly-report PRD is implemented — for now, just wire up the memory loading and print the context size). (4) After narrative generation, call extract_facts() to extract new facts and store them via MemoryStore.store(). Update memory/__init__.py to export MemoryStore, Fact, build_context, extract_facts. Update root AGENTS.md with brief memory module entry. Update fpl-mcp-server PRD's reference docs if needed. Note: the actual narrative generation (weekly-report task 14) is not yet implemented — this task wires up the memory system so it's ready when the narrative generator lands.",
    "acceptance_criteria": [
      "generate_weekly_report.py creates MemoryStore when --narrative flag is set",
      "Database stored at memory_db/{league_id}/{season}/reidar.db",
      "build_context() called with correct manager names and event_id",
      "Memory context passed to narrative generation step (or printed if generator not yet available)",
      "After narrative generation, extract_facts() is called and facts are stored",
      "memory/__init__.py exports MemoryStore, Fact, build_context, extract_facts",
      "memory_db/ added to .gitignore",
      "Root AGENTS.md updated with memory module entry",
      "Ruff clean, mypy clean, all tests pass"
    ],
    "passes": false
  }
]
```

---

## Agent Instructions

1. Read `prd/reidar-memory-activity.md` to understand current state
2. Find the next task where `"passes": false`
3. Complete all acceptance criteria for that task
4. Verify the feature works (run tests, check manually)
5. Update the task to `"passes": true`
6. Log completion in `prd/reidar-memory-activity.md`
7. Commit changes with descriptive message

**Critical:** Only modify the `passes` field. Never remove, edit, or reorder tasks.

**Before committing any task**, follow the workflow from AGENTS.md:
```bash
source venv/Scripts/activate
python -m ruff check --fix .
python -m mypy fpl/ memory/ --ignore-missing-imports
python -m pytest
```

**Reference docs:**
- `AGENTS.md` — Project conventions, testing patterns, code quality rules
- `fpl/AGENTS.md` — Module documentation, DummyAPI pattern
- `prd/weekly-report.md` — Weekly report PRD (tasks 13 and 15 are superseded by this PRD)
- `docs/WEEKLY_REPORT_PLAN.md` — Report data schema
- `docs/REIDAR_PERSONA.md` — Reidar character definition

**Relationship to weekly-report PRD:**
- This PRD supersedes weekly-report tasks 13 (memory scaffold) and 15 (memory update)
- Weekly-report task 14 (narrative generator) should reference this memory system via `build_context()`
- Weekly-report tasks 10-12 (persona docs) are unaffected
