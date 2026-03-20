# Tasks: Automated Weekly Appointment Follow-Up Tool

**Input**: Design documents from `/specs/001-appointment-followup-automation/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, quickstart.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create the project directory structure with the following folders and empty `__init__.py` files:
  ```
  src/__init__.py
  src/appointments.py     (empty)
  src/phone_normalizer.py (empty)
  src/gender_classifier.py(empty)
  src/doctor_translator.py(empty)
  src/message_generator.py(empty)
  src/excel_exporter.py   (empty)
  src/drive_handler.py    (empty)
  tests/__init__.py
  tests/unit/__init__.py
  main.py                 (empty)
  ```

- [X] T002 Create `requirements.txt` at the project root with these pinned dependencies:
  ```
  httpx>=0.27,<1.0
  pandas>=2.2,<3.0
  openai>=1.30,<2.0
  pydantic>=2.7,<3.0
  openpyxl>=3.1,<4.0
  google-api-python-client>=2.130,<3.0
  google-auth>=2.29,<3.0
  python-dotenv>=1.0,<2.0
  pytest>=8.0,<9.0
  ```

- [X] T003 [P] Create `.github/workflows/daily_run.yml` with this exact content:
  ```yaml
  name: Weekly Appointment Follow-Up

  on:
    schedule:
      - cron: "0 22 * * 6"   # Every Saturday 22:00 UTC = Sunday 00:00 Egypt time
    workflow_dispatch:

  jobs:
    run:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - uses: actions/setup-python@v5
          with:
            python-version: "3.12"
        - name: Install dependencies
          run: pip install -r requirements.txt
        - name: Run pipeline
          env:
            EHR_TOKEN: ${{ secrets.EHR_TOKEN }}
            OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
            GOOGLE_SERVICE_ACCOUNT_JSON: ${{ secrets.GOOGLE_SERVICE_ACCOUNT_JSON }}
            DRIVE_CSV_FILE_ID: ${{ secrets.DRIVE_CSV_FILE_ID }}
            DRIVE_OUTPUT_FOLDER_ID: ${{ secrets.DRIVE_OUTPUT_FOLDER_ID }}
          run: python main.py
  ```

- [X] T004 [P] Create `.env.example` at the project root listing every required environment variable with placeholder values:
  ```
  EHR_TOKEN=your_ehr_bearer_token_here
  OPENAI_API_KEY=sk-your-openai-api-key-here
  GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"..."}
  DRIVE_CSV_FILE_ID=your_google_drive_csv_file_id
  DRIVE_OUTPUT_FOLDER_ID=your_google_drive_output_folder_id
  ```

- [X] T005 [P] Create `.gitignore` at the project root with:
  ```
  .env
  __pycache__/
  *.pyc
  *.xlsx
  .pytest_cache/
  ```

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Implement Google Drive handler in `src/drive_handler.py`. This module isolates ALL Google Drive interactions. It MUST:

  1. Import: `json`, `os`, `io`, `pandas`, `google.oauth2.service_account`, `googleapiclient.discovery`, `googleapiclient.http` (MediaFileUpload, MediaIoBaseDownload)
  2. Define constant `SCOPES = ["https://www.googleapis.com/auth/drive"]`
  3. Implement `get_service()` function:
     - Read `GOOGLE_SERVICE_ACCOUNT_JSON` from `os.environ`
     - Parse it with `json.loads()`
     - Create credentials with `service_account.Credentials.from_service_account_info(info, scopes=SCOPES)`
     - Return `build("drive", "v3", credentials=creds)`
  4. Implement `download_csv(file_id: str) -> pd.DataFrame`:
     - Use `get_service()` to get the Drive service
     - Call `service.files().get_media(fileId=file_id)`
     - Download to a `BytesIO` buffer using `MediaIoBaseDownload`
     - Return `pd.read_csv(buffer)` — if empty or error, return empty DataFrame with columns `["Patient", "Gender"]`
  5. Implement `upload_csv(df: pd.DataFrame, file_id: str) -> None`:
     - Write `df` to a temporary CSV file using `df.to_csv(tmp_path, index=False)`
     - Use `MediaFileUpload(tmp_path, mimetype="text/csv")`
     - Call `service.files().update(fileId=file_id, media_body=media).execute()`
     - Clean up the temporary file
  6. Implement `upload_excel(local_path: str, folder_id: str) -> None`:
     - Use `MediaFileUpload(local_path, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")`
     - Extract filename from `local_path` using `os.path.basename()`
     - Call `service.files().create(body={"name": filename, "parents": [folder_id]}, media_body=media, fields="id").execute()`
  7. Every function MUST have a docstring explaining inputs, outputs, and side effects

- [X] T007 [P] Implement the EHR appointments fetcher in `src/appointments.py`. This module isolates ALL EHR API interactions. It MUST:

  1. Import: `os`, `httpx`, `pandas`, `logging`
  2. Define the GraphQL query as a module-level constant string `APPOINTMENTS_QUERY`. The query should accept variables `$from` and `$to` (both String!) and `$branchId` (Int!), and return appointment fields: patient name, date, doctor name, phone number. Use the EHR endpoint `https://vt.cr-ehr.com/graphql` with the token from `os.environ["EHR_TOKEN"]` as `Authorization: Bearer {token}` header.
  3. Implement `fetch_appointments(date_from: str, date_to: str) -> pd.DataFrame`:
     - Build the GraphQL POST payload with `query` and `variables` keys
     - Send via `httpx.post()` with headers `{"Authorization": f"Bearer {token}", "Content-Type": "application/json"}`
     - Parse the JSON response and extract the appointments list
     - Convert to a DataFrame with columns: `Patient`, `Date`, `Doctor`, `PhoneNumber`
     - If the response has errors or is empty, log a warning and return an empty DataFrame
  4. Use `logging.getLogger(__name__)` for all log messages
  5. Branch ID should be read from an environment variable `BRANCH_ID` with a default value of `1`

- [X] T008 Implement the logging configuration in `main.py`. Set up structured logging that will be used by all modules:

  1. Import: `logging`, `dotenv`
  2. Call `dotenv.load_dotenv()` at module level to load `.env` for local development
  3. Configure logging with:
     ```python
     logging.basicConfig(
         level=logging.INFO,
         format="%(asctime)s [%(levelname)s] %(message)s",
     )
     ```
  4. Create a logger: `logger = logging.getLogger("wellskin")`
  5. Add a placeholder `main()` function that just logs "Pipeline starting..." and "Pipeline complete."
  6. Add `if __name__ == "__main__": main()` at the bottom

**Checkpoint**: Foundation ready — user story implementation can now begin

---

## Phase 3: User Story 1 — Weekly Follow-Up File Generation (Priority: P1) 🎯 MVP

**Goal**: Fetch appointments for a 7-day window, produce an Excel file with WhatsApp links, and upload to Google Drive.

**Independent Test**: Trigger a run, verify it fetches the correct date range and produces an Excel file with PhoneNumber, Message, Date, WhatsApp Link columns.

### Implementation for User Story 1

- [X] T009 [US1] Implement the date range builder as a function in `main.py`:

  1. Import: `datetime`, `timedelta`, `timezone` from the `datetime` module
  2. Implement `get_date_range() -> tuple[str, str]`:
     - Compute `today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)`
     - Compute `to_date = today + timedelta(days=7)`
     - Return a tuple of two ISO-formatted strings:
       - `today.strftime("%Y-%m-%dT%H:%M:%S.000Z")`
       - `to_date.strftime("%Y-%m-%dT23:59:59.000Z")`
  3. Also implement `get_date_range_for_filename() -> tuple[str, str]`:
     - Same computation but returns `(today.strftime("%Y-%m-%d"), to_date.strftime("%Y-%m-%d"))` for use in the Excel filename

- [X] T010 [US1] Implement the Excel exporter in `src/excel_exporter.py`. This module creates the output Excel file. It MUST:

  1. Import: `urllib.parse`, `openpyxl`, `openpyxl.styles.Font`, `pandas`, `logging`
  2. Implement `make_wa_url(phone: str, message: str) -> str`:
     - Strip `+` and spaces from phone: `clean = phone.replace("+", "").replace(" ", "")`
     - Return `f"https://wa.me/{clean}?text={urllib.parse.quote(message)}"`
     - If phone contains `?` (flagged), return empty string
  3. Implement `export_to_excel(df: pd.DataFrame, output_path: str) -> str`:
     - Expects DataFrame with columns: `PhoneNumber`, `Message`, `Date`
     - Create a new `openpyxl.Workbook()`
     - Write header row: `PhoneNumber`, `Message`, `Date`, `WhatsApp Link`
     - For each row in the DataFrame:
       - Write PhoneNumber, Message, Date to columns 1-3
       - If phone is valid (no `?`): Generate WA URL, write an Excel HYPERLINK formula: `=HYPERLINK("{url}","Send")` to column 4, style with `Font(color="0563C1", underline="single")`
       - If phone is flagged: write "Invalid phone" to column 4
     - Save workbook to `output_path`
     - Log the number of rows written
     - Return `output_path`

- [X] T011 [US1] Wire up the MVP orchestration in `main.py`. Update the `main()` function to:

  1. Import: `os`, `src.appointments.fetch_appointments`, `src.excel_exporter.export_to_excel`, `src.drive_handler.upload_excel`
  2. In `main()`:
     - Log "Pipeline starting..."
     - Call `get_date_range()` to get `date_from, date_to`
     - Log the date range: `f"Date range: {date_from} → {date_to}"`
     - Call `fetch_appointments(date_from, date_to)` to get the DataFrame
     - Log: `f"Fetched {len(df)} appointments"`
     - If DataFrame is empty, log "No appointments found." and return
     - For now, create a placeholder `Message` column: `df["Message"] = "placeholder"`
     - Build the filename: `f"WellSkin_Followup_{start_date}_to_{end_date}.xlsx"` using `get_date_range_for_filename()`
     - Call `export_to_excel(df, filename)`
     - Call `upload_excel(filename, os.environ["DRIVE_OUTPUT_FOLDER_ID"])`
     - Log: `f"✅ Run complete. {len(df)} messages ready."`
  3. This task creates an end-to-end skeleton — later tasks will fill in the real message generation

**Checkpoint**: At this point, User Story 1 should produce an Excel file with placeholder messages, uploaded to Google Drive. Manually verify the file appears in Drive.

---

## Phase 4: User Story 2 — Gender-Aware Message Personalisation (Priority: P1)

**Goal**: Generate personalised Arabic messages with correct gendered verb forms.

**Independent Test**: Provide male and female patients, verify messages use `تكوني` for female and `تكون` for male.

### Implementation for User Story 2

- [X] T012 [US2] Implement the message generator in `src/message_generator.py`. It MUST:

  1. Import: `logging`
  2. Implement `generate_message(patient_name: str, gender: str, doctor_arabic: str, date: str) -> str`:
     - If `gender == "Female"`: use verb `تكوني`
     - If `gender == "Male"`: use verb `تكون`
     - If gender is empty/unknown: default to masculine form `تكون` and log a WARNING
     - Determine doctor prefix:
       - If `doctor_arabic == "آية"`: no prefix (use the name as-is)
       - Otherwise: prefix with `"د/"` → `f"د/{doctor_arabic}"`
     - Build the Arabic message template. The exact template is:
       ```
       مرحبا {patient_name} 👋🏻
       بنتمنالك يوم سعيد 🌸
       هاي رسالة تذكيرية بموعدك في عيادة WellSkin مع {doctor_display} بتاريخ {date} 📅
       بنتمنى {verb} بصحة وعافية دايمًا 💛
       لو عندك اي استفسار تواصل/ي معنا 📲
       ```
     - Return the message string
  3. Add a docstring explaining the gender-verb mapping and doctor prefix rule

- [X] T013 [US2] Implement the doctor name translator in `src/doctor_translator.py`. It MUST:

  1. Import: `logging`
  2. Define the translation dictionary `DOCTOR_TRANSLATIONS` at module level. This is a `dict[str, str]` mapping English lookup keys to Arabic names. The user will populate it with their doctor names. Start with this example structure:
     ```python
     DOCTOR_TRANSLATIONS: dict[str, str] = {
         # Standard first-name lookups
         # "john": "جون",
         # "sarah": "سارة",
         #
         # Full-name lookups for disambiguation (eman, mohamed)
         # "eman lastname": "إيمان",
         # "mohamed lastname": "محمد",
     }
     ```
  3. Define a set `FULL_NAME_DOCTORS = {"eman", "mohamed"}` — doctors whose first name requires full-name lookup for disambiguation
  4. Implement `translate_doctor(english_name: str) -> str`:
     - Extract the first name: `first = english_name.strip().split()[0].lower()`
     - If `first` is in `FULL_NAME_DOCTORS`: use `english_name.strip().lower()` as the lookup key
     - Otherwise: use `first` as the lookup key
     - Look up the key in `DOCTOR_TRANSLATIONS`
     - If found: return the Arabic name
     - If NOT found: log a WARNING `f"Doctor '{english_name}' not in translation dictionary — using English name"` and return the original English name
  5. Add clear docstring with the disambiguation rule

- [X] T014 [US2] Update `main.py` to integrate gender classification, doctor translation, and message generation. Modify `main()`:

  1. Add imports: `src.message_generator.generate_message`, `src.doctor_translator.translate_doctor`
  2. After fetching appointments, add these steps (in this order):
     - **Deduplicate**: `df["_first_name"] = df["Patient"].apply(lambda x: str(x).split()[0])`; then `df = df.sort_values("Date").drop_duplicates(subset=["_first_name", "PhoneNumber"], keep="first")`; log `f"After dedup: {len(df)} unique patients"`
     - **Translate doctors**: `df["DoctorArabic"] = df["Doctor"].apply(translate_doctor)`
     - **Generate messages** (placeholder Gender for now — US3 will add real classification): `df["Gender"] = ""` then `df["Message"] = df.apply(lambda r: generate_message(r["_first_name"], r["Gender"], r["DoctorArabic"], r["Date"]), axis=1)`
  3. Remove the old placeholder `df["Message"] = "placeholder"` line
  4. Keep the rest of the pipeline (Excel export + upload) the same

- [X] T015 [US2] Write unit test in `tests/unit/test_message_generator.py`:

  1. Import `generate_message` from `src.message_generator`
  2. Test `test_female_message`: call with gender="Female", verify output contains `تكوني`
  3. Test `test_male_message`: call with gender="Male", verify output contains `تكون`
  4. Test `test_unknown_gender_defaults_male`: call with gender="", verify output contains `تكون`
  5. Test `test_doctor_aya_no_prefix`: call with doctor_arabic="آية", verify output does NOT contain `"د/"`
  6. Test `test_regular_doctor_has_prefix`: call with doctor_arabic="سارة", verify output contains `"د/سارة"`

- [X] T016 [P] [US2] Write unit test in `tests/unit/test_doctor_translator.py`:

  1. Import `translate_doctor` from `src.doctor_translator`
  2. Test `test_known_doctor_first_name`: Add a test entry to DOCTOR_TRANSLATIONS in setup, verify translation works
  3. Test `test_unknown_doctor_returns_english`: call with an unknown name, verify it returns the English name
  4. Test `test_eman_uses_full_name`: Add entries for "eman x" and "eman y", verify disambiguation

**Checkpoint**: Messages are now personalised with correct Arabic verbs and doctor names. Gender is still empty (defaults to masculine) — US3 will fix this.

---

## Phase 5: User Story 3 — Gender Knowledge Base Growth (Priority: P2)

**Goal**: Classify patient genders via CSV lookup + OpenAI fallback, and grow the CSV over time.

**Independent Test**: Run twice — first run classifies unknowns via AI and saves them; second run finds them in CSV and skips AI.

### Implementation for User Story 3

- [X] T017 [US3] Implement the gender classifier in `src/gender_classifier.py`. It MUST:

  1. Import: `os`, `logging`, `pandas`, `openai`, `pydantic`
  2. Define Pydantic models for OpenAI structured output:
     ```python
     from pydantic import BaseModel
     from typing import List

     class PatientGender(BaseModel):
         name: str
         gender: str  # "Male" or "Female"

     class PatientGenderList(BaseModel):
         patients: List[PatientGender]
     ```
  3. Implement `classify_from_csv(first_names: list[str], gender_df: pd.DataFrame) -> dict[str, str]`:
     - Build a mapping: `gender_map = dict(zip(gender_df["Patient"], gender_df["Gender"]))`
     - For each name in `first_names`: look up in `gender_map`
     - Return a dict of `{name: gender}` for names that were found
     - Log: `f"Gender mapped from CSV: {len(found)} / {len(first_names)}"`
  4. Implement `classify_from_ai(unknown_names: list[str]) -> dict[str, str]`:
     - If the list is empty, return empty dict
     - Create OpenAI client: `client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])`
     - Build prompt: `f"Classify the gender of these Arabic first names as Male or Female: {', '.join(unknown_names)}"`
     - Call `client.beta.chat.completions.parse()` with:
       - `model="gpt-4o-mini"`
       - `messages=[{"role": "user", "content": prompt}]`
       - `response_format=PatientGenderList`
     - Parse the structured response into a dict `{name: gender}`
     - Log: `f"OpenAI classified {len(result)} names"`
     - If OpenAI call fails: log the error at ERROR level, return empty dict (fail-forward)
  5. Implement `classify_genders(df: pd.DataFrame, gender_df: pd.DataFrame) -> pd.DataFrame`:
     - Extract first names: `first_names = df["_first_name"].unique().tolist()`
     - Call `classify_from_csv(first_names, gender_df)` → `known`
     - Find unknown names: `unknown = [n for n in first_names if n not in known]`
     - If unknowns exist: call `classify_from_ai(unknown)` → `ai_classified`
     - Merge: `all_genders = {**known, **ai_classified}`
     - Apply to DataFrame: `df["Gender"] = df["_first_name"].map(all_genders).fillna("")`
     - Return `df`
  6. Implement `update_gender_csv(gender_df: pd.DataFrame, new_classifications: dict[str, str]) -> pd.DataFrame`:
     - Create new rows DataFrame from `new_classifications`
     - Concatenate with existing `gender_df`
     - Deduplicate on `Patient` column (keep last, so manual corrections override)
     - Sort by `Patient` column alphabetically
     - Return updated DataFrame

- [X] T018 [US3] Update `main.py` to integrate gender classification. Modify `main()`:

  1. Add imports: `src.gender_classifier.classify_genders`, `src.gender_classifier.update_gender_csv`, `src.drive_handler.download_csv`, `src.drive_handler.upload_csv`
  2. After the dedup step, add:
     - `gender_df = download_csv(os.environ["DRIVE_CSV_FILE_ID"])` — log count
     - Call `df = classify_genders(df, gender_df)`
     - Collect new AI-classified names (those not in original `gender_df`)
     - If new classifications exist: call `updated_csv = update_gender_csv(gender_df, new_classifications)` then `upload_csv(updated_csv, os.environ["DRIVE_CSV_FILE_ID"])` and log "CSV updated on Google Drive"
  3. Remove the old `df["Gender"] = ""` placeholder line — `classify_genders` now sets it
  4. The message generation step now receives real gender values

- [X] T019 [P] [US3] Write unit test in `tests/unit/test_gender_classifier.py`:

  1. Import `classify_from_csv`, `update_gender_csv` from `src.gender_classifier`
  2. Test `test_csv_lookup_finds_known_names`: create a gender_df with known names, verify lookup returns correct genders
  3. Test `test_csv_lookup_returns_empty_for_unknown`: verify unknown names return empty result
  4. Test `test_update_csv_adds_new_entries`: verify new entries are added and result is sorted
  5. Test `test_update_csv_deduplicates`: verify duplicate patient names are deduplicated (last wins)
  6. Do NOT test the OpenAI call in unit tests — that requires mocking and is optional

**Checkpoint**: Gender classification is now live. The pipeline uses CSV first, OpenAI as fallback, and updates the CSV after each run.

---

## Phase 6: User Story 4 — Doctor Name Translation in Messages (Priority: P2)

**Goal**: Doctor names appear in Arabic in messages with correct title prefix rules.

**Independent Test**: Provide appointments with various doctors, verify Arabic names and prefix rules.

### Implementation for User Story 4

- [X] T020 [US4] Populate the doctor translation dictionary in `src/doctor_translator.py` with real doctor names. The user MUST edit this file and replace the placeholder comments with actual entries:

  1. Replace the commented-out example entries with real doctor name mappings
  2. Ensure doctors named "eman" and "mohamed" use full-name keys for disambiguation
  3. Add a code comment above the dictionary explaining how to add new doctors:
     ```python
     # To add a new doctor:
     # 1. Add their lowercase English first name as key
     # 2. Add their Arabic name as value
     # 3. If the first name is "eman" or "mohamed", use full lowercase name as key
     #    (e.g., "eman hassan": "إيمان")
     ```
  4. Log a summary at module import: the number of doctors in the dictionary

> **NOTE**: This task requires the user to provide the actual doctor names. The implementer should create the structure and leave clear instructions for the user to fill in.

**Checkpoint**: Doctor translation is complete and integrated (was already wired in T013/T014).

---

## Phase 7: User Story 5 — Phone Number Validation (Priority: P2)

**Goal**: Clean and validate Egyptian phone numbers; flag bad ones with `?` suffix.

**Independent Test**: Provide various phone formats, verify normalisation and `?` flagging.

### Implementation for User Story 5

- [X] T021 [US5] Implement the phone normalizer in `src/phone_normalizer.py`. It MUST:

  1. Import: `re`, `logging`
  2. Implement `normalize_phone(raw_phone: str) -> str`:
     - If `raw_phone` is None or empty: return `"?"`
     - Strip all whitespace, dashes, parentheses: `cleaned = re.sub(r"[\s\-\(\)]+", "", str(raw_phone))`
     - Remove any leading `+` for processing: `digits = cleaned.lstrip("+")`
     - **Country code logic**:
       - If starts with `20` and total length is 12 (country code + 10 digits): prepend `+` → `+20xxxxxxxxxx`
       - If starts with `0` and total length is 11 (local format): replace leading `0` with `+20` → `+20xxxxxxxxxx`
       - If total length is 10 (no prefix): prepend `+20` → `+20xxxxxxxxxx`
       - If already starts with `+20`: keep as-is
       - Otherwise: return original with `?` suffix (flagged as suspicious)
     - **Validation**: After normalisation, verify the result matches pattern `+20\d{10}` — if not, append `?`
     - Return the normalised number
  3. Implement `normalize_phones(df: pd.DataFrame) -> pd.DataFrame`:
     - Apply `normalize_phone` to the `PhoneNumber` column
     - Count and log flagged numbers: `flagged = df["PhoneNumber"].str.contains("?", regex=False).sum()`
     - Log: `f"Phone issues (flagged with ?): {flagged}"` at WARNING level if flagged > 0
     - Return the DataFrame
  4. Add docstring with examples of each normalisation case

- [X] T022 [US5] Update `main.py` to integrate phone normalisation. Modify `main()`:

  1. Add import: `src.phone_normalizer.normalize_phones`
  2. Add the normalisation step **immediately after** fetching appointments and **before** deduplication:
     - `df = normalize_phones(df)`
  3. This ensures all downstream steps (dedup, WA links) use clean phone numbers

- [X] T023 [P] [US5] Write unit test in `tests/unit/test_phone_normalizer.py`:

  1. Import `normalize_phone` from `src.phone_normalizer`
  2. Test `test_local_format_01xxxxxxxxx`: input `"01012345678"` → output `"+2001012345678"` (wait, 01 + 9 digits = 10 total = 11 with 0). Actually: Egyptian mobile: `01x xxxx xxxx` = 11 digits starting with 0. So: `"01012345678"` → `"+201012345678"`
  3. Test `test_with_country_code`: input `"201012345678"` → output `"+201012345678"`
  4. Test `test_with_plus_country_code`: input `"+201012345678"` → output `"+201012345678"`
  5. Test `test_with_spaces`: input `"010 1234 5678"` → output `"+201012345678"`
  6. Test `test_empty_phone`: input `""` → output `"?"`
  7. Test `test_invalid_length`: input `"12345"` → output should end with `?`
  8. Test `test_none_phone`: input `None` → output `"?"`

**Checkpoint**: Phone numbers are now normalised with Egypt +20 prefix, and invalid numbers are flagged.

---

## Phase 8: User Story 6 — Output Delivery to Cloud Storage (Priority: P3)

**Goal**: Upload the Excel file to Google Drive with correct date-range naming.

**Independent Test**: Run the pipeline, verify the file appears in the Drive folder with `WellSkin_Followup_YYYY-MM-DD_to_YYYY-MM-DD.xlsx` naming.

### Implementation for User Story 6

- [X] T024 [US6] Verify and update the Excel filename pattern in `main.py`. Ensure:

  1. The filename uses both start and end dates: `f"WellSkin_Followup_{start_date}_to_{end_date}.xlsx"` where `start_date` and `end_date` come from `get_date_range_for_filename()`
  2. If this was already done in T011, verify and confirm correctness
  3. The upload call uses `upload_excel(filename, os.environ["DRIVE_OUTPUT_FOLDER_ID"])`
  4. Log: `f"Excel uploaded to Google Drive (folder: Output)"`

**Checkpoint**: Output delivery is complete. Files are correctly named and uploaded.

---

## Phase 9: User Story 7 — Structured Run Logging (Priority: P3)

**Goal**: Every pipeline step emits structured logs with summary counts.

**Independent Test**: Trigger a run and verify logs contain: date range, appointment count, gender counts, flagged phones, file name, upload confirmation, completion message.

### Implementation for User Story 7

- [X] T025 [US7] Audit and complete logging across all modules. Review each module and ensure it has comprehensive logging. Specifically:

  1. **`main.py`**: Ensure these log messages exist (add any missing):
     - `INFO`: "Pipeline starting..."
     - `INFO`: `f"Date range: {start} → {end}"`
     - `INFO`: `f"Fetched {n} appointments"`
     - `INFO`: `f"After dedup: {n} unique patients"`
     - `INFO`: `f"Gender mapped from CSV: {n} / {total}"`
     - `INFO`: `f"Sending {n} unknown names to OpenAI..."` (only if unknowns exist)
     - `INFO`: `f"OpenAI classified {n} names"` (only if AI called)
     - `INFO`: `f"CSV updated on Google Drive"` (only if new names added)
     - `INFO`: `f"Excel written: {filename}"`
     - `INFO`: `f"Excel uploaded to Google Drive (folder: Output)"`
     - `INFO`: `f"✅ Run complete. {n} messages ready."`
  2. **`src/phone_normalizer.py`**: `WARNING` for flagged phone numbers count
  3. **`src/doctor_translator.py`**: `WARNING` for each untranslated doctor name
  4. **`src/gender_classifier.py`**: `ERROR` if OpenAI call fails (with exception details)
  5. Ensure NO log message contains any secret/token values

- [X] T026 [US7] Add error handling to `main.py` for infrastructure failures. Wrap critical sections:

  1. Wrap `fetch_appointments()` call in try/except. If it fails: log `ERROR` with `f"EHR API error: {e}"` and re-raise (this is an infrastructure failure that should halt the run)
  2. Wrap `download_csv()` call in try/except. If it fails: log `WARNING` and proceed with an empty gender DataFrame (fail-forward per Constitution)
  3. Wrap `upload_excel()` call in try/except. If it fails: log `ERROR` with Drive error details and re-raise (upload failure is infrastructure-level)
  4. Wrap `upload_csv()` call in try/except. If it fails: log `WARNING` — CSV update failure is non-critical, the pipeline already produced the Excel

**Checkpoint**: All logging is in place. An administrator can verify run success from the log output alone.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Final integration verification and documentation

- [X] T027 [P] Create `README.md` at the project root with:
  1. Project title: "WellSkin Follow-Up Automation"
  2. One-paragraph description of what it does
  3. Link to quickstart.md for setup instructions
  4. Section listing the 5 required GitHub Secrets
  5. Section explaining the project structure (list of `src/` modules with one-line descriptions)
  6. Section on how to add a new doctor (edit `doctor_translator.py`)
  7. Section on how to correct a gender classification (edit the CSV in Google Drive)

- [X] T028 Run full end-to-end validation:
  1. Run `pip install -r requirements.txt` to verify all dependencies install
  2. Run `pytest tests/` to verify all unit tests pass
  3. Create a `.env` file with real credentials
  4. Run `python main.py` and verify:
     - Log output shows all expected messages
     - Excel file is created locally with correct naming
     - Excel file is uploaded to Google Drive
     - WhatsApp links in the Excel file work (click one to verify)
     - Gender CSV is updated on Google Drive with any new names

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 — MVP
- **US2 (Phase 4)**: Depends on Phase 3 (needs the orchestrator skeleton)
- **US3 (Phase 5)**: Depends on Phase 4 (needs gender column in DataFrame)
- **US4 (Phase 6)**: Can start after Phase 4 (only edits the dictionary file)
- **US5 (Phase 7)**: Can start after Phase 3 (integrates into orchestrator)
- **US6 (Phase 8)**: Can start after Phase 3 (verifies upload logic)
- **US7 (Phase 9)**: Depends on all prior phases (audits complete pipeline)
- **Polish (Phase 10)**: Depends on all user stories being complete

### Parallel Opportunities

```
After Phase 2:
  └── Phase 3 (US1)

After Phase 3:
  ├── Phase 4 (US2) — must be before Phase 5
  ├── Phase 7 (US5) — independent
  └── Phase 8 (US6) — independent

After Phase 4:
  ├── Phase 5 (US3) — depends on US2
  └── Phase 6 (US4) — independent

After all user stories:
  ├── Phase 9 (US7) — logging audit
  └── Phase 10 — polish
```

### Within Each User Story

- Implementation tasks in listed order (earlier tasks create files later tasks depend on)
- Test tasks marked [P] can run in parallel with each other
- Commit after each task or logical group

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (Drive handler + EHR fetcher + logging)
3. Complete Phase 3: User Story 1 (date range + Excel + upload)
4. **STOP and VALIDATE**: Verify Excel file appears in Google Drive with correct columns
5. Continue with remaining user stories

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 → Test: Excel file produced and uploaded (MVP!)
3. Add US2 → Test: Messages contain Arabic verbs and doctor names
4. Add US3 → Test: Gender CSV grows after each run
5. Add US5 → Test: Phone numbers normalised with +20
6. Add US4 → Test: All doctors translated correctly
7. Add US7 → Test: Logs are complete and actionable
8. Polish → README + full end-to-end validation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate independently
- All file paths are relative to the project root
- The user MUST populate `DOCTOR_TRANSLATIONS` in T020 with their real doctor names
- The user MUST configure GitHub Secrets before the first automated run
