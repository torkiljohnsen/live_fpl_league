"""Reidar memory system for persistent narrative knowledge.

Manages Reidar's persistent knowledge across gameweeks, enabling
genuine opinions, storyline tracking, and recall of specific moments
from earlier in the season.

Directory structure::

    weekly_report/reidar_memory/{league_id}/{season}/
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

import json
from pathlib import Path
from typing import Any


class ReidarMemory:
    """Manages Reidar's persistent knowledge across gameweeks.

    Constructor takes output_dir, league_id, and season to locate
    the memory directory. All load methods handle missing files
    gracefully, returning empty strings/dicts on first run.
    """

    def __init__(self, output_dir: str, league_id: str, season: str) -> None:
        self._base_path = (
            Path(output_dir) / "weekly_report" / "reidar_memory" / league_id / season
        )
        self._managers_path = self._base_path / "managers"
        self._gameweeks_path = self._base_path / "gameweeks"

    def scaffold_directories(self) -> None:
        """Create the memory directory structure.

        Creates weekly_report/reidar_memory/{league_id}/{season}/ with managers/
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

    def update_memory(
        self,
        report_json: dict[str, Any],
        narrative: str,
        client: Any,
    ) -> None:
        """Update Reidar's memory files after narrative generation.

        Makes a Claude API call with current memory, the new report data,
        and the narrative just written. Updates manager profiles, creates
        a GW summary, and updates the season arc.

        On first run (no existing profiles), bootstraps manager profiles
        from the report data.

        Args:
            report_json: The structured gameweek report dict.
            narrative: The narrative just generated.
            client: An anthropic client instance.
        """
        self.scaffold_directories()

        event_id = report_json.get("meta", {}).get("event_id", 0)
        current_profiles = self.load_manager_profiles()
        current_arc = self.load_season_arc()

        manager_names = [
            p["player_first_name"]
            for p in report_json.get("standings", [])
        ]

        system_prompt = self._build_memory_update_prompt(
            manager_names, bool(current_profiles)
        )
        user_content = self._build_memory_update_user_message(
            report_json, narrative, current_profiles, current_arc
        )

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_content}],
        )

        response_text: str = response.content[0].text  # type: ignore[union-attr]

        self._parse_and_write_memory(response_text, event_id)

    def _build_memory_update_prompt(
        self,
        manager_names: list[str],
        has_existing_profiles: bool,
    ) -> str:
        """Build the system prompt for the memory update LLM call."""
        names_list = ", ".join(manager_names)

        bootstrap_note = ""
        if not has_existing_profiles:
            bootstrap_note = (
                "\nDette er FØRSTE runde — det finnes ingen eksisterende profiler. "
                "Opprett nye profiler for hver manager basert på rundedataen. "
                "Gi dem grunnleggende vurderinger basert på denne ene runden.\n"
            )

        return (
            "Du er Reidars minneoppdaterer. Jobben din er å oppdatere "
            "Reidars minnefiler basert på ny rundedata og narrativet som "
            "nettopp ble skrevet.\n\n"
            "Skriv på norsk. Vær konsis.\n\n"
            f"Managere i ligaen: {names_list}\n"
            f"{bootstrap_note}\n"
            "Du MÅ produsere output med NØYAKTIG dette formatet. "
            "Bruk seksjonsskilletegnene eksakt som vist:\n\n"
            "For HVER manager, skriv:\n"
            "===MANAGER: {navn}===\n"
            "(profiltekst, ~200 ord)\n"
            "===END===\n\n"
            "Deretter:\n"
            "===GW_SUMMARY===\n"
            "(rundesammendrag, ~100 ord)\n"
            "===END===\n\n"
            "Til slutt:\n"
            "===SEASON_ARC===\n"
            "(sesongbue, ~300 ord)\n"
            "===END===\n\n"
            "Profiler bør inneholde: nåværende form, sesongutvikling, "
            "Reidars mening, nevneverdige øyeblikk, løpende vitser, "
            "byttemønster, kapteinvalg.\n\n"
            "Rundesammendrag bør inneholde: nøkkelhendelser, hvem Reidar "
            "roste, hvem han mobbet, historieutvikling.\n\n"
            "Sesongbue bør inneholde: tittelkamp, aktive rivaliseringer, "
            "sesongens rekorder, Reidars løpehistorier, tonenotater.\n\n"
            "VIKTIG: Oppdater eksisterende profiler med NY informasjon — "
            "ikke gjenta alt fra forrige gang. Behold det som fortsatt er "
            "relevant og legg til nytt."
        )

    def _build_memory_update_user_message(
        self,
        report_json: dict[str, Any],
        narrative: str,
        current_profiles: dict[str, str],
        current_arc: str,
    ) -> str:
        """Build the user message for the memory update LLM call."""
        parts: list[str] = []

        # Current profiles
        if current_profiles:
            parts.append("## Eksisterende managerprofiler\n")
            for name, content in current_profiles.items():
                parts.append(f"### {name}\n{content}\n")
        else:
            parts.append("## Ingen eksisterende profiler (første runde)\n")

        # Current season arc
        if current_arc:
            parts.append(f"## Eksisterende sesongbue\n{current_arc}\n")
        else:
            parts.append("## Ingen eksisterende sesongbue (første runde)\n")

        # Report JSON
        parts.append(
            "## Ny rundedata\n"
            f"```json\n{json.dumps(report_json, indent=2, ensure_ascii=False)}\n```\n"
        )

        # Narrative
        parts.append(f"## Narrativet som ble skrevet\n{narrative}\n")

        return "\n".join(parts)

    def _parse_and_write_memory(
        self, response_text: str, event_id: int
    ) -> None:
        """Parse LLM response and write memory files.

        Expected sections delimited by ===MANAGER: name===...===END===,
        ===GW_SUMMARY===...===END===, ===SEASON_ARC===...===END===.
        """
        # Parse manager profiles
        remaining = response_text
        while "===MANAGER:" in remaining:
            start_marker = remaining.index("===MANAGER:")
            # Extract name from marker line
            marker_end = remaining.index("===", start_marker + 3)
            name_part = remaining[start_marker + len("===MANAGER:"):marker_end].strip()
            # Find content between marker end and ===END===
            content_start = marker_end + 3
            # Skip newline after marker
            if content_start < len(remaining) and remaining[content_start] == "\n":
                content_start += 1
            end_marker = remaining.index("===END===", content_start)
            content = remaining[content_start:end_marker].strip()

            # Write manager profile
            profile_path = self._managers_path / f"{name_part}.md"
            profile_path.write_text(content, encoding="utf-8")

            remaining = remaining[end_marker + len("===END==="):]

        # Parse GW summary
        if "===GW_SUMMARY===" in remaining:
            start = remaining.index("===GW_SUMMARY===") + len("===GW_SUMMARY===")
            if start < len(remaining) and remaining[start] == "\n":
                start += 1
            end = remaining.index("===END===", start)
            gw_content = remaining[start:end].strip()
            gw_path = self._gameweeks_path / f"gw{event_id}.md"
            gw_path.write_text(gw_content, encoding="utf-8")
            remaining = remaining[end + len("===END==="):]

        # Parse season arc
        if "===SEASON_ARC===" in remaining:
            start = remaining.index("===SEASON_ARC===") + len("===SEASON_ARC===")
            if start < len(remaining) and remaining[start] == "\n":
                start += 1
            end = remaining.index("===END===", start)
            arc_content = remaining[start:end].strip()
            arc_path = self._base_path / "season_arc.md"
            arc_path.write_text(arc_content, encoding="utf-8")
