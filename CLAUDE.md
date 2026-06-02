# quran-data-analysis

Python toolkit (CSTC-6, under epic CSTC-5) to **verify or refute quantifiable
numerical/linguistic claims** about the Arabic text of the Quran. All analysis is
performed against the **original Arabic text, never a translation**.

## Entry points

Common commands live in the `Makefile` and run through `uv`:

| Command | What it does |
| --- | --- |
| `make install` | `uv sync` — create `.venv`, install the project + dev tools |
| `make format`  | `uv run ruff format .` |
| `make lint`    | `uv run ruff format --check .` then `uv run ruff check .` |
| `make typecheck` | `uv run mypy` (static type checking over `src` + `tests`) |
| `make test`    | `uv run pytest` |
| `make report`  | regenerate `reports/verification.md` (placeholder until Task 9) |

## Layout & key concepts

```
src/quran_analysis/
  corpus.py       # Task 2 — load vendored Tanzil editions into Corpus->Sura->Aya->Word
  normalize.py    # Task 3 — pure tashkeel/hamza/tatweel/tokenisation functions
  primitives.py   # Task 4 — claim-agnostic counts (form/substring/letter-freq/abjad/position)
  claims/
    schema.py          # Task 5 — Claim/ClaimsRegister Pydantic models + load_register()
    claims.schema.json # Task 5 — JSON Schema generated from the model (drift-guarded)
                       # Tasks 8/9 add the check registry, runner and report here
claims.yaml       # Task 6 — populated research register (16 claims), governed by claims/schema.py
tests/            # pytest suite
data/             # Task 2 — vendored Arabic corpus (committed for offline CI)
agentdocs/        # architecture.md, corpus.md, normalisation.md, claims-schema.md, claims-register.md
```

Layered flow: **tooling → corpus + normalisation → primitives → claims (schema/runner) → report.**
See `agentdocs/architecture.md` for the full design.

## Conventions

- **Dependency management:** `uv`. Dev tools (ruff, pytest, pre-commit) live in the
  PEP 735 `[dependency-groups].dev` table. **Runtime** deps go in `[project].dependencies`
  and are added **per task as needed** (`pydantic` + `pyyaml` landed in Task 5 for the
  claims schema/loader). `uv.lock` is committed.
- **Lint/format:** `ruff` (line-length 100, rules `E,F,I,UP,B`). The `ruff` version is
  pinned **identically** in `pyproject.toml` and `.pre-commit-config.yaml` so the two
  ruff paths never drift.
- **Pre-commit:** run `uv run pre-commit install` once; the hook runs ruff (check + format)
  on each commit. The `ruff-check` hook runs with `--fix`, so if it auto-fixes a file the
  commit is aborted with "files were modified by this hook" — just re-stage the fixed files
  (`git add -u`) and commit again. CI runs `make lint` directly and does not depend on pre-commit.
- **CI:** `.github/workflows/ci.yml` installs uv (`astral-sh/setup-uv`, pinned to Python
  3.11 for reproducibility) and runs `make install` → `make lint` → `make typecheck` →
  `make test`. Corpus data is vendored into git so CI needs no network access.

## Report regeneration

`make report` regenerates `reports/verification.md` (the committed deliverable linked
from CSTC-6). The real generator lands in Task 9; until then `make report` prints a notice.
