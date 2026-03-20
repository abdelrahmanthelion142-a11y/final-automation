"""Unit tests for doctor translator module."""

import pytest
from src.doctor_translator import translate_doctor, DOCTOR_TRANSLATIONS


def test_known_doctor_first_name():
    DOCTOR_TRANSLATIONS["ahmed"] = "أحمد"
    result = translate_doctor("Ahmed")
    assert result == "أحمد"
    del DOCTOR_TRANSLATIONS["ahmed"]


def test_unknown_doctor_returns_english():
    result = translate_doctor("UnknownDoctor")
    assert result == "UnknownDoctor"


def test_eman_uses_full_name():
    DOCTOR_TRANSLATIONS["eman hassan"] = "إيمان حسن"
    DOCTOR_TRANSLATIONS["eman ali"] = "إيمان علي"

    result1 = translate_doctor("Eman Hassan")
    result2 = translate_doctor("Eman Ali")

    assert result1 == "إيمان حسن"
    assert result2 == "إيمان علي"

    del DOCTOR_TRANSLATIONS["eman hassan"]
    del DOCTOR_TRANSLATIONS["eman ali"]
