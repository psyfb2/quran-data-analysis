"""Built-in claim checks.

Importing this package eagerly imports every check submodule, so each check's
:func:`~quran_analysis.claims.registry.check` decorator runs and registers it in
the global registry. The runner imports this package for that side effect.

The per-category split keeps each module small (SRP); the load-bearing
requirement is the **registry pattern**, not the file layout.
"""

from quran_analysis.claims.checks import (
    abjad,
    constants,
    letter_freq,
    pairs,
    positional,
)

__all__ = ["abjad", "constants", "letter_freq", "pairs", "positional"]
