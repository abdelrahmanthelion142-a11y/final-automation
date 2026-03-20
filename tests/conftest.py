"""Shared pytest fixtures for WellSkin Follow-Up Automation tests."""

import pytest
import pandas as pd
from unittest.mock import MagicMock, patch


@pytest.fixture
def sample_appointments_df():
    """Sample appointments DataFrame for testing."""
    return pd.DataFrame(
        [
            {
                "Patient": "أحمد محمد",
                "Date": "2024-01-15",
                "Doctor": "Ahmed",
                "PhoneNumber": "01012345678",
            },
            {
                "Patient": "سارة علي",
                "Date": "2024-01-16",
                "Doctor": "Samar",
                "PhoneNumber": "+201023456789",
            },
            {
                "Patient": "محمد حسن",
                "Date": "2024-01-17",
                "Doctor": "Mohamed Ashour",
                "PhoneNumber": "201034567890",
            },
        ]
    )


@pytest.fixture
def sample_gender_df():
    """Sample gender classification DataFrame for testing."""
    return pd.DataFrame(
        [
            {"Patient": "أحمد", "Gender": "Male"},
            {"Patient": "سارة", "Gender": "Female"},
            {"Patient": "محمد", "Gender": "Male"},
        ]
    )


@pytest.fixture
def mock_httpx_response():
    """Factory fixture for creating mock httpx responses."""

    def _create(data, status_code=200, raise_for_status=None):
        mock_response = MagicMock()
        mock_response.json.return_value = data
        mock_response.status_code = status_code
        if raise_for_status:
            mock_response.raise_for_status.side_effect = raise_for_status
        else:
            mock_response.raise_for_status.return_value = None
        return mock_response

    return _create


@pytest.fixture
def mock_openai_response():
    """Factory fixture for creating mock OpenAI responses."""

    def _create(gender_mapping):
        from src.gender_classifier import PatientGenderList, PatientGender

        patients = [
            PatientGender(name=name, gender=gender)
            for name, gender in gender_mapping.items()
        ]
        mock_response = MagicMock()
        mock_response.output_parsed = PatientGenderList(patients=patients)
        return mock_response

    return _create


@pytest.fixture
def mock_drive_service():
    """Mock Google Drive service for testing."""
    service = MagicMock()
    return service


@pytest.fixture
def sample_appointments_api_response():
    """Sample EHR API response for appointments."""
    return {
        "data": {
            "appointments": {
                "appointments": [
                    {
                        "id": "appt-1",
                        "date": "2024-01-15",
                        "status": "Scheduled",
                        "patient": {
                            "id": "patient-1",
                            "name": "أحمد محمد",
                            "phoneNo": "01012345678",
                        },
                        "doctor": {"id": "doctor-1", "name": "Ahmed"},
                        "branch": {"id": "branch-1", "name": "Main Branch"},
                    },
                    {
                        "id": "appt-2",
                        "date": "2024-01-16",
                        "status": "Scheduled",
                        "patient": {
                            "id": "patient-2",
                            "name": "سارة علي",
                            "phoneNo": "+201023456789",
                        },
                        "doctor": {"id": "doctor-2", "name": "Samar"},
                        "branch": {"id": "branch-1", "name": "Main Branch"},
                    },
                ],
                "appointmentsCount": 2,
            }
        }
    }


@pytest.fixture
def empty_appointments_api_response():
    """Empty EHR API response for appointments."""
    return {
        "data": {
            "appointments": {
                "appointments": [],
                "appointmentsCount": 0,
            }
        }
    }


@pytest.fixture
def error_appointments_api_response():
    """EHR API error response."""
    return {
        "errors": [
            {
                "message": "Authentication error",
                "extensions": {"code": "UNAUTHENTICATED"},
            }
        ]
    }
