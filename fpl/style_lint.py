"""Deterministic style lint for Reidar's narratives (issue #40, workstream E).

Stdlib only, no LLM calls. Flags the tics documented in the issue: too
long, too many em dashes, three-fragment staccato headlines, repeated
sign-offs, too many headings, repeated n-grams against recent narratives,
banned phrases/tics, and scorecard-style player-points lists.

Two uses:

1. As a library: ``lint_narrative()`` is called by
   ``fpl.narrative_generator.run_narrative_pipeline`` right after
   generation, so a bad draft can be regenerated once with the findings
   appended to the prompt.
2. As a CLI: ``python -m fpl.style_lint <file-or-dir>`` runs the linter
   over one narrative or a whole season's worth, to produce the "tells
   list" that feeds the prompt rewrite (workstream D).
"""

from __future__ import annotations

import argparse
import json
import re
import statistics as _statistics
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .front_matter import parse_front_matter

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

# Word budget per shape, from the front-matter `shape:` a later workstream
# (D) adds. Unknown/missing shape falls back to DEFAULT_WORD_LIMIT.
SHAPE_WORD_LIMITS: dict[str, int] = {
    "kortversjonen": 250,
    "spalten": 650,
    "portrettet": 650,
    "brevet": 550,
    "karakterboka": 500,
}
DEFAULT_WORD_LIMIT = 650

MAX_EM_DASH = 3
MAX_HEADING_COUNT = 3
STACCATO_FRAGMENT_COUNT = 3
LAST_LINE_SIMILARITY_THRESHOLD = 0.5
MAX_PLAYER_POINTS_SENTENCES = 1  # >= 2 sentences is a hard failure
MAX_REPEATED_NGRAMS_LISTED = 20
DEFAULT_PREVIOUS_WINDOW = 5

# (label, pattern) — label is what shows up in hard_failures / the tells summary.
_BANNED_PHRASE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("Vi sees-familien", re.compile(r"\bvi\s+sees\b", re.IGNORECASE)),
    ("Neste deadline kommer", re.compile(r"\bneste deadline kommer\b", re.IGNORECASE)),
    (
        "Det er ikke X, det er Y",
        re.compile(r"\bdet er ikke\b.{0,60}?,?\s*det er\b", re.IGNORECASE | re.DOTALL),
    ),
    ("La oss ...", re.compile(r"\bla oss\b", re.IGNORECASE)),
    ("Det er ... et valg", re.compile(r"\bdet er\b.{0,40}?\bet valg\b", re.IGNORECASE)),
]

# Norwegian number words for the "52 poeng. Femtito." tell — common
# tens/teens only, per the issue ("don't go crazy").
_ONES = {
    1: "en", 2: "to", 3: "tre", 4: "fire", 5: "fem",
    6: "seks", 7: "sju", 8: "åtte", 9: "ni",
}
_TEENS = {
    10: "ti", 11: "elleve", 12: "tolv", 13: "tretten", 14: "fjorten",
    15: "femten", 16: "seksten", 17: "sytten", 18: "atten", 19: "nitten",
}
_TENS = {
    20: "tjue", 30: "tretti", 40: "førti", 50: "femti",
    60: "seksti", 70: "sytti", 80: "åtti", 90: "nitti",
}


