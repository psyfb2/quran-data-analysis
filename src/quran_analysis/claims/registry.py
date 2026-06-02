"""Check registry — the open/closed extension point for the claim-runner.

Each claim's check is a small callable that encodes that claim's *self-contained*
operational definition by composing the Task-4 counting primitives (and the
Task-7 morphology primitives where a root/lemma count is needed). Checks register
themselves via the :func:`check` decorator, so adding a future claim is a YAML
entry **plus** a registered check — never a change to a central switch.

This module is deliberately lightweight: it imports only the data models
(:class:`~quran_analysis.corpus.Corpus`,
:class:`~quran_analysis.morphology.Morphology`,
:class:`~quran_analysis.claims.schema.Claim`) so there is no import cycle —
``checks/*`` import this module, the runner imports this module plus the checks
package, and ``schema`` imports none of them.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

from quran_analysis.claims.schema import Claim
from quran_analysis.corpus import Corpus
from quran_analysis.morphology import Morphology

#: A value a check measured from the text. Kept as a plain value (rendered
#: verbatim by the Task-9 report): a scalar count, a ``(count1, count2)`` pair for
#: pair-equality claims, a ``(sura, aya)`` position tuple, or ``None`` when nothing
#: could be measured.
Measured = int | str | tuple[int, int] | None


@dataclass(frozen=True)
class Measurement:
    """What a check measured, plus whether it satisfies the claim.

    ``matched`` lives here (not in the runner) because the comparison semantics
    differ per claim — numeric equality, pair equality, positional-tuple equality.
    The check, which encodes the claim's operational definition, owns that
    comparison; the runner only applies the cross-cutting ``ambiguous`` overrides.

    Attributes:
        value: The measured value (rendered verbatim by the report).
        matched: Whether the measurement satisfies the claim's asserted value.
    """

    value: Measured
    matched: bool


@dataclass(frozen=True)
class CheckContext:
    """The loaded data a check may need.

    Editions are keyed by name so a check can pick the edition its operational
    definition names; morphology is optional (``None`` in synthetic tests, or when
    a ``requires_morphology`` claim must stay ambiguous because no morphology was
    loaded).

    Attributes:
        corpora: Loaded corpora keyed by edition name (e.g. ``"simple-clean"``).
        morphology: The loaded QAC morphology, or ``None``.
    """

    corpora: Mapping[str, Corpus]
    morphology: Morphology | None = None

    def corpus(self, edition: str = "simple-clean") -> Corpus:
        """Return the loaded corpus for ``edition``.

        Raises:
            KeyError: If that edition was not loaded — fails loudly rather than
                silently measuring against the wrong text.
        """
        try:
            return self.corpora[edition]
        except KeyError:
            raise KeyError(f"no corpus loaded for edition {edition!r}") from None


#: A check: maps a claim + context to a measurement.
CheckFn = Callable[[Claim, CheckContext], Measurement]

_CHECKS: dict[str, CheckFn] = {}


def check(claim_id: str) -> Callable[[CheckFn], CheckFn]:
    """Register a check for ``claim_id``.

    Args:
        claim_id: The ``id`` of the claim this check evaluates.

    Returns:
        A decorator that registers the wrapped function and returns it unchanged.

    Raises:
        ValueError: If a check is already registered for ``claim_id`` (catches a
            copy-paste id typo at import time — fail fast).
    """

    def decorator(fn: CheckFn) -> CheckFn:
        if claim_id in _CHECKS:
            raise ValueError(f"duplicate check registration for {claim_id!r}")
        _CHECKS[claim_id] = fn
        return fn

    return decorator


def registry() -> Mapping[str, CheckFn]:
    """Return a read-only view of the global check registry."""
    return _CHECKS
