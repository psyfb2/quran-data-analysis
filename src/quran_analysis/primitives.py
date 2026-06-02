"""Claim-agnostic counting & analysis primitives over the corpus model.

These deterministic measurement functions operate on the immutable
:class:`~quran_analysis.corpus.Corpus` model (Task 2) and reuse the
normalisation utilities (Task 3). No claim-specific logic lives here — each
primitive returns a plain number/structure that the claim-runner (Task 8)
composes per a claim's operational definition.

**Every count is meaningful only relative to two documented conventions:**

1. The canonical normalisation pipeline (:func:`quran_analysis.normalize.normalize`)
   applied to both the corpus surface forms and the query. Callers may override
   it via the ``normalizer`` parameter (e.g. to opt into final-form folding) so
   primitives stay open/closed without baking in claim logic.
2. The abjad (gematria) table below — standard *Mashriqi* values, applied after
   normalisation. See ``agentdocs/normalisation.md`` for the full rationale.

The basmala-inclusion choice exposed by the loader
(:meth:`Corpus.words(include_basmala=...) <quran_analysis.corpus.Corpus.words>`)
is threaded through every corpus-scanning primitive. ``include_basmala`` only
toggles the *separated* basmalas (suras 2-114 except 9); sura 1's basmala is a
numbered verse and is never double-counted.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable

from quran_analysis.corpus import Corpus
from quran_analysis.normalize import normalize

#: Standard Mashriqi abjad (gematria) values, applied **after** normalisation.
#:
#: ``normalize()`` folds tatweel/tashkeel and alef/hamza-carrier variants, but it
#: does **not** fold the standalone hamza ``ء``, alef-maksura ``ى`` or teh-marbuta
#: ``ة`` — these are mapped here directly so :func:`abjad_value` is well-defined
#: without forcing :func:`~quran_analysis.normalize.normalize_final_forms`:
#:
#: * ``ء`` (U+0621) -> 1 (hamza takes the alef value, the common convention)
#: * ``ى`` (U+0649) -> 10 (as yeh)
#: * ``ة`` (U+0629) -> 5 (as heh)
#:
#: Any character absent from this table contributes 0.
_ABJAD_VALUES: dict[str, int] = {
    "ا": 1,
    "ب": 2,
    "ج": 3,
    "د": 4,
    "ه": 5,
    "و": 6,
    "ز": 7,
    "ح": 8,
    "ط": 9,
    "ي": 10,
    "ك": 20,
    "ل": 30,
    "م": 40,
    "ن": 50,
    "س": 60,
    "ع": 70,
    "ف": 80,
    "ص": 90,
    "ق": 100,
    "ر": 200,
    "ش": 300,
    "ت": 400,
    "ث": 500,
    "خ": 600,
    "ذ": 700,
    "ض": 800,
    "ظ": 900,
    "غ": 1000,
    # Forms normalize() does not fold (documented above):
    "ء": 1,  # standalone hamza
    "ى": 10,  # alef-maksura -> yeh value
    "ة": 5,  # teh-marbuta  -> heh value
}


def count_by_form(
    corpus: Corpus,
    form: str,
    *,
    include_basmala: bool = False,
    normalizer: Callable[[str], str] = normalize,
) -> int:
    """Count words whose normalised surface form exactly equals ``form``.

    Both the corpus word and ``form`` are passed through ``normalizer`` (the
    canonical :func:`~quran_analysis.normalize.normalize` by default) so a
    vowelled Uthmani form matches its bare Simple-Clean spelling.

    Args:
        corpus: The corpus to scan.
        form: The query surface form (un-normalised; normalised internally).
        include_basmala: Whether to include separated basmala words.
        normalizer: Surface-form normaliser applied to both sides.

    Returns:
        The number of words equal to the normalised ``form``; ``0`` if ``form``
        is empty/whitespace-only or after normalisation reduces to empty.
    """
    target = normalizer(form)
    if not target:
        return 0
    return sum(
        1 for w in corpus.words(include_basmala=include_basmala) if normalizer(w.text) == target
    )


def count_by_substring(
    corpus: Corpus,
    substring: str,
    *,
    include_basmala: bool = False,
    normalizer: Callable[[str], str] = normalize,
) -> int:
    """Count non-overlapping occurrences of ``substring`` within corpus words.

    Matching is **intra-word**: occurrences never span token boundaries (that
    would depend on the single-space join artifact and be ambiguous). Both the
    corpus words and ``substring`` are normalised first. Uses :meth:`str.count`
    (non-overlapping) semantics.

    Args:
        corpus: The corpus to scan.
        substring: The query substring (un-normalised; normalised internally).
        include_basmala: Whether to include separated basmala words.
        normalizer: Surface-form normaliser applied to both sides.

    Returns:
        The total non-overlapping occurrences across all words; ``0`` if
        ``substring`` is empty (guarding ``"".count`` degenerate behaviour).
    """
    needle = normalizer(substring)
    if not needle:
        return 0
    return sum(
        normalizer(w.text).count(needle) for w in corpus.words(include_basmala=include_basmala)
    )


def letter_frequency(
    corpus: Corpus,
    *,
    include_basmala: bool = False,
    normalizer: Callable[[str], str] = normalize,
) -> dict[str, int]:
    """Count characters across all normalised corpus words.

    Counts the characters of each word's normalised surface form (so diacritics
    and tatweel are already removed — the load-bearing choice). Returns a plain
    ``dict`` (insertion-ordered by first appearance via :class:`Counter`).

    Args:
        corpus: The corpus to scan.
        include_basmala: Whether to include separated basmala words.
        normalizer: Surface-form normaliser applied to each word.

    Returns:
        A mapping from character to its total occurrence count; ``{}`` for an
        empty corpus.
    """
    counter: Counter[str] = Counter()
    for w in corpus.words(include_basmala=include_basmala):
        counter.update(normalizer(w.text))
    return dict(counter)


def first_occurrence_position(
    corpus: Corpus,
    form: str,
    *,
    include_basmala: bool = False,
    normalizer: Callable[[str], str] = normalize,
) -> tuple[int, int] | None:
    """Return the ``(sura, aya)`` of the first word equal to the normalised ``form``.

    Scans words in canonical order. For a separated basmala word the aya is
    :data:`~quran_analysis.corpus.BASMALA_AYA` (0) — only reachable when
    ``include_basmala=True``.

    Args:
        corpus: The corpus to scan.
        form: The query surface form (un-normalised; normalised internally).
        include_basmala: Whether to include separated basmala words.
        normalizer: Surface-form normaliser applied to both sides.

    Returns:
        The ``(sura, aya)`` of the first match, or ``None`` if ``form`` is empty
        or never occurs.
    """
    target = normalizer(form)
    if not target:
        return None
    for w in corpus.words(include_basmala=include_basmala):
        if normalizer(w.text) == target:
            return (w.sura, w.aya)
    return None


def abjad_value(text: str, *, normalizer: Callable[[str], str] = normalize) -> int:
    """Compute the abjad (gematria) value of ``text``.

    The text is normalised first (so callers cannot accidentally feed
    tashkeel/tatweel), then each character is summed using :data:`_ABJAD_VALUES`
    (standard Mashriqi). Characters absent from the table (including spaces)
    contribute ``0``.

    Args:
        text: The string to evaluate.
        normalizer: Surface-form normaliser applied before summation.

    Returns:
        The total abjad value; ``0`` for empty input.
    """
    return sum(_ABJAD_VALUES.get(ch, 0) for ch in normalizer(text))
