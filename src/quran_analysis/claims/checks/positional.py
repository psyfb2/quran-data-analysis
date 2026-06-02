"""Check for the positional / first-occurrence claim.

The asserted value is a ``"sura:aya"`` string (per ``agentdocs/claims-schema.md``)
parsed to a ``(sura, aya)`` tuple for comparison against
:func:`~quran_analysis.primitives.first_occurrence_position`.
"""

from __future__ import annotations

from quran_analysis.claims.registry import CheckContext, Measurement, check
from quran_analysis.claims.schema import Claim
from quran_analysis.primitives import first_occurrence_position


def _parse_pos(value: int | str) -> tuple[int, int]:
    """Parse a ``"sura:aya"`` asserted value into a ``(sura, aya)`` tuple."""
    sura, aya = str(value).split(":")
    return (int(sura), int(aya))


@check("allah-first-occurrence-1-1")
def allah_first_occurrence_1_1(claim: Claim, ctx: CheckContext) -> Measurement:
    measured = first_occurrence_position(ctx.corpus("simple-clean"), "الله")
    return Measurement(measured, measured == _parse_pos(claim.asserted_value))
