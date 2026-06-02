"""Tests for the pure text-normalisation utilities.

These use small inline Arabic literals only — no corpus load — so the suite stays
fast, deterministic and offline. Diacritics / marks are written with explicit
``\\uXXXX`` escapes so each test is unambiguous about which codepoint it exercises.
"""

from __future__ import annotations

from quran_analysis.normalize import (
    normalize,
    normalize_final_forms,
    normalize_hamza,
    remove_tatweel,
    strip_tashkeel,
    tokenize,
)

# --- Reusable literals ----------------------------------------------------------
ALEF = "ا"  # ا
LAM = "ل"  # ل
REH = "ر"  # ر
HAH = "ح"  # ح
MEEM = "م"  # م
NOON = "ن"  # ن

# "الرحمن" fully vowelled, Uthmani-style (shadda, fatha, sukun, superscript alef, kasra).
UTHMANI_RAHMAN = ALEF + LAM + REH + "َّ" + HAH + "ْ" + MEEM + "َٰ" + NOON + "ِ"
# The same word as it appears in the Simple-Clean edition: bare letters only.
SIMPLE_RAHMAN = ALEF + LAM + REH + HAH + MEEM + NOON  # الرحمن


# --- strip_tashkeel -------------------------------------------------------------
def test_strip_tashkeel_removes_all_marks() -> None:
    assert strip_tashkeel(UTHMANI_RAHMAN) == SIMPLE_RAHMAN


def test_strip_tashkeel_diacritic_only_input() -> None:
    # Edge case: input is nothing but diacritics -> empty string.
    assert strip_tashkeel("ًَِّْٰ") == ""


def test_strip_tashkeel_removes_superscript_alef() -> None:
    assert strip_tashkeel(MEEM + "ٰ" + NOON) == MEEM + NOON


def test_strip_tashkeel_removes_quranic_annotation_sign() -> None:
    # U+06DC ARABIC SMALL HIGH SEEN is a Quranic annotation sign present in Uthmani.
    assert strip_tashkeel(MEEM + "ۜ" + NOON) == MEEM + NOON


def test_strip_tashkeel_leaves_letters_untouched() -> None:
    assert strip_tashkeel(SIMPLE_RAHMAN) == SIMPLE_RAHMAN


def test_strip_tashkeel_is_idempotent() -> None:
    once = strip_tashkeel(UTHMANI_RAHMAN)
    assert strip_tashkeel(once) == once


# --- remove_tatweel -------------------------------------------------------------
def test_remove_tatweel_strips_kashida_keeps_letters() -> None:
    # ر ـ ح ـ م  (tatweel U+0640 between letters) -> رحم
    assert remove_tatweel(REH + "ـ" + HAH + "ـ" + MEEM) == REH + HAH + MEEM


def test_remove_tatweel_only_input() -> None:
    assert remove_tatweel("ـــ") == ""


# --- normalize_hamza ------------------------------------------------------------
def test_normalize_hamza_maps_alef_variants() -> None:
    for variant in ("أ", "إ", "آ", "ٱ"):  # أ إ آ ٱ
        assert normalize_hamza(variant) == ALEF


def test_normalize_hamza_maps_waw_and_yeh_carriers() -> None:
    assert normalize_hamza("ؤ") == "و"  # ؤ -> و
    assert normalize_hamza("ئ") == "ي"  # ئ -> ي


def test_normalize_hamza_keeps_standalone_hamza() -> None:
    assert normalize_hamza("ء") == "ء"  # ء unchanged


def test_normalize_hamza_mixed_forms() -> None:
    mixed = "أ" + "ؤ" + "ئ" + "ء"  # أؤئء
    assert normalize_hamza(mixed) == ALEF + "و" + "ي" + "ء"


def test_normalize_hamza_does_not_touch_final_forms() -> None:
    # alef-maksura U+0649 and teh-marbuta U+0629 are out of scope for this function.
    assert normalize_hamza("ى") == "ى"
    assert normalize_hamza("ة") == "ة"


# --- normalize_final_forms ------------------------------------------------------
def test_normalize_final_forms_maps_maksura_and_marbuta() -> None:
    assert normalize_final_forms("ى") == "ي"  # ى -> ي
    assert normalize_final_forms("ة") == "ه"  # ة -> ه


def test_normalize_final_forms_excluded_from_canonical_pipeline() -> None:
    # normalize() must NOT fold final forms; they survive untouched.
    word = MEEM + "ى"  # مى
    assert "ى" in normalize(word)
    marbuta = MEEM + "ة"  # مة
    assert "ة" in normalize(marbuta)


# --- tokenize -------------------------------------------------------------------
def test_tokenize_collapses_mixed_whitespace() -> None:
    assert tokenize("a\t b\n c") == ["a", "b", "c"]


def test_tokenize_empty_string() -> None:
    assert tokenize("") == []


def test_tokenize_whitespace_only() -> None:
    assert tokenize("   \t\n ") == []


def test_tokenize_single_token_and_trims() -> None:
    assert tokenize("  word  ") == ["word"]


# --- normalize (canonical pipeline) ---------------------------------------------
def test_normalize_pipeline_on_uthmani_token() -> None:
    # tatweel + marks + superscript alef collapse to the bare surface form.
    decorated = ALEF + LAM + REH + "ـَّ" + HAH + "ْ" + MEEM + "َٰ" + NOON
    assert normalize(decorated) == SIMPLE_RAHMAN


def test_normalize_makes_editions_equal() -> None:
    # The cross-edition comparability rationale: Uthmani and Simple-Clean forms of
    # the same word must normalise to one identical surface form.
    assert normalize(UTHMANI_RAHMAN) == normalize(SIMPLE_RAHMAN) == SIMPLE_RAHMAN


def test_normalize_folds_alef_wasla() -> None:
    # ٱ (alef-wasla, common in Uthmani) -> ا via the hamza stage of the pipeline.
    assert normalize("ٱ" + LAM) == ALEF + LAM


def test_normalize_is_idempotent() -> None:
    assert normalize(normalize(UTHMANI_RAHMAN)) == normalize(UTHMANI_RAHMAN)


def test_normalize_does_not_mutate_input() -> None:
    # Strings are immutable; assert the original literal is unchanged after calls.
    original = UTHMANI_RAHMAN
    _ = normalize(original)
    assert original == UTHMANI_RAHMAN
