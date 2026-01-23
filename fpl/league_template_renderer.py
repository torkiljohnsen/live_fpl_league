from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .league_context import LeagueContext


class LeagueTemplateRenderer:
    TEMPLATE_MAP: dict[str, str] = {
        "standings": "league_standings",
        "gw_history": "league_gameweek_history",
        "ranking_progression": "ranking_progression",
    }

    context: LeagueContext
    output_type: str
    env: Any

    def __init__(self, context: LeagueContext, output_type: str, template_dir: str = "templates") -> None:
        self.context = context
        self.output_type = output_type
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            extensions=['jinja2.ext.do'],
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True
        )

    def get_template_name(self) -> str:
        if self.output_type not in self.TEMPLATE_MAP:
            raise ValueError(f"Unknown output type: {self.output_type}")
        return f"{self.TEMPLATE_MAP[self.output_type]}.html"

    def get_output_path(self) -> Path:
        league_id = self.context.id or "unknown"
        dev_mode = self.context.dev_mode
        template_name = self.TEMPLATE_MAP[self.output_type]
        suffix = "-dev" if dev_mode else ""
        filename = f"{template_name}_{league_id}{suffix}.html"
        return Path("docs") / filename

    def write_html_output(self) -> None:
        template = self.env.get_template(self.get_template_name())
        html = template.render(**self.context.as_dict(), output_type=self.output_type)
        output_path = self.get_output_path()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Static HTML generated at {output_path}")
