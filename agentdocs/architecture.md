# Architecture

The repo is layered so the research artefact (the claims register) is decoupled from
the engine that evaluates it.

1. **Project & tooling** — uv-managed `pyproject.toml`, ruff (format + lint), a
   pre-commit hook, a `Makefile` (`install/format/lint/test/report`) and CI.
2. **Corpus/data** (`corpus.py`) — vendored Tanzil Uthmani (primary) + Simple-Clean
   (secondary) editions parsed by `load_corpus()` into an immutable, frozen-dataclass
   `Corpus -> Sura -> Aya -> Word` model keyed by `(sura, aya)`, with the opening
   basmala separated and individually addressable (`Sura.basmala` /
   `words(include_basmala=...)`). See `corpus.md`.
3. **Normalisation** (Task 3) — pure string functions: diacritic stripping, hamza/alif
   normalisation, tatweel removal, tokenisation. See `normalisation.md`.
4. **Primitives** (`primitives.py`, Task 4) — claim-agnostic measurements over the
   corpus model, reusing normalisation: `count_by_form` (normalised exact-form
   occurrences), `count_by_substring` (intra-word, non-overlapping), `letter_frequency`,
   `first_occurrence_position` (`(sura, aya)` of first match, or `None`) and
   `abjad_value` (Mashriqi gematria). All corpus-scanning primitives thread the
   `include_basmala` toggle and accept a `normalizer` hook (default `normalize`) so a
   claim can opt into e.g. final-form folding without claim logic leaking into the
   layer. Counts are meaningful only relative to `normalize()` + the abjad table — see
   `normalisation.md`.
5. **Claims** (Tasks 5/6/8) — a machine-readable schema governs `claims.yaml`
   (research output); each claim's check is a registered callable; the runner returns
   `{asserted, measured, verdict}` with verdict ∈ match/mismatch/ambiguous.
6. **Reporting** (Task 9) — renders `reports/verification.md` via `make report`.

Flow: **tooling → corpus + normalisation → primitives → claims → report.**

> Stub created in Task 1; expanded by later tasks as each layer is implemented.
