"""CLI entry point for generating weekly FPL league reports.

Generates a structured JSON report for a given gameweek, including
standings, awards, and league summary data. Follows the same patterns
as generate_html.py for argument parsing and API usage.
"""

import argparse
import sys

from fpl import FPL_API
from fpl.weekly_report import WeeklyReport

FPL_LEAGUE_ID = "1639886"


def detect_current_gameweek(api: FPL_API) -> int:
    """Find the latest finished gameweek from bootstrap-static data.

    Scans events in reverse to find the most recent event with
    finished=True. Raises SystemExit if no finished gameweek is found.
    """
    bootstrap = api.get_bootstrap_static()
    events = bootstrap.get("events", [])

    for event in reversed(events):
        if event.get("finished", False):
            return int(event["id"])

    print("Error: No finished gameweek found.", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate weekly FPL league report (JSON).",
        epilog="Examples:\n"
               "  python generate_weekly_report.py                        # Auto-detect GW, default league\n"
               "  python generate_weekly_report.py -l 1639886 -e 25      # Specific league and GW\n"
               "  python generate_weekly_report.py --dev                  # Use sample data (dev mode)\n"
               "  python generate_weekly_report.py --output-dir ./out     # Custom output directory\n",
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
        "--dev", action="store_true",
        help="Use sample data instead of live FPL API.",
    )
    parser.add_argument(
        "--output-dir", type=str, default=".",
        help="Output directory for report files. Default: current directory.",
    )
    args = parser.parse_args()

    try:
        api = FPL_API(dev_mode=args.dev)

        event_id: int
        if args.event is not None:
            event_id = args.event
        else:
            event_id = detect_current_gameweek(api)

        report = WeeklyReport(api=api, league_id=args.league_id, event_id=event_id)
        result = report.build()

        league_name = result["meta"]["league_name"]
        output_path = report.save_report(args.output_dir)

        print(f"League: {league_name}")
        print(f"Gameweek: {event_id}")
        print(f"Report saved: {output_path}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
