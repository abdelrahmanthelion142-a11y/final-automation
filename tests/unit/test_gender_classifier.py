"""Unit tests for gender classifier module."""

import pytest
import pandas as pd
from src.gender_classifier import classify_from_csv, update_gender_csv


def test_csv_lookup_finds_known_names():
    gender_df = pd.DataFrame(
        [
            {"Patient": "أحمد", "Gender": "Male"},
            {"Patient": "سارة", "Gender": "Female"},
        ]
    )

    result = classify_from_csv(["أحمد", "سارة", "محمد"], gender_df)

    assert result["أحمد"] == "Male"
    assert result["سارة"] == "Female"
    assert "محمد" not in result


def test_csv_lookup_returns_empty_for_unknown():
    gender_df = pd.DataFrame(
        [
            {"Patient": "أحمد", "Gender": "Male"},
        ]
    )

    result = classify_from_csv(["محمد"], gender_df)

    assert result == {}


def test_update_csv_adds_new_entries():
    gender_df = pd.DataFrame(
        [
            {"Patient": "أحمد", "Gender": "Male"},
        ]
    )

    new_classifications = {"سارة": "Female", "محمد": "Male"}

    result = update_gender_csv(gender_df, new_classifications)

    assert len(result) == 3
    assert "سارة" in result["Patient"].values
    assert "محمد" in result["Patient"].values


def test_update_csv_deduplicates():
    gender_df = pd.DataFrame(
        [
            {"Patient": "أحمد", "Gender": "Male"},
        ]
    )

    new_classifications = {"أحمد": "Female"}

    result = update_gender_csv(gender_df, new_classifications)

    أحمد_rows = result[result["Patient"] == "أحمد"]
    assert len(أحمد_rows) == 1
    assert أحمد_rows.iloc[0]["Gender"] == "Female"
