"""Google Drive handler module for CSV and Excel file operations.

This module isolates ALL Google Drive interactions including:
- Downloading CSV files (gender classifications)
- Uploading CSV files (updated gender classifications)
- Uploading Excel files (follow-up output)

Uses Service Account authentication for headless operation in CI/CD.
"""

import json
import os
import logging
import tempfile

import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from io import BytesIO

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/drive"]


def get_service():
    """Create and return a Google Drive API service instance.

    Reads the GOOGLE_SERVICE_ACCOUNT_JSON environment variable containing
    the service account credentials JSON, parses it, and creates
    authenticated credentials for Drive API access.

    Returns:
        googleapiclient.discovery.Resource: Authenticated Drive API service

    Raises:
        KeyError: If GOOGLE_SERVICE_ACCOUNT_JSON env var is not set
        json.JSONDecodeError: If the JSON is malformed
    """
    creds_json = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]
    creds_info = json.loads(creds_json)
    creds = service_account.Credentials.from_service_account_info(
        creds_info, scopes=SCOPES
    )
    return build("drive", "v3", credentials=creds)


def download_csv(file_id: str) -> pd.DataFrame:
    """Download a CSV file from Google Drive by its file ID.

    Args:
        file_id: The Google Drive file ID of the CSV to download

    Returns:
        pd.DataFrame: The CSV contents as a pandas DataFrame.
            If the file is empty or an error occurs, returns an empty
            DataFrame with columns ["Patient", "Gender"].

    Side effects:
        Logs errors if download fails
    """
    try:
        service = get_service()
        request = service.files().get_media(fileId=file_id)

        

        buffer = BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()

        buffer.seek(0)
        df = pd.read_csv(buffer)
        logger.info(f"Downloaded CSV from Drive: {len(df)} rows")
        return df
    except Exception as e:
        logger.error(f"Failed to download CSV from Drive: {e}")
        return pd.DataFrame(columns=["Patient", "Gender"])


def upload_csv(df: pd.DataFrame, file_id: str) -> None:
    """Upload a DataFrame as CSV to Google Drive, replacing an existing file.

    Args:
        df: The pandas DataFrame to upload as CSV
        file_id: The Google Drive file ID to replace

    Side effects:
        - Creates a temporary file during upload (cleaned up after)
        - Logs success/failure messages

    Raises:
        Exception: If the upload fails
    """
    service = get_service()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as tmp:
        tmp_path = tmp.name
        df.to_csv(tmp_path, index=False)

    try:
        media = MediaFileUpload(tmp_path, mimetype="text/csv")
        service.files().update(fileId=file_id, media_body=media).execute()
        logger.info(f"Updated CSV file {file_id} on Drive")
    finally:
        os.unlink(tmp_path)


def upload_excel(local_path: str, file_id: str) -> None:
    """Upload an Excel file to Google Drive, overwriting an existing file.

    By updating an existing file owned by the user, we bypass the 
    `storageQuotaExceeded` error that occurs when Service Accounts try to 
    create new files on personal (free tier) Google Drive accounts.

    Args:
        local_path: Local filesystem path to the Excel file
        file_id: Google Drive file ID of the existing Excel file to overwrite

    Side effects:
        - Overwrites the existing file on Drive
        - Logs success message

    Raises:
        Exception: If the upload fails
    """
    service = get_service()

    media = MediaFileUpload(
        local_path,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        resumable=False
    )

    # Upload content AND rename in a single API call.
    # Using two separate update() calls was causing the file content
    # to not persist — the second metadata-only update() could reset
    # the file content on empty placeholder files.
    new_name = os.path.basename(local_path)
    metadata = {'name': new_name}

    result = service.files().update(
        fileId=file_id,
        body=metadata,
        media_body=media,
        supportsAllDrives=True,
    ).execute()

    logger.info(f"Updated Excel file on Drive: id={result.get('id')}, name={new_name}")
