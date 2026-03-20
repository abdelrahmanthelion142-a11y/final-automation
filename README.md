# WellSkin Follow-Up Automation

This Python automation pipeline runs weekly to fetch upcoming appointments from the EHR system, generate personalised Arabic WhatsApp follow-up messages, and upload an Excel file with clickable WhatsApp links to Google Drive.

## What It Does

1. Fetches a7-day appointment window from the EHR GraphQL API
2. Normalises Egyptian phone numbers to +20 international format
3. Classifies patient genders via Google Drive CSV lookup with OpenAI fallback
4. Translates doctor names to Arabic with proper title prefixes
5. Generates gender-aware Arabic follow-up messages
6. Exports to Excel with clickable WhatsApp hyperlinks
7. Uploads the Excel file to Google Drive

## Quick Start

See [quickstart.md](specs/001-appointment-followup-automation/quickstart.md) for detailed setup instructions.

## Required GitHub Secrets

Configure these secrets in your repository under **Settings → Secrets → Actions**:

1. `EHR_TOKEN` - Bearer token for the EHR GraphQL API
2. `OPENAI_API_KEY` - OpenAI API key for gender classification
3. `GOOGLE_SERVICE_ACCOUNT_JSON` - JSON credentials for Google Service Account
4. `DRIVE_CSV_FILE_ID` - Google Drive file ID for the gender classification CSV
5. `DRIVE_OUTPUT_FOLDER_ID` - Google Drive folder ID for Excel output uploads

## Project Structure

```
src/
├── appointments.py      # EHR GraphQL fetcher
├── phone_normalizer.py # Egyptian phone number normalisation
├── gender_classifier.py# Gender classification (CSV + OpenAI)
├── doctor_translator.py# English→Arabic doctor name translation
├── message_generator.py# Gender-aware Arabic message generation
├── excel_exporter.py   # Excel file with WhatsApp hyperlinks
└── drive_handler.py   # Google Drive upload/download

main.py                # Pipeline orchestrator
requirements.txt       # Python dependencies
```

## Adding a New Doctor

Edit `src/doctor_translator.py` and add entries to the `DOCTOR_TRANSLATIONS` dictionary:

```python
DOCTOR_TRANSLATIONS: dict[str, str] = {
    "ahmed": "أحمد",
    "sarah": "سارة",
    # For doctors named "eman" or "mohamed", use full name as key:
    "eman hassan": "إيمان حسن",
}
```

## Correcting Gender Classifications

Edit the gender CSV file directly in Google Drive. The CSV should have columns:
- `Patient` - First name (Arabic)
- `Gender` - "Male" or "Female"

Manual corrections override AI classifications on subsequent runs.

## Testing

Run unit tests with:

```bash
pytest tests/
```

## Scheduled Runs

The pipeline runs automatically every Sunday at midnight Egypt time (22:00 UTC Saturday) via GitHub Actions. You can also trigger it manually from the Actions tab in GitHub.