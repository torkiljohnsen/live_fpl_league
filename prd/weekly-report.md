# Weekly FPL League Report & Narrative System - Product Requirements Document

## Overview

Build an automated weekly report system for FPL mini-leagues that generates structured JSON data about each gameweek's performance, then uses Claude API to write entertaining Norwegian-language narratives through the persona of "Reidar" — a seasoned FPL columnist and retired manager type. The system runs as a nightly GitHub Actions workflow, detecting finished gameweeks and producing both data reports and narratives automatically.

## Target Users

Members of the "Sinkaberg Superliga" FPL mini-league (and any other configured league). They receive "Reidars Rapport" — weekly Norwegian-language narratives summarizing gameweek highlights, awards, and storylines with sharp wit and sports commentary flair — committed to the repo and accessible via GitHub.

## Narrative Persona: Reidar

The narratives are written in-character as "Reidar" — a blend of neutral sports journalist and retired FPL veteran who has seen it all. Key traits:

- **Sharp wit, no filter**: Pulls no punches when managers underperform. Gives genuine praise when earned.
- **Sports commentary feel**: Writes like a columnist covering a local league — personal, opinionated, entertaining.
- **Dispenses wisdom**: Judges poor FPL decisions harshly but respects bold moves that pay off.
- **Norwegian league banter**: Informal Norwegian tone, FPL culture references, inside jokes that build over weeks.
- **Statistic obscurities**: Weaves in interesting stat nuggets and historical comparisons.
- **Recurring bits**: Develops running jokes, tracks storylines across gameweeks, builds rivalries.

