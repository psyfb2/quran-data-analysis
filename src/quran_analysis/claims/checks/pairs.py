"""Checks for pair-equality claims ("X occurs as often as its opposite").

Each measures a ``(count1, count2)`` tuple and is satisfied iff the two counts
are equal. The tuple is kept as the measured value so the Task-9 report can show
"115 vs 71". The asserted value for these claims is the symbolic string
``"equal"`` (the equality is the assertion); ``bahr-barr-water-ratio`` instead
asserts the integer sea-count and measures a single root count.
"""

from __future__ import annotations

from quran_analysis.claims.registry import CheckContext, Measurement, check
from quran_analysis.claims.schema import Claim
from quran_analysis.morphology import count_by_lemma, count_by_root
from quran_analysis.primitives import count_by_form


@check("dunya-akhira-equal")
def dunya_akhira_equal(claim: Claim, ctx: CheckContext) -> Measurement:
    corpus = ctx.corpus("simple-clean")
    dunya = count_by_form(corpus, "الدنيا")
    akhira = count_by_form(corpus, "الآخرة")
    return Measurement((dunya, akhira), dunya == akhira)


@check("hayat-mawt-equal")
def hayat_mawt_equal(claim: Claim, ctx: CheckContext) -> Measurement:
    m = ctx.morphology
    if m is None:  # unreachable in practice (runner guards) — keeps mypy happy.
        return Measurement(None, False)
    life = count_by_lemma(m, "Hayaw`p")
    death = count_by_lemma(m, "mawot")
    return Measurement((life, death), life == death)


@check("malaika-shayatin-equal")
def malaika_shayatin_equal(claim: Claim, ctx: CheckContext) -> Measurement:
    m = ctx.morphology
    if m is None:
        return Measurement(None, False)
    angels = count_by_lemma(m, "malak")
    devils = count_by_lemma(m, "$ayoTa`n")
    return Measurement((angels, devils), angels == devils)


@check("rajul-imraa-equal")
def rajul_imraa_equal(claim: Claim, ctx: CheckContext) -> Measurement:
    m = ctx.morphology
    if m is None:
        return Measurement(None, False)
    man = count_by_lemma(m, "rajul")
    woman = count_by_lemma(m, "{mora>at")
    return Measurement((man, woman), man == woman)


@check("bahr-barr-water-ratio")
def bahr_barr_water_ratio(claim: Claim, ctx: CheckContext) -> Measurement:
    # The asserted figure is the sea (bahr) root count (32). The claim carries an
    # ambiguity_note, so the runner resolves it to ambiguous regardless.
    m = ctx.morphology
    if m is None:
        return Measurement(None, False)
    measured = count_by_root(m, "bHr")
    return Measurement(measured, measured == claim.asserted_value)
