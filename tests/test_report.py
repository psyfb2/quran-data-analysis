"""Tests for the Markdown report generator (Task 9).

Mostly pure / offline / synthetic — a tiny synthetic corpus + synthetic register +
a local ``checks`` table exercise every ``_format_measured`` branch (int, tuple,
None) and prove the str-enum verdict is rendered via ``.value``; a pure
``render_report`` unit covers the Markdown pipe-escaping edge case. The one
exception is the drift guard (``test_committed_report_matches_runner_output``),
which loads the real corpus + morphology to ensure the committed deliverable is
not stale — mirroring the JSON-schema drift guard in ``test_claims_schema.py``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from quran_analysis.claims.registry import CheckContext, CheckFn, Measurement
from quran_analysis.claims.report import (
    DEFAULT_REPORT_PATH,
    generate_report,
    render_report,
)
from quran_analysis.claims.runner import (
    ClaimResult,
    Verdict,
    build_default_context,
    run_register,
)
from quran_analysis.claims.schema import Claim, ClaimsRegister, load_register
from quran_analysis.corpus import Corpus, load_corpus

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


def test_generate_report_writes_wellformed_markdown(
    synthetic_corpus: Corpus, tmp_path: Path
) -> None:
    ctx = CheckContext(corpora={"simple-clean": synthetic_corpus})
    register = ClaimsRegister(
        claims=[
            _claim("c-match"),
            _claim("c-mismatch"),
            _claim("c-pair", asserted_value="equal", ambiguity_note="undisclosed"),
            _claim("c-nocheck"),
        ]
    )
    checks: dict[str, CheckFn] = {
        "c-match": lambda cl, cx: Measurement(5, True),
        "c-mismatch": lambda cl, cx: Measurement(3, False),
        "c-pair": lambda cl, cx: Measurement((115, 71), False),
        # "c-nocheck" intentionally absent -> measured None.
    }
    out = tmp_path / "verification.md"
    result_path = generate_report(register=register, ctx=ctx, checks=checks, output_path=out)

    assert result_path == out
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert content.strip(), "report must be non-empty"

    # Table header + separator row with all six columns.
    for column in ("id", "claim", "asserted", "measured", "verdict", "operational definition"):
        assert column in content
    assert "| --- |" in content

    # Every claim id appears.
    for claim_id in ("c-match", "c-mismatch", "c-pair", "c-nocheck"):
        assert claim_id in content

    # Verdicts rendered via .value (lower-case), not the str-enum repr.
    assert "match" in content
    assert "mismatch" in content
    assert "ambiguous" in content
    assert "Verdict." not in content

    # Tuple measured -> "a vs b"; None measured -> em-dash placeholder.
    assert "115 vs 71" in content
    assert "—" in content

    # Header documents edition + normalisation choices.
    assert "Simple-Clean" in content
    assert "ormalis" in content or "ormaliz" in content


def test_render_report_escapes_pipes() -> None:
    register = ClaimsRegister(claims=[_claim("c-pipe", operational_definition="count a | b forms")])
    results = [ClaimResult("c-pipe", 5, 5, Verdict.MATCH)]
    content = render_report(register, results)
    # A literal pipe in a cell must be escaped so the table row is not split.
    assert r"\|" in content
    assert "count a | b forms" not in content


def test_render_report_is_deterministic() -> None:
    register = ClaimsRegister(claims=[_claim("c-a"), _claim("c-b")])
    results = [
        ClaimResult("c-a", 5, 5, Verdict.MATCH),
        ClaimResult("c-b", 5, None, Verdict.AMBIGUOUS),
    ]
    assert render_report(register, results) == render_report(register, results)


def test_committed_report_matches_runner_output() -> None:
    """The committed ``reports/verification.md`` must equal a fresh render.

    Drift guard for the primary deliverable (mirrors
    ``test_committed_json_schema_matches_model``): if a check or a ``claims.yaml``
    entry changes without re-running ``make report``, the committed report goes
    stale and this fails loudly. Loads the real corpus + QAC morphology.
    """
    register = load_register()
    results = run_register(register, build_default_context())
    expected = render_report(register, results)
    committed = DEFAULT_REPORT_PATH.read_text(encoding="utf-8")
    assert committed == expected, "reports/verification.md is stale — run `make report` and commit"
