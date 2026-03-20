"""Main orchestration module for the WellSkin Follow-Up Automation pipeline.

This module coordinates the entire appointment follow-up process:
1. Fetch appointments from EHR for a7-day window
2. Normalize phone numbers
3. Classify patient genders (CSV lookup + OpenAI fallback)
4. Translate doctor names to Arabic
5. Generate personalised Arabic messages
6. Export to Excel with WhatsApp links
7. Upload to Google Drive
"""

import logging
import os
from datetime import datetime, timedelta, timezone

import dotenv

dotenv.load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

logger = logging.getLogger("wellskin")


def get_date_range() -> tuple[str, str]:
    """Calculate the7-day appointment window date range.

    Returns:
        tuple[str, str]: Two ISO-formatted strings:
            - Start: Today at 00:00:00 UTC
            - End: Today + 7 days at 23:59:59 UTC
    """
    today = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    to_date = today + timedelta(days=7)

    start = today.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    end = to_date.strftime("%Y-%m-%dT23:59:59.000Z")

    return start, end


def get_date_range_for_filename() -> tuple[str, str]:
    """Calculate the date range for Excel file naming.

    Returns:
        tuple[str, str]: Two date strings in YYYY-MM-DD format:
            - Start date (today)
            - End date (today + 7 days)
    """
    today = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    to_date = today + timedelta(days=7)

    start = today.strftime("%Y-%m-%d")
    end = to_date.strftime("%Y-%m-%d")

    return start, end


def main():
    """Execute the full appointment follow-up pipeline.

    Pipeline steps:
    1. Calculate date range
    2. Fetch appointments from EHR
    3. Normalize phone numbers
    4. Deduplicate by patient first name + phone
    5. Classify genders
    6. Translate doctor names to Arabic
    7. Generate personalised messages
    8. Export to Excel
    9. Upload to Google Drive
    """
    logger.info("Pipeline starting...")

    date_from, date_to = get_date_range()
    logger.info(f"Date range: {date_from} → {date_to}")

    from src.appointments import fetch_appointments
    from src.excel_exporter import export_to_excel
    from src.drive_handler import upload_excel, download_csv, upload_csv
    from src.message_generator import generate_message
    from src.doctor_translator import translate_doctor
    from src.gender_classifier import classify_genders, update_gender_csv
    from src.phone_normalizer import normalize_phones

    try:
        df = fetch_appointments(date_from, date_to)
        logger.info(f"Fetched {len(df)} appointments")
    except Exception as e:
        logger.error(f"EHR API error: {e}")
        raise

    if len(df) == 0:
        logger.warning(
            "No appointments found — skipping Excel export and Drive upload."
        )
        return

    df = normalize_phones(df)

    df["_first_name"] = df["Patient"].apply(lambda x: str(x).split()[0])
    df = df.sort_values("Date").drop_duplicates(
        subset=["_first_name", "PhoneNumber"], keep="first"
    )
    logger.info(f"After dedup: {len(df)} unique patients")

    try:
        gender_df = download_csv(os.environ["DRIVE_CSV_FILE_ID"])
        logger.info(f"Loaded gender CSV: {len(gender_df)} known names")
    except Exception as e:
        logger.warning(f"Failed to download gender CSV: {e}")
        gender_df = None

    if gender_df is None or len(gender_df) == 0:
        from pandas import DataFrame

        gender_df = DataFrame(columns=["Patient", "Gender"])

    original_names = set(gender_df["Patient"].tolist()) if len(gender_df) > 0 else set()

    df = classify_genders(df, gender_df)

    new_classifications = {}
    for _, row in df.iterrows():
        name = row["_first_name"]
        gender = row.get("Gender", "")
        if gender and name not in original_names:
            new_classifications[name] = gender

    if new_classifications:
        updated_csv = update_gender_csv(gender_df, new_classifications)
        try:
            upload_csv(updated_csv, os.environ["DRIVE_CSV_FILE_ID"])
            logger.info("CSV updated on Google Drive")
        except Exception as e:
            logger.warning(f"Failed to upload updated CSV: {e}")
    else:
        logger.info("No new gender classifications — CSV unchanged")

    df["DoctorArabic"] = df["Doctor"].apply(translate_doctor)

    df["Message"] = df.apply(generate_message, axis=1)

    start_date, end_date = get_date_range_for_filename()
    filename = f"WellSkin_Followup_{start_date}_to_{end_date}.xlsx"

    export_to_excel(df, filename)

    file_size = os.path.getsize(filename)
    logger.info(f"Excel file created: {filename} ({file_size} bytes, {len(df)} rows)")

    try:
        upload_excel(filename, os.environ["DRIVE_EXCEL_FILE_ID"])
        logger.info(f"Excel uploaded to Google Drive successfully")
    except Exception as e:
        logger.error(f"Failed to update Excel on Drive: {e}")
        raise

    logger.info(f"✅ Run complete. {len(df)} messages ready.")


if __name__ == "__main__":
    main()
