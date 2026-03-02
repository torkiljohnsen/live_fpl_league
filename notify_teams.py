"""CLI entry point for sending Teams notifications.

Reads an existing narrative markdown from disk and posts it as an
Adaptive Card to a Microsoft Teams webhook.

Requires: TEAMS_WEBHOOK_URL environment variable.
Prerequisite: run generate_narrative.py first to produce the .md file.
"""

import argparse
import os
import sys
from pathlib import Path

from fpl import FPL_API
from fpl.teams_notification import post_to_teams
from fpl.weekly_report import (
    detect_current_gameweek,
    get_narrative_path,
    get_season_from_bootstrap,
)

FPL_LEAGUE_ID = "1639886"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Send Teams notification for an existing narrative.",
        epilog="Examples:\n"
               "  python notify_teams.py -l 1638989           # Auto-detect GW\n"
               "  python notify_teams.py -l 1638989 -e 25     # Specific GW\n",
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
        help="Output directory where narrative files are stored. Default: current directory.",
    )
    parser.add_argument(
        "--cache-dir", type=str, default=None,
        help="Directory for file-based API response caching.",
    )
    args = parser.parse_args()

    webhook_url = os.environ.get("TEAMS_WEBHOOK_URL")
    if not webhook_url:
        print(
            "Error: TEAMS_WEBHOOK_URL environment variable is not set.",
            file=sys.stderr,
        )
        sys.exit(1)

    cache_dir = Path(args.cache_dir) if args.cache_dir else None
    api = FPL_API(cache_dir=cache_dir)

    event_id: int
    if args.event is not None:
        event_id = args.event
    else:
        event_id = detect_current_gameweek(api)

    bootstrap = api.get_bootstrap_static()
    season = get_season_from_bootstrap(bootstrap)

    # Load narrative markdown
    narrative_path = get_narrative_path(
        args.output_dir, args.league_id, season, event_id
    )
    if not narrative_path.is_file():
        print(
            f"Error: Narrative not found: {narrative_path}\n"
            "Run generate_narrative.py first.",
            file=sys.stderr,
        )
        sys.exit(1)

    narrative_content = narrative_path.read_text(encoding="utf-8")

    narrative_url = (
        "https://torkiljohnsen.github.io/live_fpl_league/"
        f"reidars_rapport.html?gw={event_id}"
    )
    image_url = (
        "https://torkiljohnsen.github.io/live_fpl_league/"
        "assets/reidars_rapport_5.png"
    )

    success = post_to_teams(
        webhook_url=webhook_url,
        gameweek=event_id,
        narrative=narrative_content,
        narrative_url=narrative_url,
        image_url=image_url,
    )

    if success:
        print("Teams notification sent successfully.")
    else:
        print("Error: Teams notification failed.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
