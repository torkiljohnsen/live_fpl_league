"""Front-matter parsing shared by the narrative consumers.

A narrative may start with a YAML-ish block written by Reidar himself::

    ---
    teaser: Én manager kapteinet en spiller som ikke spilte.
    mentions: Camilla, Torkil
    ---
    # Headline

Only a block that starts on line 1 with ``---`` and is closed by a line
that is exactly ``---`` counts. Keys are ``key: value`` one per line; no
YAML library. A missing or malformed block yields ``({}, text)``.
"""

from __future__ import annotations


def parse_front_matter(narrative: str) -> tuple[dict[str, str], str]:
    """Return (fields, body) with the block removed and line endings as ``\\n``."""
    normalized = narrative.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")

    if not lines or lines[0].strip() != "---":
        return {}, normalized

    close_idx = next(
        (i for i in range(1, len(lines)) if lines[i].strip() == "---"), None
    )
    if close_idx is None:
        return {}, normalized

    fields: dict[str, str] = {}
    for line in lines[1:close_idx]:
        key, sep, value = line.partition(":")
        if sep and key.strip():
            fields[key.strip()] = value.strip()

    body = "\n".join(lines[close_idx + 1 :]).lstrip("\n")
    return fields, body
