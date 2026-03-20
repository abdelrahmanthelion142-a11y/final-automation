"""Unit tests for gender classifier module."""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

from src.gender_classifier import (
    classify_from_csv,
    classify_from_ai,
    classify_genders,
    update_gender_csv,
    PatientGender,
    PatientGenderList,
)


class TestClassifyFromCsv:
    """Tests for classify_from_csv function."""

    def test_csv_lookup_finds_known_names(self):
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

    def test_csv_lookup_returns_empty_for_unknown(self):
        gender_df = pd.DataFrame(
            [
                {"Patient": "أحمد", "Gender": "Male"},
            ]
        )

        result = classify_from_csv(["محمد"], gender_df)

        assert result == {}

    def test_csv_lookup_empty_dataframe(self):
        gender_df = pd.DataFrame(columns=["Patient", "Gender"])

        result = classify_from_csv(["أحمد"], gender_df)

        assert result == {}

    def test_csv_lookup_normalizes_gender_capitalization(self):
        gender_df = pd.DataFrame(
            [
                {"Patient": "أحمد", "Gender": "male"},
                {"Patient": "سارة", "Gender": "female"},
            ]
        )

        result = classify_from_csv(["أحمد", "سارة"], gender_df)

        assert result["أحمد"] == "Male"
        assert result["سارة"] == "Female"

    def test_csv_lookup_handles_empty_names(self):
        gender_df = pd.DataFrame(
            [
                {"Patient": "أحمد", "Gender": "Male"},
            ]
        )

        result = classify_from_csv([], gender_df)

        assert result == {}


class TestClassifyFromAi:
    """Tests for classify_from_ai function."""

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    @patch("src.gender_classifier.OpenAI")
    def test_classify_from_ai_returns_mapping(self, mock_openai, mock_openai_response):
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = mock_openai_response({"أحمد": "Male", "سارة": "Female"})
        mock_client.responses.parse.return_value = mock_response

        result = classify_from_ai(["أحمد", "سارة"])

        assert result["أحمد"] == "Male"
        assert result["سارة"] == "Female"

    @patch("src.gender_classifier.OpenAI")
    def test_classify_from_ai_empty_list(self, mock_openai):
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        result = classify_from_ai([])

        assert result == {}
        mock_client.responses.parse.assert_not_called()

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    @patch("src.gender_classifier.OpenAI")
    def test_classify_from_ai_uses_original_names(
        self, mock_openai, mock_openai_response
    ):
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = mock_openai_response({"أحمد": "Male"})
        mock_client.responses.parse.return_value = mock_response

        result = classify_from_ai(["أحمد"])

        assert "أحمد" in result

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    @patch("src.gender_classifier.OpenAI")
    def test_classify_from_ai_handles_exception(self, mock_openai):
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.responses.parse.side_effect = Exception("API Error")

        with pytest.raises(Exception):
            classify_from_ai(["أحمد"])


class TestClassifyGenders:
    """Tests for classify_genders function."""

    def test_classify_genders_with_known_names(self, sample_gender_df):
        df = pd.DataFrame(
            [
                {"Patient": "أحمد محمد", "_first_name": "أحمد"},
                {"Patient": "سارة علي", "_first_name": "سارة"},
            ]
        )

        result = classify_genders(df, sample_gender_df)

        assert "Gender" in result.columns
        assert result.iloc[0]["Gender"] == "Male"
        assert result.iloc[1]["Gender"] == "Female"

    def test_classify_genders_with_unknown_names(self):
        gender_df = pd.DataFrame(columns=["Patient", "Gender"])

        df = pd.DataFrame(
            [
                {"Patient": "محمد", "_first_name": "محمد"},
            ]
        )

        with patch("src.gender_classifier.classify_from_ai") as mock_ai:
            mock_ai.return_value = {"محمد": "Male"}

            result = classify_genders(df, gender_df)

            assert result.iloc[0]["Gender"] == "Male"

    def test_classify_genders_preserves_other_columns(self):
        gender_df = pd.DataFrame(
            [
                {"Patient": "أحمد", "Gender": "Male"},
            ]
        )

        df = pd.DataFrame(
            [
                {"Patient": "أحمد محمد", "Date": "2024-01-15", "_first_name": "أحمد"},
            ]
        )

        result = classify_genders(df, gender_df)

        assert "Date" in result.columns
        assert result.iloc[0]["Date"] == "2024-01-15"

    def test_classify_genders_empty_dataframe(self):
        gender_df = pd.DataFrame(columns=["Patient", "Gender"])
        df = pd.DataFrame(columns=["Patient", "_first_name"])

        result = classify_genders(df, gender_df)

        assert len(result) == 0
        assert "Gender" in result.columns


class TestUpdateGenderCsv:
    """Tests for update_gender_csv function."""

    def test_update_csv_adds_new_entries(self):
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

    def test_update_csv_deduplicates(self):
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

    def test_update_csv_empty_new_classifications(self):
        gender_df = pd.DataFrame(
            [
                {"Patient": "أحمد", "Gender": "Male"},
            ]
        )

        result = update_gender_csv(gender_df, {})

        assert len(result) == 1
        assert "أحمد" in result["Patient"].values

    def test_update_csv_sorts_result(self):
        gender_df = pd.DataFrame(
            [
                {"Patient": "محمد", "Gender": "Male"},
            ]
        )

        new_classifications = {"أحمد": "Male", "سارة": "Female"}

        result = update_gender_csv(gender_df, new_classifications)

        patients = result["Patient"].tolist()
        assert patients == sorted(patients)

    def test_update_csv_empty_dataframe(self):
        gender_df = pd.DataFrame(columns=["Patient", "Gender"])

        new_classifications = {"أحمد": "Male"}

        result = update_gender_csv(gender_df, new_classifications)

        assert len(result) == 1
        assert result.iloc[0]["Patient"] == "أحمد"
        assert result.iloc[0]["Gender"] == "Male"
