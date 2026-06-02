"""Checks for abjad (gematria) claims.

Both are edition-independent: they operate on literal strings via
:func:`~quran_analysis.primitives.abjad_value` and never touch the corpus.
"""

from __future__ import annotations

from quran_analysis.claims.registry import CheckContext, Measurement, check
from quran_analysis.claims.schema import Claim
from quran_analysis.primitives import abjad_value


@check("abjad-allah-66")
def abjad_allah_66(claim: Claim, ctx: CheckContext) -> Measurement:
    measured = abjad_value("الله")
    return Measurement(measured, measured == claim.asserted_value)


@check("abjad-basmala-786")
def abjad_basmala_786(claim: Claim, ctx: CheckContext) -> Measurement:
    measured = abjad_value("بسم الله الرحمن الرحيم")
    return Measurement(measured, measured == claim.asserted_value)
