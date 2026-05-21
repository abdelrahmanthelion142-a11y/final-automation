"""Unit tests for appointments fetcher module."""

import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
import httpx

from src.appointments import fetch_appointments, _login


class TestLogin:
    """Tests for _login function."""

    @patch("src.appointments.httpx.post")
    def test_login_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "login": {
                    "accessToken": "test-access-token",
                    "refreshToken": "test-refresh-token",
                    "user": {
                        "id": "user-1",
                        "email": "test@example.com",
                        "avatar": None,
                        "organizationId": "org-1",
                        "language": "en",
                        "name": "Test User",
                        "position": "Doctor",
                        "__typename": "User",
                    },
                    "__typename": "LoginResponse",
                }
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        token = _login("test@example.com", "password123")

        assert token == "test-access-token"
        call_args = mock_post.call_args
        assert call_args[1]["json"]["operationName"] == "login"
        assert call_args[1]["json"]["variables"]["loginInput"]["email"] == "test@example.com"
        assert call_args[1]["json"]["variables"]["loginInput"]["password"] == "password123"

    @patch("src.appointments.httpx.post")
    def test_login_api_error(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "errors": [{"message": "Invalid credentials"}]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        with pytest.raises(Exception, match="Login failed"):
            _login("test@example.com", "wrong-password")

    @patch("src.appointments.httpx.post")
    def test_login_no_access_token(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "login": {
                    "accessToken": None,
                    "refreshToken": None,
                    "user": None,
                    "__typename": "LoginResponse",
                }
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        with pytest.raises(Exception, match="no access token"):
            _login("test@example.com", "password123")

    @patch("src.appointments.httpx.post")
    def test_login_http_error(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "error", request=MagicMock(), response=MagicMock()
        )
        mock_post.return_value = mock_response

        with pytest.raises(httpx.HTTPStatusError):
            _login("test@example.com", "password123")


class TestFetchAppointments:
    """Tests for fetch_appointments function."""

    @patch("src.appointments._login")
    @patch("src.appointments.httpx.post")
    @patch.dict("os.environ", {"EHR_EMAIL": "test@example.com", "EHR_PASSWORD": "password123"})
    def test_fetch_appointments_success(
        self, mock_post, mock_login, sample_appointments_api_response
    ):
        mock_login.return_value = "test-access-token"
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
        mock_login.assert_called_once_with("test@example.com", "password123")

    @patch("src.appointments._login")
    @patch("src.appointments.httpx.post")
    @patch.dict("os.environ", {"EHR_EMAIL": "test@example.com", "EHR_PASSWORD": "password123"})
    def test_fetch_appointments_empty_response(
        self, mock_post, mock_login, empty_appointments_api_response
    ):
        mock_login.return_value = "test-access-token"
        mock_response = MagicMock()
        mock_response.json.return_value = empty_appointments_api_response
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = fetch_appointments(
            "2024-01-01T00:00:00.000Z", "2024-01-31T23:59:59.000Z"
        )

        assert len(result) == 0
        assert list(result.columns) == ["Patient", "Date", "Doctor", "PhoneNumber"]

    @patch("src.appointments._login")
    @patch("src.appointments.httpx.post")
    @patch.dict("os.environ", {"EHR_EMAIL": "test@example.com", "EHR_PASSWORD": "password123"})
    def test_fetch_appointments_api_error(
        self, mock_post, mock_login, error_appointments_api_response
    ):
        mock_login.return_value = "test-access-token"
        mock_response = MagicMock()
        mock_response.json.return_value = error_appointments_api_response
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = fetch_appointments(
            "2024-01-01T00:00:00.000Z", "2024-01-31T23:59:59.000Z"
        )

        assert len(result) == 0
        assert list(result.columns) == ["Patient", "Date", "Doctor", "PhoneNumber"]

    @patch("src.appointments._login")
    @patch("src.appointments.httpx.post")
    @patch.dict("os.environ", {"EHR_EMAIL": "test@example.com", "EHR_PASSWORD": "password123"})
    def test_fetch_appointments_http_error(self, mock_post, mock_login):
        mock_login.return_value = "test-access-token"
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "error", request=MagicMock(), response=MagicMock()
        )
        mock_post.return_value = mock_response

        with pytest.raises(httpx.HTTPStatusError):
            fetch_appointments("2024-01-01T00:00:00.000Z", "2024-01-31T23:59:59.000Z")

    @patch("src.appointments._login")
    @patch("src.appointments.httpx.post")
    @patch.dict("os.environ", {"EHR_EMAIL": "test@example.com", "EHR_PASSWORD": "password123"})
    def test_fetch_appointments_sends_correct_payload(self, mock_post, mock_login):
        mock_login.return_value = "test-access-token"
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {"listAppointments": {"items": [], "meta": {"currentPage": 1, "pageCount": 1, "totalCount": 0}}}
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        fetch_appointments("2024-01-01T00:00:00.000Z", "2024-01-31T23:59:59.000Z")

        call_args = mock_post.call_args
        assert "ListAppointments" in call_args[1]["json"]["query"]
        assert call_args[1]["json"]["variables"]["listAppointmentsInput"]["where"]["status"] == "Scheduled"
        assert (
            call_args[1]["json"]["variables"]["listAppointmentsInput"]["where"]["dateFrom"] == "2024-01-01T00:00:00.000Z"
        )
        assert call_args[1]["json"]["variables"]["listAppointmentsInput"]["where"]["dateTo"] == "2024-01-31T23:59:59.000Z"

    @patch("src.appointments._login")
    @patch("src.appointments.httpx.post")
    @patch.dict("os.environ", {"EHR_EMAIL": "test@example.com", "EHR_PASSWORD": "password123"})
    def test_fetch_appointments_includes_auth_header(self, mock_post, mock_login):
        mock_login.return_value = "test-access-token"
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {"listAppointments": {"items": [], "meta": {"currentPage": 1, "pageCount": 1, "totalCount": 0}}}
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        fetch_appointments("2024-01-01T00:00:00.000Z", "2024-01-31T23:59:59.000Z")

        call_args = mock_post.call_args
        assert "Authorization" in call_args[1]["headers"]
        assert call_args[1]["headers"]["Authorization"] == "Bearer test-access-token"

    @patch("src.appointments._login")
    @patch("src.appointments.httpx.post")
    def test_fetch_appointments_uses_env_credentials(self, mock_post, mock_login):
        mock_login.return_value = "test-access-token"
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {"listAppointments": {"items": [], "meta": {"currentPage": 1, "pageCount": 1, "totalCount": 0}}}
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        with patch.dict("os.environ", {"EHR_EMAIL": "custom@example.com", "EHR_PASSWORD": "custom-pass"}):
            fetch_appointments("2024-01-01T00:00:00.000Z", "2024-01-31T23:59:59.000Z")

            mock_login.assert_called_once_with("custom@example.com", "custom-pass")

    @patch("src.appointments._login")
    @patch("src.appointments.httpx.post")
    @patch.dict("os.environ", {"EHR_EMAIL": "", "EHR_PASSWORD": ""})
    def test_fetch_appointments_empty_credentials(self, mock_post, mock_login):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {"listAppointments": {"items": [], "meta": {"currentPage": 1, "pageCount": 1, "totalCount": 0}}}
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        with pytest.raises(Exception, match="EHR_EMAIL and EHR_PASSWORD"):
            fetch_appointments("2024-01-01T00:00:00.000Z", "2024-01-31T23:59:59.000Z")
