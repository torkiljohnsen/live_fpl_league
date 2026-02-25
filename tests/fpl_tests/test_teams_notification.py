from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from fpl.teams_notification import (
    build_adaptive_card,
    extract_teaser,
    extract_title,
    post_to_teams,
)

# --- Sample narratives for testing ---

SAMPLE_NARRATIVE = """\
# Reidars Rapport — Runde 27

![Reidars Rapport](reidars_rapport_2.png)

**Gameweek 27** was a wild ride for the league. Several managers made bold moves that paid off handsomely.

## Ukas satisfaksjon

Ansen tok denne runden med storm og leverte en fenomenal score.

## Ukas skuffelse

Torstein hadde en tung uke med dårlige valg."""

SHORT_NARRATIVE = """\
# Heading

![img](foo.png)

A short teaser paragraph."""

LONG_PARAGRAPH_NARRATIVE = """\
# Title

This is a very long paragraph that exceeds the maximum length. """ + "word " * 80


class TestExtractTeaser:
    def test_basic_extraction(self) -> None:
        teaser = extract_teaser(SAMPLE_NARRATIVE)
        assert "Gameweek 27" in teaser
        assert "wild ride" in teaser

    def test_skips_title_line(self) -> None:
        teaser = extract_teaser(SAMPLE_NARRATIVE)
        assert "Reidars Rapport" not in teaser

    def test_skips_image_line(self) -> None:
        teaser = extract_teaser(SAMPLE_NARRATIVE)
        assert "![" not in teaser
        assert "reidars_rapport_2.png" not in teaser

    def test_strips_bold_markers(self) -> None:
        teaser = extract_teaser(SAMPLE_NARRATIVE)
        assert "**" not in teaser
        assert "Gameweek 27" in teaser

    def test_truncates_on_word_boundary(self) -> None:
        teaser = extract_teaser(LONG_PARAGRAPH_NARRATIVE, max_length=50)
        assert teaser.endswith("...")
        assert len(teaser) <= 50 + 3  # max_length + "..."
        # Should not cut in the middle of a word
        assert not teaser[:-3].endswith("wor")

    def test_no_truncation_when_under_max_length(self) -> None:
        teaser = extract_teaser(SHORT_NARRATIVE)
        assert teaser == "A short teaser paragraph."
        assert "..." not in teaser

    def test_returns_empty_for_title_and_image_only(self) -> None:
        narrative = "# Title\n\n![img](foo.png)"
        teaser = extract_teaser(narrative)
        assert teaser == ""

    def test_returns_first_real_paragraph(self) -> None:
        narrative = "# Title\n\n![img](x.png)\n\nFirst real paragraph.\n\nSecond paragraph."
        teaser = extract_teaser(narrative)
        assert teaser == "First real paragraph."


class TestExtractTitle:
    def test_extracts_title_from_heading(self) -> None:
        assert extract_title(SAMPLE_NARRATIVE) == "Reidars Rapport — Runde 27"

    def test_returns_fallback_when_no_heading(self) -> None:
        assert extract_title("No heading here.\n\nJust text.") == "Reidars Rapport"

    def test_extracts_custom_headline(self) -> None:
        narrative = "# Bench boost. Fem poeng. Null verdighet.\n\nBody text."
        assert extract_title(narrative) == "Bench boost. Fem poeng. Null verdighet."

    def test_uses_first_heading_only(self) -> None:
        narrative = "# First Heading\n\n## Second\n\nBody."
        assert extract_title(narrative) == "First Heading"


