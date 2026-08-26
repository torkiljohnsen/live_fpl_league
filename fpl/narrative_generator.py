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

from . import claude_api
from .format_scheduler import (
    choose_assignment,
    load_recent_shapes,
    record_shape,
    render_assignment,
)
from .reference_loader import load_reference_docs, select_reference_docs
from .reidar_memory import ReidarMemory
from .style_lint import lint_narrative
from .weekly_report import get_narrative_path

# Reidar reference docs live in weekly_report/ relative to the repo root
_REIDAR_DOCS_DIR = Path(__file__).resolve().parent.parent / "weekly_report"

# How many preceding gameweeks' narratives feed the style lint gate
# (sign-off similarity, repeated n-grams).
_LINT_PREVIOUS_WINDOW = 5


def read_reidar_doc(filename: str) -> str:
    """Read a Reidar reference document from the weekly_report/ directory."""
    path = _REIDAR_DOCS_DIR / filename
    return path.read_text(encoding="utf-8")


def _load_previous_narratives_for_lint(
    output_dir: str, league_id: str, season: str, event_id: int
) -> list[str]:
    """Load up to the last five narratives before event_id, most recent
    first, for the style lint's sign-off/repeated-n-gram checks."""
    texts: list[str] = []
    for gw in range(event_id - 1, max(0, event_id - 1 - _LINT_PREVIOUS_WINDOW), -1):
        path = get_narrative_path(output_dir, league_id, season, gw)
        if path.is_file():
            texts.append(path.read_text(encoding="utf-8"))
    return texts


