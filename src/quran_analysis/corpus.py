"""Corpus ingestion & in-memory model (Tanzil Uthmani + Simple-Clean).

Parses the vendored Arabic text editions (``data/tanzil-*.txt``) into an
immutable ``Corpus -> Sura -> Aya -> Word`` model keyed by ``(sura, aya)``.

The opening *basmala* is made individually addressable so any per-claim
counting convention (basmala counted or not) can be applied downstream:

* Sura 1: the basmala **is** aya ``1:1`` — a counted verse.
* Suras 2-114 except 9: the source prepends the basmala to the text of verse 1;
  the loader splits it off into ``Sura.separated_basmala`` (sentinel ``aya=0``)
  so verse 1's content words start *after* the basmala.
* Sura 9 (At-Tawbah): has no basmala.
* Aya 27:30 contains the basmala phrase as genuine mid-verse content; because
  detection is verse-1-only it is never split off.

All stored text is the **original Arabic, verbatim** (diacritics preserved);
normalisation is a later concern (Task 3/4) — this module imports no ``normalize``.

See ``agentdocs/corpus.md`` for editions, versions, and license/attribution.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# Repo-root ``data/`` directory. From src/quran_analysis/corpus.py the parents are
# [0]=quran_analysis, [1]=src, [2]=repo root. Works under pythonpath=["src"], make, CI.
DATA_DIR: Path = Path(__file__).resolve().parents[2] / "data"

#: Sentinel aya number marking words that belong to a sura-opening basmala that is
#: *not* a numbered verse (suras 2-114 except 9). Sura 1's basmala keeps aya number 1.
BASMALA_AYA: int = 0

_EDITION_FILES: dict[str, str] = {
    "uthmani": "tanzil-uthmani.txt",
    "simple-clean": "tanzil-simple-clean.txt",
}


@dataclass(frozen=True)
class Word:
    """A single whitespace-delimited token of original Arabic text.

    Attributes:
        text: The original Arabic surface form, verbatim (diacritics preserved).
        sura: 1-based sura number.
        aya: 1-based aya number, or ``BASMALA_AYA`` (0) for a separated basmala token.
        position: 0-based index of this word within its aya (or basmala).
    """

    text: str
    sura: int
    aya: int
    position: int


@dataclass(frozen=True)
class Aya:
    """A numbered verse: an ordered tuple of :class:`Word`."""

    sura: int
    number: int
    words: tuple[Word, ...]

    @property
    def text(self) -> str:
        """The verse text, words rejoined on a single space."""
        return " ".join(w.text for w in self.words)


@dataclass(frozen=True)
class Sura:
    """A chapter: ordered ayas plus an optionally-separated opening basmala.

    Attributes:
        number: 1-based sura number.
        ayas: Ordered tuple of numbered :class:`Aya`.
        separated_basmala: The opening basmala words split off from verse 1 for
            suras 2-114 (except 9); ``None`` for sura 1 (its basmala is aya 1) and
            sura 9 (no basmala).
    """

    number: int
    ayas: tuple[Aya, ...]
    separated_basmala: tuple[Word, ...] | None

    @property
    def basmala(self) -> tuple[Word, ...] | None:
        """The opening basmala words, individually addressable.

        Returns the words of aya 1 for sura 1 (where the basmala *is* a counted
        verse), the separated basmala for suras 2-114 except 9, and ``None`` for
        sura 9 (which has no basmala).
        """
        if self.number == 1:
            return self.ayas[0].words
        return self.separated_basmala

    def words(self, *, include_basmala: bool = False) -> tuple[Word, ...]:
        """All verse words of the sura.

        Args:
            include_basmala: When ``True``, prepend the *separated* basmala words
                (suras 2-114 except 9). Sura 1 is unaffected — its basmala is
                already aya 1, so it is never double-counted; sura 9 has none.
        """
        verse_words = tuple(w for aya in self.ayas for w in aya.words)
        if include_basmala and self.separated_basmala is not None:
            return self.separated_basmala + verse_words
        return verse_words

    def text(self, *, include_basmala: bool = False) -> str:
        """All verse text of the sura, words joined on a single space.

        Args:
            include_basmala: When ``True``, prepend the *separated* basmala words
                (suras 2-114 except 9). For sura 1 the basmala is always present
                because it is aya 1; sura 9 has none. Mirrors :meth:`Corpus.text`.
        """
        return " ".join(w.text for w in self.words(include_basmala=include_basmala))


@dataclass(frozen=True)
class Corpus:
    """An immutable Quran edition: ordered suras with ``(sura, aya)`` lookup.

    Attributes:
        edition: Edition key, e.g. ``"uthmani"`` or ``"simple-clean"``.
        suras: Ordered tuple of all 114 :class:`Sura`.
    """

    edition: str
    suras: tuple[Sura, ...]

    def sura(self, number: int) -> Sura:
        """Return the sura with the given 1-based number.

        Raises:
            KeyError: If no sura has that number.
        """
        for s in self.suras:
            if s.number == number:
                return s
        raise KeyError(f"sura {number} not found")

    def aya(self, sura: int, aya: int) -> Aya:
        """Return the aya keyed by ``(sura, aya)``.

        Raises:
            KeyError: If the sura or aya number is unknown.
        """
        for a in self.sura(sura).ayas:
            if a.number == aya:
                return a
        raise KeyError(f"aya {sura}:{aya} not found")

    def words(self, *, include_basmala: bool = False) -> tuple[Word, ...]:
        """All verse words of the whole corpus, in canonical order.

        Args:
            include_basmala: When ``True``, include each sura's *separated*
                basmala words (the per-claim basmala-inclusion hook consumed by
                the primitives layer). Sura 1's basmala is never double-counted.
        """
        return tuple(w for s in self.suras for w in s.words(include_basmala=include_basmala))

    def text(self, *, include_basmala: bool = False) -> str:
        """All verse text of the whole corpus, words joined on a single space."""
        return " ".join(w.text for w in self.words(include_basmala=include_basmala))


def _parse_lines(raw: str) -> list[tuple[int, int, str]]:
    """Parse ``sura|aya|text`` data lines, skipping blank and ``#`` comment lines."""
    records: list[tuple[int, int, str]] = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = line.split("|", 2)
        if len(parts) != 3:
            raise ValueError(f"malformed corpus line (expected 'sura|aya|text'): {line!r}")
        sura_str, aya_str, text = parts
        records.append((int(sura_str), int(aya_str), text.strip()))
    return records


