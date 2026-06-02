"""Unit tests for the claims register schema (Task 5).

Pure and offline: inline literal dicts only, no corpus load. Covers the
accept + reject paths that are the explicit acceptance criterion, plus the
stub-validates and JSON-Schema drift-guard checks.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from quran_analysis.claims.schema import (
    Claim,
    ClaimsRegister,
    json_schema,
    load_register,
)

SCHEMA_JSON_PATH = (
    Path(__file__).resolve().parents[1] / "src" / "quran_analysis" / "claims" / "claims.schema.json"
)


def _valid_claim_dict() -> dict[str, object]:
    """A minimal valid claim with every required field populated."""
    return {
        "id": "yawm-day-365",
        "description": "The word 'day' occurs 365 times.",
        "source": "Example source",
        "asserted_value": 365,
        "operational_definition": "Count the normalised singular form; basmala excluded.",
        "expected_result": "count == 365",
    }


# --- accept paths ----------------------------------------------------------


def test_minimal_valid_claim_accepted_with_defaults() -> None:
    claim = Claim.model_validate(_valid_claim_dict())
    assert claim.id == "yawm-day-365"
    assert claim.asserted_value == 365
    # Defaults.
    assert claim.requires_morphology is False
    assert claim.ambiguity_note is None
    assert claim.rederivation_note is None
    assert claim.tags == []


def test_asserted_value_int_preserved() -> None:
    claim = Claim.model_validate(_valid_claim_dict())
    assert isinstance(claim.asserted_value, int)


def test_asserted_value_str_preserved() -> None:
    d = _valid_claim_dict()
    d["asserted_value"] = "equal"
    claim = Claim.model_validate(d)
    assert claim.asserted_value == "equal"
    assert isinstance(claim.asserted_value, str)


def test_optional_fields_round_trip() -> None:
    d = _valid_claim_dict()
    d.update(
        requires_morphology=True,
        ambiguity_note="convention undisclosed",
        rederivation_note="re-derived from sura 2",
        tags=["constant", "pair-count"],
    )
    claim = Claim.model_validate(d)
    assert claim.requires_morphology is True
    assert claim.ambiguity_note == "convention undisclosed"
    assert claim.rederivation_note == "re-derived from sura 2"
    assert claim.tags == ["constant", "pair-count"]


# --- reject paths ----------------------------------------------------------


def test_float_asserted_value_rejected() -> None:
    d = _valid_claim_dict()
    d["asserted_value"] = 365.5
    with pytest.raises(ValidationError):
        Claim.model_validate(d)


def test_bool_asserted_value_rejected() -> None:
    # Python bool is a subclass of int; the model validator must reject it.
    d = _valid_claim_dict()
    d["asserted_value"] = True
    with pytest.raises(ValidationError):
        Claim.model_validate(d)


def test_missing_required_field_rejected() -> None:
    d = _valid_claim_dict()
    del d["operational_definition"]
    with pytest.raises(ValidationError):
        Claim.model_validate(d)


def test_extra_field_rejected() -> None:
    d = _valid_claim_dict()
    d["asserted"] = 365  # typo for asserted_value
    with pytest.raises(ValidationError):
        Claim.model_validate(d)


@pytest.mark.parametrize("bad_id", ["", "has spaces", "Uppercase", "-leading-dash", "weird!"])
def test_bad_id_rejected(bad_id: str) -> None:
    d = _valid_claim_dict()
    d["id"] = bad_id
    with pytest.raises(ValidationError):
        Claim.model_validate(d)


@pytest.mark.parametrize(
    "field", ["description", "source", "operational_definition", "expected_result"]
)
def test_empty_required_string_rejected(field: str) -> None:
    d = _valid_claim_dict()
    d[field] = ""
    with pytest.raises(ValidationError):
        Claim.model_validate(d)


def test_duplicate_ids_rejected_at_register_level() -> None:
    c = _valid_claim_dict()
    with pytest.raises(ValidationError):
        ClaimsRegister.model_validate({"claims": [c, dict(c)]})


def test_unique_ids_accepted_at_register_level() -> None:
    c1 = _valid_claim_dict()
    c2 = _valid_claim_dict()
    c2["id"] = "life-death-equal"
    register = ClaimsRegister.model_validate({"claims": [c1, c2]})
    assert [c.id for c in register.claims] == ["yawm-day-365", "life-death-equal"]


def test_empty_register_accepted() -> None:
    register = ClaimsRegister.model_validate({"claims": []})
    assert register.claims == []


# --- stub register + drift guard ------------------------------------------


def test_stub_claims_yaml_validates() -> None:
    register = load_register()
    assert len(register.claims) >= 1
    assert all(isinstance(c, Claim) for c in register.claims)


def test_committed_json_schema_matches_model() -> None:
    committed = json.loads(SCHEMA_JSON_PATH.read_text(encoding="utf-8"))
    assert committed == json_schema()


def test_load_register_missing_path_raises_clear_error(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist.yaml"
    with pytest.raises(FileNotFoundError, match="Claims register not found"):
        load_register(missing)


def test_load_register_path_override(tmp_path: Path) -> None:
    register_file = tmp_path / "synthetic.yaml"
    register_file.write_text(
        "claims:\n"
        "  - id: synthetic-claim\n"
        "    description: A synthetic claim.\n"
        "    source: test fixture\n"
        "    asserted_value: 7\n"
        "    operational_definition: count something; basmala excluded.\n"
        "    expected_result: count == 7\n",
        encoding="utf-8",
    )
    register = load_register(register_file)
    assert [c.id for c in register.claims] == ["synthetic-claim"]
    assert register.claims[0].asserted_value == 7
