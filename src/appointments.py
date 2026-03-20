"""EHR appointments fetcher module.

This module isolates ALL EHR API interactions. It fetches appointment
data from the EHR GraphQL API and returns it as a pandas DataFrame.
"""

import os
import logging

import httpx
import pandas as pd

logger = logging.getLogger(__name__)

APPOINTMENTS_QUERY = """
query Appointments($from: String!, $to: String!, $branchId: Int!) {
    appointments(from: $from, to: $to, branchId: $branchId) {
        patient {
            name
        }
        date
        doctor {
            name
        }
        phoneNumber
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
    branch_id = int(os.environ.get("BRANCH_ID", "1"))

    endpoint = "https://vt.cr-ehr.com/graphql"

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    payload = {
        "query": APPOINTMENTS_QUERY,
        "variables": {"from": date_from, "to": date_to, "branchId": branch_id},
    }

    response = httpx.post(endpoint, json=payload, headers=headers, timeout=30.0)
    response.raise_for_status()

    data = response.json()

    if "errors" in data:
        logger.warning(f"EHR API returned errors: {data['errors']}")
        return pd.DataFrame(columns=["Patient", "Date", "Doctor", "PhoneNumber"])

    appointments = data.get("data", {}).get("appointments", [])

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
                "PhoneNumber": appt.get("phoneNumber", ""),
            }
        )

    df = pd.DataFrame(rows)
    logger.info(f"Fetched {len(df)} appointments from EHR")
    return df
