"""Markdown verification report generator (Task 9).

This module is the *consumer* of the Task-8 claim-runner. It runs the runner over
the populated ``claims.yaml`` register and renders ``reports/verification.md``: a
table of ``id | claim | asserted | measured | verdict | operational definition``
preceded by a header that documents the corpus edition(s) and the normalisation
choices the counts are relative to.

The work is split into a **pure renderer** (:func:`render_report`, easily unit
tested with no I/O) and a **production driver** (:func:`generate_report`, which
loads the register + corpus, runs the runner and writes the file). The driver's
``register`` / ``ctx`` / ``checks`` parameters are the test hook — a synthetic
register + context can be injected so the test stays offline and fast, mirroring
the ``data_dir`` / ``path=`` override idiom used elsewhere in the repo.

``make report`` invokes :func:`main` via ``python -m quran_analysis.claims.report``.
The output is a pure function of ``claims.yaml`` + the vendored corpora + the
checks — no timestamp is stamped into the file, so re-running ``make report`` is
idempotent and produces no spurious diffs.
"""

from __future__ import annotations

import logging
from collections import Counter
from collections.abc import Mapping
from pathlib import Path

from quran_analysis.claims.registry import CheckContext, CheckFn, Measured
from quran_analysis.claims.runner import (
    ClaimResult,
    build_default_context,
    run_register,
)
from quran_analysis.claims.schema import ClaimsRegister, load_register

logger = logging.getLogger(__name__)

#: The committed report deliverable. ``parents[3]`` is the repo root from
#: ``src/quran_analysis/claims/report.py`` (0=claims, 1=quran_analysis, 2=src,
#: 3=repo root) — the same idiom as ``schema.DEFAULT_REGISTER_PATH``.
DEFAULT_REPORT_PATH = Path(__file__).resolve().parents[3] / "reports" / "verification.md"

#: Placeholder rendered when nothing could be measured (morphology missing /
#: no registered check) — never the literal ``"None"``.
_MISSING = "—"

_COLUMNS = ("id", "claim", "asserted", "measured", "verdict", "operational definition")


def _format_measured(value: Measured) -> str:
    """Stringify a measured value for a Markdown table cell.

    ``None`` → an em-dash placeholder; a 2-tuple ``(a, b)`` (pair counts *or* a
    ``(sura, aya)`` position — the same type) → ``"a vs b"``; ``int`` / ``str`` →
    their plain string form.
    """
    if value is None:
        return _MISSING
    if isinstance(value, tuple):
        return f"{value[0]} vs {value[1]}"
    return str(value)


def _cell(text: str) -> str:
    """Make ``text`` safe for a pipe-delimited Markdown table cell.

    Escapes literal ``|`` (a stray pipe would split the row) and collapses any
    internal whitespace/newlines into single spaces (defensive — YAML folded
    ``>-`` scalars are already single-line).
    """
    return " ".join(text.split()).replace("|", r"\|")


def _header(results: list[ClaimResult]) -> str:
    """Render the report header documenting edition + normalisation choices.

    The edition list below is hardcoded to match ``build_default_context``
    (Simple-Clean + QAC). If that context is ever extended to load another
    edition (e.g. Uthmani for a future claim), update this header so it stays
    accurate.
    """
    counts = Counter(r.verdict.value for r in results)
    summary = " / ".join(f"{counts.get(v, 0)} {v}" for v in ("match", "mismatch", "ambiguous"))
    return f"""# Quran claims — verification report

Verifies or refutes quantifiable numerical/linguistic claims about the **Arabic**
text of the Quran. All analysis is performed against the original Arabic text,
never a translation.

> **Generated file — do not edit by hand.** Regenerate (and re-commit) with
> `make report` after each analysis run.

## Corpus editions

- **Tanzil Simple-Clean** v1.1 (CC BY 3.0) — primary edition for surface-form
  (count / substring / letter-frequency / position) claims.
- **Quranic Arabic Corpus (QAC)** morphology v0.4 (GPL) — root/lemma counts for
  claims that surface forms cannot reproduce.

See `agentdocs/corpus.md` and `agentdocs/morphology.md` for editions/licences.

## Normalisation choices

Surface-form counts use the canonical `normalize()` pipeline: **tatweel removed**,
**tashkeel (diacritics) stripped**, **hamza/alif folded**. Final-form folding
(ى→ي, ة→ه) is **not** applied in the canonical pipeline. Counts are only
meaningful relative to these choices — see `agentdocs/normalisation.md`.

## Verdicts

`match` — the measured value satisfies the asserted claim · `mismatch` — it does
not · `ambiguous` — the counting convention is undisclosed/non-deterministic, or
the claim needs morphology that is unavailable (never forced to match/mismatch).

**Summary:** {summary}.
"""


def render_report(register: ClaimsRegister, results: list[ClaimResult]) -> str:
    """Render the full Markdown report (header + table) as a string.

    Pure — no I/O, no corpus load. ``results`` must be in ``register.claims``
    order (as :func:`~quran_analysis.claims.runner.run_register` guarantees) so
    each result lines up with its claim's description / operational definition.

    Args:
        register: The validated claims register (source of the description /
            operational_definition columns).
        results: The runner results, one per claim, in register order.

    Returns:
        The complete Markdown document.
    """
    lines = [_header(results), ""]
    lines.append("| " + " | ".join(_COLUMNS) + " |")
    lines.append("| " + " | ".join("---" for _ in _COLUMNS) + " |")
    for claim, result in zip(register.claims, results, strict=True):
        # Every cell is run through _cell(): ids and verdict values can never
        # contain a pipe (id is schema-constrained, verdict is an enum literal),
        # but sanitising uniformly makes "no cell can break the table" explicit.
        row = (
            _cell(result.id),
            _cell(claim.description),
            _cell(str(result.asserted)),
            _cell(_format_measured(result.measured)),
            _cell(result.verdict.value),
            _cell(claim.operational_definition),
        )
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines) + "\n"


def generate_report(
    *,
    register: ClaimsRegister | None = None,
    ctx: CheckContext | None = None,
    checks: Mapping[str, CheckFn] | None = None,
    output_path: Path = DEFAULT_REPORT_PATH,
) -> Path:
    """Run the claim-runner and write the rendered report to ``output_path``.

    Args:
        register: Register to evaluate (defaults to the committed ``claims.yaml``
            via :func:`load_register`).
        ctx: The loaded data the checks need (defaults to
            :func:`build_default_context` — Simple-Clean + QAC morphology).
        checks: Optional check-table override forwarded to the runner (test hook).
        output_path: Where to write the report (defaults to
            :data:`DEFAULT_REPORT_PATH`).

    Returns:
        The path the report was written to.
    """
    if register is None:
        register = load_register()
    if ctx is None:
        ctx = build_default_context()
    results = run_register(register, ctx, checks=checks)
    content = render_report(register, results)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    return output_path


def main() -> None:
    """Entry point for ``make report`` (``python -m quran_analysis.claims.report``)."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    path = generate_report()
    logger.info("Wrote verification report to %s", path)


if __name__ == "__main__":
    main()
