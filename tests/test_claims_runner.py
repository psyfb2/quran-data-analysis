"""Tests for the claim-runner (Task 8).

Three tiers, mirroring repo conventions:

* **Synthetic verdict-path tests** (pure, offline) — the PRD's core requirement.
  A tiny synthetic corpus + synthetic register + a local ``checks`` table exercise
  every verdict path (match, mismatch, ambiguous-via-note,
  ambiguous-via-missing-morphology, ambiguous-via-missing-check) and end-to-end
  primitive composition, without touching the global registry or the full corpus.
* **Registry-coverage guard** (pure, offline) — every catalogued claim in the real
  register has a registered check, so a forgotten check fails loudly.
* **One real-corpus integration anchor** (module-scoped fixture) — runs the full
  register against the vendored corpus + morphology and asserts re-derived
  structural properties, not magic-number transcriptions.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from quran_analysis.claims.registry import CheckContext, CheckFn, Measurement, registry
from quran_analysis.claims.runner import (
    ClaimResult,
    Verdict,
    build_default_context,
    evaluate_claim,
    run_register,
)
from quran_analysis.claims.schema import Claim, ClaimsRegister, load_register
from quran_analysis.corpus import Corpus, load_corpus
from quran_analysis.primitives import count_by_form

# --- Synthetic fixtures ---------------------------------------------------------
# Bare, un-diacritised; "الله" appears in sura 1:1 (a numbered verse).
_SYNTHETIC_SIMPLE_CLEAN = """\
1|1|بسم الله الرحمن الرحيم
1|2|الحمد لله رب العالمين
2|1|ذلك الكتاب لا ريب فيه
"""


@pytest.fixture
def synthetic_corpus(tmp_path: Path) -> Corpus:
    (tmp_path / "tanzil-simple-clean.txt").write_text(_SYNTHETIC_SIMPLE_CLEAN, encoding="utf-8")
    return load_corpus("simple-clean", data_dir=tmp_path)


def _claim(claim_id: str, **overrides: object) -> Claim:
    """Build a synthetic claim with sensible defaults for runner tests."""
    fields: dict[str, object] = {
        "id": claim_id,
        "description": "synthetic test claim",
        "source": "synthetic",
        "asserted_value": 5,
        "operational_definition": "synthetic op-def",
        "expected_result": "synthetic",
    }
    fields.update(overrides)
    return Claim.model_validate(fields)


def _raising_check(claim: Claim, ctx: CheckContext) -> Measurement:
    raise AssertionError("check must not be called when morphology is missing")


# --- (A) Synthetic verdict-path tests -------------------------------------------


def test_match_path(synthetic_corpus: Corpus) -> None:
    ctx = CheckContext(corpora={"simple-clean": synthetic_corpus})
    checks: dict[str, CheckFn] = {"c-match": lambda cl, cx: Measurement(5, True)}
    result = evaluate_claim(_claim("c-match"), ctx, checks=checks)
    assert result.verdict is Verdict.MATCH
    assert result.measured == 5
    assert result.asserted == 5


def test_mismatch_path(synthetic_corpus: Corpus) -> None:
    ctx = CheckContext(corpora={"simple-clean": synthetic_corpus})
    checks: dict[str, CheckFn] = {"c-mismatch": lambda cl, cx: Measurement(3, False)}
    result = evaluate_claim(_claim("c-mismatch"), ctx, checks=checks)
    assert result.verdict is Verdict.MISMATCH
    assert result.measured == 3


def test_ambiguous_via_ambiguity_note_keeps_measured(synthetic_corpus: Corpus) -> None:
    # An ambiguity_note forces ambiguous, but the measured value is still kept.
    ctx = CheckContext(corpora={"simple-clean": synthetic_corpus})
    checks: dict[str, CheckFn] = {"c-amb": lambda cl, cx: Measurement(9, False)}
    claim = _claim("c-amb", ambiguity_note="undisclosed convention")
    result = evaluate_claim(claim, ctx, checks=checks)
    assert result.verdict is Verdict.AMBIGUOUS
    assert result.measured == 9


def test_ambiguous_via_missing_morphology_short_circuits() -> None:
    # requires_morphology + morphology=None -> ambiguous WITHOUT calling the check.
    ctx = CheckContext(corpora={}, morphology=None)
    checks: dict[str, CheckFn] = {"c-morph": _raising_check}
    claim = _claim("c-morph", requires_morphology=True)
    result = evaluate_claim(claim, ctx, checks=checks)
    assert result.verdict is Verdict.AMBIGUOUS
    assert result.measured is None


def test_ambiguous_via_missing_check() -> None:
    # A claim whose id is absent from the check table -> ambiguous, measured None.
    ctx = CheckContext(corpora={})
    result = evaluate_claim(_claim("c-unregistered"), ctx, checks={})
    assert result.verdict is Verdict.AMBIGUOUS
    assert result.measured is None


def test_check_composes_primitive_end_to_end(synthetic_corpus: Corpus) -> None:
    # A local check that actually calls a Task-4 primitive on the synthetic corpus.
    ctx = CheckContext(corpora={"simple-clean": synthetic_corpus})

    def allah_count(claim: Claim, ctx: CheckContext) -> Measurement:
        measured = count_by_form(ctx.corpus("simple-clean"), "الله")
        return Measurement(measured, measured == claim.asserted_value)

    checks: dict[str, CheckFn] = {"c-allah": allah_count}
    # "الله" occurs once (sura 1:1; separated basmala excluded by default).
    matched = evaluate_claim(_claim("c-allah", asserted_value=1), ctx, checks=checks)
    assert matched.verdict is Verdict.MATCH
    assert matched.measured == 1
    missed = evaluate_claim(_claim("c-allah", asserted_value=99), ctx, checks=checks)
    assert missed.verdict is Verdict.MISMATCH


def test_run_register_preserves_order_and_length(synthetic_corpus: Corpus) -> None:
    ctx = CheckContext(corpora={"simple-clean": synthetic_corpus})
    checks: dict[str, CheckFn] = {
        "c-a": lambda cl, cx: Measurement(5, True),
        "c-b": lambda cl, cx: Measurement(1, False),
    }
    register = ClaimsRegister(claims=[_claim("c-a"), _claim("c-b"), _claim("c-c")])
    results = run_register(register, ctx, checks=checks)
    assert [r.id for r in results] == ["c-a", "c-b", "c-c"]
    assert [r.verdict for r in results] == [
        Verdict.MATCH,
        Verdict.MISMATCH,
        Verdict.AMBIGUOUS,  # c-c has no registered check
    ]


# --- (B) Registry-coverage guard ------------------------------------------------


def test_every_catalogued_claim_has_a_registered_check() -> None:
    register = load_register()
    registered = set(registry())
    missing = {c.id for c in register.claims} - registered
    assert not missing, f"claims with no registered check: {sorted(missing)}"


# --- (C) Real-corpus integration anchor -----------------------------------------


@pytest.fixture(scope="module")
def real_results() -> list[ClaimResult]:
    ctx = build_default_context()
    return run_register(load_register(), ctx)


def test_real_register_evaluates_all_claims(real_results: list[ClaimResult]) -> None:
    register = load_register()
    assert len(real_results) == len(register.claims) == 16
    assert all(isinstance(r.verdict, Verdict) for r in real_results)


def test_real_ambiguity_notes_resolve_ambiguous(real_results: list[ClaimResult]) -> None:
    # Re-derived from the register: every claim with an ambiguity_note -> AMBIGUOUS.
    register = load_register()
    by_id = {r.id: r for r in real_results}
    for claim in register.claims:
        if claim.ambiguity_note:
            assert by_id[claim.id].verdict is Verdict.AMBIGUOUS, claim.id


def test_real_clean_anchors_match(real_results: list[ClaimResult]) -> None:
    by_id = {r.id: r.verdict for r in real_results}
    for clean in (
        "dunya-115",
        "basmala-19-letters",
        "abjad-allah-66",
        "allah-first-occurrence-1-1",
        "malaika-shayatin-equal",
    ):
        assert by_id[clean] is Verdict.MATCH, clean


def test_real_has_at_least_one_mismatch(real_results: list[ClaimResult]) -> None:
    by_id = {r.id: r.verdict for r in real_results}
    assert by_id["yawm-singular-365"] is Verdict.MISMATCH
    assert any(r.verdict is Verdict.MISMATCH for r in real_results)
