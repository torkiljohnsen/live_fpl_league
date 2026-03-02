"""CLI entry point for generating weekly narrative via Claude API.

Reads an existing report JSON from disk, generates a Norwegian-language
narrative using Reidar's persona and memory system, and saves the
narrative markdown file.

Requires: ANTHROPIC_API_KEY environment variable.
Prerequisite: run generate_weekly_report.py first to produce the JSON.
"""

import argparse
import json
import os
import sys
from pathlib import Path

from fpl import FPL_API
from fpl.narrative_generator import run_narrative_pipeline
from fpl.weekly_report import (
    detect_current_gameweek,
    get_narrative_path,
    get_report_path,
    get_season_from_bootstrap,
)

FPL_LEAGUE_ID = "1639886"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate weekly narrative from an existing report JSON.",
        epilog="Examples:\n"
               "  python generate_narrative.py -l 1638989           # Auto-detect GW\n"
               "  python generate_narrative.py -l 1638989 -e 25     # Specific GW\n"
               "  python generate_narrative.py -l 1638989 --skip-existing\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-l", "--league_id", type=str, default=FPL_LEAGUE_ID,
        help=f"FPL league ID. Default: {FPL_LEAGUE_ID}",
    )
    parser.add_argument(
        "-e", "--event", type=int, default=None,
        help="Gameweek number. If omitted, auto-detects the latest finished GW.",
    )
    parser.add_argument(
        "--output-dir", type=str, default=".",
        help="Output directory for narrative files. Default: current directory.",
    )
    parser.add_argument(
        "--skip-existing", action="store_true",
        help="Skip generation if the narrative .md already exists on disk.",
    )
    parser.add_argument(
        "--cache-dir", type=str, default=None,
        help="Directory for file-based API response caching.",
    )
    args = parser.parse_args()

    cache_dir = Path(args.cache_dir) if args.cache_dir else None
    api = FPL_API(cache_dir=cache_dir)

    event_id: int
    if args.event is not None:
        event_id = args.event
    else:
        event_id = detect_current_gameweek(api)

    bootstrap = api.get_bootstrap_static()
    season = get_season_from_bootstrap(bootstrap)

    # Check if narrative already exists
    if args.skip_existing:
        existing_path = get_narrative_path(
            args.output_dir, args.league_id, season, event_id
        )
        if existing_path.is_file():
            print(f"Narrative already exists: {existing_path} — skipping.")
            _set_github_output("generated", "false")
            return

    # Load report JSON
    report_path = get_report_path(
        args.output_dir, args.league_id, season, event_id
    )
    if not report_path.is_file():
        print(
            f"Error: Report JSON not found: {report_path}\n"
            "Run generate_weekly_report.py first.",
            file=sys.stderr,
        )
        sys.exit(1)

    result = json.loads(report_path.read_text(encoding="utf-8"))

    # Generate narrative (full traceback on error — no swallowing)
    narrative_path = run_narrative_pipeline(
        result=result,
        league_id=args.league_id,
        event_id=event_id,
        output_dir=args.output_dir,
    )
    print(f"Narrative saved: {narrative_path}")
    _set_github_output("generated", "true")


def _set_github_output(name: str, value: str) -> None:
    """Write a step output variable for GitHub Actions.

    No-op when not running in GitHub Actions (GITHUB_OUTPUT unset).
    """
    output_file = os.environ.get("GITHUB_OUTPUT")
    if output_file:
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(f"{name}={value}\n")


if __name__ == "__main__":
    main()