class TestBuildAdaptiveCard:
    @pytest.fixture
    def card(self) -> dict:
        return build_adaptive_card(
            gameweek=27,
            teaser="A teaser text.",
            narrative_url="https://example.com/narrative.html",
            image_url="https://example.com/image.png",
        )

    def test_top_level_structure(self, card: dict) -> None:
        assert card["type"] == "message"
        assert isinstance(card["attachments"], list)
        assert len(card["attachments"]) == 1

    def test_attachment_content_type(self, card: dict) -> None:
        attachment = card["attachments"][0]
        assert attachment["contentType"] == "application/vnd.microsoft.card.adaptive"
        assert attachment["contentUrl"] is None

    def test_card_schema_and_version(self, card: dict) -> None:
        content = card["attachments"][0]["content"]
        assert content["$schema"] == "http://adaptivecards.io/schemas/adaptive-card.json"
        assert content["type"] == "AdaptiveCard"
        assert content["version"] == "1.4"

    def _get_columns(self, card: dict) -> list:
        column_set = card["attachments"][0]["content"]["body"][0]
        assert column_set["type"] == "ColumnSet"
        return column_set["columns"]

    def test_body_has_column_set(self, card: dict) -> None:
        body = card["attachments"][0]["content"]["body"]
        assert len(body) == 1
        assert body[0]["type"] == "ColumnSet"

    def test_left_column_has_title(self, card: dict) -> None:
        left = self._get_columns(card)[0]
        title_block = left["items"][0]
        assert title_block["type"] == "TextBlock"
        assert title_block["text"] == "Reidars Rapport — Runde 27"
        assert title_block["weight"] == "bolder"
        assert title_block["size"] == "large"

    def test_left_column_has_teaser(self, card: dict) -> None:
        left = self._get_columns(card)[0]
        teaser_block = left["items"][1]
        assert teaser_block["type"] == "TextBlock"
        assert teaser_block["text"] == "A teaser text."
        assert teaser_block["wrap"] is True

    def test_left_column_has_link(self, card: dict) -> None:
        left = self._get_columns(card)[0]
        link_block = left["items"][2]
        assert link_block["type"] == "TextBlock"
        assert "https://example.com/narrative.html" in link_block["text"]
        assert "Les Reidars rapport uke 27" in link_block["text"]

    def test_right_column_has_image(self, card: dict) -> None:
        right = self._get_columns(card)[1]
        image = right["items"][0]
        assert image["type"] == "Image"
        assert image["url"] == "https://example.com/image.png"
        assert image["size"] == "stretch"

    def test_custom_title_overrides_default(self) -> None:
        card = build_adaptive_card(
            gameweek=27,
            teaser="A teaser.",
            narrative_url="https://example.com",
            image_url="https://example.com/img.png",
            title="Bench boost. Fem poeng. Null verdighet.",
        )
        left = card["attachments"][0]["content"]["body"][0]["columns"][0]
        assert left["items"][0]["text"] == "Bench boost. Fem poeng. Null verdighet."

    def test_empty_title_uses_fallback(self) -> None:
        card = build_adaptive_card(
            gameweek=10,
            teaser="A teaser.",
            narrative_url="https://example.com",
            image_url="https://example.com/img.png",
            title="",
        )
        left = card["attachments"][0]["content"]["body"][0]["columns"][0]
        assert left["items"][0]["text"] == "Reidars Rapport — Runde 10"


class TestPostToTeams:
    @patch("fpl.teams_notification.requests.post")
    def test_returns_true_on_http_200(self, mock_post: MagicMock) -> None:
        mock_post.return_value = MagicMock(status_code=200)
        result = post_to_teams(
            webhook_url="https://webhook.example.com",
            gameweek=27,
            narrative=SAMPLE_NARRATIVE,
            narrative_url="https://example.com/narrative.html",
            image_url="https://example.com/image.png",
        )
        assert result is True
        mock_post.assert_called_once()

    @patch("fpl.teams_notification.requests.post")
    def test_returns_true_on_http_202(self, mock_post: MagicMock) -> None:
        mock_post.return_value = MagicMock(status_code=202)
        result = post_to_teams(
            webhook_url="https://webhook.example.com",
            gameweek=27,
            narrative=SAMPLE_NARRATIVE,
            narrative_url="https://example.com/narrative.html",
            image_url="https://example.com/image.png",
        )
        assert result is True

    @patch("fpl.teams_notification.requests.post")
    def test_returns_false_on_http_400(self, mock_post: MagicMock) -> None:
        mock_post.return_value = MagicMock(status_code=400)
        result = post_to_teams(
            webhook_url="https://webhook.example.com",
            gameweek=27,
            narrative=SAMPLE_NARRATIVE,
            narrative_url="https://example.com/narrative.html",
            image_url="https://example.com/image.png",
        )
        assert result is False

    @patch("fpl.teams_notification.requests.post")
    def test_returns_false_on_request_exception(self, mock_post: MagicMock) -> None:
        mock_post.side_effect = Exception("Connection refused")
        result = post_to_teams(
            webhook_url="https://webhook.example.com",
            gameweek=27,
            narrative=SAMPLE_NARRATIVE,
            narrative_url="https://example.com/narrative.html",
            image_url="https://example.com/image.png",
        )
        assert result is False

    @patch("fpl.teams_notification.requests.post")
    def test_never_raises(self, mock_post: MagicMock) -> None:
        mock_post.side_effect = RuntimeError("Unexpected error")
        # Should not raise — returns False instead
        result = post_to_teams(
            webhook_url="https://webhook.example.com",
            gameweek=27,
            narrative=SAMPLE_NARRATIVE,
            narrative_url="https://example.com/narrative.html",
            image_url="https://example.com/image.png",
        )
        assert result is False

    @patch("fpl.teams_notification.requests.post")
    def test_posts_json_to_webhook_url(self, mock_post: MagicMock) -> None:
        mock_post.return_value = MagicMock(status_code=200)
        post_to_teams(
            webhook_url="https://webhook.example.com/hook",
            gameweek=27,
            narrative=SAMPLE_NARRATIVE,
            narrative_url="https://example.com/narrative.html",
            image_url="https://example.com/image.png",
        )
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://webhook.example.com/hook"
        assert "json" in call_args[1]
        card = call_args[1]["json"]
        assert card["type"] == "message"