def compact_report_for_prompt(report: dict[str, Any]) -> dict[str, Any]:
    """A lighter copy of the report for the prompt (the file on disk is untouched).

    The squad lists are more than half the JSON's weight: seven keys per
    player, fifteen players, ten managers. Reidar needs the name, the club,
    the points and who was captain or benched — one string per player does
    that at a fifth of the size. Element ids and the duplicate bench list go.
    """
    compact = json.loads(json.dumps(report))
    for p in compact.get("standings", []):
        squad = []
        for pl in p.get("squad", []):
            tag = ""
            if pl.get("is_captain"):
                tag = " (C)" if pl.get("multiplier", 1) else " (C, spilte ikke)"
            elif pl.get("multiplier", 1) == 0:
                tag = " (benk)"
            squad.append(f"{pl.get('name')} ({pl.get('club')}) {pl.get('points', 0)}{tag}")
        p["squad"] = squad
        p.pop("bench_players", None)
        for key in ("captain", "vice_captain"):
            if isinstance(p.get(key), dict):
                p[key].pop("element_id", None)
        p.pop("entry_id", None)
    return compact


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
    # The device palette is the exact markup for every visual device the
    # guide refers to, so it rides along with the guide in the system prompt.
    narrative_guide = (
        read_reidar_doc("NARRATIVE_GUIDE.md")
        + "\n\n---\n\n"
        + read_reidar_doc("DEVICE_PALETTE.md")
    )
    examples = read_reidar_doc("REIDAR_EXAMPLES.md")

    # Load memory context
    memory = ReidarMemory(
        output_dir=output_dir, league_id=league_id, season=season
    )
    memory.scaffold_directories()
    memory_context = memory.get_prompt_context(event_id)

    # Memory dir computed directly (not via a ReidarMemory property) so this
    # doesn't collide with the reidar_memory.py changes another agent is
    # making — see issue #40 workstream A/B.
    memory_dir = (
        Path(output_dir) / "weekly_report" / "reidar_memory" / league_id / season
    )

    # Check for previous narrative
    previous_narrative: str | None = None
    prev_narrative_path = result["meta"].get("previous_narrative")
    if prev_narrative_path:
        full_prev_path = Path(output_dir) / prev_narrative_path
        if full_prev_path.is_file():
            previous_narrative = full_prev_path.read_text(encoding="utf-8")

    # Format rotation + season calendar (issue #40, workstreams A + B):
    # the pipeline schedules the week's shape rather than letting the model
    # default to the same six-section column every time.
    recent_shapes = load_recent_shapes(memory_dir, event_id)
    assignment = choose_assignment(
        result, recent_shapes, has_ledger=bool(memory.load_ledger().strip())
    )
    print(
        f"Assignment: {assignment.shape} "
        f"({assignment.constraint or 'none'}) — {assignment.reason}"
    )
    assignment_text = render_assignment(assignment)

    # Select and load on-demand reference docs (weekly_report/reference/),
    # only when this gameweek's data actually calls for one — see
    # fpl/reference_loader.py and weekly_report/reference/README.md.
    reference_filenames = select_reference_docs(
        result, event_id, format=assignment.shape
    )
    reference_docs = load_reference_docs(reference_filenames)
    doc_word_count = len(reference_docs.split()) if reference_docs else 0
    print(
        "Reference docs: "
        f"{', '.join(reference_filenames) if reference_filenames else 'none'} "
        f"({doc_word_count} words)"
    )

    # Recently used headlines/openers/closers/jokes — off-limits this week
    do_not_repeat = memory.get_do_not_repeat_block(event_id)

    # Generate narrative
    generator = NarrativeGenerator()
    narrative = generator.generate(
        report_json=result,
        persona=persona,
        narrative_guide=narrative_guide,
        examples=examples,
        memory_context=memory_context,
        previous_narrative=previous_narrative,
        reference_docs=reference_docs,
        assignment=assignment_text,
        do_not_repeat=do_not_repeat,
    )

    # Style lint gate: cheap, deterministic checks (issue #40, workstream E).
    # A hard failure triggers exactly one regeneration with the findings
    # appended to the prompt; whatever comes back is accepted. The scheduled
    # shape overrides the front-matter one for the word budget (workstream A/B).
    lint_previous = _load_previous_narratives_for_lint(
        output_dir, league_id, season, event_id
    )
    lint_result = lint_narrative(
        narrative, previous=lint_previous, shape=assignment.shape
    )
    if lint_result.hard_failures:
        print(
            f"Style lint: {len(lint_result.hard_failures)} hard failures → regenerating once"
        )
        extra_instructions = (
            "Forrige utkast brøt disse reglene — skriv på nytt og rett dem:\n"
            + "\n".join(f"- {failure}" for failure in lint_result.hard_failures)
        )
        narrative = generator.generate(
            report_json=result,
            persona=persona,
            narrative_guide=narrative_guide,
            examples=examples,
            memory_context=memory_context,
            previous_narrative=previous_narrative,
            reference_docs=reference_docs,
            assignment=assignment_text,
            do_not_repeat=do_not_repeat,
            extra_instructions=extra_instructions,
        )
        lint_result = lint_narrative(
            narrative, previous=lint_previous, shape=assignment.shape
        )
        remaining = len(lint_result.hard_failures)
        print(
            "Style lint: OK after regeneration"
            if remaining == 0
            else f"Style lint: {remaining} hard failures remain after regeneration"
        )
    else:
        print("Style lint: OK")

    # Save narrative
    narrative_path = generator.save_narrative(
        content=narrative,
        output_dir=output_dir,
        league_id=league_id,
        season=season,
        event_id=event_id,
    )

    # Record this gameweek's shape so future weeks know not to repeat it.
    record_shape(memory_dir, event_id, assignment)

    # Update Reidar's memory (best-effort — don't lose the narrative over a parse failure)
    try:
        memory.update_memory(
            report_json=compact_report_for_prompt(result),
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

    MODEL = claude_api.MODEL

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
        *,
        reference_docs: str | None = None,
        extra_instructions: str | None = None,
        assignment: str | None = None,
        do_not_repeat: str | None = None,
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
            reference_docs: On-demand reference material (from
                fpl/reference_loader.py), included in the user message only
                when non-empty. Kept out of the system prompt on purpose —
                it must not grow the standing context weight.
            extra_instructions: Appended at the end of the user message —
                used by the style lint gate to ask for a corrected
                regeneration (see run_narrative_pipeline).
            do_not_repeat: Norwegian "Ikke gjenta" block from
                ReidarMemory.get_do_not_repeat_block(); omitted when empty.
            assignment: This gameweek's scheduled format, rendered by
                fpl.format_scheduler.render_assignment() (issue #40,
                workstreams A + B) — the shape/constraint/calendar block,
                placed right after the report JSON.

        Returns:
            Generated markdown narrative string.
        """
        system_prompt = self._build_system_prompt(
            persona, narrative_guide, examples, memory_context
        )

        user_content = self._build_user_message(
            report_json,
            previous_narrative,
            reference_docs=reference_docs,
            extra_instructions=extra_instructions,
            assignment=assignment,
            do_not_repeat=do_not_repeat,
        )

        return claude_api.complete(
            self._client,
            system=system_prompt,
            user=user_content,
        )

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
        *,
        reference_docs: str | None = None,
        extra_instructions: str | None = None,
        assignment: str | None = None,
        do_not_repeat: str | None = None,
    ) -> str:
        """Build the user message with report data and optional previous
        narrative, plus any extra instructions appended at the end."""
        parts: list[str] = []

        parts.append(
            "Her er rundedata i JSON-format. "
            "Skriv Reidars Rapport basert på dette:\n\n"
            "```json\n"
            f"{json.dumps(compact_report_for_prompt(report_json), indent=1, ensure_ascii=False)}"
            "\n```"
        )

        if assignment:
            parts.append(f"\n\n{assignment}")

        if reference_docs:
            parts.append(
                "\n\n## Oppslagsverk (bare for denne runden)\n\n"
                f"{reference_docs}"
            )

        if previous_narrative:
            parts.append(
                "\n\nHer er forrige ukes narrativ for kontinuitet:\n\n"
                f"{previous_narrative}"
            )

        if do_not_repeat:
            parts.append(f"\n\n{do_not_repeat}")

        if extra_instructions:
            parts.append(f"\n\n{extra_instructions}")

        return "\n".join(parts)
