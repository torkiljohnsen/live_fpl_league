"""Tests for the shared front-matter parser."""

from fpl.front_matter import parse_front_matter


def test_parses_block_and_strips_it():
    fields, body = parse_front_matter("---\nteaser: Hei\nmentions: A, B\n---\n# T\n\nx")
    assert fields == {"teaser": "Hei", "mentions": "A, B"}
    assert body == "# T\n\nx"


def test_no_block_returns_text_unchanged():
    assert parse_front_matter("# T\n\nx") == ({}, "# T\n\nx")


def test_unclosed_block_is_not_front_matter():
    text = "---\nteaser: x\n# T"
    assert parse_front_matter(text) == ({}, text)


def test_crlf_is_normalized():
    fields, body = parse_front_matter("---\r\nshape: brevet\r\n---\r\n# T\r\n")
    assert fields == {"shape": "brevet"}
    assert body == "# T\n"
