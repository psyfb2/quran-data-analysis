"""Tests for the corpus loader, run against the real vendored Tanzil files.

The data is committed/offline, so these tests need no network. Structural counts
are asserted both as canonical literals *and* re-derived from the parsed files so
the test fails loudly if the vendored data drifts.
"""

from __future__ import annotations

import re

import pytest

from quran_analysis.corpus import (
    BASMALA_AYA,
    DATA_DIR,
    Corpus,
    load_corpus,
)

EDITIONS = ["uthmani", "simple-clean"]

# Canonical Tanzil structural counts (both editions), re-derived in tests below.
EXPECTED_SURAS = 114
EXPECTED_AYAS = 6236
# Suras 2-114 except 9 carry a separated opening basmala of 4 words each.
EXPECTED_SEPARATED_BASMALA_SURAS = 112
BASMALA_WORDS = 4


@pytest.fixture(scope="module", params=EDITIONS)
def corpus(request: pytest.FixtureRequest) -> Corpus:
    return load_corpus(request.param)


def _raw_data_line_count(edition: str) -> int:
    text = (DATA_DIR / f"tanzil-{edition}.txt").read_text(encoding="utf-8-sig")
    return sum(1 for line in text.splitlines() if line.strip() and not line.strip().startswith("#"))


def test_sura_count(corpus: Corpus) -> None:
    assert len(corpus.suras) == EXPECTED_SURAS
    assert [s.number for s in corpus.suras] == list(range(1, EXPECTED_SURAS + 1))


def test_total_ayas_matches_file(corpus: Corpus) -> None:
    total = sum(len(s.ayas) for s in corpus.suras)
    assert total == EXPECTED_AYAS
    # Derived: total numbered ayas equals the count of data lines in the file.
    assert total == _raw_data_line_count(corpus.edition)


def test_aya_numbering_contiguous(corpus: Corpus) -> None:
    for s in corpus.suras:
        assert [a.number for a in s.ayas] == list(range(1, len(s.ayas) + 1))


def test_sura1_basmala_is_aya_1(corpus: Corpus) -> None:
    s1 = corpus.sura(1)
    assert s1.separated_basmala is None  # not separated — it is aya 1
    assert s1.basmala is not None
    assert len(s1.basmala) == BASMALA_WORDS
    assert s1.basmala == corpus.aya(1, 1).words


def test_sura9_has_no_basmala(corpus: Corpus) -> None:
    s9 = corpus.sura(9)
    assert s9.separated_basmala is None
    assert s9.basmala is None


def test_sura2_basmala_separated(corpus: Corpus) -> None:
    s2 = corpus.sura(2)
    assert s2.separated_basmala is not None
    assert len(s2.separated_basmala) == BASMALA_WORDS
    # Basmala words carry the sentinel aya number.
    assert all(w.aya == BASMALA_AYA for w in s2.separated_basmala)
    # Verse 1 content after separation does not start with the basmala again.
    assert not corpus.aya(2, 1).text.startswith(s2.separated_basmala[0].text + " ")
    # Verse 1 still has content (the muqatta'at letters).
    assert len(corpus.aya(2, 1).words) >= 1


def test_every_expected_sura_has_separated_basmala(corpus: Corpus) -> None:
    separated = [s.number for s in corpus.suras if s.separated_basmala is not None]
    # Exactly suras 2-114 except 9.
    assert separated == [n for n in range(2, 115) if n != 9]
    assert len(separated) == EXPECTED_SEPARATED_BASMALA_SURAS
    for s in corpus.suras:
        if s.separated_basmala is not None:
            assert len(s.separated_basmala) == BASMALA_WORDS


def test_include_basmala_adds_448_words(corpus: Corpus) -> None:
    without = len(corpus.words())
    with_basmala = len(corpus.words(include_basmala=True))
    assert with_basmala - without == EXPECTED_SEPARATED_BASMALA_SURAS * BASMALA_WORDS  # 448


def test_2730_basmala_phrase_not_stripped(corpus: Corpus) -> None:
    # Aya 27:30 contains the basmala as mid-verse content; it must remain intact.
    aya = corpus.aya(27, 30)
    basmala_text = corpus.sura(2).separated_basmala[0].text  # type: ignore[index]
    # The first basmala token appears somewhere in 27:30's words.
    assert basmala_text in [w.text for w in aya.words]
    # And it is not the very first word (it is genuinely mid-verse).
    assert aya.words[0].text != basmala_text


def test_selectors(corpus: Corpus) -> None:
    assert corpus.aya(1, 1).text.strip() != ""
    assert corpus.sura(2).text().strip() != ""
    assert corpus.sura(2).number == 2
    with pytest.raises(KeyError):
        corpus.aya(999, 1)  # unknown sura
    with pytest.raises(KeyError):
        corpus.aya(1, 999)  # valid sura, unknown aya
    with pytest.raises(KeyError):
        corpus.sura(115)


def test_sura_text_include_basmala(corpus: Corpus) -> None:
    s2 = corpus.sura(2)
    base = len(s2.text().split())
    with_basmala = len(s2.text(include_basmala=True).split())
    assert with_basmala - base == BASMALA_WORDS  # 4
    # Sura 1's basmala is aya 1, so the toggle does not change its word count.
    s1 = corpus.sura(1)
    assert len(s1.text(include_basmala=True).split()) == len(s1.text().split())


def test_determinism() -> None:
    a = load_corpus("uthmani")
    b = load_corpus("uthmani")
    assert len(a.words()) == len(b.words())
    assert a.suras == b.suras  # frozen dataclasses compare by value


def test_arabic_only_no_latin_letters(corpus: Corpus) -> None:
    # Verse text must be original Arabic, never a translation / Latin transliteration.
    assert re.search(r"[A-Za-z]", corpus.text()) is None


def test_word_positions_are_zero_based_and_ordered(corpus: Corpus) -> None:
    aya = corpus.aya(1, 2)
    assert [w.position for w in aya.words] == list(range(len(aya.words)))
    assert all(w.sura == 1 and w.aya == 2 for w in aya.words)


def test_unknown_edition_raises() -> None:
    with pytest.raises(ValueError):
        load_corpus("not-an-edition")


def test_model_is_immutable(corpus: Corpus) -> None:
    from dataclasses import FrozenInstanceError

    word = corpus.aya(1, 1).words[0]
    with pytest.raises(FrozenInstanceError):
        word.text = "x"  # type: ignore[misc]
