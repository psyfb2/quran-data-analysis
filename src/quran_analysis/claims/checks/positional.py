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
    """Parse a ``"sura:aya"`` asserted value into a ``(sura, aya)`` tuple.

    Positional claims assert their position as the string ``"sura:aya"`` (e.g.
    ``"1:1"``) per ``agentdocs/claims-schema.md``. A bare int has no aya part and
    is rejected with a clear error rather than failing cryptically on unpack.
    """
    parts = str(value).split(":")
    if len(parts) != 2:
        raise ValueError(f'positional asserted_value must be "sura:aya", got {value!r}')
    sura, aya = parts
    return (int(sura), int(aya))


@check("allah-first-occurrence-1-1")
def allah_first_occurrence_1_1(claim: Claim, ctx: CheckContext) -> Measurement:
    measured = first_occurrence_position(ctx.corpus("simple-clean"), "الله")
    matched = measured == _parse_pos(claim.asserted_value)
    # Report the measured position in the same "sura:aya" notation as the asserted
    # value (rather than the raw tuple, which the report would render as "a vs b").
    rendered = f"{measured[0]}:{measured[1]}" if measured is not None else None
    return Measurement(rendered, matched)
