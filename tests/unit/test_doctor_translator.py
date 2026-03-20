"""Unit tests for doctor translator module."""

import pytest
from src.doctor_translator import (
    translate_doctor,
    DOCTOR_TRANSLATIONS,
    FULL_NAME_DOCTORS,
)


class TestTranslateDoctor:
    """Tests for translate_doctor function."""

    def test_known_doctor_first_name(self):
        DOCTOR_TRANSLATIONS["testahmed"] = "أحمد"
        try:
            result = translate_doctor("TestAhmed")
            assert result == "أحمد"
        finally:
            del DOCTOR_TRANSLATIONS["testahmed"]

    def test_unknown_doctor_returns_english(self):
        result = translate_doctor("UnknownDoctor")
        assert result == "UnknownDoctor"

    def test_eman_uses_full_name(self):
        result = translate_doctor("Eman Ahmed")
        assert result == "إيمان أحمد"

    def test_mohamed_uses_full_name(self):
        result = translate_doctor("Mohamed Ashour")
        assert result == "محمد عاشور"

    def test_ayaa_no_prefix(self):
        result = translate_doctor("Ayaa")
        assert result == "آية"

    def test_regular_doctor_has_translation(self):
        DOCTOR_TRANSLATIONS["testsamar"] = "سمر"
        try:
            result = translate_doctor("TestSamar")
            assert result == "سمر"
        finally:
            del DOCTOR_TRANSLATIONS["testsamar"]

    def test_whitespace_handling(self):
        DOCTOR_TRANSLATIONS["testwhitespace"] = "اختبار"
        try:
            result = translate_doctor("  TestWhitespace  ")
            assert result == "اختبار"
        finally:
            del DOCTOR_TRANSLATIONS["testwhitespace"]

    def test_whitespace_string_raises_error(self):
        with pytest.raises(IndexError):
            translate_doctor("   ")

    def test_case_insensitive_lookup(self):
        DOCTOR_TRANSLATIONS["testcase"] = "اختبار"
        try:
            result1 = translate_doctor("TestCase")
            result2 = translate_doctor("TESTCASE")
            result3 = translate_doctor("testcase")
            assert result1 == "اختبار"
            assert result2 == "اختبار"
            assert result3 == "اختبار"
        finally:
            del DOCTOR_TRANSLATIONS["testcase"]

    def test_existing_translations_preserved(self):
        original_count = len(DOCTOR_TRANSLATIONS)
        translate_doctor("Ayaa")
        assert len(DOCTOR_TRANSLATIONS) == original_count

    def test_full_name_doctors_constant_contains_eman(self):
        assert "eman" in FULL_NAME_DOCTORS

    def test_full_name_doctors_constant_contains_mohamed(self):
        assert "mohamed" in FULL_NAME_DOCTORS

    def test_first_name_doctor_uses_first_name_only(self):
        DOCTOR_TRANSLATIONS["testsara"] = "سارة"
        try:
            result = translate_doctor("TestSara MiddleName")
            assert result == "سارة"
        finally:
            del DOCTOR_TRANSLATIONS["testsara"]


class TestDoctorTranslations:
    """Tests for DOCTOR_TRANSLATIONS dictionary."""

    def test_dictionary_is_not_empty(self):
        assert len(DOCTOR_TRANSLATIONS) > 0

    def test_all_values_are_strings(self):
        for key, value in DOCTOR_TRANSLATIONS.items():
            assert isinstance(value, str)

    def test_all_keys_are_lowercase(self):
        for key in DOCTOR_TRANSLATIONS.keys():
            assert key == key.lower(), f"Key '{key}' is not lowercase"


class TestFullNameDoctors:
    """Tests for FULL_NAME_DOCTORS constant."""

    def test_is_set(self):
        assert isinstance(FULL_NAME_DOCTORS, set)

    def test_contains_eman(self):
        assert "eman" in FULL_NAME_DOCTORS

    def test_contains_mohamed(self):
        assert "mohamed" in FULL_NAME_DOCTORS
