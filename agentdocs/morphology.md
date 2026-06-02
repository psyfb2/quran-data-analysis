# Morphology (root/lemma) integration — Quranic Arabic Corpus

This documents the **optional morphology dataset** (PRD Task 7). It is an
*optional, conditionally-integrated* layer that sits **parallel** to `corpus.py`.

## Decision: morphology WAS required → real integration

PRD req 8 / Task 7 say to integrate a morphological dataset **only if at least one
catalogued claim requires it**. The populated `claims.yaml` (Task 6) flags **7**
claims `requires_morphology: true` (see `claims-register.md`), because their
canonical figure is a *singular-noun lemma* or *root* count that surface-form
counting cannot reproduce (e.g. surface `يوم` = 217, not the claimed 365). So
morphology **was** integrated: a loader + `count_by_root` / `count_by_lemma`
primitives in `src/quran_analysis/morphology.py`, unit-tested in
`tests/test_morphology.py`.

### Which claims morphology resolves vs leaves ambiguous

Of the 7 `requires_morphology: true` claims, the Task-8 runner can resolve only
**5** to `match`/`mismatch` once morphology lands; the other **2** also carry an
`ambiguity_note` and therefore **stay `ambiguous`** even with morphology (PRD
req 11 — undisclosed/non-deterministic conventions are never forced):

- **Can yield match/mismatch (5):** `yawm-singular-365`, `shahr-month-12`,
  `ayyam-days-30`, `malaika-shayatin-equal`, `rajul-imraa-equal`.
- **Remain `ambiguous` (2):** `hayat-mawt-equal`, `bahr-barr-water-ratio`
  (`requires_morphology: true` *and* `ambiguity_note` set). Morphology still lets
  the runner *measure* their root counts for the report.

> **Scope boundary:** Task 7 provides the **data + loader + counting primitives
> only**. Wiring claims to verdicts is Task 8. This module does not edit
> `claims.yaml`, the schema, or `primitives.py`.

## Dataset: edition, source, license

| | |
| --- | --- |
| Dataset | Quranic Arabic Corpus (QAC) — morphology |
| Version | **0.4** (2011), by Kais Dukes |
| File | `data/quranic-corpus-morphology-0.4.txt` (vendored verbatim, ~6.3 MB) |
| Source | `https://corpus.quran.com/download/` (gated behind an email form). Retrieved 2026-06-02 from the public mirror `q-ran/quran` (`sources/1.0/quranic-corpus-morphology-0.4.txt`); the file's own header was verified to state "version 0.4" + the GPL notice before trusting it. |
| License | **GNU General Public License.** "Permission is granted to copy and distribute verbatim copies of this file, but **CHANGING IT IS NOT ALLOWED**", and the Quranic Arabic Corpus must be clearly indicated with a link to <https://corpus.quran.com>. The QAC builds on the Tanzil Uthmani text and retains its copyright block (the *embedded* edition is Tanzil **v1.0.2**, whose own header states CC BY-ND 3.0 — note this is a different/older edition than the standalone CC BY 3.0 v1.1 files documented in `corpus.md`). |

The file is **vendored verbatim** (header/license preamble bytes intact, never
mutated) and committed so tests/CI run offline, exactly like the Tanzil editions.

### License-mixing note

