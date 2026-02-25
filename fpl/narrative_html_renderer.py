from __future__ import annotations

import re
from pathlib import Path

import markdown  # type: ignore[import-untyped]
from jinja2 import Environment, FileSystemLoader, select_autoescape

GITHUB_PAGES_BASE = "https://torkiljohnsen.github.io/live_fpl_league/"


class NarrativeHTMLRenderer:
    def __init__(self, template_dir: str = "templates", output_dir: str = "docs") -> None:
        self.output_dir = Path(output_dir)
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(
        self,
        narrative_md: str,
        league_id: str,
        league_name: str,
        season: str,
        event_id: int,
    ) -> Path:
        title = "Reidars Rapport"
        lines = narrative_md.split("\n")

        # Extract title from first # heading
        for line in lines:
            if line.startswith("# "):
                title = line[2:].strip()
                break

        # Remove title lines and image lines from body
        body_lines = []
        for line in lines:
            if line.startswith("# "):
                continue
            if re.match(r"!\[.*\]\(.*\)", line):
                continue
            body_lines.append(line)

        body_md = "\n".join(body_lines).strip()
        body_html = markdown.markdown(body_md, extensions=["extra"])

        # Relative path from narratives/<season>/<league_id>/ back to docs root
        base_path = "../../../"

        template = self.env.get_template("narrative.html")
        html = template.render(
            title=title,
            subtitle=f"Runde {event_id}",
            body_html=body_html,
            hero_image=f"{base_path}assets/reidars_rapport_2.png",
            base_path=base_path,
            league_id=league_id,
            league_name=league_name,
            season=season,
        )

        output_path = (
            self.output_dir
            / "narratives"
            / season
            / league_id
            / f"reidars_rapport_gw{event_id}.html"
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        return output_path

    @staticmethod
    def get_github_pages_url(league_id: str, event_id: int, season: str) -> str:
        return (
            f"{GITHUB_PAGES_BASE}"
            f"narratives/{season}/{league_id}/"
            f"reidars_rapport_gw{event_id}.html"
        )