def _number_words(n: int) -> list[str]:
    """Plausible spelled-out Norwegian forms for n (10-100)."""
    words: list[str] = []
    if n in _TEENS:
        words.append(_TEENS[n])
    if n in _TENS:
        words.append(_TENS[n])
    tens, ones = (n // 10) * 10, n % 10
    if 21 <= n <= 99 and tens in _TENS and ones in _ONES:
        words.append(_TENS[tens] + _ONES[ones])
        words.append(_TENS[tens] + "-" + _ONES[ones])
    if n == 100:
        words.append("hundre")
    return words


_NUMBER_WORD_MAP: dict[int, list[str]] = {n: _number_words(n) for n in range(10, 101)}

_WORD_RE = re.compile(r"[A-Za-zÆØÅæøåÀ-ÖØ-öø-ÿ0-9]+")
_CODE_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
_IMAGE_LINE_RE = re.compile(r"^!\[.*?\]\(.*?\)\s*$")
_HEADLINE_LINE_RE = re.compile(r"^#\s+.*$")
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_HEADLINE_RE = re.compile(r"^#[ \t]+(.*)$", re.MULTILINE)
_SUBHEADING_RE = re.compile(r"^(##|###)[ \t]+(.*)$", re.MULTILINE)
_NAME_PAREN_RE = re.compile(r"\b[A-ZÆØÅ][\wÀ-ÖØ-öø-ÿ'\-]*\s*\(\d{1,2}\)")
_NAME_COMMA_RE = re.compile(r"\b[A-ZÆØÅ][\wÀ-ÖØ-öø-ÿ'\-]*\s+\d{1,2},")


# ---------------------------------------------------------------------------
# Text preprocessing
# ---------------------------------------------------------------------------


def _strip_front_matter(text: str) -> tuple[str, dict[str, str]]:
    """Strip a leading front-matter block; keys lower-cased, quotes dropped."""
    fields, body = parse_front_matter(text)
    meta = {k.lower(): v.strip("\"'") for k, v in fields.items()}
    return body, meta


def _extract_headline(body: str) -> str:
    m = _HEADLINE_RE.search(body)
    return m.group(1).strip() if m else ""


def _headline_fragments(headline: str) -> list[str]:
    """Fragments of the headline split on '. ' / '! ' / '? '."""
    return [p for p in re.split(r"(?<=[.!?])\s+", headline.strip()) if p.strip()]


def _strip_for_word_count(body: str) -> str:
    """Remove fenced code, the headline line, image lines, and HTML tags."""
    text = _CODE_FENCE_RE.sub(" ", body)
    lines = []
    for line in text.split("\n"):
        stripped = line.strip()
        if _HEADLINE_LINE_RE.match(stripped) or _IMAGE_LINE_RE.match(stripped):
            continue
        lines.append(line)
    return _HTML_TAG_RE.sub(" ", "\n".join(lines))


def _tokenize(text: str) -> list[str]:
    return _WORD_RE.findall(text)


def _sentences(cleaned: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.!?])\s+", cleaned) if s.strip()]


# ---------------------------------------------------------------------------
# Devices (scanned on the markdown body, before HTML/headline stripping)
# ---------------------------------------------------------------------------


def _count_pull_quotes(body: str) -> int:
    return sum(1 for line in body.split("\n") if line.strip().startswith("> "))


def _count_class(body: str, cls: str) -> int:
    return len(re.findall(rf'class="{re.escape(cls)}"', body))


def _count_tables(body: str) -> int:
    count = 0
    in_table = False
    for line in body.split("\n"):
        stripped = line.strip()
        is_row = stripped.startswith("|") and stripped.endswith("|") and len(stripped) > 1
        if is_row and not in_table:
            count += 1
            in_table = True
        elif not is_row:
            in_table = False
    count += len(re.findall(r"<table", body, re.IGNORECASE))
    return count


def _count_lists(body: str) -> int:
    count = 0
    in_list = False
    for line in body.split("\n"):
        stripped = line.strip()
        is_item = bool(re.match(r"^(-\s+|\d+\.\s+)", stripped))
        if is_item and not in_list:
            count += 1
            in_list = True
        elif not is_item:
            in_list = False
    return count


def _count_hr(body: str) -> int:
    return sum(1 for line in body.split("\n") if line.strip() == "---")


def _headings(body: str) -> list[str]:
    return [m.group(2).strip() for m in _SUBHEADING_RE.finditer(body)]


def _standalone_lines(body: str) -> int:
    """Paragraphs of <= 8 words that aren't headings/lists/quotes/tables/hr."""
    count = 0
    for para in re.split(r"\n\s*\n", body):
        stripped = para.strip()
        if not stripped or "\n" in stripped or stripped == "---":
            continue
        if stripped.startswith(("#", ">", "-", "|", "<")) or re.match(r"^\d+\.", stripped):
            continue
        wc = len(_tokenize(stripped))
        if 0 < wc <= 8:
            count += 1
    return count


# ---------------------------------------------------------------------------
# Sentence-level tics
# ---------------------------------------------------------------------------


def _count_player_points_patterns(sentence: str) -> int:
    return len(_NAME_PAREN_RE.findall(sentence)) + len(_NAME_COMMA_RE.findall(sentence))


# How many tokens ahead of a digit run to look for its Norwegian spelled-out
# form. Wide enough to catch "52 poeng vinner runden. Femtito." (4 tokens
# between "52" and "Femtito") without drifting into unrelated numbers later
# in the paragraph.
_NUMBER_RESTATED_WINDOW = 4


def _detect_number_restated(tokens: list[str]) -> list[str]:
    """Digit run followed a few words later by the same number spelled out."""
    hits = []
    for i, tok in enumerate(tokens):
        if not tok.isdigit():
            continue
        words = _NUMBER_WORD_MAP.get(int(tok))
        if not words:
            continue
        window = [t.lower() for t in tokens[i + 1 : i + 1 + _NUMBER_RESTATED_WINDOW]]
        for w in words:
            if w in window:
                hits.append(f"{tok} … {w}")
                break
    return hits


