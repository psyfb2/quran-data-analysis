"""Shared literal strings used by edition-independent checks.

Keeping the basmala phrase in one place avoids the two edition-independent check
families (abjad value, 19-letter count) drifting out of sync if the canonical
spelling ever changes.
"""

from __future__ import annotations

#: The basmala phrase "bismillah al-rahman al-rahim" (un-diacritised).
BASMALA: str = "بسم الله الرحمن الرحيم"
