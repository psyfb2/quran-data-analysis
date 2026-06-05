"""Contract tests for the populated claims register (``claims.yaml``).

These assert the *research contract* PRD Task 6 (reqs 6/8/10/13) demands, not the
measured corpus counts (that is the Task-8 runner's territory). They are pure and
offline: they only call :func:`load_register` and never load the full corpus, so
``make test`` stays fast and deterministic.
"""

from __future__ import annotations

import pytest

from quran_analysis.claims import load_register
from quran_analysis.claims.schema import ClaimsRegister

EDITION_MARKERS = ("Simple-Clean", "Uthmani", "Edition-independent")


@pytest.fixture(scope="module")
def register() -> ClaimsRegister:
    """The real repo-root ``claims.yaml``, validated against the schema."""
    return load_register()


def test_register_is_non_trivial(register: ClaimsRegister) -> None:
    # The honest research catalogue spans constant/pair/letter-freq/abjad/positional.
    assert len(register.claims) >= 8


def test_every_claim_has_rederivation_note(register: ClaimsRegister) -> None:
    # PRD req 13: sources are untrusted — every assertion must be re-derived from
    # the Arabic text, evidenced per entry.
    for claim in register.claims:
        assert claim.rederivation_note, f"{claim.id} is missing a rederivation_note"
        assert claim.rederivation_note.strip()


def test_every_operational_definition_names_an_edition(register: ClaimsRegister) -> None:
    # PRD req 6: each operational_definition must be self-contained — it must name
    # its own edition (or declare itself edition-independent).
    for claim in register.claims:
        assert any(marker in claim.operational_definition for marker in EDITION_MARKERS), (
            f"{claim.id} operational_definition does not name an edition"
        )


def test_at_least_one_claim_requires_morphology(register: ClaimsRegister) -> None:
    # PRD req 8 / §7 decision: the day=365 / month=12 / lemma-pair family cannot be
    # tested with surface counting, so morphology integration (Task 7) is required.
    assert any(claim.requires_morphology for claim in register.claims)


def test_ambiguity_notes_recorded(register: ClaimsRegister) -> None:
    # PRD req 10: claims with undisclosed/non-deterministic conventions must carry
    # an explicit ambiguity note rather than a forced verdict.
    assert any(claim.ambiguity_note for claim in register.claims)


def test_ids_are_unique(register: ClaimsRegister) -> None:
    ids = [claim.id for claim in register.claims]
    assert len(ids) == len(set(ids))


def test_deterministic_anchor_present(register: ClaimsRegister) -> None:
    # Spot-check a clean deterministic match anchor exists (the "19 letters" claim).
    assert any(claim.asserted_value == 19 for claim in register.claims)


def test_categories_are_covered(register: ClaimsRegister) -> None:
    # The catalogue should span the five primitive-backed categories.
    tags = {tag for claim in register.claims for tag in claim.tags}
    for expected in ("constant", "pair-count", "letter-freq", "abjad", "positional"):
        assert expected in tags, f"no claim tagged {expected!r}"
