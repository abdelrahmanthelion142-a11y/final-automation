import os
import logging

import httpx
import pandas as pd

logger = logging.getLogger(__name__)

BASE_URL = "https://app.clinicr.health"
GRAPHQL_URL = "https://app.clinicr.health/graphql"

BRANCH_ID = "e1c823bf-f2a6-42e3-a1dc-c44d2a5b4352"

LOGIN_MUTATION = """
mutation login($loginInput: LoginInput!) {
  login(loginInput: $loginInput) {
    accessToken
    refreshToken
    user {
      id
      email
      avatar
      organizationId
      language
      name
      position
      __typename
    }
    __typename
  }
}
"""

APPOINTMENTS_QUERY = """
query ListAppointments($listAppointmentsInput: ListAppointmentsInput!) {
    listAppointments(listAppointmentsInput: $listAppointmentsInput) {
        items {
            id
            date
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
        meta {
            currentPage
            pageCount
            totalCount
        }
    }
}
"""


def _login(email: str, password: str) -> str:
    """Authenticate with EHR and return the access token.

    Args:
        email: User email for authentication
        password: User password for authentication

    Returns:
        str: The access token from the login response

    Raises:
        Exception: If login fails or no access token is returned
    """
    headers = {
        "Content-Type": "application/json",
        "Origin": BASE_URL,
        "Referer": BASE_URL + "/appointments",
        "User-Agent": "Mozilla/5.0", #the api requires the api requests to be from a browser so we mock that i have not been using
        "Accept": "*/*",             #the api unathorized i took permision from the clinic owner and crm developer that i will perform this automation
    }

    payload = {
        "operationName": "login",
        "query": LOGIN_MUTATION,
        "variables": {
            "loginInput": {
                "email": email,
                "password": password,
            }
        },
    }

    response = httpx.post(
        GRAPHQL_URL, json=payload, headers=headers, timeout=30.0, follow_redirects=True
    )
    response.raise_for_status()

    data = response.json()

    if "errors" in data:
        raise Exception(f"Login failed: {data['errors']}")

    access_token = data.get("data", {}).get("login", {}).get("accessToken")
    if not access_token:
        raise Exception("Login succeeded but no access token was returned")

    logger.info("Successfully authenticated with EHR")
    return access_token


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
    email = os.environ.get("EHR_EMAIL", "")
    password = os.environ.get("EHR_PASSWORD", "")

    if not email or not password:
        raise Exception("EHR_EMAIL and EHR_PASSWORD environment variables are required")

    token = _login(email, password)

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Origin": BASE_URL,
        "Referer": BASE_URL + "/appointments",
        "User-Agent": "Mozilla/5.0", #the api requires the api requests to be from a browser so we mock that 
        "Accept": "*/*",             #i have not been using the api unathorized i took permision from the clinic owner and crm developer that i will perform this automation
    }

    all_appointments = []
    page = 1
    page_count = 1

    while page <= page_count:
        payload = {
            "operationName": "ListAppointments",
            "query": APPOINTMENTS_QUERY,
            "variables": {
                "listAppointmentsInput": {
                    "where": {
                        "branchId": BRANCH_ID,
                        "status": "Scheduled",
                        "dateFrom": date_from,
                        "dateTo": date_to,
                    },
                    "pagination": {
                        "page": page,
                        "limit": 100, #i explicitly put a limit in the query because the graphql api automaticly adds a limit of 100 
                    },                #so i explcitly added it so its clear that we have to loop over the pages and cant fetch the data at once
                        
                }
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

        appt_data = data.get("data", {}).get("listAppointments", {})
        appointments = appt_data.get("items", []) if appt_data else []
        meta = appt_data.get("meta", {})

        page_count = meta.get("pageCount", 1)

        for appt in appointments:
            all_appointments.append(
                {
                    "Patient": appt.get("patient", {}).get("name", ""),
                    "Date": appt.get("date", ""),
                    "Doctor": appt.get("doctor", {}).get("name", ""),
                    "PhoneNumber": appt.get("patient", {}).get("phoneNo", ""),
                }
            )

        page += 1

    if not all_appointments:
        logger.warning("No appointments returned from EHR API")
        return pd.DataFrame(columns=["Patient", "Date", "Doctor", "PhoneNumber"])

    df = pd.DataFrame(all_appointments)
    logger.info(f"Fetched {len(df)} appointments from EHR")
    return df
