"""Unit tests for message generator module."""

import pytest
from src.message_generator import generate_message, get_verb_form


class TestGetVerbForm:
    """Tests for get_verb_form function."""

    def test_female_returns_female_verb(self):
        result = get_verb_form("Female")
        assert result == "تكوني"

    def test_male_returns_male_verb(self):
        result = get_verb_form("Male")
        assert result == "تكون"

    def test_empty_returns_male_verb(self):
        result = get_verb_form("")
        assert result == "تكون"

    def test_unknown_returns_male_verb(self):
        result = get_verb_form("Unknown")
        assert result == "تكون"

    def test_none_returns_male_verb(self):
        result = get_verb_form(None)
        assert result == "تكون"

    def test_case_sensitive_female(self):
        result = get_verb_form("female")
        assert result == "تكون"

    def test_whitespace_handled(self):
        result = get_verb_form(" Female ")
        assert result == "تكون"


class TestGenerateMessage:
    """Tests for generate_message function."""

    def test_female_message(self):
        row = {
            "Patient": "سارة",
            "Gender": "Female",
            "DoctorArabic": "آية",
            "Doctor": "آية",
        }
        result = generate_message(row)
        assert "تكوني" in result
        assert "سارة" in result

    def test_male_message(self):
        row = {
            "Patient": "أحمد",
            "Gender": "Male",
            "DoctorArabic": "محمد",
            "Doctor": "محمد",
        }
        result = generate_message(row)
        assert "تكون" in result
        assert "أحمد" in result

    def test_unknown_gender_defaults_male(self):
        row = {
            "Patient": "محمد",
            "Gender": "",
            "DoctorArabic": "محمد",
            "Doctor": "محمد",
        }
        result = generate_message(row)
        assert "تكون" in result

    def test_doctor_aya_no_prefix(self):
        row = {
            "Patient": "أحمد",
            "Gender": "Male",
            "DoctorArabic": "آية",
            "Doctor": "آية",
        }
        result = generate_message(row)
        assert "د/" not in result
        assert "آية" in result

    def test_regular_doctor_has_prefix(self):
        row = {
            "Patient": "أحمد",
            "Gender": "Male",
            "DoctorArabic": "سارة",
            "Doctor": "سارة",
        }
        result = generate_message(row)
        assert "د/سارة" in result

    def test_message_contains_wellskin(self):
        row = {
            "Patient": "أحمد",
            "Gender": "Male",
            "DoctorArabic": "محمد",
            "Doctor": "محمد",
        }
        result = generate_message(row)
        assert "Wellskin" in result

    def test_message_contains_arabic_greeting(self):
        row = {
            "Patient": "أحمد",
            "Gender": "Male",
            "DoctorArabic": "محمد",
            "Doctor": "محمد",
        }
        result = generate_message(row)
        assert "مساء" in result

    def test_patient_name_in_message(self):
        row = {
            "Patient": "محمد حسن",
            "Gender": "Male",
            "DoctorArabic": "أحمد",
            "Doctor": "أحمد",
        }
        result = generate_message(row)
        assert "محمد حسن" in result

    def test_doctor_name_in_message(self):
        row = {
            "Patient": "أحمد",
            "Gender": "Male",
            "DoctorArabic": "محمد عبد الوهاب",
            "Doctor": "محمد عبد الوهاب",
        }
        result = generate_message(row)
        assert "محمد عبد الوهاب" in result

    def test_female_verb_for_female_patient(self):
        row = {
            "Patient": "سارة",
            "Gender": "Female",
            "DoctorArabic": "آية",
            "Doctor": "آية",
        }
        result = generate_message(row)
        assert "تكوني" in result
        assert "تكون" not in result or result.count("تكون") == result.count("تكوني")

    def test_male_verb_for_male_patient(self):
        row = {
            "Patient": "أحمد",
            "Gender": "Male",
            "DoctorArabic": "محمد",
            "Doctor": "محمد",
        }
        result = generate_message(row)
        assert "تكون" in result
        assert "تكوني" not in result
