
from typing import Optional
from .fpl_league import FPLLeague
from .fpl_api import FPL_API

LOGO_PATH = "assets/fpl_logo.svg"

class LeagueContext:
    def __init__(self, league_data: dict, league_join_code: Optional[str], logo_svg: str, output_type: str, dev_mode: bool = False):
        self.league_data = league_data
        self.league_join_code = league_join_code
        self.logo_svg = logo_svg
        self.output_type = output_type
        self.dev_mode = dev_mode

    @classmethod
    def build(
        cls,
        league_id: str,
        dev_mode: bool,
        league_join_code: Optional[str],
        output_type: str,
        fpl_api=None,
    ) -> "LeagueContext":
        if fpl_api is None:
            fpl_api = FPL_API(dev_mode=dev_mode)
        league = FPLLeague(league_id, fpl_api)
        league_data = league.get_summary()
        logo_svg = cls._get_logo_svg()
        return cls(
            league_data=league_data,
            league_join_code=league_join_code,
            logo_svg=logo_svg,
            output_type=output_type,
            dev_mode=dev_mode
        )

    @staticmethod
    def _get_logo_svg() -> str:
        with open(LOGO_PATH, "r", encoding="utf-8") as f:
            return f.read()

    @property
    def id(self):
        return self.league_data.get("id") or self.league_data.get("league", {}).get("id")

    def as_dict(self):
        # Flatten for template rendering
        d = dict(self.league_data)
        d["league_join_code"] = self.league_join_code
        d["logo_svg"] = self.logo_svg
        d["output_type"] = self.output_type
        d["dev_mode"] = self.dev_mode
        return d