def _last_paragraph(body: str) -> str:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    return paragraphs[-1] if paragraphs else ""


def _last_line_similarity(
    current_last: str, previous_lasts: list[str]
) -> list[dict[str, Any]]:
    """Normalised token Jaccard vs each previous last line, plus a 3-word
    exact-tail-match flag."""
    cur_tokens_list = _tokenize(current_last)
    cur_tokens = {t.lower() for t in cur_tokens_list}
    cur_tail = tuple(t.lower() for t in cur_tokens_list[-3:])

    results = []
    for i, prev_last in enumerate(previous_lasts):
        prev_tokens_list = _tokenize(prev_last)
        prev_tokens = {t.lower() for t in prev_tokens_list}
        union = cur_tokens | prev_tokens
        jaccard = len(cur_tokens & prev_tokens) / len(union) if union else 0.0
        prev_tail = tuple(t.lower() for t in prev_tokens_list[-3:])
        exact_tail = bool(cur_tail) and cur_tail == prev_tail
        results.append(
            {"previous_index": i, "jaccard": round(jaccard, 3), "exact_tail_match": exact_tail}
        )
    return results


def _ngrams(tokens: list[str], n: int) -> list[tuple[str, ...]]:
    return [tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]


def _is_significant_ngram(ngram: tuple[str, ...]) -> bool:
    """Ignore n-grams that are all stop-words/names: keep only those with
    >= 2 alphabetic tokens of length >= 4."""
    return sum(1 for tok in ngram if tok.isalpha() and len(tok) >= 4) >= 2


def _repeated_ngrams(
    current_tokens: list[str], previous_tokens_list: list[list[str]]
) -> list[str]:
    current_lower = [t.lower() for t in current_tokens]
    prev_sets = [
        {" ".join(g) for n in (3, 4) for g in _ngrams([t.lower() for t in toks], n)}
        for toks in previous_tokens_list
    ]

    found: list[str] = []
    seen: set[str] = set()
    for n in (3, 4):
        for gram in _ngrams(current_lower, n):
            if not _is_significant_ngram(gram):
                continue
            phrase = " ".join(gram)
            if phrase in seen:
                continue
            if any(phrase in ps for ps in prev_sets):
                found.append(phrase)
                seen.add(phrase)
                if len(found) >= MAX_REPEATED_NGRAMS_LISTED:
                    return found
    return found


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


@dataclass
class Limits:
    """Hard/soft thresholds. Override for tests or a stricter shape."""

    max_word_count: int | None = None  # None => derive from shape
    max_em_dash: int = MAX_EM_DASH
    max_heading_count: int = MAX_HEADING_COUNT
    staccato_fragment_count: int = STACCATO_FRAGMENT_COUNT
    last_line_similarity_threshold: float = LAST_LINE_SIMILARITY_THRESHOLD
    max_player_points_sentences: int = MAX_PLAYER_POINTS_SENTENCES
    shape_word_limits: dict[str, int] = field(default_factory=lambda: dict(SHAPE_WORD_LIMITS))
    default_word_limit: int = DEFAULT_WORD_LIMIT

    def word_limit_for_shape(self, shape: str | None) -> int:
        if self.max_word_count is not None:
            return self.max_word_count
        if shape:
            return self.shape_word_limits.get(shape.strip().lower(), self.default_word_limit)
        return self.default_word_limit


@dataclass
class LintResult:
    metrics: dict[str, Any]
    hard_failures: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "metrics": self.metrics,
            "hard_failures": self.hard_failures,
            "warnings": self.warnings,
        }


