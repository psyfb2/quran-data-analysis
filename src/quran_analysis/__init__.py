"""quran_analysis — tooling to verify quantifiable claims about the Arabic Quran.

Layered design (see agentdocs/architecture.md):
tooling -> corpus + normalisation -> primitives -> claims (schema/runner) -> report.
All textual analysis is performed against the original Arabic text, never a translation.
"""

__version__ = "0.1.0"
