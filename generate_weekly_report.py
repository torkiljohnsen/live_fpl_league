"""CLI entry point for generating weekly FPL league reports.

Generates a structured JSON report for a given gameweek, including
standings, awards, and league summary data. Optionally generates a
Norwegian-language narrative via Claude API using Reidar's persona
and persistent memory system.
"""

import argparse
import json
import os
import sys
from pathlib import Path

from fpl import FPL_API
from fpl.narrative_generator import NarrativeGenerator
from fpl.narrative_html_renderer import NarrativeHTMLRenderer
from fpl.reidar_memory import ReidarMemory
from fpl.teams_notification import post_to_teams
from fpl.weekly_report import WeeklyReport, get_season_from_bootstrap

FPL_LEAGUE_ID = "1639886"

# Reidar reference docs live in weekly_report/ relative to this script
_SCRIPT_DIR = Path(__file__).resolve().parent
_REIDAR_DOCS_DIR = _SCRIPT_DIR / "weekly_report"


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


def _read_reidar_doc(filename: str) -> str:
    """Read a Reidar reference document from the weekly_report/ directory."""
    path = _REIDAR_DOCS_DIR / filename
    return path.read_text(encoding="utf-8")


def _generate_narrative(
    result: dict,
    league_id: str,
    event_id: int,
    output_dir: str,
) -> str:
    """Run the full narrative pipeline: generate, save, update memory.

    Returns the path to the saved narrative file.
    """
    season = result["meta"]["season"]

    # Read Reidar reference docs
    persona = _read_reidar_doc("REIDAR_PERSONA.md")
    narrative_guide = _read_reidar_doc("NARRATIVE_GUIDE.md")
    examples = _read_reidar_doc("REIDAR_EXAMPLES.md")

    # Load memory context
    memory = ReidarMemory(
        output_dir=output_dir, league_id=league_id, season=season
    )
    memory.scaffold_directories()
    memory_context = memory.get_prompt_context(event_id)

    # Check for previous narrative
    previous_narrative: str | None = None
    prev_narrative_path = result["meta"].get("previous_narrative")
    if prev_narrative_path:
        full_prev_path = Path(output_dir) / prev_narrative_path
        if full_prev_path.is_file():
            previous_narrative = full_prev_path.read_text(encoding="utf-8")

    # Generate narrative
    generator = NarrativeGenerator()
    narrative = generator.generate(
        report_json=result,
        persona=persona,
        narrative_guide=narrative_guide,
        examples=examples,
        memory_context=memory_context,
        previous_narrative=previous_narrative,
    )

    # Save narrative
    narrative_path = generator.save_narrative(
        content=narrative,
        output_dir=output_dir,
        league_id=league_id,
        season=season,
        event_id=event_id,
    )

    # Update Reidar's memory
    memory.update_memory(
        report_json=result,
        narrative=narrative,
        client=generator._client,
    )

    return str(narrative_path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate weekly FPL league report (JSON + optional narrative).",
        epilog="Examples:\n"
               "  python generate_weekly_report.py                        # Auto-detect GW, default league\n"
               "  python generate_weekly_report.py -l 1639886 -e 25      # Specific league and GW\n"
               "  python generate_weekly_report.py --dev                  # Use sample data (dev mode)\n"
               "  python generate_weekly_report.py --dev --narrative      # Dev mode with narrative\n"
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
        "--narrative", action="store_true",
        help="Generate a Norwegian narrative via Claude API after building the report.",
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
    parser.add_argument(
        "--notify-teams", action="store_true",
        help="Post Teams notification after narrative generation. Requires TEAMS_WEBHOOK_URL env var.",
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

        # Resolve paths for skip-existing checks
        report_exists = False
        narrative_exists = False
        report_path: Path | None = None
        narrative_path_expected: Path | None = None

        if args.skip_existing:
            bootstrap = api.get_bootstrap_static()
            season = get_season_from_bootstrap(bootstrap)
            report_path = (
                Path(args.output_dir)
                / "weekly_report"
                / "reports"
                / args.league_id
                / season
                / f"gw{event_id}.json"
            )
            narrative_path_expected = (
                Path(args.output_dir)
                / "weekly_report"
                / "narratives"
                / args.league_id
                / season
                / f"gw{event_id}.md"
            )
            assert report_path is not None
            assert narrative_path_expected is not None
            report_exists = report_path.is_file()
            narrative_exists = narrative_path_expected.is_file()

            if report_exists and (not args.narrative or narrative_exists):
                print(f"Report already exists: {report_path} — skipping.")
                return

        # Build or load report
        if report_exists and report_path is not None:
            print(f"Report already exists: {report_path} — loading for narrative retry.")
            result = json.loads(report_path.read_text(encoding="utf-8"))
            league_name = result["meta"]["league_name"]
        else:
            report = WeeklyReport(api=api, league_id=args.league_id, event_id=event_id)
            result = report.build()
            league_name = result["meta"]["league_name"]
            output_path = report.save_report(args.output_dir)
            print(f"Report saved: {output_path}")

        print(f"League: {league_name}")
        print(f"Gameweek: {event_id}")

        if args.narrative and not narrative_exists:
            try:
                narrative_path = _generate_narrative(
                    result=result,
                    league_id=args.league_id,
                    event_id=event_id,
                    output_dir=args.output_dir,
                )
                print(f"Narrative saved: {narrative_path}")

                # --- HTML rendering (non-fatal) ---
                try:
                    renderer = NarrativeHTMLRenderer()
                    narrative_content = Path(narrative_path).read_text(encoding="utf-8")
                    html_path = renderer.render(
                        narrative_md=narrative_content,
                        league_id=args.league_id,
                        league_name=league_name,
                        season=result["meta"]["season"],
                        event_id=event_id,
                    )
                    print(f"Narrative HTML rendered: {html_path}")
                except Exception as e:
                    print(f"WARNING: HTML rendering failed: {e}", file=sys.stderr)

                # --- Teams notification (non-fatal) ---
                try:
                    if args.notify_teams:
                        webhook_url = os.environ.get("TEAMS_WEBHOOK_URL")
                        if webhook_url:
                            narrative_content = Path(narrative_path).read_text(encoding="utf-8")
                            narrative_url = NarrativeHTMLRenderer.get_github_pages_url(
                                args.league_id, event_id,
                            )
                            image_url = "https://torkiljohnsen.github.io/live_fpl_league/reidars_rapport_2.png"
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
                                print("WARNING: Teams notification failed.", file=sys.stderr)
                        else:
                            print("WARNING: TEAMS_WEBHOOK_URL not set — skipping Teams notification.", file=sys.stderr)
                except Exception as e:
                    print(f"WARNING: Teams notification failed: {e}", file=sys.stderr)

            except Exception as e:
                print(f"WARNING: Narrative generation failed: {e}", file=sys.stderr)
                print("Report was saved successfully. Narrative skipped.", file=sys.stderr)
        elif args.narrative and narrative_exists:
            print(f"Narrative already exists: {narrative_path_expected} — skipping.")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
