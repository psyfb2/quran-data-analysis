"""Claims layer — schema, register loading, check registry and claim-runner.

Implemented across Tasks 5/8/9. The claims register (``claims.yaml``) is data
governed by a machine-readable schema (:mod:`quran_analysis.claims.schema`);
each claim's check is a small callable registered to a registry so the runner
stays open/closed.
"""

# Importing the checks package for its side effect: each check module registers
# itself with the registry via the ``@check`` decorator at import time. The runner
# also triggers this, but importing it here makes registry population explicit and
# robust to refactors that bypass the runner.
from quran_analysis.claims import checks as _checks  # noqa: F401
from quran_analysis.claims.registry import CheckContext
from quran_analysis.claims.runner import (
    ClaimResult,
    Verdict,
    build_default_context,
    evaluate_claim,
    run_register,
)
from quran_analysis.claims.schema import (
    DEFAULT_REGISTER_PATH,
    Claim,
    ClaimsRegister,
    json_schema,
    load_register,
)

__all__ = [
    "DEFAULT_REGISTER_PATH",
    "CheckContext",
    "Claim",
    "ClaimResult",
    "ClaimsRegister",
    "Verdict",
    "build_default_context",
    "evaluate_claim",
    "json_schema",
    "load_register",
    "run_register",
]
