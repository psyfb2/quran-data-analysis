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
5. **Claims** (Tasks 5/6/8) — a machine-readable schema (`claims/schema.py`,
   Task 5) governs the repo-root `claims.yaml` register (research output). The
   Pydantic v2 `Claim` / `ClaimsRegister` models are the source of truth; the
   committed `claims/claims.schema.json` is generated from them (drift-guarded by a
   test). `load_register()` validates the YAML into models and is reused by the
   runner. The register is **populated** in Task 6 (16 researched claims spanning
   constant/pair-count/letter-freq/abjad/positional); its edition policy,
   re-derivation discipline and the morphology decision are in `claims-register.md`.
   See also `claims-schema.md`.

   **Claim-runner** (Task 8) — open/closed via a decorator registry. Each claim's
   check is a small callable registered with `@check("<id>")` (`claims/registry.py`)
   that composes the Task-4 primitives (and the Task-7 morphology primitives where
   the op-def needs root/lemma) per the claim's *self-contained* operational
   definition. The checks live under `claims/checks/` grouped by category and
   register on import; adding a future claim is a YAML entry **plus** a registered
   check — never a change to a central switch. `runner.py` exposes `evaluate_claim`
   / `run_register` (preserving register order) returning `ClaimResult{id, asserted,
   measured, verdict}` with verdict ∈ match/mismatch/ambiguous. Verdict-decision
   order: (1) **no registered check → ambiguous** (graceful; a forgotten real check
   is still caught loudly by a registry-coverage test); (2) `requires_morphology`
   but no morphology loaded → ambiguous *without* calling the check; (3) an
   `ambiguity_note` → ambiguous but the measured value is kept (PRD req 11: never
   forced); (4) otherwise the honest comparison decided by the check. There is no
   broad `try/except` around a check — swallowing would silently hide a bug as
   ambiguous. The check owns the comparison semantics (numeric vs pair vs
   positional equality); the runner only applies these cross-cutting overrides.
   `build_default_context()` loads only Simple-Clean + QAC morphology (all current
   checks name Simple-Clean). The current register evaluates to 7 match / 4
   mismatch / 5 ambiguous.
6. **Reporting** (Task 9) — renders `reports/verification.md` via `make report`.

**Optional: Morphology** (`morphology.py`, Task 7) — a dataset *parallel* to the
corpus. The Quranic Arabic Corpus (QAC) morphology edition is vendored and parsed
by `load_morphology()` into a frozen-dataclass `Morphology -> MorphologyWord`
model keyed by `(sura, aya, word)`, with `count_by_root` / `count_by_lemma`
primitives (exact Buckwalter match). It was integrated because the populated
register flags claims (e.g. day=365) that need *lemma/root* counts surface forms
cannot reproduce. It keeps `corpus.py` / `primitives.py` untouched and adds **no**
runtime dependency. The QAC data is **GPL** (vendored verbatim; mere aggregation —
the MIT code is not relicensed). See `morphology.md`.

Flow: **tooling → corpus + normalisation → primitives → claims → report**, with
the optional morphology dataset feeding the claim-runner's root/lemma checks.

> Stub created in Task 1; expanded by later tasks as each layer is implemented.
