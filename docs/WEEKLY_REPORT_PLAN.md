# Weekly FPL League Report - Implementation Plan

## Feature Overview

The weekly report feature generates structured data about a mini-league's gameweek performance, designed as input for an LLM narrative writer. The system follows the existing architecture flow:

**Data Collection → Data Processing → Report Building → JSON Output → (LLM) → Narrative Markdown**

The report collects per-participant gameweek detail (picks, transfers, bench, captain, chips) and calculates league-wide awards (top scorer, biggest climber, bench disaster, etc.). The output is a self-contained JSON file with all data an LLM needs to write an entertaining gameweek summary — no API access required at narrative time.

### How It Fits in the Architecture

| Existing flow | Weekly report flow |
|---|---|
| `fpl_api.py` → `fpl_league.py` → `league_context.py` → templates → HTML | `fpl_api.py` → `weekly_report.py` → `weekly_report_stats.py` → JSON → (LLM) → Markdown |

The weekly report reuses the existing `FPL_API` client and `FPLLeague` data aggregation, adding new API methods, a player lookup registry, and report-specific stat calculations.

---

## FPL API Endpoints

### Already Available

| Method | Endpoint | Returns |
|---|---|---|
| `get_bootstrap_static()` | `/bootstrap-static/` | Global data: events, elements (players), teams, chips |
| `get_league_standings(league_id)` | `/leagues-classic/{id}/standings/` | League standings, participant list |
| `get_team_history(team_id)` | `/entry/{id}/history/` | GW history: points, rank, bank, value, transfers, chips |
| `get_team_picks(team_id, event_id)` | `/entry/{id}/event/{eid}/picks/` | Squad picks: captain, vice-captain, bench order, auto-subs |

### New Methods Required

| Method | Endpoint | Returns | Notes |
|---|---|---|---|
| `get_transfers(team_id)` | `/entry/{id}/transfers/` | Transfer history: element_in, element_out, cost, event | Returns a JSON **array**, not dict — requires type widening in `_get()` |
| `get_event_live(event_id)` | `/event/{id}/live/` | Live event data: per-player GW points and stats | One call per GW, shared across all participants |

### API Call Budget

For an 18-person league, one report requires approximately **2N + 2** API calls:
- 1 `get_bootstrap_static()` (shared, likely cached)
- 1 `get_event_live(event_id)` (shared across participants)
- N `get_team_picks(team_id, event_id)` (one per participant)
- N `get_transfers(team_id)` (one per participant)

Total for 18 participants: ~38 calls. Dev mode caching eliminates repeat calls.

---

## New Modules

### 1. `fpl/player_registry.py` — Player Lookup Service

Maps FPL element IDs to human-readable player names and metadata. Wraps the `elements` and `teams` arrays from bootstrap data.

```python
class PlayerRegistry:
    def __init__(self, bootstrap_data: dict) -> None: ...
    def get_player_name(self, element_id: int) -> str: ...        # "Mohamed Salah"
    def get_player_info(self, element_id: int) -> dict: ...       # {name, team, position}
    def get_team_name(self, team_code: int) -> str: ...           # "Liverpool"
```

**Design**: Builds lookup dicts once at construction from bootstrap `elements` and `teams`. No API calls — pure data transformation.

### 2. `fpl/weekly_report.py` — Report Orchestrator

Core class that collects all data for a gameweek and builds the report dict.

```python
class WeeklyReport:
    def __init__(self, api: FPLAPIProtocol, league_id: str, event_id: int) -> None: ...
    def build(self) -> dict: ...  # Collects data, calculates awards, returns full report
```

**Responsibilities**:
- Fetch league standings, picks, transfers, live data
- Build `GameweekParticipantData` for each participant
- Call `weekly_report_stats` functions to compute awards
- Assemble final report dict with metadata + standings + awards
- Save JSON to storage path

### 3. `fpl/weekly_report_stats.py` — Award Calculations

Pure functions following the `statistics.py` pattern: raw data in, dicts out, no formatting.

```python
def get_highest_gameweek_scorer(participants_data: list[dict]) -> dict | None: ...
def get_lowest_gameweek_scorer(participants_data: list[dict]) -> dict | None: ...
def get_biggest_rank_rise(participants_data: list[dict]) -> dict | None: ...
def get_biggest_rank_fall(participants_data: list[dict]) -> dict | None: ...
def get_bench_disasters(participants_data: list[dict], threshold: int = 20) -> list[dict]: ...
def get_transfer_impact(participants_data: list[dict]) -> dict | None: ...
def get_captain_summary(participants_data: list[dict]) -> dict: ...
def get_chip_usage(participants_data: list[dict]) -> list[dict]: ...
def get_hit_takers(participants_data: list[dict]) -> list[dict]: ...
```

### 4. `generate_weekly_report.py` — CLI Entry Point

```bash
python generate_weekly_report.py -l 1639886 -e 15 --dev
python generate_weekly_report.py -l 1639886              # auto-detect current GW
```

