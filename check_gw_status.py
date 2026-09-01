"""Check gameweek status for the hourly CI workflow.

Compares two simple counts against a persisted state file:
  - finished_fixtures: total fixtures played (finished or provisionally so)
  - finished_events: total events marked finished by FPL, i.e. locked

If the counts change, GitHub Actions outputs are set:
  - has_new_finished_fixtures → refresh dashboards (generate_html, generate_index)
  - gameweek_finished         → generate weekly report, narrative, Teams notification

A third output, has_finished_gameweek, is absolute rather than a delta: it
says whether any gameweek has finished at all this season. Manual dispatch
uses it to skip the report steps before the first gameweek is played.

--pending-notification answers a different question, asked after the push:
is there a narrative on disk that the league has not been told about yet?
The workflow gates the Teams card on it, and --mark-notified records the
send, so a card held back because GitHub Pages had not caught up is retried
by the next hourly run instead of being lost.

The state file (.gw_state.json) is committed to the repo so it persists
across workflow runs.
"""

import argparse
import json
import os
from pathlib import Path

from fpl import FPL_API
from fpl.fpl_api_protocol import FPLAPIProtocol
from fpl.weekly_report import get_narrative_path, get_season_from_bootstrap

STATE_FILE = ".gw_state.json"
FPL_LEAGUE_ID = "848662"


def load_state(state_path: Path) -> dict:
    """Load persisted state from disk, or return empty state."""
    if state_path.is_file():
        return json.loads(state_path.read_text(encoding="utf-8"))
    return {}


def save_state(state_path: Path, state: dict) -> None:
    """Persist state to disk."""
    state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def count_finished_fixtures(api: FPLAPIProtocol) -> int:
    """Count fixtures that have been played, across all gameweeks.

    Counts `finished_provisional` as well as `finished`. From 2026/27 FPL
    locks gameweek scores at 09:00 UK on the day after the gameweek's final
    match, rather than an hour after each match, so a played fixture keeps
    `finished: false` for days while `finished_provisional` flips at full
    time. Dashboards follow the provisional signal so standings refresh on
    match day; the weekly report waits for the locked event instead — see
    count_finished_events().
    """
    fixtures = api.get_fixtures()
    return sum(
        1 for f in fixtures
        if f.get("finished", False) or f.get("finished_provisional", False)
    )


def count_finished_events(api: FPLAPIProtocol) -> int:
    """Count total events marked finished in bootstrap-static.

    Requires both `finished` and `data_checked`. The lockdown at 09:00 UK
    on the day after the gameweek's final match is what makes scores final,
    and `data_checked` is the flag that tracks it; `finished` alone has
    historically flipped earlier. Generating the report before the lock
    would bake pre-review BPS and Defensive Contribution numbers into
    Reidar's memory permanently, so wait for both.
    """
    bootstrap = api.get_bootstrap_static()
    events = bootstrap.get("events", [])
    return sum(
        1 for e in events
        if e.get("finished", False) and e.get("data_checked", False)
    )


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


def save_counts(api: FPLAPIProtocol, state_path: Path) -> tuple[int, int]:
    """Persist the current fixture/event counts, keeping the rest of the state.

    Merges rather than replaces: notified_events lives in the same file and
    is written later in the run, after the Teams card actually goes out.
    """
    state = load_state(state_path)
    state["finished_fixtures"] = count_finished_fixtures(api)
    state["finished_events"] = count_finished_events(api)
    save_state(state_path, state)
    return state["finished_fixtures"], state["finished_events"]


def latest_finished_event(api: FPLAPIProtocol) -> int | None:
    """Return the highest locked gameweek id, or None if none is locked.

    Same finished + data_checked test as count_finished_events(); this
    returns which gameweek rather than how many.
    """
    bootstrap = api.get_bootstrap_static()
    for event in reversed(bootstrap.get("events", [])):
        if event.get("finished", False) and event.get("data_checked", False):
            return int(event["id"])
    return None


def pending_notification(
    api: FPLAPIProtocol,
    state_path: Path,
    league_id: str,
    output_dir: str = ".",
) -> tuple[int | None, str]:
    """Return (event_id, season) for a narrative that still needs announcing.

    A gameweek is pending when it is locked, its narrative exists on disk,
    and it is not already in the state file's notified_events. Returns
    (None, "") when there is nothing to send.
    """
    event_id = latest_finished_event(api)
    if event_id is None:
        return None, ""

    season = get_season_from_bootstrap(api.get_bootstrap_static())
    if not get_narrative_path(output_dir, league_id, season, event_id).is_file():
        return None, ""

    if event_id in load_state(state_path).get("notified_events", []):
        return None, ""

    return event_id, season


def mark_notified(state_path: Path, event_id: int) -> None:
    """Record that the Teams card for a gameweek has been sent."""
    state = load_state(state_path)
    notified = set(state.get("notified_events", []))
    notified.add(event_id)
    state["notified_events"] = sorted(notified)
    save_state(state_path, state)


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
        "--pending-notification", action="store_true",
        help="Report whether a narrative on disk still needs a Teams card. "
             "Sets pending_notification, pending_event and pending_season.",
    )
    parser.add_argument(
        "--mark-notified", type=int, default=None, metavar="GW",
        help="Record that the Teams card for this gameweek has been sent.",
    )
    parser.add_argument(
        "-l", "--league_id", type=str, default=FPL_LEAGUE_ID,
        help=f"FPL league ID, for locating narratives. Default: {FPL_LEAGUE_ID}",
    )
    parser.add_argument(
        "--output-dir", type=str, default=".",
        help="Directory holding docs/narratives/. Default: current directory.",
    )
    parser.add_argument(
        "--cache-dir", type=str, default=None,
        help="Directory for file-based API response caching.",
    )
    args = parser.parse_args()

    state_path = Path(args.state_file)

    # Purely a state-file write; no API call needed.
    if args.mark_notified is not None:
        mark_notified(state_path, args.mark_notified)
        print(f"Marked GW {args.mark_notified} as notified.")
        return

    cache_dir = Path(args.cache_dir) if args.cache_dir else None
    api = FPL_API(cache_dir=cache_dir)

    if args.pending_notification:
        event_id, season = pending_notification(
            api, state_path, args.league_id, args.output_dir
        )
        pending = event_id is not None
        print(f"pending_notification={str(pending).lower()}")
        print(f"pending_event={event_id if pending else ''}")
        print(f"pending_season={season}")
        _set_github_output("pending_notification", str(pending).lower())
        _set_github_output("pending_event", str(event_id) if pending else "")
        _set_github_output("pending_season", season)
        if not pending:
            print("No report is waiting to be announced.")
        return

    if args.save:
        fixtures_count, events_count = save_counts(api, state_path)
        print(f"State saved: {fixtures_count} finished fixtures, "
              f"{events_count} finished events.")
        return

    has_new, gw_finished, new_state = check_status(api, state_path)
    has_finished_gw = new_state["finished_events"] > 0

    print(f"has_new_finished_fixtures={str(has_new).lower()}")
    print(f"gameweek_finished={str(gw_finished).lower()}")
    print(f"has_finished_gameweek={str(has_finished_gw).lower()}")

    _set_github_output("has_new_finished_fixtures", str(has_new).lower())
    _set_github_output("gameweek_finished", str(gw_finished).lower())
    _set_github_output("has_finished_gameweek", str(has_finished_gw).lower())

    if not has_new and not gw_finished:
        print("Nothing changed since last check.")


if __name__ == "__main__":
    main()
