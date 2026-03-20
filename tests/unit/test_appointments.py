"""Unit tests for appointments fetcher module."""

import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
import httpx

from src.appointments import fetch_appointments


class TestFetchAppointments:
    """Tests for fetch_appointments function."""

    @patch("src.appointments.httpx.post")
    @patch.dict("os.environ", {"EHR_TOKEN": "test-token"})
    def test_fetch_appointments_success(
        self, mock_post, sample_appointments_api_response
    ):
        mock_response = MagicMock()
        mock_response.json.return_value = sample_appointments_api_response
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = fetch_appointments(
            "2024-01-01T00:00:00.000Z", "2024-01-31T23:59:59.000Z"
        )

        assert len(result) == 2
        assert "Patient" in result.columns
        assert "Date" in result.columns
        assert "Doctor" in result.columns
        assert "PhoneNumber" in result.columns
        assert result.iloc[0]["Patient"] == "أحمد محمد"

    @patch("src.appointments.httpx.post")
    @patch.dict("os.environ", {"EHR_TOKEN": "test-token"})
    def test_fetch_appointments_empty_response(
        self, mock_post, empty_appointments_api_response
    ):
        mock_response = MagicMock()
        mock_response.json.return_value = empty_appointments_api_response
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = fetch_appointments(
            "2024-01-01T00:00:00.000Z", "2024-01-31T23:59:59.000Z"
        )

        assert len(result) == 0
        assert list(result.columns) == ["Patient", "Date", "Doctor", "PhoneNumber"]

    @patch("src.appointments.httpx.post")
    @patch.dict("os.environ", {"EHR_TOKEN": "test-token"})
    def test_fetch_appointments_api_error(
        self, mock_post, error_appointments_api_response
    ):
        mock_response = MagicMock()
        mock_response.json.return_value = error_appointments_api_response
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = fetch_appointments(
            "2024-01-01T00:00:00.000Z", "2024-01-31T23:59:59.000Z"
        )

        assert len(result) == 0
        assert list(result.columns) == ["Patient", "Date", "Doctor", "PhoneNumber"]

    @patch("src.appointments.httpx.post")
    @patch.dict("os.environ", {"EHR_TOKEN": "test-token"})
    def test_fetch_appointments_http_error(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "error", request=MagicMock(), response=MagicMock()
        )
        mock_post.return_value = mock_response

        with pytest.raises(httpx.HTTPStatusError):
            fetch_appointments("2024-01-01T00:00:00.000Z", "2024-01-31T23:59:59.000Z")

    @patch("src.appointments.httpx.post")
    @patch.dict("os.environ", {"EHR_TOKEN": "test-token"})
    def test_fetch_appointments_sends_correct_payload(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {"appointments": {"appointments": [], "appointmentsCount": 0}}
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        fetch_appointments("2024-01-01T00:00:00.000Z", "2024-01-31T23:59:59.000Z")

        call_args = mock_post.call_args
        assert "appointments" in call_args[1]["json"]["query"]
        assert call_args[1]["json"]["variables"]["status"] == "Scheduled"
        assert (
            call_args[1]["json"]["variables"]["dateFrom"] == "2024-01-01T00:00:00.000Z"
        )
        assert call_args[1]["json"]["variables"]["dateTo"] == "2024-01-31T23:59:59.000Z"

    @patch("src.appointments.httpx.post")
    @patch.dict("os.environ", {"EHR_TOKEN": "test-token"})
    def test_fetch_appointments_includes_auth_header(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {"appointments": {"appointments": [], "appointmentsCount": 0}}
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        fetch_appointments("2024-01-01T00:00:00.000Z", "2024-01-31T23:59:59.000Z")

        call_args = mock_post.call_args
        assert "Authorization" in call_args[1]["headers"]
        assert call_args[1]["headers"]["Authorization"] == "Bearer test-token"

    @patch("src.appointments.httpx.post")
    def test_fetch_appointments_uses_env_token(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {"appointments": {"appointments": [], "appointmentsCount": 0}}
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        with patch.dict("os.environ", {"EHR_TOKEN": "custom-token"}):
            fetch_appointments("2024-01-01T00:00:00.000Z", "2024-01-31T23:59:59.000Z")

            call_args = mock_post.call_args
            assert call_args[1]["headers"]["Authorization"] == "Bearer custom-token"

    @patch("src.appointments.httpx.post")
    @patch.dict("os.environ", {"EHR_TOKEN": ""})
    def test_fetch_appointments_empty_token(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {"appointments": {"appointments": [], "appointmentsCount": 0}}
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        fetch_appointments("2024-01-01T00:00:00.000Z", "2024-01-31T23:59:59.000Z")

        call_args = mock_post.call_args
        assert call_args[1]["headers"]["Authorization"] == "Bearer "
