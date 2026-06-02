"""Tests for the QAC morphology loader and root/lemma primitives.

Two layers, mirroring ``test_primitives.py``:

* **Synthetic fixtures** written into ``tmp_path`` and parsed via the public
  loader (or, for spans smaller than the whole Quran, via the module's
  parse/aggregate helpers) — fast, deterministic, exercising exact counts and
  edge cases.
* **One module-scoped real-data anchor** loading the vendored QAC file, asserting
  only re-derived / structural facts (no magic numbers, no claim verdicts).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from quran_analysis.morphology import (
    MORPHOLOGY_FILE,
    Morphology,
    _build_words,
    _read_segments,
    count_by_lemma,
    count_by_root,
    load_morphology,
)

# A realistic QAC preamble + column header. The loader must skip every ``#``
# comment line and the ``LOCATION\tFORM\tTAG\tFEATURES`` header before the data.
_PREAMBLE = (
    "# PLEASE DO NOT REMOVE OR CHANGE THIS COPYRIGHT BLOCK\n"
    "#  Quranic Arabic Corpus (morphology, version 0.4)\n"
    "#  License: GNU General Public License\n"
    "\n"
    "LOCATION\tFORM\tTAG\tFEATURES\n"
)

# A small but representative corpus covering every aggregation/edge case:
# * a multi-segment word (prefix + stem + suffix) that must collapse to ONE word;
# * a particle word with no root/lemma/pos;
# * two words sharing a root (ywm) with different lemmas;
# * two words sharing a lemma (yawom).
_SYNTHETIC_ROWS = (
    # word (1:1:1): prefix + stem(ROOT:ywm, LEM:yawom) + suffix -> 1 word
    "(1:1:1:1)\tbi\tP\tPREFIX|bi+\n"
    "(1:1:1:2)\tyawomi\tN\tSTEM|POS:N|LEM:yawom|ROOT:ywm|M|GEN\n"
    "(1:1:1:3)\thi\tPRON\tSUFFIX|PRON:3MS\n"
    # word (1:1:2): particle, no root/lemma/pos
    "(1:1:2:1)\twa\tCONJ\tPREFIX|w:CONJ+\n"
    # word (1:1:3): shares ROOT ywm, different lemma (plural form)
    "(1:1:3:1)\t>ay~aAmK\tN\tSTEM|POS:N|LEM:>ay~aAm|ROOT:ywm|MP|ACC\n"
    # word (1:2:1): shares LEMMA yawom with (1:1:1)
    "(1:2:1:1)\tyawoma\tN\tSTEM|POS:N|LEM:yawom|ROOT:ywm|M|ACC\n"
    # word (1:2:2): another root entirely
    "(1:2:2:1)\tmawotu\tN\tSTEM|POS:N|LEM:mawot|ROOT:mwt|M|NOM\n"
)


def _write_morphology(directory: Path, data_rows: str) -> None:
    """Write a synthetic QAC morphology file (preamble + header + rows)."""
    (directory / MORPHOLOGY_FILE).write_text(_PREAMBLE + data_rows, encoding="utf-8")


def _parse_unvalidated(path: Path) -> Morphology:
    """Parse a synthetic file via the public helpers, skipping the 114/6236 guard.

    The real :func:`load_morphology` enforces a whole-Quran structural guard
    which a tiny fixture cannot satisfy, so synthetic parser/counting tests build
    the model through the same parse + aggregate helpers without that guard.
    """
    raw = path.read_text(encoding="utf-8")
    return Morphology(words=_build_words(_read_segments(raw)))


def test_synthetic_counts_and_aggregation(tmp_path: Path) -> None:
    """Multi-segment words collapse to one; root/lemma counts are exact."""
    _write_morphology(tmp_path, _SYNTHETIC_ROWS)
    m = _parse_unvalidated(tmp_path / MORPHOLOGY_FILE)

    # 5 distinct words despite 7 segment rows (the 3-segment word collapses to 1).
    assert len(m.words) == 5

    # The multi-segment word took root/lemma/pos/form from its STEM segment.
    w = m.word(1, 1, 1)
    assert w.form == "yawomi"
    assert w.root == "ywm"
    assert w.lemma == "yawom"
    assert w.pos == "N"

    # Particle word: no morphological features.
    particle = m.word(1, 1, 2)
    assert particle.root is None
    assert particle.lemma is None
    assert particle.pos is None

    # root ywm appears on 3 words (yawomi, >ay~aAm, yawoma); lemma yawom on 2.
    assert count_by_root(m, "ywm") == 3
    assert count_by_lemma(m, "yawom") == 2
    assert count_by_root(m, "mwt") == 1
    assert count_by_lemma(m, ">ay~aAm") == 1


def test_synthetic_edge_cases(tmp_path: Path) -> None:
    """Unknown / empty / whitespace queries, unknown keys, and an empty model."""
    _write_morphology(tmp_path, _SYNTHETIC_ROWS)
    m = _parse_unvalidated(tmp_path / MORPHOLOGY_FILE)

    # Unknown root/lemma -> 0.
    assert count_by_root(m, "zzz") == 0
    assert count_by_lemma(m, "zzz") == 0
    # Empty / whitespace-only -> 0 (guarded).
    assert count_by_root(m, "") == 0
    assert count_by_root(m, "   ") == 0
    assert count_by_lemma(m, "") == 0
    assert count_by_lemma(m, "\t") == 0
    # Unknown word key -> KeyError.
    with pytest.raises(KeyError):
        m.word(9, 9, 9)

    # Header-only file (no data rows) -> empty morphology, counts 0, KeyError.
    empty = Morphology(words=())
    assert count_by_root(empty, "ywm") == 0
    assert count_by_lemma(empty, "yawom") == 0
    with pytest.raises(KeyError):
        empty.word(1, 1, 1)


def test_validate_rejects_partial_span(tmp_path: Path) -> None:
    """``load_morphology`` enforces the 114-sura guard."""
    _write_morphology(tmp_path, _SYNTHETIC_ROWS)
    with pytest.raises(ValueError, match="suras not exactly 1..114"):
        load_morphology(data_dir=tmp_path)


def test_validate_rejects_wrong_aya_count(tmp_path: Path) -> None:
    """The 6236-aya guard fires independently when all 114 suras are present.

    Build exactly 114 suras with one aya each (114 ``(sura, aya)`` pairs, not
    6236) so the sura guard passes and the aya guard is what rejects the data.
    """
    rows = "".join(
        f"({s}:1:1:1)\tyawomi\tN\tSTEM|POS:N|LEM:yawom|ROOT:ywm|M|GEN\n" for s in range(1, 115)
    )
    _write_morphology(tmp_path, rows)
    with pytest.raises(ValueError, match="6236"):
        load_morphology(data_dir=tmp_path)


def test_malformed_line_rejected(tmp_path: Path) -> None:
    """A data row with too few tab columns is rejected."""
    _write_morphology(tmp_path, "(1:1:1:1)\tyawomi\n")  # only 2 columns
    with pytest.raises(ValueError, match="malformed QAC data line"):
        load_morphology(data_dir=tmp_path)


# --- One real-data anchor (module-scoped fixture: load the vendored file once). -


@pytest.fixture(scope="module")
def real_morphology() -> Morphology:
    """Load the vendored QAC file once (mirrors ``real_corpus`` in test_primitives).

    A module-scoped fixture (not an import-time load) defers the I/O to test
    execution, so an absent/corrupt vendored file fails the real-data tests with
    a clear, scoped error rather than a cryptic collection-phase traceback.
    """
    return load_morphology()


def test_real_structural_span(real_morphology: Morphology) -> None:
    """The vendored QAC file spans exactly 114 suras and 6236 ayas."""
    assert {w.sura for w in real_morphology.words} == set(range(1, 115))
    assert len({(w.sura, w.aya) for w in real_morphology.words}) == 6236


def test_real_count_is_consistent(real_morphology: Morphology) -> None:
    """``count_by_root`` matches an independent re-derivation (no magic number)."""
    root = "ywm"  # day
    expected = sum(1 for w in real_morphology.words if w.root == root)
    assert count_by_root(real_morphology, root) == expected
    assert count_by_root(real_morphology, root) > 0


def test_real_root_subsumes_lemma(real_morphology: Morphology) -> None:
    """A root count is >= any single lemma's count under it (structural invariant)."""
    # Every word with lemma 'yawom' has root 'ywm', so root >= lemma.
    assert count_by_root(real_morphology, "ywm") >= count_by_lemma(real_morphology, "yawom")
    assert count_by_lemma(real_morphology, "yawom") > 0


def test_real_basmala_sura1_only(real_morphology: Morphology) -> None:
    """Sura 1's basmala is words of aya 1:1; suras 2-114 don't repeat it."""
    allah = real_morphology.word(1, 1, 2)
    assert allah.lemma == "{ll~ah"
    # Sura 2 word 1 is the muqatta'at "Alm", NOT a repeated basmala 'bi' particle.
    assert real_morphology.word(2, 1, 1).form.startswith("Al")