See `prd/weekly-report-resources/previous-gameweek-reports.md` for tone reference (written by a league participant — Reidar's perspective is that of an outside observer, not a participant).

## Core Requirements

1. Extend the FPL API client with transfer history and live event data endpoints
2. Build a player registry that maps FPL element IDs to human-readable names
3. Calculate gameweek awards (top scorer, bench disasters, captain picks, etc.)
4. Orchestrate data collection into a self-contained JSON report per gameweek
5. Provide a CLI for manual report and narrative generation with dev mode support
6. Define the "Reidar" persona with voice rules, personality, and example outputs
7. Generate entertaining Norwegian narratives via Claude API (anthropic SDK) in Reidar's voice
8. Automate the full pipeline via GitHub Actions (nightly cron, GW detection, auto-commit)

## Tech Stack

- **Language**: Python 3.13
- **HTTP Client**: requests (existing)
- **LLM Client**: anthropic SDK (new dependency)
- **Testing**: pytest + pytest-cov (existing)
- **Linting**: ruff (existing)
- **Type Checking**: mypy (existing)
- **CI/CD**: GitHub Actions
- **API Key Management**: ANTHROPIC_API_KEY environment variable / GitHub secret

## Data Model

### GameweekParticipantData (intermediate, per participant per GW)

Key fields: `entry_id`, `team_name`, `manager_name`, `player_first_name`, `event_total`, `net_points`, `total_points`, `league_rank`, `league_rank_previous`, `league_rank_change`, `overall_rank`, `team_value`, `bank`, `bench_points`, `bench_players[]`, `chip_played`, `captain{}`, `vice_captain{}`, `squad[]`, `transfers[]`, `transfer_cost`, `transfers_made`

### Report Output (JSON)

Structure: `{ meta{}, standings[], awards{}, league_summary{} }`

See `docs/WEEKLY_REPORT_PLAN.md` for full schema definitions.

### Storage

```
reports/{league_id}/{season}/gw{N}.json           # Structured data
narratives/{league_id}/{season}/gw{N}.md          # LLM-generated narrative

reidar_memory/{league_id}/{season}/
  season_arc.md                                    # Rolling season summary, records, narrative threads
  managers/
    {first_name}.md                                # Per-manager profile (one per participant)
  gameweeks/
    gw{N}.md                                       # Brief GW recap (key events, Reidar's takes)
```

### Reidar Memory System

**"Reidar never forgets."** The memory system gives Reidar persistent knowledge across gameweeks, building genuine opinions, tracking storylines, and recalling specific moments from earlier in the season.

**Per-manager profile** (~200 words each, 8 files): current form, season trajectory, Reidar's evolving opinion, notable moments, running jokes, transfer habits, captain tendencies, personality notes.

**Season arc** (~300 words): title race narrative, active rivalry threads, season records, Reidar's ongoing storylines, tonal notes for the current phase of the season.

**GW summaries** (~100 words each): brief recap of key events, who Reidar praised/mocked, storyline developments.

**Prompt assembly (rolling window):** All 8 manager profiles + season arc + last 5 GW summaries. At any point in the season, memory context is ~4k words — stable and manageable.

**Update flow:** After each narrative is generated, a second LLM call updates all memory files with new facts (from report JSON) and subjective takes (from the narrative just written). On first run, profiles are bootstrapped from the report data.

## Awards Calculated

| Award | Function | Description |
|---|---|---|
| Top Gun | `get_highest_gameweek_scorer` | Highest net GW points |
| Tough Week | `get_lowest_gameweek_scorer` | Lowest net GW points |
| Comeback Kid | `get_biggest_rank_rise` | Most league positions gained (>=2) |
| Free Fall | `get_biggest_rank_fall` | Most league positions lost (>=2) |
| Bench Disaster | `get_bench_disasters` | 20+ bench pts without Bench Boost |
| Sharpest Trader | `get_transfer_impact` (best) | Best net transfer point gain |
| Transfer Tangle | `get_transfer_impact` (worst) | Worst net transfer result |
| Captain Picks | `get_captain_summary` | Most popular, best/worst captain |
| Chip Master | `get_chip_usage` | Chip played and result |
| Hit Takers | `get_hit_takers` | Point hits taken for transfers |

## Success Criteria

- GitHub Actions workflow runs nightly on cron schedule
- Workflow detects newly finished gameweeks via FPL API `finished` flag
- JSON report is generated with correct standings, awards, and metadata
- Claude API generates Norwegian narrative from JSON + narrative guide
- Both report and narrative are auto-committed to the repository
- CLI (`generate_weekly_report.py`) works for manual runs with `--dev` mode
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
    "category": "api",
    "title": "Extend FPL API with transfer and live event methods",
    "description": "Widen _get() and _call_api() and _read_sample_or_generate() return types from dict to dict | list (the transfers endpoint returns a JSON array). Add get_transfers(team_id) method calling /entry/{id}/transfers/ and get_event_live(event_id) method calling /event/{id}/live/. Update FPLAPIProtocol in fpl_api_protocol.py with the two new method signatures. Follow existing method patterns in fpl_api.py. Ensure dev mode sample generation works for the new endpoints (the file naming pattern in _read_sample_or_generate handles these paths automatically).",
    "acceptance_criteria": [
      "FPL_API._get() return type is dict | list",
      "FPL_API.get_transfers(team_id) exists and calls /entry/{team_id}/transfers/",
      "FPL_API.get_event_live(event_id) exists and calls /event/{event_id}/live/",
      "FPLAPIProtocol includes get_transfers and get_event_live signatures",
      "Dev mode works: calling get_transfers and get_event_live with dev_mode=True reads/generates sample files",
      "Ruff clean, mypy clean, all existing tests still pass"
    ],
    "passes": true
  },
  {
    "id": 2,
    "category": "data",
    "title": "Implement PlayerRegistry class",
    "description": "Create fpl/player_registry.py with a PlayerRegistry class that maps FPL element IDs to human-readable player names and metadata. Constructor takes bootstrap_data dict (from get_bootstrap_static()). Methods: get_player_name(element_id) -> str (e.g. 'Mohamed Salah'), get_player_info(element_id) -> dict (with name, team, position), get_team_name(team_code) -> str (e.g. 'Liverpool'). Build lookup dicts once at construction from bootstrap elements[] and teams[] arrays. No API calls - pure data transformation. Follow existing module patterns.",
    "acceptance_criteria": [
      "fpl/player_registry.py exists with PlayerRegistry class",
      "PlayerRegistry.__init__(bootstrap_data) builds element and team lookup dicts",
      "get_player_name(element_id) returns 'FirstName LastName' string",
      "get_player_info(element_id) returns dict with name, team, position keys",
      "get_team_name(team_code) returns team name string",
      "Handles missing IDs gracefully (returns 'Unknown Player' / 'Unknown Team')",
      "Ruff clean, mypy clean"
    ],
    "passes": true
  },
  {
    "id": 3,
    "category": "test",
    "title": "Tests for API extensions and PlayerRegistry",
    "description": "Write tests for the new API methods and PlayerRegistry. For API: create sample data files in tests/fpl_tests/data_samples/ for transfers (JSON array) and event live data (dict with elements). Test get_transfers and get_event_live using DummyAPI pattern. Update DummyAPI in test files to support the new methods. For PlayerRegistry: create a minimal bootstrap fixture with a few elements and teams, test all three methods including edge cases (missing IDs). Follow existing test patterns in tests/fpl_tests/.",
    "acceptance_criteria": [
      "Sample data files exist for transfers and event live endpoints in tests/fpl_tests/data_samples/",
      "DummyAPI supports get_transfers() and get_event_live() methods",
      "Tests verify get_transfers returns a list",
      "Tests verify get_event_live returns a dict with elements key",
      "Tests verify PlayerRegistry.get_player_name() returns correct names",
      "Tests verify PlayerRegistry.get_player_info() returns correct dicts",
      "Tests verify PlayerRegistry handles missing element IDs gracefully",
      "All tests pass: python -m pytest"
    ],
    "passes": true
  },
  {
    "id": 4,
    "category": "feature",
    "title": "Implement all weekly report stat functions",
    "description": "Create fpl/weekly_report_stats.py with all award calculation functions. These are pure functions: list of participant data dicts in, result dicts out. No formatting, no side effects. Functions: get_highest_gameweek_scorer(participants_data) -> dict|None, get_lowest_gameweek_scorer(participants_data) -> dict|None, get_biggest_rank_rise(participants_data) -> dict|None, get_biggest_rank_fall(participants_data) -> dict|None, get_bench_disasters(participants_data, threshold=20) -> list[dict], get_transfer_impact(participants_data) -> dict|None, get_captain_summary(participants_data) -> dict, get_chip_usage(participants_data) -> list[dict], get_hit_takers(participants_data) -> list[dict]. Follow the pure-function pattern from fpl/statistics.py. See docs/WEEKLY_REPORT_PLAN.md for return value schemas and threshold rules.",
    "acceptance_criteria": [
      "fpl/weekly_report_stats.py exists with all 9 functions",
      "All functions accept list[dict] and return dict/list/None as specified",
      "get_highest/lowest_gameweek_scorer use net_points field",
      "get_biggest_rank_rise/fall check league_rank_change, filter by threshold >= 2",
      "get_bench_disasters filters by threshold (default 20), excludes bench_boost chip users",
      "get_transfer_impact returns best and worst transfer results (include hit cost)",
      "get_captain_summary returns most_popular, best_pick, worst_pick",
      "get_chip_usage only returns entries where chip_played is not null",
      "get_hit_takers only returns entries where transfer_cost > 0",
      "All functions handle empty input lists gracefully",
      "Ruff clean, mypy clean"
    ],
    "passes": true
  },
  {
    "id": 5,
    "category": "test",
    "title": "Tests for weekly report stat functions",
    "description": "Write comprehensive tests for all 9 functions in weekly_report_stats.py. Create test fixtures with realistic participant data dicts matching the GameweekParticipantData schema from docs/WEEKLY_REPORT_PLAN.md. Test each function with: normal case (multiple participants), edge cases (ties, empty list, single participant), threshold boundaries (bench disasters at exactly 20, rank changes at exactly 2). Follow test patterns from tests/fpl_tests/test_statistics.py.",
    "acceptance_criteria": [
      "tests/fpl_tests/test_weekly_report_stats.py exists",
      "Test fixtures use realistic GameweekParticipantData dicts",
      "Each of the 9 functions has at least 2 test cases",
      "Edge cases tested: empty list input, single participant, ties",
      "Threshold boundaries tested: bench disasters at 19 (excluded) and 20 (included)",
      "All tests pass: python -m pytest tests/fpl_tests/test_weekly_report_stats.py"
    ],
    "passes": true
  },
  {
    "id": 6,
    "category": "feature",
    "title": "Implement WeeklyReport data collection and participant building",
    "description": "Create fpl/weekly_report.py with WeeklyReport class. Constructor takes api (FPLAPIProtocol), league_id (str), event_id (int). Implement the data collection phase: fetch league standings, fetch picks and transfers for each participant, fetch event live data (one shared call), build PlayerRegistry from bootstrap. Build GameweekParticipantData dict for each participant by combining picks, transfers, live point data, and player names. Calculate bench_points, captain points (with multiplier), transfer_cost, league_rank_change (comparing to previous GW if available from history). Store participants data as an internal list for later assembly. The build() method should be the public entry point.",
    "acceptance_criteria": [
      "fpl/weekly_report.py exists with WeeklyReport class",
      "Constructor accepts api (FPLAPIProtocol), league_id (str), event_id (int)",
      "build() method fetches all required data via API",
      "Builds GameweekParticipantData dict for each participant with all fields from schema",
      "Captain points correctly multiplied (2x captain, 3x triple captain)",
      "Bench points calculated from non-playing squad positions",
      "Transfer cost and transfers_made populated from transfers endpoint",
      "Player names resolved via PlayerRegistry (not raw element IDs)",
      "League rank change calculated by comparing current vs previous GW rank",
      "Ruff clean, mypy clean"
    ],
    "passes": false
  },
  {
    "id": 7,
    "category": "feature",
    "title": "Implement WeeklyReport assembly and JSON output",
    "description": "Extend the WeeklyReport.build() method to assemble the final report dict after participant data is built. Call all weekly_report_stats functions to populate the awards section. Build the meta section (league_id, league_name, season, event_id, generated_at timestamp, previous_report path). Build league_summary (average_score, leader, total_participants). Sort standings by league rank. Implement save_report(output_dir) method that writes the JSON to reports/{league_id}/{season}/gw{N}.json, creating directories as needed. Season format derived from bootstrap data (e.g. '2025-26'). Return the full report dict from build().",
    "acceptance_criteria": [
      "build() returns complete report dict with meta, standings, awards, league_summary",
      "Awards section populated by calling all weekly_report_stats functions",
      "Meta section includes league_id, league_name, season, event_id, generated_at, previous_report path",
      "League summary includes average_score, leader, total_participants",
      "Standings sorted by league_rank",
      "save_report(output_dir) writes JSON to correct path: {output_dir}/reports/{league_id}/{season}/gw{N}.json",
      "Directories created automatically if they don't exist",
      "Season format extracted from bootstrap data (e.g. '2025-26')",
      "JSON output is valid and matches schema from docs/WEEKLY_REPORT_PLAN.md",
      "Ruff clean, mypy clean"
    ],
    "passes": false
  },
  {
    "id": 8,
    "category": "test",
    "title": "WeeklyReport integration tests",
    "description": "Write integration tests for WeeklyReport using DummyAPI. Create comprehensive sample data in tests/fpl_tests/data_samples/ that includes: bootstrap with elements and teams, league standings, team picks with captains and bench, transfers (as JSON array), event live data with player points. Test the full build() flow: verify report structure, verify participant data is correctly assembled, verify awards are populated, verify JSON output. Test edge cases: participant with no transfers, participant playing a chip.",
    "acceptance_criteria": [
      "tests/fpl_tests/test_weekly_report.py exists",
      "DummyAPI fixture provides all required endpoints (including new ones)",
      "Test sample data is realistic and internally consistent",
      "Test verifies build() returns dict with meta, standings, awards, league_summary keys",
      "Test verifies participant data has all required fields",
      "Test verifies save_report() creates correct file path and valid JSON",
      "Edge cases: no transfers, chip played, tied scores",
      "All tests pass: python -m pytest tests/fpl_tests/test_weekly_report.py"
    ],
    "passes": false
  },
  {
    "id": 9,
    "category": "feature",
    "title": "Implement CLI entry point for weekly report",
    "description": "Create generate_weekly_report.py following generate_html.py patterns. Argparse with: -l/--league_id (default: 1639886), -e/--event (optional gameweek number), --dev (use sample data), --output-dir (default: current directory). When -e is omitted, auto-detect current gameweek from bootstrap-static (find latest event where finished=True). Create FPL_API instance, create WeeklyReport, call build() and save_report(). Print summary to stdout (league name, GW number, file path). Dev mode should work end-to-end with sample data.",
    "acceptance_criteria": [
      "generate_weekly_report.py exists with main() function and argparse",
      "Accepts -l/--league_id, -e/--event, --dev, --output-dir arguments",
      "Auto-detects current gameweek when -e is omitted (latest finished event)",
      "Creates shared FPL_API instance with dev_mode flag",
      "Calls WeeklyReport.build() and save_report()",
      "Prints summary to stdout: league name, gameweek, output file path",
      "Dev mode works end-to-end: python generate_weekly_report.py -l 1639886 --dev",
      "Ruff clean, mypy clean"
    ],
    "passes": false
  },
  {
    "id": 10,
    "category": "feature",
    "title": "Define Reidar persona document",
    "description": "Create docs/REIDAR_PERSONA.md defining the 'Reidar' character who writes the weekly narratives ('Reidars Rapport'). Reidar is a blend of neutral sports journalist and retired FPL veteran — sharp wit, no filter, dispenses wisdom, judges poor FPL decisions harshly, respects bold moves. Include: background/identity (seasoned columnist covering the league as an outside observer, not a participant), voice rules (Norwegian informal tone, sports commentary cadence, when to be sarcastic vs genuine), personality traits (what triggers praise, mockery, grudging respect), relationship to different manager archetypes (the frontrunner, the comeback kid, the perennial underperformer, the lucky one), recurring narrative devices (running jokes, catchphrases, callbacks to previous weeks, stat obscurities), things Reidar NEVER does (takes sides, makes excuses for bad play, uses corporate language). Reference prd/weekly-report-resources/previous-gameweek-reports.md for the tone these narratives should match and exceed.",
    "acceptance_criteria": [
      "docs/REIDAR_PERSONA.md exists",
      "Background section: seasoned columnist, outside observer, not a league participant",
      "Voice rules: Norwegian informal tone, sports commentary cadence, sarcasm guidelines",
      "Personality traits: what triggers praise, mockery, grudging respect",
      "Manager archetypes section: how Reidar treats different performance patterns",
      "Recurring devices: running jokes, callbacks, stat nuggets, catchphrases",
      "Anti-patterns: things Reidar never does",
      "References the sample reports for tone baseline"
    ],
    "passes": false
  },
  {
    "id": 11,
    "category": "feature",
    "title": "Create narrative structure guide",
    "description": "Create docs/NARRATIVE_GUIDE.md as the structural reference for the LLM narrative writer. This document works alongside REIDAR_PERSONA.md (persona/voice) to define HOW the narrative is structured. Include: narrative structure (opening hook, round winner spotlight, award-by-award coverage, standings implications, look-ahead/deadline reminder), award name mappings (English code names to Norwegian narrative angles — e.g. 'highest_scorer' → 'Rundevinneren', 'bench_disasters' → 'Benkeslitere'), week-over-week continuity rules (how to reference previous narrative, track form streaks, build rivalries, maintain running jokes), Norwegian FPL terminology glossary, length guidelines (~500-800 words). This document will be included in the Claude API prompt alongside the persona document.",
    "acceptance_criteria": [
      "docs/NARRATIVE_GUIDE.md exists",
      "Narrative structure section: opening, spotlight, awards, standings, look-ahead",
      "Award name mapping table: English code name → Norwegian narrative name + angle",
      "Week-over-week continuity rules (previous narrative, streaks, rivalries)",
      "Norwegian FPL terminology glossary (chips, transfers, bench, captain, etc.)",
      "Length/format guidelines (~500-800 words, markdown output)",
      "References docs/REIDAR_PERSONA.md for voice/personality"
    ],
    "passes": false
  },
  {
    "id": 12,
    "category": "feature",
    "title": "Create example Reidar narratives from sample reports",
    "description": "Create docs/REIDAR_EXAMPLES.md with 2-3 example narratives written in Reidar's voice, based on the raw data patterns from prd/weekly-report-resources/previous-gameweek-reports.md. These are NOT rewrites of the existing reports — they are examples of what Reidar WOULD write given similar gameweek data. Transform the participant-perspective reports into Reidar's outside-observer columnist voice. Include examples covering different scenarios: a dominant round winner, a close contest, a disaster week. These examples serve as few-shot references in the Claude API prompt to calibrate Reidar's tone. Each example should be 400-600 words in Norwegian.",
    "acceptance_criteria": [
      "docs/REIDAR_EXAMPLES.md exists",
      "Contains 2-3 complete example narratives in Norwegian",
      "Examples written from Reidar's outside-observer perspective (not participant)",
      "Each example is 400-600 words",
      "Covers different scenarios: dominant winner, close contest, disaster week",
      "Demonstrates Reidar's personality traits: sharp wit, praise, mockery, stat nuggets",
      "Demonstrates recurring devices: callbacks, catchphrases, running commentary",
      "Suitable as few-shot examples in an LLM prompt"
    ],
    "passes": false
  },
  {
    "id": 13,
    "category": "feature",
    "title": "Scaffold Reidar memory system",
    "description": "Create fpl/reidar_memory.py with a ReidarMemory class that manages Reidar's persistent knowledge. Constructor takes output_dir, league_id, season. Methods: (1) scaffold_directories() — creates reidar_memory/{league_id}/{season}/ with managers/ and gameweeks/ subdirectories. (2) load_manager_profiles() -> dict[str, str] — reads all manager .md files from managers/ dir, returns {first_name: content}. (3) load_season_arc() -> str — reads season_arc.md (returns empty string if not exists). (4) load_recent_gameweeks(current_event: int, window: int = 5) -> list[str] — reads last N GW summaries. (5) get_prompt_context(current_event: int) -> str — assembles all memory into a formatted string for prompt inclusion (all manager profiles + season arc + last 5 GW summaries). Handle missing files gracefully (first run returns minimal/empty context). Create template markdown showing the expected structure of each file type as docstrings or comments in the module.",
    "acceptance_criteria": [
      "fpl/reidar_memory.py exists with ReidarMemory class",
      "scaffold_directories() creates reidar_memory/{league_id}/{season}/managers/ and gameweeks/",
      "load_manager_profiles() reads all .md files from managers/ dir",
      "load_season_arc() reads season_arc.md, returns empty string if missing",
      "load_recent_gameweeks() reads last N GW summaries (rolling window)",
      "get_prompt_context() assembles all memory into formatted prompt string",
      "All load methods handle missing files gracefully (no errors on first run)",
      "Module docstring or constants document the expected file structure/templates",
      "Ruff clean, mypy clean, all existing tests pass"
    ],
    "passes": false
  },
  {
    "id": 14,
    "category": "feature",
    "title": "Implement narrative generator with memory support",
    "description": "Create fpl/narrative_generator.py with NarrativeGenerator class. Constructor takes anthropic client (or creates one from ANTHROPIC_API_KEY env var). Method generate(report_json: dict, persona: str, narrative_guide: str, examples: str, memory_context: str, previous_narrative: str | None = None) -> str builds a system prompt from persona + guide + examples + memory_context, includes the report JSON as user content and optional previous narrative for continuity, calls Claude API (claude-sonnet-4-6 model), returns the generated markdown string. The memory_context comes from ReidarMemory.get_prompt_context() and gives Reidar full recall of the season so far. Method save_narrative(content: str, output_dir: str, league_id: str, season: str, event_id: int) writes to narratives/{league_id}/{season}/gw{N}.md. Add 'anthropic' to requirements.txt.",
    "acceptance_criteria": [
      "fpl/narrative_generator.py exists with NarrativeGenerator class",
      "Constructor creates anthropic client from ANTHROPIC_API_KEY env var",
      "generate() accepts persona, narrative_guide, examples, memory_context, and optional previous_narrative",
      "System prompt includes Reidar persona + narrative guide + examples + memory context",
      "User message includes report JSON and optional previous narrative",
      "generate() calls Claude API with claude-sonnet-4-6 model",
      "generate() returns markdown string",
      "save_narrative() writes to correct path: {output_dir}/narratives/{league_id}/{season}/gw{N}.md",
      "anthropic package added to requirements.txt",
      "Ruff clean, mypy clean"
    ],
    "passes": false
  },
  {
    "id": 15,
    "category": "feature",
    "title": "Implement Reidar memory update after narrative generation",
    "description": "Add update_memory(report_json: dict, narrative: str, anthropic_client) method to ReidarMemory. After a narrative is generated, this method makes a second Claude API call to update Reidar's memory files. The LLM receives: current manager profiles, current season arc, the new report JSON, and the narrative just written. It returns updated content for: (1) each manager's profile — new facts (score, rank, transfers, captain choice) + Reidar's evolving opinions, running jokes, notable moments; (2) a new GW summary — brief recap of key events and Reidar's takes; (3) updated season arc — narrative threads, records, rivalry updates. On first run (no existing profiles), the method bootstraps manager profiles from the report data. Write the updated content back to the respective .md files. Use a structured prompt that clearly separates each output section. The LLM call should use claude-sonnet-4-6 for cost efficiency.",
    "acceptance_criteria": [
      "ReidarMemory.update_memory(report_json, narrative, client) method exists",
      "Makes a Claude API call with current memory + report + narrative as context",
      "Updates all manager profile .md files with new facts and opinions",
      "Creates gw{N}.md summary in gameweeks/ directory",
      "Updates season_arc.md with new narrative threads and records",
      "Handles first-run gracefully: bootstraps profiles from report data when no profiles exist",
      "Prompt clearly separates output sections for reliable parsing",
      "Uses claude-sonnet-4-6 model for cost efficiency",
      "Manager profiles stay concise (~200 words each)",
      "Ruff clean, mypy clean"
    ],
    "passes": false
  },
  {
    "id": 16,
    "category": "test",
    "title": "Tests for narrative generator and memory system",
    "description": "Write tests for NarrativeGenerator and ReidarMemory with mocked Claude API calls. For ReidarMemory: test scaffold_directories creates correct structure, test load methods with missing files (first run), test load methods with existing files, test get_prompt_context assembles all memory, test update_memory writes correct files. For NarrativeGenerator: test prompt includes persona/guide/examples/memory, test save_narrative creates correct path, test missing API key raises clear error. Use unittest.mock to patch the anthropic client and tmp_path for file operations. Do NOT make real API calls.",
    "acceptance_criteria": [
      "tests/fpl_tests/test_narrative_generator.py exists",
      "tests/fpl_tests/test_reidar_memory.py exists",
      "ReidarMemory scaffold_directories tested",
      "ReidarMemory load methods tested with missing files (first run)",
      "ReidarMemory load methods tested with existing files",
      "ReidarMemory get_prompt_context tested (assembles all memory)",
      "ReidarMemory update_memory tested with mocked LLM (writes correct files)",
      "NarrativeGenerator prompt includes persona, guide, examples, and memory context",
      "NarrativeGenerator save_narrative tested",
      "Missing ANTHROPIC_API_KEY raises clear error",
      "All tests pass: python -m pytest"
    ],
    "passes": false
  },
  {
    "id": 17,
    "category": "feature",
    "title": "Integrate narrative and memory into CLI",
    "description": "Update generate_weekly_report.py to support narrative generation with memory. Add --narrative flag that triggers the full pipeline after the JSON report is built. When --narrative is set: (1) read docs/REIDAR_PERSONA.md, docs/NARRATIVE_GUIDE.md, and docs/REIDAR_EXAMPLES.md; (2) create ReidarMemory and load memory context; (3) check for previous narrative file; (4) create NarrativeGenerator and call generate() with all context; (5) save narrative; (6) call ReidarMemory.update_memory() to update Reidar's files. Handle missing ANTHROPIC_API_KEY with a clear error message. Print narrative file path to stdout. The --dev flag should still work end-to-end.",
    "acceptance_criteria": [
      "generate_weekly_report.py accepts --narrative flag",
      "When --narrative is set, reads all three Reidar docs (persona, guide, examples)",
      "Creates ReidarMemory and loads memory context for the prompt",
      "Checks for and loads previous gameweek narrative if it exists",
      "Calls NarrativeGenerator.generate() with all context including memory",
      "After narrative generation, calls ReidarMemory.update_memory()",
      "Prints narrative output path to stdout",
      "Missing ANTHROPIC_API_KEY shows clear error (not a traceback)",
      "Works with --dev flag end-to-end",
      "Ruff clean, mypy clean, all tests pass"
    ],
    "passes": false
  },
  {
    "id": 18,
    "category": "setup",
    "title": "Create GitHub Actions weekly report workflow",
    "description": "Create .github/workflows/weekly_report.yml. Nightly cron schedule (e.g. 06:00 UTC). Also supports workflow_dispatch for manual triggers. Steps: checkout repo, setup Python 3.13, install dependencies from requirements.txt, run a detection script that checks bootstrap-static for the latest finished event and compares against existing reports (if reports/{league_id}/{season}/gw{N}.json already exists, skip). If new GW detected: run generate_weekly_report.py with --narrative flag, commit and push report JSON, narrative markdown, AND updated reidar_memory/ files. Use ANTHROPIC_API_KEY from GitHub secrets. Use a bot commit message like 'chore: generate weekly report for GW{N}'. Configure the workflow to skip if no new gameweek is detected (exit 0).",
    "acceptance_criteria": [
      ".github/workflows/weekly_report.yml exists",
      "Triggers on cron schedule (nightly) and workflow_dispatch",
      "Sets up Python 3.13 and installs requirements.txt",
      "Detects latest finished GW from FPL API",
      "Skips if report already exists for that GW",
      "Runs generate_weekly_report.py with --narrative when new GW detected",
      "Uses ANTHROPIC_API_KEY from GitHub secrets",
      "Commits and pushes report + narrative + updated reidar_memory/ files",
      "Workflow exits cleanly (exit 0) when no new GW detected",
      "YAML is valid GitHub Actions syntax"
    ],
    "passes": false
  },
  {
    "id": 19,
    "category": "setup",
    "title": "Update documentation and module exports",
    "description": "Update fpl/__init__.py to export PlayerRegistry, WeeklyReport, NarrativeGenerator, and ReidarMemory. Update AGENTS.md (root) to document the weekly report flow alongside the existing HTML flow, including the Reidar persona and memory system. Update fpl/AGENTS.md with documentation for all new modules (player_registry.py, weekly_report.py, weekly_report_stats.py, narrative_generator.py, reidar_memory.py). Add reports/ to .gitignore. Verify the full pipeline works end-to-end in dev mode.",
    "acceptance_criteria": [
      "fpl/__init__.py exports PlayerRegistry, WeeklyReport, NarrativeGenerator, ReidarMemory",
      "Root AGENTS.md documents weekly report architecture flow including Reidar memory system",
      "fpl/AGENTS.md documents all new modules including reidar_memory.py",
      "reports/ directory in .gitignore",
      "End-to-end dev mode works: python generate_weekly_report.py --dev --narrative",
      "Ruff clean, mypy clean, all tests pass"
    ],
    "passes": false
  }
]
```

---

## Agent Instructions

1. Read `prd/weekly-report-activity.md` to understand current state
2. Find the next task where `"passes": false`
3. Complete all acceptance criteria for that task
4. Verify the feature works (run tests, check manually)
5. Update the task to `"passes": true`
6. Log completion in `prd/weekly-report-activity.md`
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
- `docs/WEEKLY_REPORT_PLAN.md` — Full data schemas, API endpoints, award definitions
- `docs/REIDAR_PERSONA.md` — Reidar character definition (created in task 10)
- `docs/NARRATIVE_GUIDE.md` — Narrative structure and award mappings (created in task 11)
- `docs/REIDAR_EXAMPLES.md` — Few-shot example narratives (created in task 12)
- `prd/weekly-report-resources/previous-gameweek-reports.md` — Tone reference from manually-written reports
- `AGENTS.md` — Project conventions, testing patterns, code quality rules
- `fpl/AGENTS.md` — Module documentation, DummyAPI pattern, Participant dataclass
