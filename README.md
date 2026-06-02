# quran-data-analysis

Python toolkit to **verify or refute quantifiable numerical/linguistic claims** about
the Arabic text of the Quran (CSTC-6, under epic CSTC-5 "Quran data analysis"). All
analysis is performed against the **original Arabic text, never a translation**, and
word-level integrity is preserved.

## What it does

Popular and academic literature circulates many numerical/linguistic "patterns" in the
Quran (paired-word counts, counts tied to constants like 365/12/19, letter-frequency and
abjad claims, …) presented as evidence of divine authorship. This toolkit catalogues each
such claim that can be reduced to a **deterministic count** into a schema-governed register
(`claims.yaml`), re-derives every figure from the vendored Arabic corpus, and emits a
verdict of **match / mismatch / ambiguous** per claim.

`ambiguous` is a first-class verdict: claims whose counting convention is undisclosed or
non-deterministic (or that need morphology that is unavailable) are recorded as `ambiguous`
rather than forced to a match/mismatch (PRD reqs 10/11).

## What it produces

The deliverable is [`reports/verification.md`](reports/verification.md) — a table of
`id | claim | asserted | measured | verdict | operational definition`, preceded by a header
documenting the corpus editions and normalisation choices the counts are relative to.

Current outcome: **16 catalogued claims → 7 match / 4 mismatch / 5 ambiguous.** Regenerate
it with `make report` (see below).

## Quickstart

Requires [`uv`](https://docs.astral.sh/uv/).

| Command | What it does |
| --- | --- |
| `make install` | `uv sync` — create `.venv`, install the project + dev tools |
| `make format`  | `uv run ruff format .` |
| `make lint`    | `uv run ruff format --check .` then `uv run ruff check .` |
| `make typecheck` | `uv run mypy` (static type checking over `src` + `tests`) |
| `make test`    | `uv run pytest` |
| `make report`  | regenerate `reports/verification.md` from `claims.yaml` + the corpus |

Optionally enable the ruff pre-commit hook:

```bash
uv run pre-commit install
```

## Regenerating the report

`make report` rewrites `reports/verification.md` purely from `claims.yaml` + the vendored
corpora. It emits no timestamp, so regeneration is **idempotent** — re-run it and re-commit
the result after any analysis change. Full detail is in `CLAUDE.md` ("Report regeneration").

## Where to look next

- `CLAUDE.md` — entry points, repo layout, conventions, and the report workflow.
- `agentdocs/` — design detail: `architecture.md` (the
  tooling → corpus/normalisation → primitives → claim-runner → report flow),
  `corpus.md` (editions + licences), `normalisation.md` (every normalisation choice + the
  abjad table), `claims-schema.md` (the register schema), `claims-register.md` (research
  conventions + verdict mix), and `morphology.md` (the QAC root/lemma integration).

## Data & licensing

The code is MIT-licensed (`LICENSE`). Vendored data carries its own licences: the Tanzil
Quran editions are **CC BY 3.0**, and the Quranic Arabic Corpus (QAC) morphology dataset is
**GPL**, vendored verbatim (mere aggregation — it does not relicense the code). See
`agentdocs/corpus.md` and `agentdocs/morphology.md` for editions, versions, and attribution.