def lint_narrative(
    text: str,
    previous: list[str] | None = None,
    limits: Limits | None = None,
    *,
    shape: str | None = None,
) -> LintResult:
    """Lint a single narrative markdown string.

    Args:
        text: The full narrative markdown, front-matter included.
        previous: Up to five previous narratives (raw markdown), most
            recent first, used for sign-off similarity and repeated
            n-grams. May be empty/None for the first narrative of a season.
        limits: Override the default hard-limit thresholds.
        shape: The pipeline-scheduled shape (issue #40, workstream A/B),
            overriding whatever the front-matter `shape:` says. Falls back
            to the front matter when omitted.

    Returns:
        A LintResult with metrics, hard_failures (for the regeneration
        prompt), and warnings.
    """
    previous = previous or []
    limits = limits or Limits()

    body, front_matter = _strip_front_matter(text)
    headline = _extract_headline(body)
    headline_shape = len(_headline_fragments(headline))

    cleaned = _strip_for_word_count(body)
    tokens = _tokenize(cleaned)
    word_count = len(tokens)

    sentences = _sentences(cleaned)
    sentence_lengths = [n for n in (len(_tokenize(s)) for s in sentences) if n > 0]

    if sentence_lengths:
        mean_len = _statistics.fmean(sentence_lengths)
        if len(sentence_lengths) >= 2:
            p90 = _statistics.quantiles(sentence_lengths, n=100, method="inclusive")[89]
        else:
            p90 = float(sentence_lengths[0])
        share_le_5 = sum(1 for n in sentence_lengths if n <= 5) / len(sentence_lengths)
    else:
        mean_len = p90 = share_le_5 = 0.0

    em_dash_count = len(re.findall(r"—", cleaned)) + len(re.findall(r"\s–\s", cleaned))
    em_dash_per_100 = (em_dash_count / word_count * 100) if word_count else 0.0

    last_line = _last_paragraph(body)
    previous_last_lines = [_last_paragraph(_strip_front_matter(p)[0]) for p in previous]
    last_line_sim = _last_line_similarity(last_line, previous_last_lines)
    max_jaccard = max((r["jaccard"] for r in last_line_sim), default=0.0)
    any_exact_tail = any(r["exact_tail_match"] for r in last_line_sim)

    headings = _headings(body)
    heading_count = len(headings)

    devices = {
        "pull_quotes": _count_pull_quotes(body),
        "fact_boxes": _count_class(body, "fact-box"),
        "tables": _count_tables(body),
        "lists": _count_lists(body),
        "big_numbers": _count_class(body, "big-number"),
        "receipts": _count_class(body, "receipt"),
        "timelines": _count_class(body, "timeline"),
        "for_against": _count_class(body, "for-against"),
        "standalone_lines": _standalone_lines(body),
    }
    hr_count = _count_hr(body)

    previous_tokens_list = [
        _tokenize(_strip_for_word_count(_strip_front_matter(p)[0])) for p in previous
    ]
    repeated_ngrams = _repeated_ngrams(tokens, previous_tokens_list)

    player_points_list = sum(1 for s in sentences if _count_player_points_patterns(s) >= 3)

    banned_phrases: list[str] = []
    for name, pattern in _BANNED_PHRASE_PATTERNS:
        if pattern.search(cleaned):
            banned_phrases.append(name)
    for hit in _detect_number_restated(re.findall(_WORD_RE, cleaned)):
        banned_phrases.append(f"Tall gjentatt som ord ({hit})")

    shape = shape if shape is not None else front_matter.get("shape")
    word_limit = limits.word_limit_for_shape(shape)

    metrics: dict[str, Any] = {
        "word_count": word_count,
        "word_limit": word_limit,
        "shape": shape,
        "em_dash_count": em_dash_count,
        "em_dash_per_100_words": round(em_dash_per_100, 2),
        "sentence_length": {
            "mean": round(mean_len, 2),
            "p90": round(p90, 2),
            "share_le_5": round(share_le_5, 3),
            "count": len(sentence_lengths),
        },
        "headline": headline,
        "headline_shape": headline_shape,
        "last_line": last_line,
        "last_line_similarity": last_line_sim,
        "heading_count": heading_count,
        "headings": headings,
        "devices": devices,
        "hr_count": hr_count,
        "repeated_ngrams": repeated_ngrams,
        "banned_phrases": banned_phrases,
        "player_points_list": player_points_list,
    }

    hard_failures: list[str] = []
    warnings: list[str] = []

    if word_count > word_limit:
        hard_failures.append(
            f"For langt: {word_count} ord (grense {word_limit} for shape={shape or 'default'})."
        )
    if em_dash_count > limits.max_em_dash:
        hard_failures.append(
            f"For mange tankestreker: {em_dash_count} (maks {limits.max_em_dash})."
        )
    if headline_shape == limits.staccato_fragment_count:
        hard_failures.append(
            f"Tittelen har {headline_shape} fragmenter (stakkato-formel): «{headline}»."
        )
    if max_jaccard >= limits.last_line_similarity_threshold or any_exact_tail:
        hard_failures.append(
            "Siste linje ligner for mye på en tidligere avslutning "
            f"(jaccard={max_jaccard:.2f}, eksakt halevending={any_exact_tail}): «{last_line}»."
        )
    if heading_count > limits.max_heading_count:
        hard_failures.append(
            f"For mange overskrifter: {heading_count} (maks {limits.max_heading_count})."
        )
    for phrase in banned_phrases:
        hard_failures.append(f"Forbudt frase/tic: {phrase}.")
    if player_points_list > limits.max_player_points_sentences:
        hard_failures.append(
            f"Scorecard-aktig spillerpoeng-opplisting i {player_points_list} setninger."
        )

    if heading_count == limits.max_heading_count:
        warnings.append("Overskriftsantall er på grensen.")
    if repeated_ngrams:
        preview = ", ".join(repeated_ngrams[:5])
        more = "..." if len(repeated_ngrams) > 5 else ""
        warnings.append(f"{len(repeated_ngrams)} gjentatte fraser fra tidligere runder: {preview}{more}")
    if share_le_5 > 0.3:
        warnings.append(f"Mange svært korte setninger ({share_le_5:.0%} <= 5 ord).")
    if not any(devices.values()):
        warnings.append("Ingen visuelle elementer brukt.")

    return LintResult(metrics=metrics, hard_failures=hard_failures, warnings=warnings)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _gw_number(path: Path) -> int:
    m = re.search(r"gw(\d+)", path.stem)
    return int(m.group(1)) if m else 0


