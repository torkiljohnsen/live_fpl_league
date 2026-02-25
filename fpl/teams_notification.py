from __future__ import annotations

import sys
from typing import Any

import requests


def extract_teaser(narrative: str, max_length: int = 300) -> str:
    """Extract a teaser paragraph from a narrative markdown string."""
    paragraphs = narrative.split("\n\n")

    for paragraph in paragraphs:
        stripped = paragraph.strip()
        if not stripped:
            continue
        if stripped.startswith("# "):
            continue
        if stripped.startswith("!["):
            continue
        teaser = stripped.replace("**", "")
        if len(teaser) <= max_length:
            return teaser
        # Truncate on word boundary
        truncated = teaser[:max_length]
        last_space = truncated.rfind(" ")
        if last_space > 0:
            truncated = truncated[:last_space]
        return truncated + "..."

    return ""


def build_adaptive_card(
    gameweek: int, teaser: str, narrative_url: str, image_url: str
) -> dict[str, Any]:
    """Build an Adaptive Card payload for Teams webhook."""
    return {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "contentUrl": None,
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.4",
                    "body": [
                        {
                            "type": "Image",
                            "url": image_url,
                            "size": "stretch",
                        },
                        {
                            "type": "TextBlock",
                            "text": f"Reidars Rapport — Runde {gameweek}",
                            "weight": "bolder",
                            "size": "large",
                            "wrap": True,
                        },
                        {
                            "type": "TextBlock",
                            "text": teaser,
                            "wrap": True,
                            "size": "medium",
                        },
                    ],
                    "actions": [
                        {
                            "type": "Action.OpenUrl",
                            "title": "Les hele Reidars Rapport",
                            "url": narrative_url,
                        }
                    ],
                },
            }
        ],
    }


def post_to_teams(
    webhook_url: str,
    gameweek: int,
    narrative: str,
    narrative_url: str,
    image_url: str,
) -> bool:
    """Post an Adaptive Card to Teams via webhook. Returns True on success, False on failure."""
    try:
        teaser = extract_teaser(narrative)
        card = build_adaptive_card(gameweek, teaser, narrative_url, image_url)
        response = requests.post(
            webhook_url,
            json=card,
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
