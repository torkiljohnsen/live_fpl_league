import argparse
import sys
from fpl import LeagueTemplateRenderer, LeagueContext, FPL_API

FPL_LEAGUE_ID = "1639886"
DEFAULT_OUTPUT = "standings"
TEMPLATE_MAP = {
    "standings": "league_standings",
    "gw_history": "league_gameweek_history",
}

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate static HTML for FPL mini-league dashboard.")
    parser.add_argument("-l", "--league_id", type=str, default=FPL_LEAGUE_ID, help="FPL league ID (default: %(default)s)")
    parser.add_argument("-j", "--join_code", type=str, default=None, help="League join code (optional, only shown if provided)")
    parser.add_argument("--dev", action="store_true", help="Enable dev mode (use sample data)")
    parser.add_argument(
        "-o", "--output",
        type=str,
        choices=list(TEMPLATE_MAP.keys()),
        default=DEFAULT_OUTPUT,
        help=f"Which output to generate: {', '.join(TEMPLATE_MAP.keys())} (default: {DEFAULT_OUTPUT})"
    )
    args = parser.parse_args()

    try:
        context: LeagueContext = LeagueContext.build(
            args.league_id, args.dev, args.join_code, args.output, fpl_api=FPL_API(dev_mode=args.dev)
        )
        renderer = LeagueTemplateRenderer(context, args.output)
        renderer.write_html_output()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()