from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from fpl.teams_notification import (
    build_adaptive_card,
    extract_mentions,
    extract_teaser,
    extract_title,
    hero_image_filename,
    parse_front_matter,
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

FRONT_MATTER_NARRATIVE = """\
---
teaser: Én manager kapteinet en spiller som ikke spilte. Ikke den du tror, Camilla.
mentions: Camilla, Torkil, Daniel
---
# Headline

![Reidars Rapport](../../reidars_rapport_3.png)

Body paragraph here."""


class TestParseFrontMatter:
    def test_present_block_is_parsed(self) -> None:
        fields, body = parse_front_matter(FRONT_MATTER_NARRATIVE)
        assert fields["teaser"] == (
            "Én manager kapteinet en spiller som ikke spilte. "
            "Ikke den du tror, Camilla."
        )
        assert fields["mentions"] == "Camilla, Torkil, Daniel"
        assert not body.startswith("---")
        assert body.startswith("# Headline")

    def test_absent_block_returns_empty_fields(self) -> None:
        fields, body = parse_front_matter(SAMPLE_NARRATIVE)
        assert fields == {}
        assert body == SAMPLE_NARRATIVE

    def test_malformed_block_no_closing_marker_degrades_gracefully(self) -> None:
        narrative = "---\nteaser: no closing marker\n# Headline\n\nBody."
        fields, body = parse_front_matter(narrative)
        assert fields == {}
        assert body == narrative

    def test_dashes_not_on_first_line_is_not_front_matter(self) -> None:
        narrative = "# Headline\n\n---\n\nBody."
        fields, body = parse_front_matter(narrative)
        assert fields == {}
        assert body == narrative

    def test_extra_unknown_keys_are_kept(self) -> None:
        narrative = "---\nteaser: A teaser.\nshape: Kortversjonen\n---\n# H\n\nBody."
        fields, _ = parse_front_matter(narrative)
        assert fields["shape"] == "Kortversjonen"
        assert fields["teaser"] == "A teaser."

    def test_windows_line_endings(self) -> None:
        narrative = (
            "---\r\nteaser: En vinter-teaser.\r\nmentions: Ola\r\n---\r\n"
            "# Headline\r\n\r\nBody."
        )
        fields, body = parse_front_matter(narrative)
        assert fields["teaser"] == "En vinter-teaser."
        assert fields["mentions"] == "Ola"
        assert body.startswith("# Headline")

    def test_empty_front_matter_block(self) -> None:
        narrative = "---\n---\n# Headline\n\nBody."
        fields, body = parse_front_matter(narrative)
        assert fields == {}
        assert body.startswith("# Headline")


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

    def test_prefers_front_matter_teaser_over_body_paragraph(self) -> None:
        teaser = extract_teaser(FRONT_MATTER_NARRATIVE)
        assert teaser == (
            "Én manager kapteinet en spiller som ikke spilte. "
            "Ikke den du tror, Camilla."
        )
        assert "Body paragraph" not in teaser

    def test_front_matter_teaser_hard_capped_at_200_chars(self) -> None:
        long_teaser = "Et manus " * 40  # well over 200 chars
        narrative = f"---\nteaser: {long_teaser.strip()}\n---\n# H\n\nBody."
        teaser = extract_teaser(narrative, max_length=300)
        assert len(teaser) <= 200 + 3
        assert teaser.endswith("...")

    def test_falls_back_when_front_matter_has_no_teaser_key(self) -> None:
        narrative = "---\nmentions: Ola\n---\n# Title\n\n![x](y.png)\n\nFallback paragraph."
        teaser = extract_teaser(narrative)
        assert teaser == "Fallback paragraph."


class TestExtractMentions:
    def test_parses_comma_separated_names(self) -> None:
        mentions = extract_mentions(FRONT_MATTER_NARRATIVE)
        assert mentions == ["Camilla", "Torkil", "Daniel"]

    def test_returns_empty_list_when_no_front_matter(self) -> None:
        assert extract_mentions(SAMPLE_NARRATIVE) == []

    def test_returns_empty_list_when_no_mentions_key(self) -> None:
        narrative = "---\nteaser: A teaser.\n---\n# Title\n\nBody."
        assert extract_mentions(narrative) == []

    def test_strips_whitespace_around_names(self) -> None:
        narrative = "---\nmentions:  Ola ,  Kari  , Per\n---\n# T\n\nBody."
        assert extract_mentions(narrative) == ["Ola", "Kari", "Per"]


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

    def test_skips_front_matter_block(self) -> None:
        assert extract_title(FRONT_MATTER_NARRATIVE) == "Headline"


class TestHeroImageFilename:
    @pytest.mark.parametrize(
        ("gameweek", "expected"),
        [
            (1, "reidars_rapport_2.png"),
            (2, "reidars_rapport_3.png"),
            (3, "reidars_rapport_4.png"),
            (4, "reidars_rapport_5.png"),
            (5, "reidars_rapport_6.png"),
            (6, "reidars_rapport_1.png"),
            (10, "reidars_rapport_5.png"),
            (27, "reidars_rapport_4.png"),
        ],
    )
    def test_rotates_through_six_images(self, gameweek: int, expected: str) -> None:
        assert hero_image_filename(gameweek) == expected


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
        assert card["type"] == "AdaptiveCard"
        assert card["$schema"] == "http://adaptivecards.io/schemas/adaptive-card.json"
        assert card["version"] == "1.4"

    def _get_columns(self, card: dict) -> list:
        column_set = card["body"][0]
        assert column_set["type"] == "ColumnSet"
        return column_set["columns"]

    def test_body_has_column_set(self, card: dict) -> None:
        body = card["body"]
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

    def test_link_label_rotates_by_gameweek(self) -> None:
        labels = set()
        for gw in range(5):
            card = build_adaptive_card(
                gameweek=gw,
                teaser="t",
                narrative_url="https://example.com",
                image_url="https://example.com/i.png",
            )
            left = card["body"][0]["columns"][0]
            link_text = left["items"][2]["text"]
            labels.add(link_text)
        # Five different gameweeks (0-4) should give five distinct labels
        assert len(labels) == 5

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
        left = card["body"][0]["columns"][0]
        assert left["items"][0]["text"] == "Bench boost. Fem poeng. Null verdighet."

    def test_empty_title_uses_fallback(self) -> None:
        card = build_adaptive_card(
            gameweek=10,
            teaser="A teaser.",
            narrative_url="https://example.com",
            image_url="https://example.com/img.png",
            title="",
        )
        left = card["body"][0]["columns"][0]
        assert left["items"][0]["text"] == "Reidars Rapport — Runde 10"

    def test_mentions_line_present_when_mentions_given(self) -> None:
        card = build_adaptive_card(
            gameweek=27,
            teaser="A teaser.",
            narrative_url="https://example.com",
            image_url="https://example.com/img.png",
            mentions=["Camilla", "Torkil", "Daniel"],
        )
        left = card["body"][0]["columns"][0]
        mentions_block = left["items"][-1]
        assert mentions_block["text"] == "Nevnt denne uka: Camilla, Torkil, Daniel"
        assert mentions_block["isSubtle"] is True
        assert mentions_block["size"] == "small"

    def test_mentions_line_omitted_when_no_mentions(self, card: dict) -> None:
        left = self._get_columns(card)[0]
        assert len(left["items"]) == 3
        for item in left["items"]:
            assert "Nevnt denne uka" not in item["text"]

    def test_mentions_line_omitted_when_empty_list(self) -> None:
        card = build_adaptive_card(
            gameweek=27,
            teaser="A teaser.",
            narrative_url="https://example.com",
            image_url="https://example.com/img.png",
            mentions=[],
        )
        left = card["body"][0]["columns"][0]
        assert len(left["items"]) == 3


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

    @patch("fpl.teams_notification.requests.post")
    def test_passes_mentions_from_front_matter_to_card(
        self, mock_post: MagicMock
    ) -> None:
        mock_post.return_value = MagicMock(status_code=200)
        post_to_teams(
            webhook_url="https://webhook.example.com",
            gameweek=27,
            narrative=FRONT_MATTER_NARRATIVE,
            narrative_url="https://example.com/narrative.html",
            image_url="https://example.com/image.png",
        )
        card = mock_post.call_args[1]["json"]["attachments"][0]["content"]
        left = card["body"][0]["columns"][0]
        mentions_block = left["items"][-1]
        assert "Camilla" in mentions_block["text"]
        assert "Torkil" in mentions_block["text"]
        assert "Daniel" in mentions_block["text"]