def lint_path(
    target: Path, previous_window: int = DEFAULT_PREVIOUS_WINDOW
) -> list[tuple[Path, LintResult]]:
    """Lint a single file, or every gw*.md file in a directory (sorted by
    GW number), using the preceding `previous_window` files as context."""
    files = [target] if target.is_file() else sorted(target.glob("gw*.md"), key=_gw_number)
    texts = {f: f.read_text(encoding="utf-8") for f in files}

    results: list[tuple[Path, LintResult]] = []
    for idx, f in enumerate(files):
        # Most recent preceding file first, capped at previous_window.
        previous_texts = [
            texts[files[j]] for j in range(idx - 1, max(-1, idx - 1 - previous_window), -1)
        ]
        results.append((f, lint_narrative(texts[f], previous=previous_texts)))
    return results


def _print_table(results: list[tuple[Path, LintResult]]) -> None:
    header = f"{'file':<14}{'words':>7}{'em/100w':>9}{'headshape':>10}{'headings':>9}{'hardfail':>9}"
    print(header)
    print("-" * len(header))
    for path, result in results:
        m = result.metrics
        print(
            f"{path.name:<14}{m['word_count']:>7}{m['em_dash_per_100_words']:>9.1f}"
            f"{m['headline_shape']:>10}{m['heading_count']:>9}{len(result.hard_failures):>9}"
        )


def _print_summary(results: list[tuple[Path, LintResult]]) -> None:
    n = len(results)
    print()
    if n == 0:
        print("Ingen filer funnet.")
        return

    words = [r.metrics["word_count"] for _, r in results]
    em100 = [r.metrics["em_dash_per_100_words"] for _, r in results]
    print(f"Totalt {n} fil(er).")
    print(f"Gjennomsnittlig lengde: {_statistics.fmean(words):.0f} ord")
    print(f"Gjennomsnittlig tankestrek/100 ord: {_statistics.fmean(em100):.2f}")

    tell_counter: Counter[str] = Counter()
    for _, r in results:
        seen_this_file = {item.split(":")[0] for item in r.hard_failures + r.warnings}
        for key in seen_this_file:
            tell_counter[key] += 1

    recurring = [(key, count) for key, count in tell_counter.most_common() if count / n >= 0.5]
    if recurring:
        print(f"Gjentakende tells (>= 50% av filene, {n} filer):")
        for key, count in recurring:
            print(f"  - {key}: {count}/{n}")
    else:
        print("Ingen tics gjentar seg i >= 50% av filene.")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Style lint for Reidar's narratives (issue #40, workstream E)."
    )
    parser.add_argument("target", help="A narrative .md file, or a directory of gw*.md files")
    parser.add_argument(
        "--previous",
        type=int,
        default=DEFAULT_PREVIOUS_WINDOW,
        help="How many preceding gameweeks to compare against (directory mode only)",
    )
    parser.add_argument("--json", action="store_true", help="Dump the full results as JSON")
    args = parser.parse_args(argv)

    results = lint_path(Path(args.target), previous_window=args.previous)

    if args.json:
        payload = [{"file": str(path), **result.to_dict()} for path, result in results]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    _print_table(results)
    _print_summary(results)


if __name__ == "__main__":
    main()
