"""Reidar memory system for persistent narrative knowledge.

Manages Reidar's persistent knowledge across gameweeks, enabling
genuine opinions, storyline tracking, and recall of specific moments
from earlier in the season.

Directory structure::

    weekly_report/reidar_memory/{league_id}/{season}/
        season_arc.md               # Rolling season summary, records, threads
        ledger.md                   # Prediction ledger (LLM-maintained)
        threads.md                  # Open running bits (LLM-maintained)
        recent.json                 # Last 8 headlines/openers/closers/jokes (code-maintained)
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
import re
from pathlib import Path
from typing import Any

from . import claude_api
from .front_matter import parse_front_matter

_RECENT_MAX_ENTRIES = 8
_LEDGER_MAX_LINES = 20
_THREADS_MAX_LINES = 10
_PROMPT_CONTEXT_WORD_CAP = 350
_DO_NOT_REPEAT_WORD_CAP = 200
_DO_NOT_REPEAT_ITEM_WORD_CAP = 15


def _cap_words(text: str, max_words: int) -> str:
    """Truncate text to at most max_words words, appending an ellipsis if cut."""
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + "…"


def _tail_lines(text: str, max_lines: int) -> str:
    """Keep only the last max_lines non-empty lines of text."""
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if len(lines) <= max_lines:
        return "\n".join(lines)
    return "\n".join(lines[-max_lines:])


def _strip_front_matter(narrative: str) -> str:
    """Strip a leading front-matter block, if present."""
    return parse_front_matter(narrative)[1]


def _first_sentence(text: str) -> str:
    """Return the first sentence of text (up to the first . ! or ?)."""
    flat = " ".join(text.split())
    match = re.search(r"^.*?[.!?](?=\s|$)", flat)
    if match:
        return match.group(0).strip()
    return flat.strip()


def _extract_headline(narrative: str) -> str:
    """Extract the headline from the first '# ' heading in the narrative."""
    for line in narrative.split("\n"):
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def _real_paragraphs(narrative: str) -> list[str]:
    """Return non-empty paragraphs, skipping front matter, headings, and images."""
    body = _strip_front_matter(narrative)
    paragraphs: list[str] = []
    for para in body.split("\n\n"):
        stripped = para.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        if stripped.startswith("!["):
            continue
        paragraphs.append(stripped)
    return paragraphs


def _extract_opener(narrative: str) -> str:
    """Return the first sentence of the first real paragraph."""
    paragraphs = _real_paragraphs(narrative)
    if not paragraphs:
        return ""
    return _first_sentence(paragraphs[0])


def _extract_closer(narrative: str) -> str:
    """Return the last non-empty paragraph, capped at 40 words."""
    paragraphs = _real_paragraphs(narrative)
    if not paragraphs:
        return ""
    closer = " ".join(paragraphs[-1].split())
    return _cap_words(closer, 40)


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
        self._ledger_path = self._base_path / "ledger.md"
        self._threads_path = self._base_path / "threads.md"
        self._recent_path = self._base_path / "recent.json"

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

    def load_ledger(self) -> str:
        """Read the ledger.md file (prediction ledger).

        Returns the file content, or an empty string if the file
        doesn't exist (first run / no predictions logged yet).
        """
        if not self._ledger_path.is_file():
            return ""
        return self._ledger_path.read_text(encoding="utf-8")

    def load_threads(self) -> str:
        """Read the threads.md file (open running bits).

        Returns the file content, or an empty string if the file
        doesn't exist (first run).
        """
        if not self._threads_path.is_file():
            return ""
        return self._threads_path.read_text(encoding="utf-8")

    def load_recent(self) -> list[dict[str, Any]]:
        """Read recent.json (code-maintained recently-used tracker).

        Returns a list of entry dicts, ordered oldest to newest.
        Returns an empty list if the file is missing, empty, or malformed.
        """
        if not self._recent_path.is_file():
            return []
        try:
            data = json.loads(self._recent_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
        if not isinstance(data, list):
            return []
        return data

    def record_recent(
        self,
        event_id: int,
        narrative: str,
        jokes: list[str] | None = None,
    ) -> None:
        """Append this week's headline/opener/closer/jokes to recent.json.

        Code-maintained (no LLM call). Extracts the headline (first '# '
        heading), the opener (first sentence of the first real paragraph
        after any front matter/heading/image), and the closer (last
        non-empty paragraph, capped at 40 words). Keeps only the last
        8 entries.
        """
        entries = self.load_recent()
        entries.append(
            {
                "event_id": event_id,
                "headline": _extract_headline(narrative),
                "opener": _extract_opener(narrative),
                "closer": _extract_closer(narrative),
                "jokes": jokes or [],
            }
        )
        entries = entries[-_RECENT_MAX_ENTRIES:]
        self._base_path.mkdir(parents=True, exist_ok=True)
        self._recent_path.write_text(
            json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def get_do_not_repeat_block(self, current_event: int, window: int = 5) -> str:
        """Build a Norwegian do-not-repeat block from recent.json.

        Looks at entries from the last `window` gameweeks before
        current_event and lists the headlines, openers, closers, and
        jokes already used, so the generator avoids reusing them.
        Returns an empty string when nothing is recorded in that window.
        """
        recent = self.load_recent()
        cutoff = current_event - window
        relevant = [
            e
            for e in recent
            if cutoff <= e.get("event_id", -1) < current_event
        ]
        if not relevant:
            return ""

        def _items(key: str) -> list[str]:
            values = [str(e[key]).strip() for e in relevant if e.get(key)]
            return [
                _cap_words(v, _DO_NOT_REPEAT_ITEM_WORD_CAP) for v in values if v
            ]

        headlines = _items("headline")
        openers = _items("opener")
        closers = _items("closer")
        jokes: list[str] = []
        for e in relevant:
            jokes.extend(str(j).strip() for j in (e.get("jokes") or []) if str(j).strip())
        # Cap item count before per-item word capping so a single window
        # can't blow the overall word budget through sheer joke volume.
        jokes = [_cap_words(j, _DO_NOT_REPEAT_ITEM_WORD_CAP) for j in jokes[-10:]]

        if not (headlines or openers or closers or jokes):
            return ""

        lines = ["## Ikke gjenta (brukt de siste fem rundene)"]
        if headlines:
            lines.append("**Overskrifter:** " + "; ".join(headlines))
        if openers:
            lines.append("**Åpninger:** " + "; ".join(openers))
        if closers:
            lines.append("**Avslutninger:** " + "; ".join(closers))
        if jokes:
            lines.append("**Vitser og bilder:** " + "; ".join(jokes))
        lines.append("Disse er brukt opp. Finn noe annet.")

        return _cap_words("\n".join(lines), _DO_NOT_REPEAT_WORD_CAP)

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

        # Prediction ledger + open threads, capped ~350 words combined
        ledger = _tail_lines(self.load_ledger(), _LEDGER_MAX_LINES)
        threads = _tail_lines(self.load_threads(), _THREADS_MAX_LINES)
        if ledger or threads:
            extra_parts: list[str] = []
            if ledger:
                extra_parts.append(f"## Spådomsprotokoll\n{ledger}")
            if threads:
                extra_parts.append(f"## Åpne tråder\n{threads}")
            sections.append(
                _cap_words("\n\n".join(extra_parts), _PROMPT_CONTEXT_WORD_CAP) + "\n"
            )

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
        current_ledger = self.load_ledger()
        current_threads = self.load_threads()

        manager_names = [
            p["player_first_name"]
            for p in report_json.get("standings", [])
        ]

        system_prompt = self._build_memory_update_prompt(
            manager_names, bool(current_profiles)
        )
        user_content = self._build_memory_update_user_message(
            report_json,
            narrative,
            current_profiles,
            current_arc,
            current_ledger,
            current_threads,
        )

        response_text = claude_api.complete(
            client,
            system=system_prompt,
            user=user_content,
        )

        self._save_debug_response(response_text, event_id)
        jokes = self._parse_and_write_memory(response_text, event_id)
        self.record_recent(event_id, narrative, jokes)

    def _save_debug_response(self, response_text: str, event_id: int) -> None:
        """Save the raw LLM response for debugging memory update parsing.

        Writes to {base_path}/debug/gw{N}_memory_response.txt so that
        parse failures can be investigated after the fact.
        """
        debug_dir = self._base_path / "debug"
        debug_dir.mkdir(parents=True, exist_ok=True)
        debug_path = debug_dir / f"gw{event_id}_memory_response.txt"
        debug_path.write_text(response_text, encoding="utf-8")

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
            "Husk også å ha med ===END=== på siste managerprofil"
            " — det er viktig for parsing.\n\n"
            "Deretter:\n"
            "===GW_SUMMARY===\n"
            "(rundesammendrag, ~100 ord)\n"
            "===END===\n\n"
            "Deretter:\n"
            "===SEASON_ARC===\n"
            "(sesongbue, ~300 ord)\n"
            "===END===\n\n"
            "Deretter:\n"
            "===LEDGER===\n"
            "(prediksjonslogg, én linje per spådom:\n"
            "- GW{runde} | <spådom, Reidars ord, maks 20 ord> | avgjøres: "
            "<GW eller betingelse> | status: åpen|riktig|feil (GW{løst}))\n"
            "===END===\n\n"
            "Deretter:\n"
            "===THREADS===\n"
            "(åpne tråder, én linje per tråd:\n"
            "- <tråds navn> | <én setning> | sist brukt: GW{runde})\n"
            "===END===\n\n"
            "Til slutt:\n"
            "===JOKES===\n"
            "(3–6 korte linjer: metaforer, gjentatte vitser, kallenavn "
            "brukt i narrativet denne uken)\n"
            "===END===\n\n"
            "Profiler bør inneholde: nåværende form, sesongutvikling, "
            "Reidars mening, nevneverdige øyeblikk, løpende vitser, "
            "byttemønster, kapteinvalg.\n\n"
            "Rundesammendrag bør inneholde: nøkkelhendelser, hvem Reidar "
            "roste, hvem han mobbet, historieutvikling.\n\n"
            "Sesongbue bør inneholde: tittelkamp, aktive rivaliseringer, "
            "sesongens rekorder, Reidars løpehistorier, tonenotater.\n\n"
            "Prediksjonslogg: ta med HVER åpen linje fra eksisterende logg "
            "uendret, legg til hver spådom/tips i denne ukens narrativ "
            "(fraser som «jeg spår», «jeg tipper», «kommer til å», "
            "«Reidars råd»), og løs opp linjer der rundedataen nå avgjør "
            "utfallet (sett status riktig/feil med runde). Maks 20 linjer "
            "— dropp de eldste løste først.\n\n"
            "Åpne tråder: oppdater «sist brukt» KUN når narrativet faktisk "
            "brukte tråden denne uken. Legg til nye tråder sparsomt. "
            "Fjern tråder ubrukt i 8+ runder. Maks 10 linjer.\n\n"
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
        current_ledger: str = "",
        current_threads: str = "",
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

        # Current ledger + threads (carried forward by the LLM)
        if current_ledger:
            parts.append(f"## Eksisterende prediksjonslogg\n{current_ledger}\n")
        else:
            parts.append("## Ingen eksisterende prediksjonslogg (første runde)\n")

        if current_threads:
            parts.append(f"## Eksisterende åpne tråder\n{current_threads}\n")
        else:
            parts.append("## Ingen eksisterende åpne tråder (første runde)\n")

        # Report JSON
        parts.append(
            "## Ny rundedata\n"
            f"```json\n{json.dumps(report_json, indent=1, ensure_ascii=False)}\n```\n"
        )

        # Narrative
        parts.append(f"## Narrativet som ble skrevet\n{narrative}\n")

        return "\n".join(parts)

    def _parse_and_write_memory(
        self, response_text: str, event_id: int
    ) -> list[str] | None:
        """Parse LLM response and write memory files.

        Expected sections delimited by ===MANAGER: name===...===END===,
        ===GW_SUMMARY===...===END===, ===SEASON_ARC===...===END===,
        ===LEDGER===...===END===, ===THREADS===...===END===, and
        ===JOKES===...===END===.

        Saves each section independently — a malformed section is skipped
        with a warning so that other sections are still written.

        Returns the parsed list of jokes (for `record_recent`), or None
        if the JOKES section is missing/malformed.
        """
        warnings: list[str] = []
        jokes: list[str] | None = None

        # Parse manager profiles
        remaining = response_text
        while "===MANAGER:" in remaining:
            try:
                start_marker = remaining.index("===MANAGER:")
                marker_end = remaining.index("===", start_marker + 3)
            except ValueError:
                warnings.append(
                    "MANAGER section: could not find closing '===' "
                    "for manager name marker. Skipping remaining managers."
                )
                break
            name_part = remaining[start_marker + len("===MANAGER:"):marker_end].strip()
            content_start = marker_end + 3
            if content_start < len(remaining) and remaining[content_start] == "\n":
                content_start += 1
            try:
                end_marker = remaining.index("===END===", content_start)
            except ValueError:
                warnings.append(
                    f"MANAGER section for '{name_part}': could not find "
                    "'===END===' delimiter. Skipping this manager."
                )
                # Advance past the broken marker to continue parsing
                remaining = remaining[content_start:]
                continue
            content = remaining[content_start:end_marker].strip()

            profile_path = self._managers_path / f"{name_part}.md"
            profile_path.write_text(content, encoding="utf-8")

            remaining = remaining[end_marker + len("===END==="):]

        # Parse GW summary
        if "===GW_SUMMARY===" in remaining:
            start = remaining.index("===GW_SUMMARY===") + len("===GW_SUMMARY===")
            if start < len(remaining) and remaining[start] == "\n":
                start += 1
            try:
                end = remaining.index("===END===", start)
                gw_content = remaining[start:end].strip()
                gw_path = self._gameweeks_path / f"gw{event_id}.md"
                gw_path.write_text(gw_content, encoding="utf-8")
                remaining = remaining[end + len("===END==="):]
            except ValueError:
                warnings.append(
                    "GW_SUMMARY section: could not find '===END===' delimiter. "
                    "Skipping GW summary."
                )

        # Parse season arc
        if "===SEASON_ARC===" in remaining:
            start = remaining.index("===SEASON_ARC===") + len("===SEASON_ARC===")
            if start < len(remaining) and remaining[start] == "\n":
                start += 1
            try:
                end = remaining.index("===END===", start)
                arc_content = remaining[start:end].strip()
                arc_path = self._base_path / "season_arc.md"
                arc_path.write_text(arc_content, encoding="utf-8")
            except ValueError:
                warnings.append(
                    "SEASON_ARC section: could not find '===END===' delimiter. "
                    "Skipping season arc."
                )

        # Parse prediction ledger
        if "===LEDGER===" in remaining:
            start = remaining.index("===LEDGER===") + len("===LEDGER===")
            if start < len(remaining) and remaining[start] == "\n":
                start += 1
            try:
                end = remaining.index("===END===", start)
                ledger_content = remaining[start:end].strip()
                self._ledger_path.write_text(ledger_content, encoding="utf-8")
            except ValueError:
                warnings.append(
                    "LEDGER section: could not find '===END===' delimiter. "
                    "Skipping prediction ledger."
                )

        # Parse open threads
        if "===THREADS===" in remaining:
            start = remaining.index("===THREADS===") + len("===THREADS===")
            if start < len(remaining) and remaining[start] == "\n":
                start += 1
            try:
                end = remaining.index("===END===", start)
                threads_content = remaining[start:end].strip()
                self._threads_path.write_text(threads_content, encoding="utf-8")
            except ValueError:
                warnings.append(
                    "THREADS section: could not find '===END===' delimiter. "
                    "Skipping open threads."
                )

        # Parse jokes (returned to the caller, not written to a file —
        # record_recent() folds them into recent.json)
        if "===JOKES===" in remaining:
            start = remaining.index("===JOKES===") + len("===JOKES===")
            if start < len(remaining) and remaining[start] == "\n":
                start += 1
            try:
                end = remaining.index("===END===", start)
                jokes_content = remaining[start:end].strip()
                jokes = [
                    line.lstrip("-").strip()
                    for line in jokes_content.split("\n")
                    if line.strip()
                ]
            except ValueError:
                warnings.append(
                    "JOKES section: could not find '===END===' delimiter. "
                    "Skipping jokes."
                )

        if warnings:
            import sys

            print(
                "WARNING: Memory update partially failed — "
                "some sections could not be parsed:\n"
                + "\n".join(f"  - {w}" for w in warnings),
                file=sys.stderr,
            )

        return jokes
