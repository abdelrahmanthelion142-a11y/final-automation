# Quickstart: Automated Weekly Appointment Follow-Up Tool

**Branch**: `001-appointment-followup-automation`

## Prerequisites

- Python 3.12+
- A Google Cloud Service Account with Drive API enabled
- Access to the EHR system (bearer token)
- An OpenAI API key

## Local Setup

1. **Clone and install dependencies**:

   ```bash
   git clone <repo-url>
   cd <repo-dir>
   pip install -r requirements.txt
   ```

2. **Create a `.env` file** in the project root with your secrets:

   ```env
   EHR_TOKEN=your_ehr_bearer_token
   OPENAI_API_KEY=your_openai_api_key
   GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
   DRIVE_CSV_FILE_ID=your_google_drive_csv_file_id
   DRIVE_OUTPUT_FOLDER_ID=your_google_drive_output_folder_id
   ```

3. **Run the pipeline**:

   ```bash
   python main.py
   ```

   The pipeline will:
   - Compute a 7-day date window from today
   - Fetch appointments from the EHR
   - Normalise phone numbers (Egypt +20)
   - Classify genders (CSV lookup + OpenAI fallback)
   - Translate doctor names to Arabic
   - Generate personalised Arabic messages
   - Export to Excel with WhatsApp links
   - Upload to Google Drive

4. **Check output**: The Excel file will appear in your configured Google
   Drive output folder as `WellSkin_Followup_YYYY-MM-DD_to_YYYY-MM-DD.xlsx`.

## GitHub Actions (automated daily runs)

1. Add the 5 secrets to your repository settings under **Settings → Secrets → Actions**:
   - `EHR_TOKEN`
   - `OPENAI_API_KEY`
   - `GOOGLE_SERVICE_ACCOUNT_JSON`
   - `DRIVE_CSV_FILE_ID`
   - `DRIVE_OUTPUT_FOLDER_ID`

2. The pipeline runs every Sunday at midnight Egypt time (22:00 UTC Saturday)
   via the cron schedule in `.github/workflows/daily_run.yml`.

3. To trigger manually: go to **Actions → Daily Appointment Follow-Up →
   Run workflow**.

## Google Drive One-Time Setup

1. Create a Google Cloud project and enable the Drive API.
2. Create a Service Account and download the JSON key.
3. Upload an initial `classified_patients.csv` to Drive with headers: `Patient,Gender`.
4. Share the CSV file **and** the output folder with the service account email.
5. Copy the file ID and folder ID from the Drive URLs into your secrets.

## Verifying a Run

- Check the GitHub Actions run log for structured output at each step.
- Open the Google Drive output folder and confirm the Excel file is present.
- Open the Excel file, click a WhatsApp link, and verify it opens WhatsApp Web
  with the correct pre-populated Arabic message.
