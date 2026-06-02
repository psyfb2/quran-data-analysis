# Normalisation

Implemented in `src/quran_analysis/normalize.py` (Task 3). These pure, side-effect-free
string functions are the **leaf** layer of the project. **Every downstream count and
verdict is only meaningful relative to the choices documented here** — there is no
"neutral" normalisation, so each choice is stated explicitly together with its rationale.

The corpus loader stores the original Arabic text **verbatim** (diacritics and Quranic
annotation marks preserved); normalisation happens here, never in the loader. This module
imports nothing from `corpus` (one-directional layering: tooling → corpus + normalisation
→ primitives).

The exact codepoints below were **grounded empirically** against the vendored
`data/tanzil-uthmani.txt` and `data/tanzil-simple-clean.txt` files (not assumed): every
non-letter Arabic-block codepoint actually present was classified as a mark to remove or a
letter to map. The Arabic annotation signs `U+0610`–`U+061A` were **checked and are absent**
from both editions, so they are deliberately *not* in the deletion set.

## Functions and choices

### `strip_tashkeel(text)` — remove diacritics & annotation marks
Removes the combining marks present in the corpus:

| Range / codepoint | What | Why removed |
| --- | --- | --- |
| `U+064B`–`U+065F` | harakat & tanwin (fathatan, damma, kasra, **shadda** `U+0651`, **sukun** `U+0652`, maddah-above `U+0653`, hamza-above `U+0654`, …) | vocalisation marks; absent from Simple-Clean, so they must go for cross-edition form equality |
| `U+0670` | superscript (dagger) alef | treated as a **diacritic** and removed. This is a deliberate choice — it materially affects letter-frequency and abjad counts (Task 4), and Simple-Clean does not carry it |
| `U+06D6`–`U+06DC`, `U+06DF`–`U+06E8`, `U+06EA`–`U+06ED` | Quranic annotation signs (small high marks, pause/stop signs, small low meem, …) | present only in the Uthmani edition; stripping them is **essential** or Uthmani forms would never compare equal to Simple-Clean forms |

Base letters (`U+0621`–`U+064A`, alef-wasla `U+0671`) are never touched here.

### `remove_tatweel(text)` — remove kashida
Deletes the tatweel `U+0640` (`ـ`), a purely cosmetic elongation that carries no lexical
meaning. (Present in the Uthmani edition.)

### `normalize_hamza(text)` — alef / hamza-carrier folding
Folds orthographic variants of the same letter to a base form:

| From | To | Note |
| --- | --- | --- |
| `أ` `U+0623`, `إ` `U+0625`, `آ` `U+0622`, `ٱ` `U+0671` (alef-wasla) | `ا` `U+0627` (alef) | all alef variants → bare alef |
| `ؤ` `U+0624` | `و` `U+0648` | waw-with-hamza → waw |
| `ئ` `U+0626` | `ي` `U+064A` | yeh-with-hamza → yeh |

**Standalone hamza `ء` (`U+0621`) is kept as-is** — it is a distinct grapheme, and
dropping vs keeping it changes counts; keeping it is the conservative default.
Alef-maksura and teh-marbuta are **not** touched by this function (see below).

### `normalize_final_forms(text)` — opt-in final-form folding
Maps `ى` (alef-maksura `U+0649`) → `ي` (`U+064A`) and `ة` (teh-marbuta `U+0629`) →
`ه` (`U+0647`). This is a **separate, opt-in** function and is **deliberately excluded**
from the canonical `normalize()` pipeline, because these mappings materially change counts
and several claims may want the raw forms. Per-claim operational definitions (Task 6) and
counting primitives (Task 4) cite it **explicitly** when they want this behaviour, so it is
never bundled silently.

### `tokenize(text)` — whitespace tokenisation
Uses `str.split()` semantics: collapses runs of any Unicode whitespace and trims, so empty
or whitespace-only input yields `[]`. No normalisation is applied inside the tokeniser
(kept orthogonal — callers compose `tokenize(normalize(text))`).

### `normalize(text)` — canonical pipeline
Fixed, documented order:

```
remove_tatweel → strip_tashkeel → normalize_hamza
```

Tatweel and marks are removed **before** letter-mapping. `normalize_final_forms` is **not**
part of this pipeline. This is the single "normalised surface form" entry point that the
Task 4 counting primitives use.

## Consequences
- A fully-vowelled Uthmani word and its bare Simple-Clean spelling collapse to the **same**
  normalised surface form (this is asserted in the tests), which is what makes cross-edition
  counting coherent.
- Because superscript alef and final-form folding change counts, any claim sensitive to them
  must state its own convention in its operational definition (Task 6) rather than relying on
  a global default.

## Primitives & the abjad table (Task 4)

The counting primitives in `src/quran_analysis/primitives.py` are all defined **relative to
the normalisation above**. Each corpus-scanning primitive applies a `normalizer`
(default `normalize()`) to *both* the corpus surface forms and the query, and threads the
`include_basmala` toggle exposed by the loader. Two conventions are load-bearing:

### Substring matching is intra-word
`count_by_substring` counts **non-overlapping** (`str.count` semantics) occurrences of the
normalised needle **within each normalised word**. Matches never span token boundaries —
spanning would depend on the single-space join artifact and be ambiguous. Empty/whitespace
or diacritic-only needles (which normalise to empty) return `0` (guarding the degenerate
`"".count` behaviour).

### Abjad (gematria) table — standard *Mashriqi*
`abjad_value` normalises first, then sums per-character values:

```
ا1  ب2  ج3  د4  ه5  و6  ز7  ح8  ط9  ي10  ك20  ل30  م40  ن50  س60
ع70 ف80 ص90 ق100 ر200 ش300 ت400 ث500 خ600 ذ700 ض800 ظ900 غ1000
```

`normalize()` does **not** fold the standalone hamza `ء`, alef-maksura `ى` or teh-marbuta
`ة`, so these are mapped **directly** in the table (`ء`→1, `ى`→10 as yeh, `ة`→5 as heh) and
`abjad_value` is well-defined without forcing `normalize_final_forms`. Any character absent
from the table (digits, punctuation, spaces) contributes `0`. Example: `abjad_value("الله")`
= 1 + 30 + 30 + 5 = **66**.