Follows `generate_html.py` patterns: argparse, shared API instance, dev mode flag.

---

## Data Structures

### GameweekParticipantData

Built per participant per gameweek. This is an intermediate structure used internally by `WeeklyReport.build()`:

```python
{
    "entry_id": 12345,
    "team_name": "Salah's Soldiers",
    "manager_name": "Ola Nordmann",
    "player_first_name": "Ola",

    # Points
    "event_total": 67,           # Gross GW points
    "net_points": 63,            # After hits
    "total_points": 1245,        # Season total to date

    # Rank
    "league_rank": 3,
    "league_rank_previous": 5,
    "league_rank_change": 2,     # Positive = climbed
    "overall_rank": 156000,

    # Value
    "team_value": 103.5,         # In millions (value / 10)
    "bank": 0.5,

    # Bench
    "bench_points": 22,          # Total points from benched players
    "bench_players": [           # Benched player details
        {"name": "Player Name", "points": 12, "element_id": 456}
    ],

    # Chip
    "chip_played": "wildcard",   # Or null

    # Captain
    "captain": {"name": "Mohamed Salah", "points": 24, "element_id": 123},
    "vice_captain": {"name": "Erling Haaland", "points": 6, "element_id": 456},

    # Squad (all 15 players with GW points)
    "squad": [
        {"element_id": 123, "name": "Player", "position": 1, "points": 12, "is_captain": true, "multiplier": 2}
    ],

    # Transfers
    "transfers": [
        {"player_in": "New Player", "player_out": "Old Player", "cost": 0}
    ],
    "transfer_cost": 4,          # Total hit points
    "transfers_made": 2
}
```

### Report Output Format (JSON)

The full report saved to disk:

```python
{
    "meta": {
        "league_id": "1639886",
        "league_name": "Sinkaberg Superliga",
        "season": "2025-26",
        "event_id": 15,
        "generated_at": "2026-02-24T12:00:00Z",
        "previous_report": "reports/1639886/2025-26/gw14.json",
        "previous_narrative": "narratives/1639886/2025-26/gw14.md"
    },

    "standings": [
        # Sorted list of GameweekParticipantData dicts (see above)
    ],

    "awards": {
        "highest_scorer": {"player_name": "Ola", "points": 87, "team_name": "..."},
        "lowest_scorer": {"player_name": "Kari", "points": 23, "team_name": "..."},
        "biggest_rise": {"player_name": "Per", "old_rank": 12, "new_rank": 5, "change": 7},
        "biggest_fall": {"player_name": "Lars", "old_rank": 3, "new_rank": 11, "change": -8},
        "bench_disasters": [{"player_name": "Nils", "bench_points": 32, "event_total": 45}],
        "best_transfer": {"player_name": "Eva", "net_gain": 18, "transfers": [...]},
        "worst_transfer": {"player_name": "Tor", "net_loss": -12, "transfers": [...]},
        "captain_summary": {
            "most_popular": {"player": "Salah", "count": 8},
            "best_pick": {"manager": "Ola", "captain": "Salah", "points": 24},
            "worst_pick": {"manager": "Kari", "captain": "Fernandes", "points": 2}
        },
        "chip_usage": [{"player_name": "Per", "chip": "bench_boost", "points": 87}],
        "hit_takers": [{"player_name": "Lars", "cost": 8, "net_points": 55}]
    },

    "league_summary": {
        "average_score": 52.3,
        "highest_ever_gw_score": 98,    # Season record
        "leader": {"player_name": "Ola", "total_points": 1245},
        "total_participants": 18
    }
}
```

---

## Stats / Awards to Calculate

| Award | Function | Description | Threshold/Notes |
|---|---|---|---|
| **Top Gun** | `get_highest_gameweek_scorer` | Highest net GW points | Always shown |
| **Tough Week** | `get_lowest_gameweek_scorer` | Lowest net GW points | Always shown |
| **Comeback Kid** | `get_biggest_rank_rise` | Most league positions gained | Show if change >= 2 |
| **Free Fall** | `get_biggest_rank_fall` | Most league positions lost | Show if change >= 2 |
| **Bench Disaster** | `get_bench_disasters` | High points left on bench | Threshold: 20+ bench pts without BB |
| **Sharpest Trader** | `get_transfer_impact` (best) | Best net transfer point gain | Include hit cost in calculation |
| **Transfer Tangle** | `get_transfer_impact` (worst) | Worst net transfer result | Include hit cost in calculation |
| **Captain Picks** | `get_captain_summary` | Most popular captain, best/worst pick | Always shown |
| **Chip Master** | `get_chip_usage` | Who played a chip and how it went | Only if chip was played |
| **Hit Takers** | `get_hit_takers` | Who took point hits for transfers | Only if hits were taken |

---

## Narrative System

### Purpose

The JSON report is input for an LLM (Claude) that writes an entertaining gameweek narrative in Norwegian. The narrative system is separated from the data pipeline:

1. **Data pipeline** (this plan) produces structured JSON
2. **Narrative agent** (separate, future) reads JSON + guide and writes markdown

