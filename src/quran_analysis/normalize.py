"""Text-normalisation utilities (pure, side-effect-free string functions).

These are the load-bearing leaf primitives of the project: every downstream count
or verdict is only meaningful *relative to* the normalisation choices made here.
Each choice is documented in ``agentdocs/normalisation.md``.

Design constraints (see the Task 3 plan):

* Pure standard library only (``re`` / ``str.translate``); no third-party deps.
* Leaf module — imports no :mod:`quran_analysis.corpus`. The corpus stores the
  original Arabic verbatim (with diacritics); these functions do the stripping.
* Each function is single-responsibility and composable; :func:`normalize` wires the
  canonical pipeline so callers (Task 4 primitives) have one obvious entry point.

The exact codepoints removed/mapped below were grounded empirically against the
vendored ``data/tanzil-uthmani.txt`` and ``data/tanzil-simple-clean.txt`` editions:
the Arabic annotation signs ``U+0610``–``U+061A`` were checked and are *absent* from
both editions, so they are intentionally not in the deletion set.
"""

from __future__ import annotations

# --- Tashkeel / annotation marks to delete --------------------------------------
# Combining marks carry no lexical identity for surface-form counting and differ
# between the Uthmani (heavily annotated) and Simple-Clean editions, so stripping
# them is essential for cross-edition form comparability.
_TASHKEEL_CODEPOINTS: frozenset[int] = frozenset(
    [
        *range(0x064B, 0x0660),  # harakat & tanwin: fathatan..U+065F (incl. shadda,
        #                          sukun, maddah-above U+0653, hamza-above U+0654)
        0x0670,  # superscript (dagger) alef — treated as a diacritic and removed
        *range(0x06D6, 0x06DD),  # Quranic annotation small high marks (..small high seen)
        *range(0x06DF, 0x06E9),  # small high rounded zero .. small high noon
        *range(0x06EA, 0x06EE),  # empty-centre stops .. small low meem
    ]
)
_TASHKEEL_DELETE: dict[int, None] = dict.fromkeys(_TASHKEEL_CODEPOINTS)

# --- Tatweel (kashida) ----------------------------------------------------------
_TATWEEL: int = 0x0640  # ARABIC TATWEEL — purely cosmetic elongation, no meaning
_TATWEEL_DELETE: dict[int, None] = {_TATWEEL: None}

# --- Hamza / alif normalisation -------------------------------------------------
# Map alef and hamza-carrier variants to their bare base letter so orthographic
# variants of the same word compare equal. Standalone hamza U+0621 is KEPT.
_HAMZA_MAP: dict[int, int] = {
    0x0623: 0x0627,  # ALEF WITH HAMZA ABOVE  -> ALEF
    0x0625: 0x0627,  # ALEF WITH HAMZA BELOW  -> ALEF
    0x0622: 0x0627,  # ALEF WITH MADDA ABOVE  -> ALEF
    0x0671: 0x0627,  # ALEF WASLA             -> ALEF
    0x0624: 0x0648,  # WAW WITH HAMZA ABOVE   -> WAW
    0x0626: 0x064A,  # YEH WITH HAMZA ABOVE   -> YEH
}

# --- Final-form normalisation (opt-in; NOT in the canonical pipeline) ------------
# These materially change counts, so they are exposed as a separate named function
# that per-claim operational definitions (Task 6) cite explicitly when wanted.
_FINAL_FORMS_MAP: dict[int, int] = {
    0x0649: 0x064A,  # ALEF MAKSURA -> YEH
    0x0629: 0x0647,  # TEH MARBUTA  -> HEH
}


def strip_tashkeel(text: str) -> str:
    """Remove Arabic diacritics (harakat/tanwin) and Quranic annotation marks.

    Deletes the combining marks in ``U+064B``-``U+065F``, the superscript (dagger)
    alef ``U+0670``, and the Quranic annotation signs (``U+06D6``-``U+06DC``,
    ``U+06DF``-``U+06E8``, ``U+06EA``-``U+06ED``). Base letters are left untouched.

    Args:
        text: Arabic text, possibly fully vowelled / annotated.

    Returns:
        The text with all diacritic and annotation marks removed.
    """
    return text.translate(_TASHKEEL_DELETE)


def remove_tatweel(text: str) -> str:
    """Remove the tatweel/kashida (``U+0640``), a cosmetic elongation character.

    Args:
        text: Arabic text possibly containing tatweel.

    Returns:
        The text with every tatweel character deleted.
    """
    return text.translate(_TATWEEL_DELETE)


def normalize_hamza(text: str) -> str:
    """Normalise alef and hamza-carrier variants to their bare base letters.

    Maps ``أ``/``إ``/``آ``/``ٱ`` -> ``ا``, ``ؤ`` -> ``و`` and ``ئ`` -> ``ي``. The
    standalone hamza ``ء`` (``U+0621``) is intentionally kept as-is, and alef-maksura
    / teh-marbuta are left untouched (see :func:`normalize_final_forms`).

    Args:
        text: Arabic text.

    Returns:
        The text with alef/hamza-carrier variants folded to their base letters.
    """
    return text.translate(_HAMZA_MAP)


def normalize_final_forms(text: str) -> str:
    """Fold word-final letter variants: ``ى`` -> ``ي`` and ``ة`` -> ``ه``.

    This is an **opt-in** transform, deliberately excluded from the canonical
    :func:`normalize` pipeline because it materially changes counts; per-claim
    operational definitions (Task 6) cite it explicitly when desired.

    Args:
        text: Arabic text.

    Returns:
        The text with alef-maksura mapped to yeh and teh-marbuta mapped to heh.
    """
    return text.translate(_FINAL_FORMS_MAP)


def tokenize(text: str) -> list[str]:
    """Split text into whitespace-delimited tokens.

    Uses :meth:`str.split` semantics: runs of any Unicode whitespace are collapsed
    and leading/trailing whitespace is trimmed, so empty or whitespace-only input
    yields ``[]``. No normalisation is applied here — compose with the other
    functions (e.g. ``tokenize(normalize(text))``) when needed.

    Args:
        text: Arabic text.

    Returns:
        The list of non-empty whitespace-delimited tokens.
    """
    return text.split()


def normalize(text: str) -> str:
    """Apply the canonical normalisation pipeline for surface-form comparison.

    Fixed order: :func:`remove_tatweel` -> :func:`strip_tashkeel` ->
    :func:`normalize_hamza`. Tatweel and marks are removed before letter-mapping.
    Final-form folding (:func:`normalize_final_forms`) is **not** part of this
    pipeline. This is the single "normalised surface form" entry point used by the
    Task 4 counting primitives.

    Args:
        text: Arabic text.

    Returns:
        The canonically normalised text.
    """
    return normalize_hamza(strip_tashkeel(remove_tatweel(text)))
