"""Claim-runner — evaluate each claim to a ``{id, asserted, measured, verdict}``.

The runner reuses :func:`~quran_analysis.claims.schema.load_register` (Task 5) to
obtain validated claims, then maps each claim to its registered check (Task-8
registry) and applies the cross-cutting verdict rules. Verdict logic that depends
on the claim's *semantics* (numeric vs pair vs positional equality) lives in the
check; the runner only applies the verdict rules that are common to all claims.

Verdict-decision order (deliberate, see :func:`evaluate_claim`):

1. No registered check -> ``ambiguous`` (graceful, open/closed; guarded by a
   registry-coverage test so a forgotten real check is still caught loudly).
2. ``requires_morphology`` but no morphology loaded -> ``ambiguous`` *without*
   calling the check (it would need ``ctx.morphology``). Satisfies Task 7's
   documented split.
3. The claim carries an ``ambiguity_note`` -> ``ambiguous``, but the measured
   value is kept (PRD req 11: undisclosed/non-deterministic conventions are never
   forced to match/mismatch).
4. Otherwise the honest comparison decided by the check: ``match`` / ``mismatch``.

There is intentionally **no** broad ``try/except`` around the check — checks are
tested and must be correct; swallowing exceptions would silently turn a bug into
``ambiguous``. Only the two explicit, data-driven conditions yield ambiguity.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum

from quran_analysis.claims import checks as _checks  # noqa: F401  (registers checks on import)
from quran_analysis.claims.registry import CheckContext, CheckFn, Measured, registry
from quran_analysis.claims.schema import Claim, ClaimsRegister
from quran_analysis.corpus import load_corpus
from quran_analysis.morphology import load_morphology


class Verdict(str, Enum):
    """The outcome of evaluating a claim against the text."""

    MATCH = "match"
    MISMATCH = "mismatch"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True)
class ClaimResult:
    """The PRD result contract for a single claim.

    Attributes:
        id: The claim id.
        asserted: The asserted figure (verbatim from ``claims.yaml``).
        measured: The value measured from the text, or ``None`` when nothing
            could be measured.
        verdict: ``match`` / ``mismatch`` / ``ambiguous``.
    """

    id: str
    asserted: int | str
    measured: Measured
    verdict: Verdict


def evaluate_claim(
    claim: Claim,
    ctx: CheckContext,
    *,
    checks: Mapping[str, CheckFn] | None = None,
) -> ClaimResult:
    """Evaluate a single claim to a :class:`ClaimResult`.

    Args:
        claim: The claim to evaluate.
        ctx: The loaded data a check may need.
        checks: Optional check table override (defaults to the global registry).
            The injection hook lets tests exercise verdict paths with synthetic
            claim ids without touching the global registry.

    Returns:
        The ``{id, asserted, measured, verdict}`` result.
    """
    table = registry() if checks is None else checks
    fn = table.get(claim.id)

    # (1) No registered check -> cannot measure -> ambiguous.
    if fn is None:
        return ClaimResult(claim.id, claim.asserted_value, None, Verdict.AMBIGUOUS)

    # (2) Needs morphology but none loaded -> ambiguous WITHOUT calling the check.
    if claim.requires_morphology and ctx.morphology is None:
        return ClaimResult(claim.id, claim.asserted_value, None, Verdict.AMBIGUOUS)

    measurement = fn(claim, ctx)

    # (3) Undisclosed/non-deterministic convention -> never forced (PRD req 11).
    if claim.ambiguity_note:
        return ClaimResult(claim.id, claim.asserted_value, measurement.value, Verdict.AMBIGUOUS)

    # (4) Honest comparison decided by the check.
    verdict = Verdict.MATCH if measurement.matched else Verdict.MISMATCH
    return ClaimResult(claim.id, claim.asserted_value, measurement.value, verdict)


def run_register(
    register: ClaimsRegister,
    ctx: CheckContext,
    *,
    checks: Mapping[str, CheckFn] | None = None,
) -> list[ClaimResult]:
    """Evaluate every claim in ``register``, preserving register order.

    Order is preserved so the Task-9 report can zip results with
    ``register.claims`` for the description / operational_definition columns.
    """
    return [evaluate_claim(c, ctx, checks=checks) for c in register.claims]


def build_default_context() -> CheckContext:
    """Build the production context: the vendored Simple-Clean edition + QAC morphology.

    All current corpus-scanning checks name *Tanzil Simple-Clean* in their
    operational definition, so only that edition is loaded (loading Uthmani too
    would be unused I/O). :meth:`CheckContext.corpus` raises a clear ``KeyError``
    if a future check asks for an edition that was not loaded.
    """
    return CheckContext(
        corpora={"simple-clean": load_corpus("simple-clean")},
        morphology=load_morphology(),
    )
