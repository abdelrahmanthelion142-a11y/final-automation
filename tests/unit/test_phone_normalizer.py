"""Unit tests for phone normalizer module."""

import pytest
import pandas as pd
from src.phone_normalizer import normalize_phone, normalize_phones, is_valid_phone


class TestIsValidPhone:
    """Tests for is_valid_phone function."""

    def test_valid_10_digits(self):
        assert is_valid_phone("0101234567") == True

    def test_valid_11_digits(self):
        assert is_valid_phone("01012345678") == True

    def test_valid_12_digits(self):
        assert is_valid_phone("201012345678") == True

    def test_valid_13_digits(self):
        assert is_valid_phone("+201012345678") == True

    def test_valid_14_digits(self):
        assert is_valid_phone("22010123456780") == True

    def test_valid_15_digits(self):
        assert is_valid_phone("201012345678901") == True

    def test_invalid_8_digits(self):
        assert is_valid_phone("01234567") == False

    def test_invalid_16_digits(self):
        assert is_valid_phone("0123456789012345") == False


class TestNormalizePhone:
    """Tests for normalize_phone function."""

    def test_local_format_11_digits(self):
        result = normalize_phone("01012345678")
        assert result == "01012345678"

    def test_12_digits_with_country_code(self):
        result = normalize_phone("201012345678")
        assert result == "01012345678"

    def test_13_digits_with_plus_country_code(self):
        result = normalize_phone("+201012345678")
        assert result == "01012345678"

    def test_with_spaces(self):
        result = normalize_phone("010 1234 5678")
        assert result == "01012345678"

    def test_empty_phone(self):
        result = normalize_phone("")
        assert result == "?"

    def test_invalid_10_digits(self):
        result = normalize_phone("1012345678")
        assert result == "1012345678?"

    def test_none_phone(self):
        result = normalize_phone(None)
        assert result == "?"

    def test_with_dashes(self):
        result = normalize_phone("010-1234-5678")
        assert result == "01012345678"

    def test_with_parentheses(self):
        result = normalize_phone("(010)12345678")
        assert result == "01012345678"

    def test_13_digit_special_format(self):
        result = normalize_phone("2201001234560")
        assert result == "01001234560"

    def test_14_digit_format(self):
        result = normalize_phone("22010012345670")
        assert result == "01001234567"

    def test_invalid_15_digits(self):
        result = normalize_phone("201012345678901")
        assert result == "201012345678901?"

    def test_too_short_returns_flagged(self):
        result = normalize_phone("123")
        assert result == "123?"

    def test_with_multiple_spaces(self):
        result = normalize_phone("010   1234   5678")
        assert result == "01012345678"

    def test_with_tabs(self):
        result = normalize_phone("010\t1234\t5678")
        assert result == "01012345678"

    def test_mixed_formatting(self):
        result = normalize_phone(" (010) - 1234 - 5678 ")
        assert result == "01012345678"

    def test_international_with_plus(self):
        result = normalize_phone("+201012345678")
        assert result == "01012345678"

    def test_international_without_plus(self):
        result = normalize_phone("201012345678")
        assert result == "01012345678"

    def test_invalid_11_digits_no_leading_zero(self):
        result = normalize_phone("10123456789")
        assert result == "10123456789?"

    def test_invalid_12_digits_no_leading_zero_after_strip(self):
        result = normalize_phone("210123456789")
        assert result == "210123456789?"


class TestNormalizePhones:
    """Tests for normalize_phones function (DataFrame version)."""

    def test_normalize_phones_basic(self):
        df = pd.DataFrame(
            [
                {"PhoneNumber": "01012345678"},
                {"PhoneNumber": "+201023456789"},
            ]
        )

        result = normalize_phones(df)

        assert result.iloc[0]["PhoneNumber"] == "01012345678"
        assert result.iloc[1]["PhoneNumber"] == "01023456789"

    def test_normalize_phones_preserves_other_columns(self):
        df = pd.DataFrame(
            [
                {"Patient": "Ahmed", "PhoneNumber": "01012345678"},
                {"Patient": "Sara", "PhoneNumber": "+201023456789"},
            ]
        )

        result = normalize_phones(df)

        assert "Patient" in result.columns
        assert result.iloc[0]["Patient"] == "Ahmed"
        assert result.iloc[1]["Patient"] == "Sara"

    def test_normalize_phones_handles_invalid(self):
        df = pd.DataFrame(
            [
                {"PhoneNumber": "01012345678"},
                {"PhoneNumber": "invalid"},
            ]
        )

        result = normalize_phones(df)

        assert result.iloc[0]["PhoneNumber"] == "01012345678"
        assert result.iloc[1]["PhoneNumber"] == "invalid?"

    def test_normalize_phones_handles_empty(self):
        df = pd.DataFrame(
            [
                {"PhoneNumber": ""},
                {"PhoneNumber": "01012345678"},
            ]
        )

        result = normalize_phones(df)

        assert result.iloc[0]["PhoneNumber"] == "?"
        assert result.iloc[1]["PhoneNumber"] == "01012345678"

    def test_normalize_phones_handles_none(self):
        df = pd.DataFrame(
            [
                {"PhoneNumber": None},
                {"PhoneNumber": "01012345678"},
            ]
        )

        result = normalize_phones(df)

        assert result.iloc[0]["PhoneNumber"] == "?"
        assert result.iloc[1]["PhoneNumber"] == "01012345678"

    def test_normalize_phones_empty_dataframe(self):
        df = pd.DataFrame(columns=["PhoneNumber"])

        result = normalize_phones(df)

        assert len(result) == 0
        assert "PhoneNumber" in result.columns
