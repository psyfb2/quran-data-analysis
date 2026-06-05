# Claims register (`claims.yaml`) — research notes & conventions

`claims.yaml` (repo root) is the **research artefact** produced in Task 6 (Phase 1):
a catalogue of quantifiable numerical/linguistic claims about the Arabic Quran that
are circulated as evidence of divine authorship. It is *data*, governed by the
schema in `src/quran_analysis/claims/schema.py` (see `claims-schema.md`). This file
documents the **research-phase conventions** behind the entries; the engine that
evaluates them (the claim-runner) is Task 8 and the report is Task 9.

## Edition policy (load-bearing)

Two editions are vendored (see `corpus.md`): **Tanzil Uthmani** (archaic rasm) and
**Tanzil Simple-Clean** (modern spelling). The edition is **decisive** for any claim
whose word uses archaic rasm, so **every `operational_definition` names its own
edition** (or declares itself *edition-independent* for pure abjad/string claims).

Default for popular modern-spelling claims: **Tanzil Simple-Clean**, because the
Uthmani surface form often differs and would spuriously read as 0. Re-derived
examples (2026-06-02):

| Form | Uthmani | Simple-Clean | Why |
| --- | --- | --- | --- |
| `الحياة` (life) | **0** | 63 | Uthmani spells it `الحيوة` (wāw + dagger-alef) |
| `الملائكة` (the angels) | **0** | 38 | archaic rasm |
| `الشيطان` (the devil) | **0** | 63 | archaic rasm |
| `الموت` (death) | 35 | 35 | identical |
| `الدنيا` (this world) | 115 | 115 | identical |

Counts are only meaningful **relative to the edition + the normalisation choices**
(see `normalisation.md`); each entry states both.

## Re-derivation discipline (PRD req 13 — sources are untrusted)

The popular *asserted* figure is stored in `asserted_value` but is **never trusted**.
For every claim the underlying assertion was **re-measured from the vendored Arabic
text** using the Task-4 primitives (`count_by_form`, `count_by_substring`,
`letter_frequency`, `first_occurrence_position`, `abjad_value`), and the measured
value + the primitive used are recorded in `rederivation_note`. The Task-8 runner /
Task-9 report derive each verdict from the **measurement**, not from the source.

A throwaway `uv run python` scratchpad was used for the measurements; it is a
research aid and is intentionally **not committed**.

## Morphology decision (PRD req 8)

PRD req 8 requires a **per-claim** decision and says to integrate morphology *only
if at least one catalogued claim requires it*. Re-derivation shows the
**day=365 / month=12 / days=30** constant family and the lemma **pair** claims
(life/death, angels/devils, man/woman, sea/land) **cannot** be tested with surface
counting — e.g. surface `يوم` = 217 (not 365); the 365 figure is a *singular-noun
lemma* count. These entries set **`requires_morphology: true`**.

**Consequence:** at least one catalogued claim genuinely needs morphology, so
**Task 7 was a real Quranic-Arabic-Corpus integration** (root/lemma loader +
`count_by_root` / `count_by_lemma` in `morphology.py`), not a "no morphology
needed" close-out — see `morphology.md` for the dataset, license, and the
per-claim Buckwalter root/lemma codes the Task-8 checks use. Of the 7
`requires_morphology` claims, Task 8 can resolve **5** to match/mismatch; the **2**
that also carry an `ambiguity_note` (`hayat-mawt-equal`, `bahr-barr-water-ratio`)
stay `ambiguous` even with morphology (PRD req 11). A `requires_morphology` claim
resolves to `ambiguous` only if its lemma path is unavailable.

## Verdict mix (honest outcome)

The register deliberately yields a **mix** of outcomes — this is the point of the
project, not a flaw. The final outcome over the 16 catalogued claims is
**7 match / 4 mismatch / 5 ambiguous** (matching `reports/verification.md` and
`architecture.md`):

- **Match (7):** `dunya-115` (115), `qaf-surah50-frequency` (`ق` = 57),
  `basmala-19-letters` (19), `abjad-allah-66` (66), `abjad-basmala-786` (786),
  `allah-first-occurrence-1-1` ((1,1)), `malaika-shayatin-equal` (88 == 88, the one
  morphology-backed match).
- **Mismatch (4):** `yawm-singular-365` (lemma `yawom` = 405), `shahr-month-12`
  (lemma `$ahor` = 21), `ayyam-days-30` (lemma `yawom` = 405 — QAC merges the singular
  and plural into one lemma), `rajul-imraa-equal` (29 vs 26).
- **Ambiguous (5)** (`ambiguity_note` set → the measured value is kept, never forced):
  `sab-seven-heavens` (surface 14), `dunya-akhira-equal` (115 vs 71),
  `noon-surah68-frequency` (131), `hayat-mawt-equal` (76 vs 50, root counts),
  `bahr-barr-water-ratio` (root `bHr` = 42).

## Adding or revising a claim

1. Re-derive the value from the Arabic text with the primitives **before** editing.
2. Add the entry with all schema fields; make `operational_definition` self-contained
   (edition + basmala + diacritic handling + the exact form/lemma counted).
3. Record the measured value in `rederivation_note`; set `requires_morphology` /
   `ambiguity_note` honestly.
4. Validate: `uv run python -c "from quran_analysis.claims import load_register; load_register()"`
   (`extra="forbid"` catches typo'd keys). Run `make lint test`.
