import argparse
import sys
from pathlib import Path

from fpl import FPL_API, LeagueContext, LeagueTemplateRenderer

FPL_LEAGUE_ID = "1639886"
ALL_OUTPUT = "ALL"
TEMPLATE_MAP = {
    "standings": "league_standings",
    "gw_history": "league_gameweek_history",
    "ranking_progression": "ranking_progression",
}

def parse_league_ids(raw_ids: list[str]) -> list[str]:
    ids: list[str] = []
    for item in raw_ids:
        # Support comma-separated lists as well as repeated flags
        parts = [p.strip() for p in item.split(',') if p.strip()]
        ids.extend(parts)
    # De-duplicate preserving order
    seen = set()
    deduped: list[str] = []
    for lid in ids:
        if lid not in seen:
            seen.add(lid)
            deduped.append(lid)
    return deduped

def render_league_outputs(league_id: str, outputs: list, join_code: str, dev_mode: bool, shared_api):
    """Render all requested outputs for a single league, reusing league data."""
    # Build context once per league
    context = LeagueContext.build(
        league_id, dev_mode, join_code, fpl_api=shared_api
    )
    for output_type in outputs:
        renderer = LeagueTemplateRenderer(context, output_type)
        print(f"Generating {output_type} for league {league_id}...")
        renderer.write_html_output()

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate static HTML dashboards for FPL mini-leagues.",
        epilog="Examples:\n"
               "  python generate_html.py                          # Generate all views for default league\n"
               "  python generate_html.py -l 1638989               # Generate all views for specific league\n"
               "  python generate_html.py -l 1638989,1639886       # Multiple leagues (comma-separated)\n"
               "  python generate_html.py -l 1638989 -l 1639886    # Multiple leagues (repeated flag)\n"
               "  python generate_html.py -o ranking_progression   # Generate only ranking progression view\n"
               "  python generate_html.py --dev                    # Use sample data (dev mode)\n",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "-l", "--league_id", dest="league_ids", action="append",
        help=f"FPL league ID(s). Can be comma-separated or repeated. Default: {FPL_LEAGUE_ID}"
    )
    parser.add_argument(
        "-j", "--join_code", type=str, default=None,
        help="League join code (optional, applied to all leagues)"
    )
    parser.add_argument(
        "--dev", action="store_true",
        help="Use sample data instead of live FPL API (outputs have '-dev.html' suffix)"
    )
    parser.add_argument(
        "-o", "--output", type=str, default=ALL_OUTPUT,
        choices=list(TEMPLATE_MAP.keys()) + [ALL_OUTPUT],
        help=f"Output view to generate. Options: {', '.join(TEMPLATE_MAP.keys())}, {ALL_OUTPUT}. Default: {ALL_OUTPUT}"
    )
    parser.add_argument(
        "--cache-dir", type=str, default=None,
        help="Directory for file-based API response caching.",
    )
    args = parser.parse_args()

    # Use default league ID only if user didn't provide any
    raw_league_ids = args.league_ids if args.league_ids else [FPL_LEAGUE_ID]
    league_ids = parse_league_ids(raw_league_ids)
    requested_outputs = list(TEMPLATE_MAP.keys()) if args.output == ALL_OUTPUT else [args.output]

    try:
        cache_dir = Path(args.cache_dir) if args.cache_dir else None
        shared_api = FPL_API(dev_mode=args.dev, cache_dir=cache_dir)
        for league_id in league_ids:
            render_league_outputs(
                league_id=league_id,
                outputs=requested_outputs,
                join_code=args.join_code,
                dev_mode=args.dev,
                shared_api=shared_api,
            )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
