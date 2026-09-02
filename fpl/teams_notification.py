from __future__ import annotations

import sys
from typing import Any

import requests

from .front_matter import parse_front_matter

# Rotates by gameweek % 5 so the Teams card doesn't look identical every week.
_LINK_LABELS = [
    "Les hele rapporten",
    "Reidar har ordet",
    "Hele spalten her",
    "Les Reidars dom",
    "Til rapporten →",
]

_TEASER_FRONT_MATTER_MAX = 200


def _truncate_on_word_boundary(text: str, max_length: int) -> str:
    """Truncate text to max_length on a word boundary, appending '...'."""
    if len(text) <= max_length:
        return text
    truncated = text[:max_length]
    last_space = truncated.rfind(" ")
    if last_space > 0:
        truncated = truncated[:last_space]
    return truncated + "..."


def hero_image_filename(gameweek: int) -> str:
    """Return the rotated hero image filename for a gameweek.

    Rotates through assets/reidars_rapport_1.png .. _6.png keyed by
    `gameweek % 6`, so the card and the report page don't always show
    the same image.
    """
    return f"reidars_rapport_{(gameweek % 6) + 1}.png"


def extract_title(narrative: str) -> str:
    """Extract the headline from the first # heading in the narrative body.

    Skips any front-matter block before looking for the heading.
    """
    _, body = parse_front_matter(narrative)
    for line in body.split("\n"):
        if line.startswith("# "):
            return line[2:].strip()
    return "Reidars Rapport"


def extract_teaser(narrative: str, max_length: int = 300) -> str:
    """Extract a teaser for a narrative markdown string.

    Prefers the `teaser` field from a front-matter block, if present
    (stripped, hard-capped at 200 chars on a word boundary). Otherwise
    falls back to the first real paragraph of the body.
    """
    fields, body = parse_front_matter(narrative)

    front_matter_teaser = fields.get("teaser", "").strip()
    if front_matter_teaser:
        return _truncate_on_word_boundary(
            front_matter_teaser, _TEASER_FRONT_MATTER_MAX
        )

    paragraphs = body.split("\n\n")

    for paragraph in paragraphs:
        stripped = paragraph.strip()
        if not stripped:
            continue
        if stripped.startswith("# "):
            continue
        if stripped.startswith("!["):
            continue
        teaser = stripped.replace("**", "")
        return _truncate_on_word_boundary(teaser, max_length)

    return ""


def extract_mentions(narrative: str) -> list[str]:
    """Extract the comma-separated `mentions` field from front-matter, if any."""
    fields, _ = parse_front_matter(narrative)
    mentions_field = fields.get("mentions", "")
    if not mentions_field:
        return []
    return [name.strip() for name in mentions_field.split(",") if name.strip()]


def build_adaptive_card(
    gameweek: int,
    teaser: str,
    narrative_url: str,
    image_url: str,
    title: str = "",
    *,
    mentions: list[str] | None = None,
) -> dict[str, Any]:
    """Build an Adaptive Card payload for Power Automate webhook."""
    card_title = title if title else f"Reidars Rapport — Runde {gameweek}"
    link_label = _LINK_LABELS[gameweek % 5]

    left_items: list[dict[str, Any]] = [
        {
            "type": "TextBlock",
            "text": card_title,
            "weight": "bolder",
            "size": "large",
            "wrap": True,
        },
        {
            "type": "TextBlock",
            "text": teaser,
            "wrap": True,
            "size": "medium",
            "spacing": "small",
        },
        {
            "type": "TextBlock",
            "text": f"[{link_label}]({narrative_url})",
            "wrap": True,
            "spacing": "medium",
        },
    ]

    if mentions:
        left_items.append(
            {
                "type": "TextBlock",
                "text": f"Nevnt denne uka: {', '.join(mentions)}",
                "wrap": True,
                "isSubtle": True,
                "size": "small",
                "spacing": "small",
            }
        )

    return {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "ColumnSet",
                "columns": [
                    {
                        "type": "Column",
                        "width": "stretch",
                        "items": left_items,
                    },
                    {
                        "type": "Column",
                        "width": "stretch",
                        "items": [
                            {
                                "type": "Image",
                                "url": image_url,
                                "size": "stretch",
                            },
                        ],
                    },
                ],
            },
        ],
    }


def post_to_teams(
    webhook_url: str,
    gameweek: int,
    narrative: str,
    narrative_url: str,
    image_url: str,
) -> bool:
    """Post an Adaptive Card to Teams via Power Automate webhook.

    Returns True on success, False on failure.
    """
    try:
        title = extract_title(narrative)
        teaser = extract_teaser(narrative)
        mentions = extract_mentions(narrative)
        card = build_adaptive_card(
            gameweek,
            teaser,
            narrative_url,
            image_url,
            title=title,
            mentions=mentions,
        )
        payload = {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": card,
                }
            ],
        }
        response = requests.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        if 200 <= response.status_code < 300:
            return True
        print(
            f"Warning: Teams webhook returned HTTP {response.status_code}",
            file=sys.stderr,
        )
        return False
    except Exception as e:
        print(f"Warning: Teams notification failed: {e}", file=sys.stderr)
        return False
