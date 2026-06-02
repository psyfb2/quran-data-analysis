# quran-data-analysis

Python toolkit to **verify or refute quantifiable numerical/linguistic claims** about
the Arabic text of the Quran (CSTC-6, under epic CSTC-5 "Quran data analysis"). All
analysis is performed against the original Arabic text, never a translation.

## Quickstart

Requires [`uv`](https://docs.astral.sh/uv/).

```bash
make install   # create .venv and install project + dev tools
make lint      # ruff format-check + lint
make test      # run the test suite
make report    # regenerate reports/verification.md (Task 9)
```

Optionally enable the ruff pre-commit hook:

```bash
uv run pre-commit install
```

See `CLAUDE.md` and `agentdocs/` for architecture and design details. A fuller overview
is added in Task 10.
