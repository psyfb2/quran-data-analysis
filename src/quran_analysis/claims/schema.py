"""Claims register schema — the machine-readable contract for ``claims.yaml``.

The claims register is *data* (a YAML file), decoupled from the engine that
evaluates it. This module is the single **source of truth** for that data's
shape: a Pydantic v2 model (:class:`Claim` / :class:`ClaimsRegister`) that both
the research task (which authors ``claims.yaml``) and the claim-runner (which
loads and evaluates it) build against. A JSON Schema is *generated* from the
model (:func:`json_schema`) and committed beside it as a derived artefact
(``claims.schema.json``); a test guards the two from drifting.

Each :class:`Claim` is self-contained: its ``operational_definition`` states
that claim's own basmala and diacritic handling rather than relying on a global
convention, so the register does not depend on loader internals.

``load_register`` is intentionally minimal — it validates ``claims.yaml`` and
returns the model. The claim-runner (a later task) is built *on top of* this
loader and is deliberately **not** implemented here.

See ``agentdocs/claims-schema.md`` for the field reference and how-to.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

#: Repo-root ``claims.yaml`` register. From src/quran_analysis/claims/schema.py the
#: parents are [0]=claims, [1]=quran_analysis, [2]=src, [3]=repo root. Works under
#: pythonpath=["src"], make, and CI.
DEFAULT_REGISTER_PATH: Path = Path(__file__).resolve().parents[3] / "claims.yaml"

#: Slug rule for claim ids: lowercase alphanumerics, ``_`` and ``-``; must start
#: with an alphanumeric. Keeps ids stable, file/URL-safe and human-scannable.
ID_PATTERN: str = r"^[a-z0-9][a-z0-9_-]*$"


class Claim(BaseModel):
    """A single quantifiable claim about the Arabic text of the Quran.

    ``extra="forbid"`` makes the "rejects invalid entries" contract meaningful:
    an unknown or typo'd key (e.g. ``asserted`` instead of ``asserted_value``)
    raises rather than being silently dropped, catching authoring mistakes early.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=ID_PATTERN, min_length=1)
    description: str = Field(min_length=1)
    source: str = Field(min_length=1)
    # Exact asserted quantity. ``int`` for numeric claims (e.g. 365, 12, 19);
    # ``str`` for symbolic claims (e.g. "equal" for pair-equality). Float is
    # excluded deliberately — counts are integers, keeping verdicts deterministic.
    asserted_value: int | str
    # Self-contained: must state this claim's own basmala + diacritic handling
    # and which forms/roots/lemmas count.
    operational_definition: str = Field(min_length=1)
    expected_result: str = Field(min_length=1)
    # Flags claims needing root/lemma analysis (drives the optional morphology
    # task and the runner). Always present on the model; defaults to False.
    requires_morphology: bool = False
    # Set when the counting convention is undisclosed/non-deterministic; the
    # runner resolves such claims to an "ambiguous" verdict rather than forcing one.
    ambiguity_note: str | None = None
    # Evidence that the assertion was re-derived from the Arabic text itself
    # (research-phase sources are treated as untrusted).
    rederivation_note: str | None = None
    # Optional categorisation (pair-count / constant / letter-freq / abjad /
    # positional). Convenience only — not load-bearing.
    tags: list[str] = Field(default_factory=list)

    @field_validator("asserted_value", mode="before")
    @classmethod
    def _asserted_value_not_bool(cls, value: object) -> object:
        # Python ``bool`` is a subclass of ``int``; under the ``int | str`` union a
        # YAML ``true``/``false`` would otherwise be coerced to ``1``/``0`` and
        # silently accepted. Reject before coercion — a boolean is never a valid
        # asserted quantity for this register.
        if isinstance(value, bool):
            raise ValueError("asserted_value must be an int or str, not a bool")
        return value


class ClaimsRegister(BaseModel):
    """The full claims register: an ordered list of claims with unique ids."""

    model_config = ConfigDict(extra="forbid")

    claims: list[Claim] = Field(default_factory=list)

    @model_validator(mode="after")
    def _unique_ids(self) -> ClaimsRegister:
        seen: set[str] = set()
        duplicates: set[str] = set()
        for claim in self.claims:
            if claim.id in seen:
                duplicates.add(claim.id)
            seen.add(claim.id)
        if duplicates:
            joined = ", ".join(sorted(duplicates))
            raise ValueError(f"duplicate claim id(s): {joined}")
        return self


def load_register(path: Path = DEFAULT_REGISTER_PATH) -> ClaimsRegister:
    """Load and validate a claims register from ``path`` (default: repo-root
    ``claims.yaml``).

    The ``path`` override is the hook later tasks use to load a small synthetic
    register fixture (mirroring the corpus loader's ``data_dir`` override). The
    claim-runner reuses this function — it is the only entry point for turning
    the YAML register into validated models.
    """
    raw: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
    if raw is None:
        raw = {"claims": []}
    return ClaimsRegister.model_validate(raw)


def json_schema() -> dict[str, Any]:
    """Return the JSON Schema generated from :class:`ClaimsRegister`.

    The committed ``claims.schema.json`` is generated from this; a drift-guard
    test asserts the two stay in sync. Regenerate with::

        uv run python -c "import json, quran_analysis.claims.schema as s; \\
            print(json.dumps(s.json_schema(), indent=2, ensure_ascii=False))" \\
            > src/quran_analysis/claims/claims.schema.json
    """
    return ClaimsRegister.model_json_schema()
