"""Check gameweek status for the hourly CI workflow.

Compares two simple counts against a persisted state file:
  - finished_fixtures: total finished fixtures across all gameweeks
  - finished_events: total events marked finished by FPL

If the counts change, GitHub Actions outputs are set:
  - has_new_finished_fixtures → refresh dashboards (generate_html, generate_index)
  - gameweek_finished         → generate weekly report, narrative, Teams notification

The state file (.gw_state.json) is committed to the repo so it persists
across workflow runs.
"""

import argparse
import json
import os
from pathlib import Path

from fpl import FPL_API
from fpl.fpl_api_protocol import FPLAPIProtocol

STATE_FILE = ".gw_state.json"


def load_state(state_path: Path) -> dict:
    """Load persisted state from disk, or return empty state."""
    if state_path.is_file():
        return json.loads(state_path.read_text(encoding="utf-8"))
    return {}


def save_state(state_path: Path, state: dict) -> None:
    """Persist state to disk."""
    state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def count_finished_fixtures(api: FPLAPIProtocol) -> int:
    """Count total finished fixtures across all gameweeks."""
    fixtures = api.get_fixtures()
    return sum(1 for f in fixtures if f.get("finished", False))


def count_finished_events(api: FPLAPIProtocol) -> int:
    """Count total events marked finished in bootstrap-static."""
    bootstrap = api.get_bootstrap_static()
    events = bootstrap.get("events", [])
    return sum(1 for e in events if e.get("finished", False))


def check_status(
    api: FPLAPIProtocol, state_path: Path
) -> tuple[bool, bool, dict]:
    """Compare live counts against persisted state.

    Returns (has_new_finished_fixtures, gameweek_finished, new_state).
    """
    fixtures_count = count_finished_fixtures(api)
    events_count = count_finished_events(api)

    new_state = {
        "finished_fixtures": fixtures_count,
        "finished_events": events_count,
    }

    old_state = load_state(state_path)
    old_fixtures = old_state.get("finished_fixtures", 0)
    old_events = old_state.get("finished_events", 0)

    has_new = fixtures_count > old_fixtures
    gw_finished = events_count > old_events

    return has_new, gw_finished, new_state


def _set_github_output(name: str, value: str) -> None:
    """Write a step output variable for GitHub Actions."""
    output_file = os.environ.get("GITHUB_OUTPUT")
    if output_file:
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(f"{name}={value}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check gameweek status for the hourly CI workflow.",
    )
    parser.add_argument(
        "--state-file", type=str, default=STATE_FILE,
        help=f"Path to the state file. Default: {STATE_FILE}",
    )
    parser.add_argument(
        "--save", action="store_true",
        help="Save current state without checking for changes. "
             "Use after a successful workflow run to persist state.",
    )
    parser.add_argument(
        "--cache-dir", type=str, default=None,
        help="Directory for file-based API response caching.",
    )
    args = parser.parse_args()

    cache_dir = Path(args.cache_dir) if args.cache_dir else None
    api = FPL_API(cache_dir=cache_dir)
    state_path = Path(args.state_file)

    if args.save:
        fixtures_count = count_finished_fixtures(api)
        events_count = count_finished_events(api)
        state = {
            "finished_fixtures": fixtures_count,
            "finished_events": events_count,
        }
        save_state(state_path, state)
        print(f"State saved: {fixtures_count} finished fixtures, "
              f"{events_count} finished events.")
        return

    has_new, gw_finished, _ = check_status(api, state_path)

    print(f"has_new_finished_fixtures={str(has_new).lower()}")
    print(f"gameweek_finished={str(gw_finished).lower()}")

    _set_github_output("has_new_finished_fixtures", str(has_new).lower())
    _set_github_output("gameweek_finished", str(gw_finished).lower())

    if not has_new and not gw_finished:
        print("Nothing changed since last check.")


if __name__ == "__main__":
    main()
