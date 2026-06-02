# Quran claims — verification report

Verifies or refutes quantifiable numerical/linguistic claims about the **Arabic**
text of the Quran. All analysis is performed against the original Arabic text,
never a translation.

> **Generated file — do not edit by hand.** Regenerate (and re-commit) with
> `make report` after each analysis run.

## Corpus editions

- **Tanzil Simple-Clean** v1.1 (CC BY 3.0) — primary edition for surface-form
  (count / substring / letter-frequency / position) claims.
- **Quranic Arabic Corpus (QAC)** morphology v0.4 (GPL) — root/lemma counts for
  claims that surface forms cannot reproduce.

See `agentdocs/corpus.md` and `agentdocs/morphology.md` for editions/licences.

## Normalisation choices

Surface-form counts use the canonical `normalize()` pipeline: **tatweel removed**,
**tashkeel (diacritics) stripped**, **hamza/alif folded**. Final-form folding
(ى→ي, ة→ه) is **not** applied in the canonical pipeline. Counts are only
meaningful relative to these choices — see `agentdocs/normalisation.md`.

## Verdicts

`match` — the measured value satisfies the asserted claim · `mismatch` — it does
not · `ambiguous` — the counting convention is undisclosed/non-deterministic, or
the claim needs morphology that is unavailable (never forced to match/mismatch).

**Summary:** 7 match / 4 mismatch / 5 ambiguous.