The repo **code** is MIT; this QAC **data file** is GPL. Vendoring a GPL *data
file* verbatim alongside MIT *code* is **mere aggregation** — it does **not**
relicense the code. The QAC file keeps its own license header; the standalone
Tanzil files (CC BY 3.0 — see line above for the *embedded* v1.0.2's CC BY-ND 3.0)
are a separate, separately-documented data license (see `corpus.md`). No code in
this repo is derived from the GPL data.

## File format (re-derived empirically from the vendored file)

- A `#`-comment **preamble** (QAC + Tanzil copyright blocks) precedes a single
  TAB-separated column header line `LOCATION\tFORM\tTAG\tFEATURES`; data rows
  follow. The loader skips every `#` line, blank lines, and any line not starting
  with `(` (so the header and any footer are skipped).
- Each data row is one **segment**:
  `(sura:aya:word:segment)\tFORM\tTAG\tFEATURES`. `LOCATION` is 1-based and
  parenthesised. `FORM` is the Buckwalter surface form of that segment.
- `FEATURES` is `|`-delimited. The **stem** segment carries `ROOT:`, `LEM:` and
  `POS:` features; **prefix/suffix** segments do not. Example stem features:
  `STEM|POS:N|LEM:yawom|ROOT:ywm|M|GEN`.
- **ROOT and LEM are Buckwalter-encoded ASCII** (e.g. root `ywm`, lemma `yawom`),
  *not* Arabic script.

### Segment → word aggregation

One *word* `(sura, aya, word)` spans multiple *segments* (prefix / stem / suffix).
The loader collapses them into a single `MorphologyWord`, taking `root` / `lemma`
/ `pos` and the stored `form` from the **stem** segment (the first segment
carrying any of `ROOT:`/`LEM:`/`POS:`; a word has at most one). Words with no such
segment — pure function words (particles) — get `root=None` / `lemma=None` /
`pos=None` and never match a count.

### Basmala alignment (verified)

QAC is built on the Uthmani text. Empirically: **sura 1's basmala IS the words of
aya `1:1`** (a counted verse), and **suras 2-114 do *not* repeat the opening
basmala as words** (verse `2:1` begins directly with the muqatta'at `Al^m^`). This
matches the morphology claims' "separated basmalas excluded" operational
definition. The structural guard (114 suras / 6236 ayas) pins QAC's verse
numbering against `corpus.py`. The day/month/life/death lemmas are not basmala
words, so the claim counts are robust regardless.

## Public API (`src/quran_analysis/morphology.py`)

```python
DATA_DIR: Path                       # repo-root data/ (mirrors corpus.DATA_DIR)
MORPHOLOGY_FILE = "quranic-corpus-morphology-0.4.txt"

@dataclass(frozen=True)
class MorphologyWord:
    sura: int; aya: int; word: int
    form: str
    root: str | None; lemma: str | None; pos: str | None   # Buckwalter, raw

@dataclass(frozen=True)
class Morphology:
    words: tuple[MorphologyWord, ...]
    def word(self, sura, aya, word) -> MorphologyWord       # KeyError if missing

load_morphology(*, data_dir=DATA_DIR) -> Morphology         # data_dir = synthetic-fixture hook
count_by_root(morphology, root: str) -> int                 # exact Buckwalter match; empty/ws -> 0
count_by_lemma(morphology, lemma: str) -> int               # exact Buckwalter match; empty/ws -> 0
```

`load_morphology` validates the parse with an **edition-independent structural
guard**: distinct suras must be exactly `{1..114}` and distinct `(sura, aya)`
pairs must equal `6236`. Word-index contiguity is **not** asserted (QAC omits some
word positions, so a 1..k check would falsely fail). `data_dir` overrides the data
directory for synthetic fixtures, mirroring `load_corpus`.

## Buckwalter vs Arabic — query representation (decision)

QAC stores root/lemma in **Buckwalter transliteration** (ASCII); the rest of the
codebase is Arabic-native. **Decision: store and match on the raw Buckwalter
strings** (KISS, lossless, deterministic). Converting Buckwalter→Arabic at load
time was rejected: lemmas carry short-vowel/sukun diacritics (`a u i o`) that map
ambiguously/lossily to Arabic script and would risk silent mismatches. Buckwalter
is exact and testable.

Consequently, the **Task-8 claim checks pass Buckwalter literals**. The relevant
codes for the 7 morphology claims, **re-derived empirically** from the vendored
file (counts as of QAC 0.4):

| Claim | Concept | Buckwalter ROOT | Buckwalter LEM (head form) | `count_by_root` | `count_by_lemma` |
| --- | --- | --- | --- | --- | --- |
| `yawm-singular-365` | day (singular) | `ywm` | `yawom` | 405 | 405 |
| `ayyam-days-30` | days (plural) | `ywm` | `yawom` | 405 | 405 |
| `shahr-month-12` | month | `$hr` | `$ahor` | 21 | 21 |
| `hayat-mawt-equal` | life | `Hyy` | `Hayaw`p` (حياة) | 184 | 76 |
| `hayat-mawt-equal` | death | `mwt` | `mawot` | 165 | 50 |
| `malaika-shayatin-equal` | angels | `mlk` | `malak` | 206 | 88 |
| `malaika-shayatin-equal` | devils | `$Tn` | `$ayoTa`n` | 88 | 88 |
| `rajul-imraa-equal` | man | `rjl` | `rajul` | 73 | 29 |
| `rajul-imraa-equal` | woman | `mrA` | `{mora>at` | 38 | 26 |
| `bahr-barr-water-ratio` | sea | `bHr` | `baHor` | 42 | 41 |
| `bahr-barr-water-ratio` | land | `brr` | `bar~` | 32 | 22 |

> **Finding for Task 8 (day/days):** QAC lemmatises *both* the singular `يوم` and
> the plural `أيام` to the **same** lemma `yawom` under root `ywm` (there is no
> distinct plural lemma). So `count_by_lemma("yawom")` (405) covers singular **and**
> plural, and cannot by itself isolate the singular "365" or plural "30" figures.
> Task 8 must decide the operational interpretation per claim (and may well land on
> `mismatch`/`ambiguous`); Task 7 only supplies the mechanism, not the verdict.
> The codes above are exact Buckwalter strings — copy them verbatim into checks.

## Tests (`tests/test_morphology.py`)

- **Synthetic fixtures** (`tmp_path`, parsed via the public parse/aggregate
  helpers): exact `count_by_root`/`count_by_lemma`, multi-segment word collapse,
  stem root/lemma/pos extraction, particle → `None`, and edge cases (unknown /
  empty / whitespace query → 0; unknown key → `KeyError`; empty model; malformed
  line and partial-span `ValueError`).
- **One module-scoped real-data anchor**: re-derived structural facts only
  (114 suras / 6236 ayas; a root count re-derived two ways and `> 0`; root ≥ lemma
  invariant; basmala-only-in-sura-1). It deliberately does **not** assert any
  lemma equals 365/12/30 — that comparison is the Task-8 runner's job.
