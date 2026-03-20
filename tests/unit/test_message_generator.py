"""Unit tests for message generator module."""

import pytest
from src.message_generator import generate_message


def test_female_message():
    result = generate_message("أحمد", "Female", "سارة", "2024-01-15")
    assert "تكوني" in result
    assert "أحمد" in result
    assert "سارة" in result


def test_male_message():
    result = generate_message("أحمد", "Male", "محمد", "2024-01-15")
    assert "تكون" in result
    assert "أحمد" in result
    assert "محمد" in result


def test_unknown_gender_defaults_male():
    result = generate_message("أحمد", "", "محمد", "2024-01-15")
    assert "تكون" in result


def test_doctor_aya_no_prefix():
    result = generate_message("أحمد", "Male", "آية", "2024-01-15")
    assert "د/" not in result
    assert "آية" in result


def test_regular_doctor_has_prefix():
    result = generate_message("أحمد", "Male", "سارة", "2024-01-15")
    assert "د/سارة" in result