| id | claim | asserted | measured | verdict | operational definition |
| --- | --- | --- | --- | --- | --- |
| yawm-singular-365 | The singular word for "day" (yawm, يوم) is claimed to occur exactly 365 times in the Quran, matching the number of days in a solar year. | 365 | 405 | mismatch | Edition: Tanzil Simple-Clean. Normalisation: canonical normalize() pipeline (tatweel removed, tashkeel stripped, hamza folded; final-form folding NOT applied). Basmala: separated basmalas (suras 2–114 except 9) excluded; the sura-1 basmala counts as aya 1:1. Counted: the singular noun lemma "yawm" across all case endings and attached clitics, EXCLUDING the dual (yawmayn), plurals (ayyam) and the adverbial fused form "yawma'idhin". This is a lemma-level count, not an exact surface-form count — it cannot be reproduced from count_by_form/count_by_substring alone. |
| shahr-month-12 | The singular word for "month" (shahr, شهر) is claimed to occur exactly 12 times, matching the number of months in a year. | 12 | 21 | mismatch | Edition: Tanzil Simple-Clean. Normalisation: canonical normalize() pipeline, no final-form folding. Basmala: separated basmalas excluded. Counted: the singular noun lemma "shahr" across case endings and clitics, EXCLUDING the plural "ashhur"/"shuhur". Lemma-level — not reproducible from surface counts alone. |
| ayyam-days-30 | The plural word for "days" (ayyam, أيام) is claimed to occur 30 times, matching the number of days in a month. | 30 | 405 | mismatch | Edition: Tanzil Simple-Clean. Normalisation: canonical normalize() pipeline (which folds the initial hamza, so "أيام" and "ايام" coincide), no final-form folding. Basmala: separated basmalas excluded. Counted: the plural lemma "ayyam" of yawm across case endings and clitics. Lemma-level — not an exact surface-form count. |
| sab-seven-heavens | The word "seven" (sab', سبع) — as in the seven heavens — is claimed to occur exactly 7 times in the Quran. | 7 | 14 | ambiguous | Edition: Tanzil Simple-Clean. Normalisation: canonical normalize() pipeline, no final-form folding. Basmala: separated basmalas excluded. The popular statement does not disclose whether it counts only the bare cardinal "سبع", or also "سبعا", "سبعة", "سبعون", and feminine/clitic variants, nor whether the restriction is to the "seven heavens" context only. Counted here (for the re-derivation) as the exact normalised surface form "سبع". |
| dunya-115 | The word "this world" (al-dunya, الدنيا) is claimed to occur exactly 115 times. | 115 | 115 | match | Edition: Tanzil Simple-Clean. Normalisation: canonical normalize() pipeline, no final-form folding. Basmala: separated basmalas excluded. Counted: the exact normalised surface form "الدنيا" (definite article attached) via count_by_form. No lemma analysis — a pure surface-form count. |
| dunya-akhira-equal | The words "this world" (al-dunya, الدنيا) and "the hereafter" (al-akhira, الآخرة) are claimed to occur an equal number of times (popularly, 115 each). | equal | 115 vs 71 | ambiguous | Edition: Tanzil Simple-Clean. Normalisation: canonical normalize() pipeline (which folds the hamza/madda so "الآخرة" and "الاخرة" coincide), no final-form folding. Basmala: separated basmalas excluded. Counted: the exact normalised surface forms "الدنيا" and "الآخرة" via count_by_form; the claim holds iff the two counts are equal. |
| hayat-mawt-equal | The words "life" (al-hayat, الحياة) and "death" (al-mawt, الموت) are claimed to occur an equal number of times (popularly, 145 each). | equal | 76 vs 50 | ambiguous | Edition: Tanzil Simple-Clean (REQUIRED here: in Uthmani rasm "life" is spelled الحيوة so its surface form is 0 — see agentdocs/claims-register.md). Normalisation: canonical normalize() pipeline, no final-form folding. Basmala: separated basmalas excluded. The popular "145 each" figure counts every derived form of the roots ح-ي-ي (life) and م-و-ت (death), not just the definite singular nouns; the canonical test therefore needs root/lemma counts. |
| malaika-shayatin-equal | The words "angels" (mala'ika, ملائكة) and "devils/satans" (shayatin, شياطين) are claimed to occur an equal number of times (popularly, 88 each). | equal | 88 vs 88 | match | Edition: Tanzil Simple-Clean (REQUIRED: both words use modern rasm; their Uthmani surface forms are 0). Normalisation: canonical normalize() pipeline, no final-form folding. Basmala: separated basmalas excluded. The popular "88 each" figure counts all derived forms (singular malak/shaytan, plurals, definite and clitic-attached variants) of each lemma, so the canonical test needs lemma counts rather than a single surface form. |
| rajul-imraa-equal | The words "man" (rajul, رجل) and "woman" (imra'a, امرأة) are claimed to occur an equal number of times (popularly, 24 each). | equal | 29 vs 26 | mismatch | Edition: Tanzil Simple-Clean. Normalisation: canonical normalize() pipeline, no final-form folding. Basmala: separated basmalas excluded. The popular "24 each" figure counts the singular lemmas "rajul" (man) and "imra'a" (woman) across case endings and clitics, excluding the plurals "rijal"/"nisa'". A lemma-level count, not an exact surface-form count. |
| bahr-barr-water-ratio | The word "sea" (bahr, بحر) is claimed to occur 32 times and "land" (barr, بر) 13 times, so sea/(sea+land) = 32/45 ≈ 71.1%, matching the proportion of the Earth's surface covered by water. | 32 | 42 | ambiguous | Edition: Tanzil Simple-Clean. Normalisation: canonical normalize() pipeline, no final-form folding. Basmala: separated basmalas excluded. The popular claim counts ALL derived forms of the root b-h-r meaning sea (singular, dual, plural, definite, clitic-attached) as 32, and the forms of b-r-r meaning land as 13 — a lemma/root count. The asserted_value here is the sea figure (32). |
| basmala-19-letters | The basmala "بسم الله الرحمن الرحيم" (bismillah al-rahman al-rahim) is claimed to consist of exactly 19 Arabic letters — the basis of the "Code 19" literature. | 19 | 19 | match | Edition-independent (operates on the literal basmala string, not a corpus scan). Normalisation: canonical normalize() pipeline (tatweel removed, tashkeel stripped, hamza folded), no final-form folding. Counted: the number of non-space characters in normalize("بسم الله الرحمن الرحيم") — i.e. letters only, diacritics and spaces excluded. |
| qaf-surah50-frequency | Surah Qaf (chapter 50), which opens with the disjoined letter ق (qaf), is claimed to contain the letter ق exactly 57 times. | 57 | 57 | match | Edition: Tanzil Simple-Clean. Normalisation: canonical normalize() pipeline (tashkeel stripped so only consonantal skeleton letters are counted), no final-form folding. Scope: surah 50 only. Basmala: the separated basmala prefixed to verse 1 of surah 50 is EXCLUDED (counts cover the numbered ayas of surah 50 only). Counted: occurrences of the character ق across all words of surah 50 via per-sura letter frequency. |
| noon-surah68-frequency | Surah Al-Qalam (chapter 68), which opens with the disjoined letter ن (nun), is examined for the frequency of the letter ن; popularly asserted as 131. | 131 | 131 | ambiguous | Edition: Tanzil Simple-Clean. Normalisation: canonical normalize() pipeline, no final-form folding. Scope: surah 68 only. Basmala: separated basmala of surah 68 EXCLUDED. Counted: occurrences of the character ن across all words of surah 68 via per-sura letter frequency. Note the opening word is written نون ("nun") in full; this surface spelling (two visible ن letters) is what is counted, an orthographic convention that the claim does not always disclose. |
| abjad-allah-66 | The abjad (gematria) value of the divine name "Allah" (الله) is claimed to be 66. | 66 | 66 | match | Edition-independent (operates on the literal string الله, not a corpus scan). Normalisation: canonical normalize() pipeline before summing. Abjad table: the standard Mashriqi values documented in agentdocs/normalisation.md (ا=1, ل=30, ه=5). Value = 1 + 30 + 30 + 5 = 66 (the doubled lam of the ligature counted twice). |
| abjad-basmala-786 | The abjad (gematria) value of the basmala phrase "بسم الله الرحمن الرحيم" (bismillah al-rahman al-rahim) is claimed to be 786. | 786 | 786 | match | Edition-independent (operates on the literal basmala string, not a corpus scan). Normalisation: canonical normalize() pipeline before summing; spaces contribute 0. Abjad table: standard Mashriqi values per agentdocs/normalisation.md. Value = sum of the abjad values of every letter of "بسم الله الرحمن الرحيم". |
| allah-first-occurrence-1-1 | The divine name "Allah" (الله) is claimed to first appear in the opening verse of the Quran (aya 1:1, the basmala). | 1:1 | 1:1 | match | Edition: Tanzil Simple-Clean. Normalisation: canonical normalize() pipeline, no final-form folding. Basmala: the sura-1 basmala IS aya 1:1 and is included (it is a numbered verse). Counted: the (sura, aya) position of the first occurrence of the exact normalised surface form "الله" via first_occurrence_position, scanning in canonical order. |
