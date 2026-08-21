"""Shared Claude API access for Reidar's narrative pipeline.

One place to hold the model choice and the request shape, so the
narrative generator and the memory updater cannot drift apart.
"""

from __future__ import annotations

import sys
from typing import Any

MODEL = "claude-opus-5"

# Non-streaming ceiling. The memory update in particular writes eight
# manager profiles plus a GW summary and a season arc in one response —
# at 4096 it was silently truncated mid-response and the season arc was
# never written.
MAX_TOKENS = 16000

# Server-side refusal fallback: if a policy classifier declines the
# request, the API re-runs it on a fallback model within the same call
# instead of leaving the weekly report empty. If the beta is not
# available to the account we fall back to a plain request rather than
# failing the weekly run.
FALLBACK_BETA = "server-side-fallback-2026-07-01"


def _request_with_fallbacks(
    client: Any, system: str, user: str, max_tokens: int
) -> Any:
    return client.beta.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        betas=[FALLBACK_BETA],
        fallbacks="default",
        system=system,
        messages=[{"role": "user", "content": user}],
    )


def _request_plain(client: Any, system: str, user: str, max_tokens: int) -> Any:
    return client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )


def _is_fallbacks_unsupported(exc: Exception) -> bool:
    """True if the request was rejected because of the fallbacks beta."""
    if getattr(exc, "status_code", None) != 400:
        return False
    message = str(exc).lower()
    return "fallback" in message or "beta" in message


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
    try:
        response = _request_with_fallbacks(client, system, user, max_tokens)
    except Exception as exc:
        if not _is_fallbacks_unsupported(exc):
            raise
        print(
            f"WARNING: refusal fallbacks ({FALLBACK_BETA}) rejected by the API "
            f"({exc}). Retrying without them.",
            file=sys.stderr,
        )
        response = _request_plain(client, system, user, max_tokens)

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
