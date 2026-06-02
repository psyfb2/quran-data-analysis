# Corpus

The vendored Arabic Quran text and how the loader (`src/quran_analysis/corpus.py`)
parses it. **All analysis uses the original Arabic text only — never a translation.**

## Editions (vendored, committed for offline CI)

Two [Tanzil Project](https://tanzil.net) plain-text editions are committed under `data/`:

| File | Edition | Role | Version | Size |
| --- | --- | --- | --- | --- |
| `data/tanzil-uthmani.txt` | Tanzil Uthmani | **primary** | 1.1 | ~1.3 MB |
| `data/tanzil-simple-clean.txt` | Tanzil Simple Clean | secondary | 1.1 | ~0.76 MB |

- **Downloaded:** 2026-06-02, via the Tanzil download endpoint (`txt-2` =
  pipe-delimited `sura|aya|text` with verse markers):
  - Uthmani: `https://tanzil.net/pub/download/index.php?quranType=uthmani&outType=txt-2&agree=true`
  - Simple-Clean: `https://tanzil.net/pub/download/index.php?quranType=simple-clean&outType=txt-2&agree=true`
- Files are committed **verbatim**, including the trailing `#`-comment copyright
  footer, so the license travels with the data.

### License / attribution

Tanzil Quran Text, Copyright © 2007–2026 Tanzil Project — **Creative Commons
Attribution 3.0**. Terms of use (reproduced from the file footer):

- Verbatim copies may be copied and distributed, but **changing the text is not allowed**.
- May be used in any website/application **provided the source (Tanzil Project) is
  clearly indicated and a link is made to <https://tanzil.net>**.
- The copyright notice must be included in all verbatim copies and reproduced in
  derived files — hence the footer is kept inside each vendored file.

The loader reads the text verbatim and never mutates the vendored files.

## File format

Each data line is `sura|aya|text`, e.g. `1|1|بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ`.
Blank lines and `#`-comment lines (the footer) are skipped. Files are read with
`encoding="utf-8-sig"` to tolerate a possible UTF-8 BOM.

## Structural counts (both editions, re-derived in tests)

- **114** suras, numbered contiguously `1..114`.
- **6236** numbered ayas total; aya numbers are contiguous `1..k` within each sura.
- These are asserted both as canonical literals and re-derived from the parsed
  file (`tests/test_corpus.py`), so vendored-data drift fails loudly.

## In-memory model

Immutable, hashable frozen dataclasses (no runtime dependency added):

```
Word(text, sura, aya, position)            # original Arabic, verbatim (diacritics kept)
Aya(sura, number, words)                   # .text -> words joined on a space
Sura(number, ayas, separated_basmala)      # separated_basmala: tuple | None
Corpus(edition, suras)                      # .sura(n) / .aya(s,a) / .words(...) / .text(...)
```

- `Word.text` keeps the **original** Arabic verbatim; normalisation belongs to the
  normalisation/primitives layers (Tasks 3/4) — `corpus.py` imports no `normalize`.
- `DATA_DIR = Path(__file__).resolve().parents[2] / "data"` resolves the repo-root
  `data/` dir under `pythonpath=["src"]`, `make`, and CI. `load_corpus(edition, *,
  data_dir=...)` accepts a `data_dir` override so later tasks can point at synthetic
  fixtures.
- Selectors: `Corpus.sura(n)`, `Corpus.aya(sura, aya)` (raise `KeyError` on unknown
  keys), `Corpus.words(*, include_basmala=False)`, `Corpus.text(...)`, plus
  `Sura.words(...)/.text(...)` and `Aya.words/.text`.

## Basmala handling (the load-bearing subtlety)

The opening basmala (بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ, exactly **4 tokens**) is made
**individually addressable** so any per-claim counting convention can be applied:

- **Sura 1:** the basmala **is** aya `1:1` — a counted verse. `separated_basmala` is
  `None`; `Sura.basmala` returns aya 1's words.
- **Suras 2–114 except 9:** the source **prepends** the basmala to verse 1's text;
  the loader splits it into `Sura.separated_basmala` (sentinel **`aya=0`**, exposed as
  the constant `BASMALA_AYA`) and verse 1's content words start *after* it. There are
  **112** such suras → `words(include_basmala=True)` adds 112 × 4 = **448** words over
  `words()` (sura 1 is never double-counted).
- **Sura 9** (At-Tawbah): no basmala — `separated_basmala` and `Sura.basmala` are `None`.
- **Aya 27:30** contains the basmala phrase as genuine mid-verse content (Solomon's
  letter). Detection is **verse-1-only**, so 27:30 is never split.

**Detection:** verse-1-only, suras ∉ {1, 9}, using sura 1's own basmala as the
reference (edition-agnostic, no hard-coded strings). Only the **trailing three tokens**
(`ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ`) must match exactly; the first token (`bismi`) is matched
loosely because the **Uthmani** edition spells it with a shadda variant (`بِّسْمِ` vs
`بِسْمِ`) in **suras 95 and 97**. The first token is still stored verbatim. This is safe
because every sura except 9 opens with the basmala.
