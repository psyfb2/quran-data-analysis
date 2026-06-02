"""Checks for "constant" claims — a count asserted to equal a calendar /
cosmological number (day=365, month=12, days=30, seven, dunya=115).

Each check encodes the executable form of its claim's ``operational_definition``.
The asserted figure is read from ``claim.asserted_value`` (DRY — ``claims.yaml``
stays the single source for the asserted number).
"""

from __future__ import annotations

from quran_analysis.claims.registry import CheckContext, Measurement, check
from quran_analysis.claims.schema import Claim
from quran_analysis.morphology import count_by_lemma
from quran_analysis.primitives import count_by_form


@check("yawm-singular-365")
def yawm_singular_365(claim: Claim, ctx: CheckContext) -> Measurement:
    # Singular-noun lemma count; QAC lemmatises singular يوم under lemma "yawom"
    # (root ywm). Note: QAC merges singular + plural under the same lemma "yawom",
    # so this measures 405 and honestly mismatches the asserted 365.
    m = ctx.morphology
    if m is None:  # unreachable in practice (runner guards) — keeps mypy happy.
        return Measurement(None, False)
    measured = count_by_lemma(m, "yawom")
    return Measurement(measured, measured == claim.asserted_value)


@check("shahr-month-12")
def shahr_month_12(claim: Claim, ctx: CheckContext) -> Measurement:
    m = ctx.morphology
    if m is None:
        return Measurement(None, False)
    measured = count_by_lemma(m, "$ahor")
    return Measurement(measured, measured == claim.asserted_value)


@check("ayyam-days-30")
def ayyam_days_30(claim: Claim, ctx: CheckContext) -> Measurement:
    # QAC has no distinct plural lemma — both singular يوم and plural أيام share
    # lemma "yawom" — so this measures 405 and mismatches the asserted 30.
    m = ctx.morphology
    if m is None:
        return Measurement(None, False)
    measured = count_by_lemma(m, "yawom")
    return Measurement(measured, measured == claim.asserted_value)


@check("sab-seven-heavens")
def sab_seven_heavens(claim: Claim, ctx: CheckContext) -> Measurement:
    # Exact surface form per the op-def (the claim carries an ambiguity_note, so
    # the runner resolves it to ambiguous regardless of this match flag).
    measured = count_by_form(ctx.corpus("simple-clean"), "سبع")
    return Measurement(measured, measured == claim.asserted_value)


@check("dunya-115")
def dunya_115(claim: Claim, ctx: CheckContext) -> Measurement:
    measured = count_by_form(ctx.corpus("simple-clean"), "الدنيا")
    return Measurement(measured, measured == claim.asserted_value)
