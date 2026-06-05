"""Quranic Arabic Corpus (QAC) morphology ingestion & root/lemma primitives.

Parses the vendored QAC morphology edition
(``data/quranic-corpus-morphology-0.4.txt``) into an immutable
``Morphology -> MorphologyWord`` model keyed by ``(sura, aya, word)``, and
provides claim-agnostic ``count_by_root`` / ``count_by_lemma`` primitives.

This module sits **parallel** to :mod:`quran_analysis.corpus`: QAC is a separate
dataset with its own location scheme, so keeping it out of ``corpus.py`` /
``primitives.py`` preserves the clean one-way layering (the Corpus primitives
stay Corpus-only).

Why this exists: the populated claims register (``claims.yaml``) flags several
claims (e.g. day=365, month=12) whose canonical figure is a *singular-noun
lemma* or *root* count rather than a surface-form count, so morphological
(root/lemma) analysis is genuinely required to test them.

Key format facts (re-derived empirically from the vendored v0.4 file):

* The file opens with a ``#`` comment preamble (QAC + Tanzil copyright blocks)
  followed by a single TAB-separated column header line
  ``LOCATION\\tFORM\\tTAG\\tFEATURES``; data rows follow.
* Each data row is one *segment*: ``(sura:aya:word:segment)\\tFORM\\tTAG\\tFEATURES``.
  ``LOCATION`` is 1-based and parenthesised. ``FEATURES`` is ``|``-delimited;
  the **stem** segment carries ``ROOT:`` / ``LEM:`` / ``POS:`` features
  (Buckwalter-encoded ASCII), while prefixes/suffixes do not.
* One *word* ``(sura, aya, word)`` aggregates its multiple segments into a single
  :class:`MorphologyWord`; root/lemma/pos come from the stem segment (a word has
  at most one). Function words (particles) have no stem root/lemma -> ``None``.
* QAC's sura-1 basmala **is** word-positions of aya ``1:1`` (a counted verse);
  suras 2-114 do **not** repeat the opening basmala as words (verified: ``2:1``
  begins with the muqatta'at). This matches the morphology claims' "separated
  basmalas excluded" operational definition.
* Root/lemma are stored as the **raw QAC Buckwalter strings** (lossless,
  deterministic). See ``agentdocs/morphology.md`` for the per-claim Buckwalter
  code table that the claim-runner (Task 8) uses.

See ``agentdocs/morphology.md`` for dataset version, license/attribution, the
license-mixing note, and the per-claim root/lemma codes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# Repo-root ``data/`` directory. Mirrors :data:`quran_analysis.corpus.DATA_DIR`.
DATA_DIR: Path = Path(__file__).resolve().parents[2] / "data"

#: Vendored QAC morphology filename (version 0.4).
MORPHOLOGY_FILE: str = "quranic-corpus-morphology-0.4.txt"

# Feature-key prefixes within the ``|``-delimited FEATURES column.
_ROOT_PREFIX = "ROOT:"
_LEMMA_PREFIX = "LEM:"
_POS_PREFIX = "POS:"


@dataclass(frozen=True)
class MorphologyWord:
    """A single Quran word with its aggregated morphological annotation.

    A QAC *word* spans one or more segments (prefix / stem / suffix); this model
    collapses them to one record, taking root/lemma/pos from the stem segment.

    Attributes:
        sura: 1-based sura number.
        aya: 1-based aya number.
        word: 1-based word index within the aya.
        form: Buckwalter surface form of the stem segment (verbatim from QAC).
        root: Buckwalter root string of the stem, or ``None`` (e.g. particles).
        lemma: Buckwalter lemma string of the stem, or ``None``.
        pos: Part-of-speech tag of the stem (``POS:`` feature), or ``None``.
    """

    sura: int
    aya: int
    word: int
    form: str
    root: str | None
    lemma: str | None
    pos: str | None


@dataclass(frozen=True)
class Morphology:
    """An immutable QAC morphology edition: one record per ``(sura, aya, word)``.

    Attributes:
        words: Ordered tuple of all :class:`MorphologyWord`, in file order.
    """

    words: tuple[MorphologyWord, ...]

    def word(self, sura: int, aya: int, word: int) -> MorphologyWord:
        """Return the morphology record keyed by ``(sura, aya, word)``.

        Raises:
            KeyError: If no word has that ``(sura, aya, word)`` key.
        """
        for w in self.words:
            if w.sura == sura and w.aya == aya and w.word == word:
                return w
        raise KeyError(f"morphology word {sura}:{aya}:{word} not found")


def _parse_location(location: str) -> tuple[int, int, int, int]:
    """Parse a ``(sura:aya:word:segment)`` location into its four 1-based ints."""
    inner = location.strip().strip("()")
    parts = inner.split(":")
    if len(parts) != 4:
        raise ValueError(f"malformed QAC location (expected 4 parts): {location!r}")
    sura, aya, word, segment = (int(p) for p in parts)
    return sura, aya, word, segment


def _parse_features(features: str) -> tuple[str | None, str | None, str | None]:
    """Extract ``(root, lemma, pos)`` from a ``|``-delimited FEATURES string.

    Returns ``None`` for any feature the segment does not carry (prefixes and
    suffixes carry no ``ROOT:`` / ``LEM:`` / ``POS:``).
    """
    root: str | None = None
    lemma: str | None = None
    pos: str | None = None
    for feature in features.split("|"):
        if feature.startswith(_ROOT_PREFIX):
            root = feature[len(_ROOT_PREFIX) :]
        elif feature.startswith(_LEMMA_PREFIX):
            lemma = feature[len(_LEMMA_PREFIX) :]
        elif feature.startswith(_POS_PREFIX):
            pos = feature[len(_POS_PREFIX) :]
    return root, lemma, pos


def _build_words(
    segments: list[tuple[tuple[int, int, int, int], str, str]],
) -> tuple[MorphologyWord, ...]:
    """Aggregate ordered ``(location, form, features)`` segments into words.

    Segments sharing a ``(sura, aya, word)`` key are collapsed into one
    :class:`MorphologyWord`. Root/lemma/pos and the stored ``form`` are taken
    from the **stem** segment — i.e. the first segment carrying any of
    ``ROOT:`` / ``LEM:`` / ``POS:``. Words with no such segment (rare pure
    function words) keep ``root``/``lemma``/``pos`` as ``None`` and store the
    first segment's form.
    """
    words: list[MorphologyWord] = []
    current_key: tuple[int, int, int] | None = None
    first_form: str = ""
    stem_form: str | None = None
    stem_root: str | None = None
    stem_lemma: str | None = None
    stem_pos: str | None = None

    def flush() -> None:
        nonlocal current_key
        if current_key is None:
            return
        sura, aya, word = current_key
        words.append(
            MorphologyWord(
                sura=sura,
                aya=aya,
                word=word,
                form=stem_form if stem_form is not None else first_form,
                root=stem_root,
                lemma=stem_lemma,
                pos=stem_pos,
            )
        )

    for (sura, aya, word, _segment), form, features in segments:
        key = (sura, aya, word)
        if key != current_key:
            flush()
            current_key = key
            first_form = form
            stem_form = None
            stem_root = None
            stem_lemma = None
            stem_pos = None
        root, lemma, pos = _parse_features(features)
        if (root is not None or lemma is not None or pos is not None) and stem_form is None:
            # First segment carrying morphological features is the stem.
            stem_form = form
            stem_root = root
            stem_lemma = lemma
            stem_pos = pos

    flush()
    return tuple(words)


def _validate(words: tuple[MorphologyWord, ...]) -> None:
    """Fail fast on parse/dataset drift.

    Guards that are *edition-independent* and shared with :mod:`corpus`:
    distinct suras must be exactly ``{1..114}`` and the number of distinct
    ``(sura, aya)`` pairs must equal ``6236``. (Word-index contiguity is **not**
    asserted: QAC omits some word positions, so a 1..k check would falsely fail.)
    """
    suras = {w.sura for w in words}
    if suras != set(range(1, 115)):
        raise ValueError(f"morphology suras not exactly 1..114: got {len(suras)} distinct suras")
    aya_pairs = {(w.sura, w.aya) for w in words}
    if len(aya_pairs) != 6236:
        raise ValueError(f"morphology (sura, aya) pairs != 6236: got {len(aya_pairs)}")


def _read_segments(raw: str) -> list[tuple[tuple[int, int, int, int], str, str]]:
    """Parse the raw file text into ordered ``(location, form, features)`` segments.

    Skips the ``#`` comment preamble/footer, blank lines, and the
    ``LOCATION\\tFORM\\tTAG\\tFEATURES`` column header (any line not starting with
    ``(``). Raises ``ValueError`` on a malformed data row.
    """
    segments: list[tuple[tuple[int, int, int, int], str, str]] = []
    for line in raw.splitlines():
        # Skip the comment preamble/footer, blank lines, and the column header
        # (data rows start with a parenthesised location).
        if not line or line.startswith("#") or not line.startswith("("):
            continue
        parts = line.split("\t")
        if len(parts) < 4:
            raise ValueError(f"malformed QAC data line (expected 4 tab columns): {line!r}")
        location, form, _tag, features = parts[0], parts[1], parts[2], parts[3]
        segments.append((_parse_location(location), form, features))
    return segments


def load_morphology(*, data_dir: Path = DATA_DIR) -> Morphology:
    """Load the vendored QAC morphology edition into an immutable :class:`Morphology`.

    Args:
        data_dir: Directory holding the vendored morphology file; override to
            point at a synthetic fixture (used by tests, mirroring
            :func:`quran_analysis.corpus.load_corpus`).

    Returns:
        The parsed, validated morphology.

    Raises:
        ValueError: If a data line is malformed or the dataset is structurally
            invalid (see :func:`_validate`).
    """
    raw = (data_dir / MORPHOLOGY_FILE).read_text(encoding="utf-8-sig")
    words = _build_words(_read_segments(raw))
    _validate(words)
    return Morphology(words=words)


def count_by_root(morphology: Morphology, root: str) -> int:
    """Count words whose stem root equals ``root`` (exact Buckwalter match).

    Args:
        morphology: The loaded morphology.
        root: Buckwalter root string (e.g. ``"ywm"`` for day). Empty or
            whitespace-only queries return ``0``.

    Returns:
        The number of :class:`MorphologyWord` with that stem root. Words with
        ``root is None`` never match.
    """
    if not root.strip():
        return 0
    return sum(1 for w in morphology.words if w.root == root)


def count_by_lemma(morphology: Morphology, lemma: str) -> int:
    """Count words whose stem lemma equals ``lemma`` (exact Buckwalter match).

    Args:
        morphology: The loaded morphology.
        lemma: Buckwalter lemma string (e.g. ``"yawom"`` for the singular
            "day"). Empty or whitespace-only queries return ``0``.

    Returns:
        The number of :class:`MorphologyWord` with that stem lemma. Words with
        ``lemma is None`` never match.
    """
    if not lemma.strip():
        return 0
    return sum(1 for w in morphology.words if w.lemma == lemma)
