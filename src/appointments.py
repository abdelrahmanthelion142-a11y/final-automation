"""EHR appointments fetcher module.

This module isolates ALL EHR API interactions. It fetches appointment
data from the EHR GraphQL API and returns it as a pandas DataFrame.
"""

import os
import logging

import httpx
import pandas as pd

logger = logging.getLogger(__name__)

BASE_URL = "https://cr-ehr.com"
GRAPHQL_URL = "https://cr-ehr.com/graphql"

BRANCH_ID = "e1c823bf-f2a6-42e3-a1dc-c44d2a5b4352"

APPOINTMENTS_QUERY = """
query ($status: AppointmentStatus, $dateFrom: Date, $dateTo: Date, $branchId: ID) {
    appointments(
        status: $status
        dateFrom: $dateFrom
        dateTo: $dateTo
        branchId: $branchId
    ) {
        appointments {
            id
            date
            status
            patient {
                id
                name
                phoneNo
            }
            doctor {
                id
                name
            }
            branch {
                id
                name
            }
        }
        appointmentsCount
    }
}
"""


def fetch_appointments(date_from: str, date_to: str) -> pd.DataFrame:
    """Fetch appointments from the EHR GraphQL API for a date range.

    Args:
        date_from: Start date in ISO format (e.g., "2024-01-01T00:00:00.000Z")
        date_to: End date in ISO format (e.g., "2024-01-07T23:59:59.000Z")

    Returns:
        pd.DataFrame: Appointments with columns:
            - Patient: Patient name (string)
            - Date: Appointment date (string)
            - Doctor: Doctor name (string)
            - PhoneNumber: Phone number (string)
            Returns an empty DataFrame with these columns if no appointments
            or if the API returns valid-but-empty responses.

    Raises:
        Exception: If the EHR API request fails

    Side effects:
        Logs warnings on valid-but-empty API responses
    """
    token = os.environ.get("EHR_TOKEN", "")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Origin": BASE_URL,
        "Referer": BASE_URL + "/appointments",
        "User-Agent": "Mozilla/5.0",
        "Accept": "*/*",
    }

    payload = {
        "operationName": None,
        "query": APPOINTMENTS_QUERY,
        "variables": {
            "status": "Scheduled",
            "dateFrom": date_from,
            "dateTo": date_to,
            "branchId": BRANCH_ID,
        },
    }

    response = httpx.post(
        GRAPHQL_URL, json=payload, headers=headers, timeout=30.0, follow_redirects=True
    )
    response.raise_for_status()

    data = response.json()

    if "errors" in data:
        logger.warning(f"EHR API returned errors: {data['errors']}")
        return pd.DataFrame(columns=["Patient", "Date", "Doctor", "PhoneNumber"])

    appt_data = data.get("data", {}).get("appointments", {})
    appointments = appt_data.get("appointments", []) if appt_data else []

    if not appointments:
        logger.warning("No appointments returned from EHR API")
        return pd.DataFrame(columns=["Patient", "Date", "Doctor", "PhoneNumber"])

    rows = []
    for appt in appointments:
        rows.append(
            {
                "Patient": appt.get("patient", {}).get("name", ""),
                "Date": appt.get("date", ""),
                "Doctor": appt.get("doctor", {}).get("name", ""),
                "PhoneNumber": appt.get("patient", {}).get("phoneNo", ""),
            }
        )

    df = pd.DataFrame(rows)
    logger.info(f"Fetched {len(df)} appointments from EHR")
    return df
