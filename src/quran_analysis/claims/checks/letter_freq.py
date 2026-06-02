"""Checks for letter-frequency / muqatta'at claims and the basmala-19 claim.

Per-sura letter frequency is **not** a primitive; it is derived by reusing
:func:`~quran_analysis.primitives.letter_frequency` over a single-sura sub-corpus
(DRY — no new primitive). ``basmala-19-letters`` is edition-independent: it
operates on a literal string via :func:`~quran_analysis.normalize.normalize`.
"""

from __future__ import annotations

from quran_analysis.claims.registry import CheckContext, Measurement, check
from quran_analysis.claims.schema import Claim
from quran_analysis.corpus import Corpus
from quran_analysis.normalize import normalize
from quran_analysis.primitives import letter_frequency

_BASMALA = "بسم الله الرحمن الرحيم"


def _sura_letter_freq(corpus: Corpus, sura: int) -> dict[str, int]:
    """Letter frequency over a single sura (separated basmala excluded)."""
    sub = Corpus(edition=corpus.edition, suras=(corpus.sura(sura),))
    return letter_frequency(sub)


@check("qaf-surah50-frequency")
def qaf_surah50_frequency(claim: Claim, ctx: CheckContext) -> Measurement:
    measured = _sura_letter_freq(ctx.corpus("simple-clean"), 50).get("ق", 0)
    return Measurement(measured, measured == claim.asserted_value)


@check("noon-surah68-frequency")
def noon_surah68_frequency(claim: Claim, ctx: CheckContext) -> Measurement:
    # Carries an ambiguity_note (spelled-out نون vs single-symbol convention) so
    # the runner resolves it to ambiguous regardless of this match flag.
    measured = _sura_letter_freq(ctx.corpus("simple-clean"), 68).get("ن", 0)
    return Measurement(measured, measured == claim.asserted_value)


@check("basmala-19-letters")
def basmala_19_letters(claim: Claim, ctx: CheckContext) -> Measurement:
    # Edition-independent: literal string, no corpus scan.
    measured = len(normalize(_BASMALA).replace(" ", ""))
    return Measurement(measured, measured == claim.asserted_value)
