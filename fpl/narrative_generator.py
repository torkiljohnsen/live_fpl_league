"""Narrative generator for weekly FPL reports.

Uses the Anthropic Claude API to generate entertaining Norwegian-language
narratives in Reidar's voice, based on structured gameweek report data
and persistent memory context.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .reidar_memory import ReidarMemory

# Reidar reference docs live in weekly_report/ relative to the repo root
_REIDAR_DOCS_DIR = Path(__file__).resolve().parent.parent / "weekly_report"


def read_reidar_doc(filename: str) -> str:
    """Read a Reidar reference document from the weekly_report/ directory."""
    path = _REIDAR_DOCS_DIR / filename
    return path.read_text(encoding="utf-8")


def run_narrative_pipeline(
    result: dict[str, Any],
    league_id: str,
    event_id: int,
    output_dir: str,
) -> str:
    """Run the full narrative pipeline: generate, save, update memory.

    Returns the path to the saved narrative file.
    """
    season = result["meta"]["season"]

    # Read Reidar reference docs
    persona = read_reidar_doc("REIDAR_PERSONA.md")
    narrative_guide = read_reidar_doc("NARRATIVE_GUIDE.md")
    examples = read_reidar_doc("REIDAR_EXAMPLES.md")

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

    # Update Reidar's memory (best-effort — don't lose the narrative over a parse failure)
    try:
        memory.update_memory(
            report_json=result,
            narrative=narrative,
            client=generator._client,
        )
    except Exception:
        import sys
        import traceback

        print(
            "WARNING: Memory update failed. Narrative was saved successfully.\n"
            f"{traceback.format_exc()}",
            file=sys.stderr,
        )

    return str(narrative_path)


class NarrativeGenerator:
    """Generates weekly narratives via Claude API.

    Constructor creates an anthropic client from the ANTHROPIC_API_KEY
    environment variable. The generate() method builds a prompt from
    Reidar's persona, narrative guide, examples, memory context, and
    the report JSON, then calls the Claude API.
    """

    MODEL = "claude-sonnet-4-6"

    def __init__(self, client: Any | None = None) -> None:
        """Initialize with an anthropic client.

        Args:
            client: An anthropic client instance. If None, creates one
                from the ANTHROPIC_API_KEY environment variable.

        Raises:
            RuntimeError: If ANTHROPIC_API_KEY is not set and no client
                is provided.
        """
        if client is not None:
            self._client = client
            return

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY environment variable is not set. "
                "Set it to your Anthropic API key to generate narratives."
            )

        import anthropic

        self._client = anthropic.Anthropic(api_key=api_key)

    def generate(
        self,
        report_json: dict[str, Any],
        persona: str,
        narrative_guide: str,
        examples: str,
        memory_context: str,
        previous_narrative: str | None = None,
    ) -> str:
        """Generate a narrative from report data and context.

        Builds a system prompt from persona + guide + examples + memory,
        includes the report JSON as user content, and calls Claude API.

        Args:
            report_json: The structured gameweek report dict.
            persona: Reidar persona document content.
            narrative_guide: Narrative structure guide content.
            examples: Example narratives for few-shot prompting.
            memory_context: Assembled memory from ReidarMemory.
            previous_narrative: Previous gameweek narrative for continuity.

        Returns:
            Generated markdown narrative string.
        """
        system_prompt = self._build_system_prompt(
            persona, narrative_guide, examples, memory_context
        )

        user_content = self._build_user_message(
            report_json, previous_narrative
        )

        response = self._client.messages.create(
            model=self.MODEL,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_content}],
        )

        return response.content[0].text  # type: ignore[union-attr]

    def save_narrative(
        self,
        content: str,
        output_dir: str,
        league_id: str,
        season: str,
        event_id: int,
    ) -> Path:
        """Save narrative markdown to the standard path.

        Writes to {output_dir}/docs/narratives/{season}/{league_id}/gw{N}.md,
        creating directories as needed. This path matches the fetch URL used
        by the client-side reidars_rapport.html page.

        Args:
            content: The narrative markdown content.
            output_dir: Base output directory.
            league_id: FPL league ID.
            season: Season string (e.g. '2025-26').
            event_id: Gameweek number.

        Returns:
            Path to the saved file.
        """
        output_path = (
            Path(output_dir)
            / "docs"
            / "narratives"
            / season
            / league_id
            / f"gw{event_id}.md"
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        return output_path

    def _build_system_prompt(
        self,
        persona: str,
        narrative_guide: str,
        examples: str,
        memory_context: str,
    ) -> str:
        """Assemble the system prompt from all context documents."""
        sections = [
            persona,
            narrative_guide,
            examples,
        ]

        if memory_context:
            sections.append(memory_context)

        return "\n\n---\n\n".join(sections)

    def _build_user_message(
        self,
        report_json: dict[str, Any],
        previous_narrative: str | None,
    ) -> str:
        """Build the user message with report data and optional previous narrative."""
        parts: list[str] = []

        parts.append(
            "Her er rundedata i JSON-format. "
            "Skriv Reidars Rapport basert på dette:\n\n"
            f"```json\n{json.dumps(report_json, indent=2, ensure_ascii=False)}\n```"
        )

        if previous_narrative:
            parts.append(
                "\n\nHer er forrige ukes narrativ for kontinuitet:\n\n"
                f"{previous_narrative}"
            )

        return "\n".join(parts)
