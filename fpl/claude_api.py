"""Shared Claude API access for Reidar's narrative pipeline.

One place to hold the model choice and the request shape, so the
narrative generator and the memory updater cannot drift apart.
"""

from __future__ import annotations

from typing import Any

MODEL = "claude-sonnet-5"

# Non-streaming ceiling. The memory update in particular writes eight
# manager profiles plus a GW summary and a season arc in one response —
# at 4096 it was silently truncated mid-response, which is why the
# 2025-26 season arc and GW summaries stopped updating after GW27.
MAX_TOKENS = 16000

# No `fallbacks` parameter here: server-side refusal fallback is not
# supported on Sonnet 5 (the API returns 400). A refusal raises below
# instead, so a failed run is loud and the next scheduled run retries.


def complete(
    client: Any,
    *,
    system: str,
    user: str,
    max_tokens: int = MAX_TOKENS,
) -> str:
    """Send a single-turn request to Claude and return the text response.

    Args:
        client: An anthropic client instance.
        system: System prompt.
        user: User message content.
        max_tokens: Output ceiling for the response.

    Returns:
        The concatenated text blocks of the response.

    Raises:
        RuntimeError: If the request was refused, or the response was cut
            off by max_tokens (a truncated response writes broken memory).
    """
    response = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )

    stop_reason = getattr(response, "stop_reason", None)
    if stop_reason == "refusal":
        details = getattr(response, "stop_details", None)
        category = getattr(details, "category", None)
        raise RuntimeError(
            f"Claude refused the request (category: {category}). "
            "No narrative or memory was written."
        )

    # Thinking is on by default, so the text is not necessarily the first
    # block — collect every text block instead of indexing into content.
    text = "".join(
        block.text for block in response.content if block.type == "text"
    )

    if stop_reason == "max_tokens":
        raise RuntimeError(
            f"Claude response hit the {max_tokens} token limit and was "
            "truncated. Raise MAX_TOKENS in fpl/claude_api.py."
        )

    return text