### Guide Document

A `docs/NARRATIVE_GUIDE.md` will be created as a reference for the LLM narrative writer, containing:
- Tone guidelines (fun, entertaining, Norwegian league culture)
- Award name explanations and suggested narrative angles
- Examples of good narrative passages
- Rules for week-over-week continuity (reference previous GW highlights)

### Norwegian Tone

The narrative uses informal Norwegian league banter. Award names in the JSON are English (code-friendly), but the narrative guide maps them to Norwegian-flavored descriptions.

### Week-over-Week Continuity

Each report JSON includes `previous_narrative` path. The narrative agent can read the previous week's story to:
- Reference ongoing storylines (hot streaks, rivalries)
- Track running jokes or themes
- Note changes in form ("after last week's disaster, X bounced back with...")

---

## Storage

### Directory Structure

```
reports/
  {league_id}/
    {season}/
      gw{N}.json          # Structured report data

narratives/
  {league_id}/
    {season}/
      gw{N}.md            # LLM-generated narrative
```

### Example Paths

```
reports/1639886/2025-26/gw15.json
narratives/1639886/2025-26/gw15.md
```

### Conventions

- Season format: `2025-26` (derived from bootstrap data)
- Gameweek numbers are zero-padded in filenames only if needed for sorting (start without padding)
- Reports directory is gitignored (contains generated data)
- Narratives directory may be committed (human-reviewed content)

---

## Implementation Phases

### Phase 1: API Layer & Player Registry

**Goal**: Extend the API client and build the player lookup service.

| # | Task | File(s) | Dependencies |
|---|---|---|---|
| 1.1 | Widen `_get()` return type to `dict | list` | `fpl/fpl_api.py` | None |
| 1.2 | Add `get_transfers(team_id)` method | `fpl/fpl_api.py` | 1.1 |
| 1.3 | Add `get_event_live(event_id)` method | `fpl/fpl_api.py` | None |
| 1.4 | Update `FPLAPIProtocol` with new methods | `fpl/fpl_api_protocol.py` | 1.2, 1.3 |
| 1.5 | Implement `PlayerRegistry` class | `fpl/player_registry.py` | None |
| 1.6 | Tests for new API methods | `tests/fpl_tests/test_fpl_api.py` | 1.2, 1.3 |
| 1.7 | Tests for `PlayerRegistry` | `tests/fpl_tests/test_player_registry.py` | 1.5 |
| 1.8 | Add sample data files for new endpoints | `fpl/sample_data/` | 1.2, 1.3 |

### Phase 2: Award Calculations

**Goal**: Implement all stat/award functions as pure calculation functions.

| # | Task | File(s) | Dependencies |
|---|---|---|---|
| 2.1 | Create `weekly_report_stats.py` with all award functions | `fpl/weekly_report_stats.py` | None (operates on dicts) |
| 2.2 | Tests for each award function | `tests/fpl_tests/test_weekly_report_stats.py` | 2.1 |

### Phase 3: Report Orchestration

**Goal**: Build the core report class that ties everything together.

| # | Task | File(s) | Dependencies |
|---|---|---|---|
| 3.1 | Implement `WeeklyReport` class | `fpl/weekly_report.py` | 1.2–1.5, 2.1 |
| 3.2 | JSON output and file storage logic | `fpl/weekly_report.py` | 3.1 |
| 3.3 | Integration tests with DummyAPI | `tests/fpl_tests/test_weekly_report.py` | 3.1 |

### Phase 4: CLI & Polish

**Goal**: CLI entry point, documentation updates, dev mode verification.

| # | Task | File(s) | Dependencies |
|---|---|---|---|
| 4.1 | Implement CLI entry point | `generate_weekly_report.py` | 3.1 |
| 4.2 | Auto-detect current gameweek when `-e` omitted | `generate_weekly_report.py` | 4.1 |
| 4.3 | Verify dev mode caching for new endpoints | Manual testing | 1.8 |
| 4.4 | Update `fpl/__init__.py` exports | `fpl/__init__.py` | 1.5, 3.1 |
| 4.5 | Update `AGENTS.md` with weekly report docs | `AGENTS.md`, `fpl/AGENTS.md` | All |
| 4.6 | Create narrative guide document | `docs/NARRATIVE_GUIDE.md` | All |

---

## Future Enhancements

These are out of scope for the initial implementation but worth noting:

- **Automated narrative generation**: Integrate Claude API to auto-generate narratives from report JSON
- **Delivery**: Email or Microsoft Teams webhook to push weekly narratives to league members
- **Season-long awards**: Running tallies across all gameweeks (most bench points total, transfer roi, consistency king)
- **Form tracker**: Rolling 5-GW form with trend indicators
- **Head-to-head records**: Track GW wins between specific pairs of managers
- **Differential tracking**: Players owned by only 1-2 managers and their impact
- **Historical comparison**: Compare current season to previous seasons
- **Web dashboard**: Render narratives as HTML pages alongside existing dashboard views
