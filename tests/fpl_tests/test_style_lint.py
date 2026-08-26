"""Tests for the style lint (fpl/style_lint.py, issue #40 workstream E)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from fpl.style_lint import Limits, lint_narrative, lint_path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _narrative(
    headline: str = "En helt vanlig runde",
    body: str = "Dette er en helt vanlig setning uten noen spesielle triks eller tics.",
    last_line: str = "Vi snakkes neste uke.",
) -> str:
    return f"# {headline}\n\n![Reidars Rapport](../../reidars_rapport_1.png)\n\n{body}\n\n{last_line}\n"


# ---------------------------------------------------------------------------
# Preprocessing / word count
# ---------------------------------------------------------------------------


class TestPreprocessing:
    def test_headline_and_image_line_excluded_from_word_count(self):
        text = _narrative(headline="Ti ekstra ord som ikke skal telles i det hele tatt egentlig")
        result = lint_narrative(text)
        # headline words must not appear in the count
        body_only = lint_narrative(
            "# X\n\n![img](x.png)\n\n"
            "Dette er en helt vanlig setning uten noen spesielle triks eller tics.\n\n"
            "Vi snakkes neste uke.\n"
        )
        assert result.metrics["word_count"] == body_only.metrics["word_count"]

    def test_front_matter_is_stripped(self):
        text = "---\nteaser: Noe skjer\nshape: spalten\n---\n" + _narrative()
        result = lint_narrative(text)
        assert result.metrics["shape"] == "spalten"
        assert "teaser" not in result.metrics["headline"].lower()

    def test_html_tags_and_code_fences_excluded_from_word_count(self):
        # Tags themselves are stripped (not their inner text); fenced code
        # blocks are removed entirely, tags and content both.
        plain = lint_narrative(_narrative(body="Ordinær tekst her uten noe rart i det hele tatt."))
        with_html = lint_narrative(
            _narrative(body="Ordinær tekst her uten noe rart i det hele tatt. <span></span> ```kode her```")
        )
        assert with_html.metrics["word_count"] == plain.metrics["word_count"]

    def test_word_count_basic(self):
        result = lint_narrative(_narrative(body="En to tre fire fem seks sju åtte ni ti."))
        assert result.metrics["word_count"] == 10 + len(  # body words
            _tokens_in("Vi snakkes neste uke.")
        )


def _tokens_in(s: str) -> list[str]:
    import re

    return re.findall(r"[A-Za-zÆØÅæøåÀ-ÖØ-öø-ÿ0-9]+", s)


# ---------------------------------------------------------------------------
# Hard limits
# ---------------------------------------------------------------------------


class TestWordCountLimit:
    def test_under_limit_no_hard_failure(self):
        result = lint_narrative(_narrative())
        assert not any("For langt" in f for f in result.hard_failures)

    def test_over_default_limit_is_hard_failure(self):
        body = " ".join(["ord"] * 700)
        result = lint_narrative(_narrative(body=body))
        assert any("For langt" in f for f in result.hard_failures)
        assert result.metrics["word_count"] > 650

    def test_shape_specific_limit_applies(self):
        text = "---\nshape: kortversjonen\n---\n" + _narrative(body=" ".join(["ord"] * 300))
        result = lint_narrative(text)
        assert result.metrics["word_limit"] == 250
        assert any("For langt" in f for f in result.hard_failures)

    def test_shape_specific_limit_not_exceeded(self):
        text = "---\nshape: kortversjonen\n---\n" + _narrative(body=" ".join(["ord"] * 100))
        result = lint_narrative(text)
        assert not any("For langt" in f for f in result.hard_failures)

    def test_custom_limits_override_default(self):
        result = lint_narrative(_narrative(body=" ".join(["ord"] * 20)), limits=Limits(max_word_count=10))
        assert any("For langt" in f for f in result.hard_failures)


class TestEmDash:
    def test_no_em_dash_is_clean(self):
        result = lint_narrative(_narrative(body="En setning uten noen tankestreker i det hele tatt."))
        assert result.metrics["em_dash_count"] == 0
        assert not any("tankestreker" in f for f in result.hard_failures)

    def test_three_em_dash_is_within_limit(self):
        body = "Én — to — tre — det holder akkurat innenfor grensen som er satt her nå."
        result = lint_narrative(_narrative(body=body))
        assert result.metrics["em_dash_count"] == 3
        assert not any("tankestreker" in f for f in result.hard_failures)

    def test_four_em_dash_is_hard_failure(self):
        body = "Én — to — tre — fire — det er for mange tankestreker for en runde nå."
        result = lint_narrative(_narrative(body=body))
        assert result.metrics["em_dash_count"] == 4
        assert any("tankestreker" in f for f in result.hard_failures)

    def test_en_dash_as_spaced_dash_counts(self):
        body = "Én – to – tre – fire – for mange bindestreker brukt som tankestrek her nå."
        result = lint_narrative(_narrative(body=body))
        assert result.metrics["em_dash_count"] == 4

    def test_em_dash_per_100_words_computed(self):
        body = "Én — dash i en kort tekst uten flere ord enn dette her."
        result = lint_narrative(_narrative(body=body))
        expected = result.metrics["em_dash_count"] / result.metrics["word_count"] * 100
        assert result.metrics["em_dash_per_100_words"] == round(expected, 2)


class TestHeadlineShape:
    def test_three_fragment_staccato_is_hard_failure(self):
        result = lint_narrative(_narrative(headline="Chip-karneval. Ny leder. Anders krasjlander."))
        assert result.metrics["headline_shape"] == 3
        assert any("stakkato" in f for f in result.hard_failures)

    def test_two_fragment_headline_is_fine(self):
        result = lint_narrative(_narrative(headline="Fem ekstra poeng. Én chip mindre."))
        assert result.metrics["headline_shape"] == 2
        assert not any("stakkato" in f for f in result.hard_failures)

    def test_single_fragment_headline_with_em_dash_is_fine(self):
        result = lint_narrative(_narrative(headline="Sesongens siste kapittel — og Haaland spilte ikke"))
        assert result.metrics["headline_shape"] == 1


class TestHeadingCount:
    def test_three_headings_is_ok(self):
        body = "## En\n\nTekst.\n\n## To\n\nTekst.\n\n## Tre\n\nTekst."
        result = lint_narrative(_narrative(body=body))
        assert result.metrics["heading_count"] == 3
        assert not any("overskrifter" in f for f in result.hard_failures)

    def test_four_headings_is_hard_failure(self):
        body = "## En\n\nT.\n\n## To\n\nT.\n\n## Tre\n\nT.\n\n## Fire\n\nT."
        result = lint_narrative(_narrative(body=body))
        assert result.metrics["heading_count"] == 4
        assert any("overskrifter" in f for f in result.hard_failures)

    def test_headline_itself_not_counted_as_heading(self):
        result = lint_narrative(_narrative())
        assert result.metrics["heading_count"] == 0


class TestLastLineSimilarity:
    def test_no_previous_means_no_similarity_failure(self):
        result = lint_narrative(_narrative(last_line="Vi sees."))
        assert not any("Siste linje" in f for f in result.hard_failures)

    def test_identical_last_line_is_hard_failure(self):
        result = lint_narrative(
            _narrative(last_line="Vi sees neste uke, som alltid."),
            previous=[_narrative(last_line="Vi sees neste uke, som alltid.")],
        )
        assert any("Siste linje" in f for f in result.hard_failures)
        assert result.metrics["last_line_similarity"][0]["exact_tail_match"] is True

    def test_dissimilar_last_line_is_fine(self):
        result = lint_narrative(
            _narrative(last_line="En helt annen avslutning denne uken, spent på fortsettelsen."),
            previous=[_narrative(last_line="Ingenting med dette har noe til felles i det hele tatt her.")],
        )
        assert not any("Siste linje" in f for f in result.hard_failures)


class TestBannedPhrases:
    def test_vi_sees_family_flagged(self):
        result = lint_narrative(_narrative(last_line="Vi sees neste sesong."))
        assert "Vi sees-familien" in result.metrics["banned_phrases"]
        assert any("Forbudt frase" in f for f in result.hard_failures)

    def test_la_oss_flagged(self):
        result = lint_narrative(_narrative(body="La oss snakke om det alle tenker på akkurat nå."))
        assert "La oss ..." in result.metrics["banned_phrases"]

    def test_neste_deadline_kommer_flagged(self):
        result = lint_narrative(_narrative(body="Neste deadline kommer. Den gjør alltid det, uansett."))
        assert "Neste deadline kommer" in result.metrics["banned_phrases"]

    def test_det_er_ikke_x_det_er_y_flagged(self):
        result = lint_narrative(
            _narrative(body="Det er ikke flaks som svikter, det er templaten som slår tilbake her.")
        )
        assert "Det er ikke X, det er Y" in result.metrics["banned_phrases"]

    def test_number_restated_as_word_flagged(self):
        result = lint_narrative(_narrative(body="52 poeng vinner runden. Femtito, altså, helt greit."))
        assert any("Tall gjentatt som ord" in p for p in result.metrics["banned_phrases"])

    def test_clean_text_has_no_banned_phrases(self):
        result = lint_narrative(_narrative())
        assert result.metrics["banned_phrases"] == []
        assert not any("Forbudt frase" in f for f in result.hard_failures)


class TestPlayerPointsList:
    def test_two_or_more_scorecard_sentences_is_hard_failure(self):
        body = (
            "Bowen (12), Bruno (14) og Watkins (13) var alle solide denne uken helt klart. "
            "Salah (8), Haaland (6) og Palmer (9) leverte lite til sammenligning her."
        )
        result = lint_narrative(_narrative(body=body))
        assert result.metrics["player_points_list"] >= 2
        assert any("Scorecard" in f for f in result.hard_failures)

    def test_one_scorecard_sentence_is_only_a_metric_not_a_failure(self):
        body = "Bowen (12), Bruno (14) og Watkins (13) var alle solide denne uken helt klart."
        result = lint_narrative(_narrative(body=body))
        assert result.metrics["player_points_list"] == 1
        assert not any("Scorecard" in f for f in result.hard_failures)

    def test_normal_prose_is_not_flagged(self):
        result = lint_narrative(_narrative())
        assert result.metrics["player_points_list"] == 0


class TestDevicesAndHeadings:
    def test_pull_quote_counted(self):
        body = "Tekst her.\n\n> Et sitat fra Reidar selv om noe viktig som skjedde.\n\nMer tekst her."
        result = lint_narrative(_narrative(body=body))
        assert result.metrics["devices"]["pull_quotes"] == 1

    def test_fact_box_counted(self):
        body = '<div class="fact-box" markdown="1">\n\n- Ett poeng\n\n</div>'
        result = lint_narrative(_narrative(body=body))
        assert result.metrics["devices"]["fact_boxes"] == 1

    def test_table_counted(self):
        body = "| A | B |\n|---|---|\n| 1 | 2 |"
        result = lint_narrative(_narrative(body=body))
        assert result.metrics["devices"]["tables"] == 1

    def test_hr_counted(self):
        body = "Tekst.\n\n---\n\nMer tekst."
        result = lint_narrative(_narrative(body=body))
        assert result.metrics["hr_count"] == 1

    def test_standalone_line_counted(self):
        body = (
            "En lang setning med mange ord som ikke er standalone i det hele tatt egentlig.\n\n"
            "Kort og godt.\n\n"
            "En annen lang setning med mange ord som fyller opp plassen godt nok her òg."
        )
        result = lint_narrative(_narrative(body=body))
        assert result.metrics["devices"]["standalone_lines"] >= 1


class TestRepeatedNgrams:
    def test_repeated_significant_phrase_detected(self):
        shared = "det holder til rundeseier i en runde"
        current = _narrative(body=f"Han vant fordi {shared} uten problemer denne gangen.")
        previous = _narrative(body=f"Hun tapte selv om {shared} var innenfor rekkevidde òg.")
        result = lint_narrative(current, previous=[previous])
        assert any(shared.split()[0] in gram for gram in result.metrics["repeated_ngrams"])

    def test_stopword_only_ngram_ignored(self):
        current = _narrative(
            body="Det var det som det var, i det store og det hele her.",
            last_line="Blåbær cykler forbi glassveggen i morgengryet.",
        )
        previous = _narrative(
            body="Det var det som det var, men noe annet skjedde helt der.",
            last_line="Gulrøtter danser rundt fyrtårnet ved midnatt.",
        )
        result = lint_narrative(current, previous=[previous])
        # every 3/4-gram here is short function words -> nothing should qualify
        assert result.metrics["repeated_ngrams"] == []

    def test_no_previous_means_no_repeats(self):
        result = lint_narrative(_narrative())
        assert result.metrics["repeated_ngrams"] == []

    def test_capped_at_twenty(self):
        shared_words = [f"spesialord{i}xxxx ekstraord{i}yyyy" for i in range(30)]
        shared = " ".join(shared_words)
        current = _narrative(body=shared)
        previous = _narrative(body=shared)
        result = lint_narrative(current, previous=[previous])
        assert len(result.metrics["repeated_ngrams"]) <= 20


class TestSentenceLengthDistribution:
    def test_metrics_present_and_reasonable(self):
        body = "Kort. Litt lengre setning her. En mye lengre setning med flere ord enn de andre to."
        result = lint_narrative(_narrative(body=body))
        sl = result.metrics["sentence_length"]
        assert sl["count"] >= 3
        assert sl["mean"] > 0
        assert 0.0 <= sl["share_le_5"] <= 1.0


class TestToDict:
    def test_to_dict_has_expected_keys(self):
        result = lint_narrative(_narrative())
        d = result.to_dict()
        assert set(d.keys()) == {"metrics", "hard_failures", "warnings"}


# ---------------------------------------------------------------------------
# Fixtures against real published narratives (regression against real tics)
# ---------------------------------------------------------------------------


class TestRealNarratives:
    def test_gw38_2025_26_flags_la_oss_and_vi_sees(self):
        path = REPO_ROOT / "docs" / "narratives" / "2025-26" / "1638989" / "gw38.md"
        text = path.read_text(encoding="utf-8")
        result = lint_narrative(text)
        # gw38 has "La oss snakke om det alle tenker på." and ends "Vi sees neste sesong."
        assert "La oss ..." in result.metrics["banned_phrases"]
        assert "Vi sees-familien" in result.metrics["banned_phrases"]

    def test_gw27_2025_26_ends_without_vi_sees(self):
        path = REPO_ROOT / "docs" / "narratives" / "2025-26" / "1638989" / "gw27.md"
        text = path.read_text(encoding="utf-8")
        result = lint_narrative(text)
        # gw27 ends "Som alltid." — not part of the Vi sees family.
        assert "Vi sees-familien" not in result.metrics["banned_phrases"]

    def test_gw38_2025_26_word_count_over_default_limit(self):
        path = REPO_ROOT / "docs" / "narratives" / "2025-26" / "1638989" / "gw38.md"
        text = path.read_text(encoding="utf-8")
        result = lint_narrative(text)
        # These reports are long, per the issue's own measurements (821-1383 words).
        assert result.metrics["word_count"] > 650


# ---------------------------------------------------------------------------
# lint_path() / directory mode
# ---------------------------------------------------------------------------


class TestLintPath:
    def test_single_file(self, tmp_path: Path):
        f = tmp_path / "gw5.md"
        f.write_text(_narrative(), encoding="utf-8")
        results = lint_path(f)
        assert len(results) == 1
        assert results[0][0] == f

    def test_directory_sorted_by_gw_number(self, tmp_path: Path):
        (tmp_path / "gw10.md").write_text(_narrative(), encoding="utf-8")
        (tmp_path / "gw2.md").write_text(_narrative(), encoding="utf-8")
        (tmp_path / "gw1.md").write_text(_narrative(), encoding="utf-8")
        results = lint_path(tmp_path)
        names = [p.name for p, _ in results]
        assert names == ["gw1.md", "gw2.md", "gw10.md"]

    def test_previous_window_respected(self, tmp_path: Path):
        for i in range(1, 8):
            (tmp_path / f"gw{i}.md").write_text(
                _narrative(last_line=f"Avslutning nummer {i} her, ganske unik hver gang."),
                encoding="utf-8",
            )
        results = lint_path(tmp_path, previous_window=2)
        # gw7 should only be compared against gw6 and gw5 (2 previous)
        gw7_result = next(r for p, r in results if p.name == "gw7.md")
        assert len(gw7_result.metrics["last_line_similarity"]) == 2


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


class TestCLI:
    def test_json_output_is_valid_and_a_list(self, tmp_path: Path):
        f = tmp_path / "gw1.md"
        f.write_text(_narrative(), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, "-m", "fpl.style_lint", str(f), "--json"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(proc.stdout)
        assert isinstance(payload, list)
        assert payload[0]["file"] == str(f)
        assert "metrics" in payload[0]

    def test_table_output_for_directory(self, tmp_path: Path):
        (tmp_path / "gw1.md").write_text(_narrative(), encoding="utf-8")
        (tmp_path / "gw2.md").write_text(_narrative(), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, "-m", "fpl.style_lint", str(tmp_path)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "gw1.md" in proc.stdout
        assert "gw2.md" in proc.stdout
        assert "Totalt 2 fil(er)." in proc.stdout
