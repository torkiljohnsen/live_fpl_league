"""Reidar memory system for persistent narrative knowledge.

Manages Reidar's persistent knowledge across gameweeks, enabling
genuine opinions, storyline tracking, and recall of specific moments
from earlier in the season.

Directory structure::

    reidar_memory/{league_id}/{season}/
        season_arc.md               # Rolling season summary, records, threads
        managers/
            {first_name}.md         # Per-manager profile (~200 words)
        gameweeks/
            gw{N}.md                # Brief GW recap (~100 words)

Manager profile template (~200 words each)::

    # {First Name}
    **Team:** {Team Name}
    **Current Form:** ...
    **Season Trajectory:** ...
    **Reidar's Take:** ...
    **Notable Moments:** ...
    **Running Jokes:** ...
    **Transfer Habits:** ...
    **Captain Tendencies:** ...

Season arc template (~300 words)::

    # Sesongbue {season}
    **Tittelkamp:** ...
    **Aktive rivaliseringer:** ...
    **Sesongens rekorder:** ...
    **Reidars loepehistorier:** ...
    **Tonenotater:** ...

GW summary template (~100 words)::

    # Runde {N}
    **Noekkelhendelser:** ...
    **Reidar roste:** ...
    **Reidar mobbet:** ...
    **Historieutvikling:** ...
"""

from __future__ import annotations

from pathlib import Path


class ReidarMemory:
    """Manages Reidar's persistent knowledge across gameweeks.

    Constructor takes output_dir, league_id, and season to locate
    the memory directory. All load methods handle missing files
    gracefully, returning empty strings/dicts on first run.
    """

    def __init__(self, output_dir: str, league_id: str, season: str) -> None:
        self._base_path = (
            Path(output_dir) / "reidar_memory" / league_id / season
        )
        self._managers_path = self._base_path / "managers"
        self._gameweeks_path = self._base_path / "gameweeks"

    def scaffold_directories(self) -> None:
        """Create the memory directory structure.

        Creates reidar_memory/{league_id}/{season}/ with managers/
        and gameweeks/ subdirectories.
        """
        self._managers_path.mkdir(parents=True, exist_ok=True)
        self._gameweeks_path.mkdir(parents=True, exist_ok=True)

    def load_manager_profiles(self) -> dict[str, str]:
        """Read all manager profile .md files.

        Returns a dict mapping first_name (stem of the .md file)
        to the file content. Returns empty dict if the managers/
        directory doesn't exist or is empty.
        """
        if not self._managers_path.is_dir():
            return {}

        profiles: dict[str, str] = {}
        for md_file in sorted(self._managers_path.glob("*.md")):
            profiles[md_file.stem] = md_file.read_text(encoding="utf-8")
        return profiles

    def load_season_arc(self) -> str:
        """Read the season_arc.md file.

        Returns the file content, or an empty string if the file
        doesn't exist (first run).
        """
        arc_path = self._base_path / "season_arc.md"
        if not arc_path.is_file():
            return ""
        return arc_path.read_text(encoding="utf-8")

    def load_recent_gameweeks(
        self, current_event: int, window: int = 5
    ) -> list[str]:
        """Read the last N gameweek summaries before current_event.

        Reads gw{N}.md files for the gameweeks immediately preceding
        current_event, up to window count. Returns a list of file
        contents ordered from oldest to newest. Returns empty list
        if no summaries exist.
        """
        summaries: list[str] = []
        start = max(1, current_event - window)
        for gw in range(start, current_event):
            gw_path = self._gameweeks_path / f"gw{gw}.md"
            if gw_path.is_file():
                summaries.append(gw_path.read_text(encoding="utf-8"))
        return summaries

    def get_prompt_context(self, current_event: int) -> str:
        """Assemble all memory into a formatted prompt string.

        Combines all manager profiles, the season arc, and the last
        5 gameweek summaries into a single string suitable for
        inclusion in an LLM prompt. Returns minimal context on
        first run (no files exist).
        """
        sections: list[str] = []

        # Manager profiles
        profiles = self.load_manager_profiles()
        if profiles:
            sections.append("## Managerprofiler\n")
            for name, content in profiles.items():
                sections.append(f"### {name}\n{content}\n")

        # Season arc
        season_arc = self.load_season_arc()
        if season_arc:
            sections.append(f"## Sesongbue\n{season_arc}\n")

        # Recent gameweek summaries
        recent = self.load_recent_gameweeks(current_event)
        if recent:
            sections.append("## Tidligere runder\n")
            for summary in recent:
                sections.append(f"{summary}\n")

        if not sections:
            return ""

        return "# Reidars minne\n\n" + "\n".join(sections)