def _build_sura(number: int, rows: list[tuple[int, int, str]], basmala_ref: str) -> Sura:
    """Build a :class:`Sura` from its ordered ``(sura, aya, text)`` rows.

    Splits the opening basmala off verse 1 for suras 2-114 except 9. Detection is
    verse-1-only (so the basmala phrase appearing mid-verse in 27:30 is never
    touched) and uses sura 1's own basmala (``basmala_ref``) as the reference, so
    it is edition-agnostic and depends on no ``normalize`` module.

    The reference's first token (``bismi``) is matched *loosely* — only the trailing
    three tokens (``Allah ar-Rahman ar-Rahim``) must match exactly — because the
    Uthmani edition spells the first word with a shadda variant (``بِّسْمِ`` vs
    ``بِسْمِ``) in suras 95 and 97. The first token is still stored verbatim. This is
    safe for this corpus: every sura except 9 opens with the basmala, so a verse-1
    prefix of ``<bismi-variant> Allah ar-Rahman ar-Rahim`` is unambiguously a basmala.
    """
    basmala_tokens = basmala_ref.split()
    basmala_len = len(basmala_tokens)
    ref_tail = basmala_tokens[1:]  # stable across spelling variants

    separated_basmala: tuple[Word, ...] | None = None
    ayas: list[Aya] = []
    for sura_no, aya_no, text in rows:
        tokens = text.split()
        if (
            aya_no == 1
            and number not in (1, 9)
            and len(tokens) > basmala_len
            and tokens[1:basmala_len] == ref_tail
        ):
            separated_basmala = tuple(
                Word(tok, number, BASMALA_AYA, i) for i, tok in enumerate(tokens[:basmala_len])
            )
            tokens = tokens[basmala_len:]
        words = tuple(Word(tok, number, aya_no, i) for i, tok in enumerate(tokens))
        ayas.append(Aya(sura=sura_no, number=aya_no, words=words))
    return Sura(number=number, ayas=tuple(ayas), separated_basmala=separated_basmala)


def _validate(suras: tuple[Sura, ...]) -> None:
    """Fail fast on structural drift: contiguous suras 1..N and ayas 1..k each."""
    numbers = [s.number for s in suras]
    if numbers != list(range(1, len(suras) + 1)):
        raise ValueError(f"sura numbers not contiguous 1..N: {numbers}")
    for s in suras:
        expected = list(range(1, len(s.ayas) + 1))
        actual = [a.number for a in s.ayas]
        if actual != expected:
            raise ValueError(f"sura {s.number} aya numbers not contiguous 1..k: {actual}")


def load_corpus(edition: str, *, data_dir: Path = DATA_DIR) -> Corpus:
    """Load a vendored Tanzil edition into an immutable :class:`Corpus`.

    Args:
        edition: One of ``"uthmani"`` or ``"simple-clean"``.
        data_dir: Directory holding the vendored ``tanzil-*.txt`` files; override
            to point at a synthetic fixture (used by later tasks' tests).

    Returns:
        The parsed, validated corpus.

    Raises:
        ValueError: If the edition is unknown or the file is structurally invalid.
    """
    try:
        filename = _EDITION_FILES[edition]
    except KeyError:
        raise ValueError(
            f"unknown edition {edition!r}; expected one of {sorted(_EDITION_FILES)}"
        ) from None

    raw = (data_dir / filename).read_text(encoding="utf-8-sig")
    records = _parse_lines(raw)

    # Capture this edition's own basmala (aya 1:1) as the split reference.
    basmala_ref = next((text for sura, aya, text in records if sura == 1 and aya == 1), None)
    if basmala_ref is None:
        raise ValueError("corpus missing aya 1:1 (cannot determine basmala reference)")

    # Group rows by sura, preserving file order.
    grouped: dict[int, list[tuple[int, int, str]]] = {}
    order: list[int] = []
    for sura, aya, text in records:
        if sura not in grouped:
            grouped[sura] = []
            order.append(sura)
        grouped[sura].append((sura, aya, text))

    suras = tuple(_build_sura(n, grouped[n], basmala_ref) for n in order)
    _validate(suras)
    return Corpus(edition=edition, suras=suras)


def load_uthmani(*, data_dir: Path = DATA_DIR) -> Corpus:
    """Load the Tanzil Uthmani edition (primary)."""
    return load_corpus("uthmani", data_dir=data_dir)


def load_simple_clean(*, data_dir: Path = DATA_DIR) -> Corpus:
    """Load the Tanzil Simple-Clean edition (secondary)."""
    return load_corpus("simple-clean", data_dir=data_dir)
