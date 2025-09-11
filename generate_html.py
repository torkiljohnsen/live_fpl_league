import argparse
import sys
from typing import List
from fpl import LeagueTemplateRenderer, LeagueContext, FPL_API

FPL_LEAGUE_ID = "1639886"
ALL_OUTPUT = "ALL"
TEMPLATE_MAP = {
    "standings": "league_standings",
    "gw_history": "league_gameweek_history",
}

def parse_league_ids(raw_ids: List[str]) -> List[str]:
    ids: List[str] = []
    for item in raw_ids:
        # Support comma-separated lists as well as repeated flags
        parts = [p.strip() for p in item.split(',') if p.strip()]
        ids.extend(parts)
    # De-duplicate preserving order
    seen = set()
    deduped: List[str] = []
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
    parser = argparse.ArgumentParser(description="Generate static HTML for FPL mini-league dashboard.")
    parser.add_argument(
        "-l", "--league_id", dest="league_ids", action="append", default=[FPL_LEAGUE_ID],
        help="FPL league ID(s). Provide multiple times or comma-separated to generate for several leagues."
    )
    parser.add_argument("-j", "--join_code", type=str, default=None, help="League join code (optional, applied to all leagues)")
    parser.add_argument("--dev", action="store_true", help="Enable dev mode (use sample data)")
    parser.add_argument(
        "-o", "--output", type=str, default=ALL_OUTPUT,
        choices=list(TEMPLATE_MAP.keys()) + [ALL_OUTPUT],
        help="Which output to generate (template key) or ALL (default)."
    )
    args = parser.parse_args()

    league_ids = parse_league_ids(args.league_ids)
    requested_outputs = list(TEMPLATE_MAP.keys()) if args.output == ALL_OUTPUT else [args.output]

    try:
        shared_api = FPL_API(dev_mode=args.dev)
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