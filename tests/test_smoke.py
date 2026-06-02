"""Smoke test: the package and its placeholder modules import cleanly."""

import quran_analysis
from quran_analysis import claims, corpus, normalize, primitives


def test_version() -> None:
    assert quran_analysis.__version__ == "0.1.0"


def test_submodules_import() -> None:
    # Importing the placeholder modules guarantees the skeleton is import-clean.
    assert corpus is not None
    assert normalize is not None
    assert primitives is not None
    assert claims is not None
