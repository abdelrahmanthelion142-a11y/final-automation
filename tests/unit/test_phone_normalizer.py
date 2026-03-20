"""Unit tests for phone normalizer module."""

import pytest
from src.phone_normalizer import normalize_phone


def test_local_format_11_digits():
    result = normalize_phone("01012345678")
    assert result == "01012345678"


def test_12_digits_with_country_code():
    result = normalize_phone("201012345678")
    assert result == "01012345678"


def test_13_digits_with_plus_country_code():
    result = normalize_phone("+201012345678")
    assert result == "01012345678"


def test_with_spaces():
    result = normalize_phone("010 1234 5678")
    assert result == "01012345678"


def test_empty_phone():
    result = normalize_phone("")
    assert result == "?"


def test_invalid_10_digits():
    result = normalize_phone("1012345678")
    assert result == "1012345678?"


def test_none_phone():
    result = normalize_phone(None)
    assert result == "?"


def test_with_dashes():
    result = normalize_phone("010-1234-5678")
    assert result == "01012345678"


def test_with_parentheses():
    result = normalize_phone("(010)12345678")
    assert result == "01012345678"


def test_13_digit_special_format():
    result = normalize_phone("2201001234560")
    assert result == "01001234560"
