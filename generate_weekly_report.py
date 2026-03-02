"""CLI entry point for generating weekly FPL league reports (JSON only).

Generates a structured JSON report for a given gameweek, including
standings, awards, and league summary data.

For narrative generation, see generate_narrative.py.
For Teams notification, see notify_teams.py.
"""

import argparse
import sys
from pathlib import Path

from fpl import FPL_API
from fpl.weekly_report import (
    WeeklyReport,
    detect_current_gameweek,
    get_report_path,
    get_season_from_bootstrap,
)

FPL_LEAGUE_ID = "1639886"


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
    parser.add_argument(
        "--skip-existing", action="store_true",
        help="Skip generation if the report JSON already exists on disk.",
    )
    parser.add_argument(
        "--cache-dir", type=str, default=None,
        help="Directory for file-based API response caching.",
    )
    args = parser.parse_args()

    try:
        cache_dir = Path(args.cache_dir) if args.cache_dir else None
        api = FPL_API(dev_mode=args.dev, cache_dir=cache_dir)

        event_id: int
        if args.event is not None:
            event_id = args.event
        else:
            event_id = detect_current_gameweek(api)

        # Check if report already exists
        if args.skip_existing:
            bootstrap = api.get_bootstrap_static()
            season = get_season_from_bootstrap(bootstrap)
            report_path = get_report_path(
                args.output_dir, args.league_id, season, event_id
            )
            if report_path.is_file():
                print(f"Report already exists: {report_path} — skipping.")
                return

        # Build and save report
        report = WeeklyReport(api=api, league_id=args.league_id, event_id=event_id)
        result = report.build()
        league_name = result["meta"]["league_name"]
        output_path = report.save_report(args.output_dir)

        print(f"Report saved: {output_path}")
        print(f"League: {league_name}")
        print(f"Gameweek: {event_id}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
