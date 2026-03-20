# Feature Specification: Automated Weekly Appointment Follow-Up Tool

**Feature Branch**: `001-appointment-followup-automation`  
**Created**: 2026-03-20  
**Status**: Draft  
**Input**: User description: "A GitHub Actions pipeline that runs weekly (every Sunday at midnight Egypt time), fetches the next 7 days of scheduled appointments from the EHR system, classifies patient genders using a cloud-hosted CSV + AI fallback, generates personalised Arabic WhatsApp messages, and delivers a ready-to-send Excel file to Google Drive."

## Clarifications

### Session 2026-03-20

- Q: What country code should phone number normalisation assume when a number lacks an international prefix? → A: Egypt (`+20`) — prepend if missing.
- Q: If a patient has multiple appointments in the 7-day window, should the system send one message per appointment or one per patient? → A: One message per patient — deduplicate and keep the earliest appointment only.
- Q: Should the output file cover a full 7-day lookahead or only a single day, and how should it be named? → A: Full 7-day lookahead; file named with the week’s from/to date range (e.g., `WellSkin_Followup_2026-03-20_to_2026-03-27.xlsx`).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Weekly Follow-Up File Generation (Priority: P1)

As a clinic administrator, I want the system to automatically run every week, fetch the next 7 days of appointments from the EHR system, and produce a ready-to-send Excel file so that I can send personalised WhatsApp follow-up messages to patients without any manual data gathering.

**Why this priority**: This is the core value proposition — eliminating the weekly manual work of pulling appointment data, composing messages, and formatting output. Without this, the tool has no purpose.

**Independent Test**: Can be fully tested by triggering a run (manually or on schedule), verifying that it fetches appointments for the correct 7-day window, and produces an Excel file with one row per appointment containing the patient's phone number, a personalised Arabic message, the appointment date, and a clickable WhatsApp link.

**Acceptance Scenarios**:

1. **Given** the system is configured with valid EHR credentials, **When** the daily run is triggered, **Then** the system fetches all appointments from today through 7 days ahead and produces an Excel file with columns: PhoneNumber, Message, Date, and WhatsApp Link.
2. **Given** there are 43 appointments in the next 7 days, **When** the run completes, **Then** the output Excel contains exactly 43 rows (one per appointment) and each row has a non-empty message, a valid phone number, and a clickable WhatsApp link.
3. **Given** the system runs weekly, **When** a new week begins (Sunday at midnight Egypt time), **Then** the date range automatically recalculates (no hardcoded dates) using today as the start.

---

### User Story 2 - Gender-Aware Message Personalisation (Priority: P1)

As a clinic administrator, I want each follow-up message to address the patient correctly based on their gender (using the appropriate Arabic verb form) so that messages feel personal and culturally appropriate.

**Why this priority**: Sending a message with the wrong gender form is noticeable and unprofessional in Arabic. This directly impacts patient perception and is essential for usable output.

**Independent Test**: Can be tested by providing a list of appointments with known male and female patients and verifying that each generated message uses the correct gendered Arabic verb form (`تكوني` for female, `تكون` for male).

**Acceptance Scenarios**:

1. **Given** a female patient named "فاطمة" with a known gender, **When** the message is generated, **Then** the Arabic text uses the feminine verb form `تكوني`.
2. **Given** a male patient named "أحمد" with a known gender, **When** the message is generated, **Then** the Arabic text uses the masculine verb form `تكون`.
3. **Given** a patient whose name is not in the known-names list, **When** gender classification runs, **Then** the system uses an AI service to classify the gender, and the result is stored for future runs so that the AI is not called again for the same name.

---

### User Story 3 - Gender Knowledge Base Growth (Priority: P2)

As a clinic administrator, I want the system to remember previously classified patient genders so that over time it becomes faster and cheaper (fewer AI calls) and more accurate.

**Why this priority**: Without persistent gender storage, the system would call the AI service for every patient on every run, increasing cost and latency. A growing knowledge base is essential for long-term efficiency.

**Independent Test**: Can be tested by running the system twice — the first run classifies unknown names via AI and saves them; the second run should find those same names already classified and skip the AI call.

**Acceptance Scenarios**:

1. **Given** a cloud-hosted CSV file with previously classified patient names and genders, **When** the system runs, **Then** it first looks up each patient's first name in the CSV before calling any external service.
2. **Given** 5 patient names are not found in the CSV, **When** the AI classifies them, **Then** the CSV is updated with the 5 new entries and re-uploaded to cloud storage.
3. **Given** a name was previously misclassified by AI and a human has manually corrected it in the CSV, **When** the next run occurs, **Then** the corrected gender from the CSV takes precedence over any AI classification.

---

### User Story 4 - Doctor Name Translation in Messages (Priority: P2)

As a clinic administrator, I want the follow-up message to include the doctor's name in Arabic so that the patient knows which doctor they have an appointment with, presented in their native language.

**Why this priority**: The EHR stores doctor names in English. Arabic-speaking patients expect Arabic text. Translating doctor names is required for message completeness and professionalism.

**Independent Test**: Can be tested by providing appointments with various doctor names and verifying each message contains the correctly translated Arabic doctor name, with the appropriate title prefix.

**Acceptance Scenarios**:

1. **Given** an appointment with doctor "John" in the EHR, **When** the message is generated, **Then** the doctor's name appears in Arabic as defined in the translation dictionary.
2. **Given** a doctor whose Arabic name is "آية", **When** the message is generated, **Then** the "د/" title prefix is omitted from the doctor's name.
3. **Given** doctors named "eman" or "mohamed" (who share first names with other doctors), **When** their name is looked up, **Then** the full English name is used for disambiguation before translation.

---

### User Story 5 - Phone Number Validation (Priority: P2)

As a clinic administrator, I want the system to clean and validate phone numbers so that the WhatsApp links in the Excel file work correctly, and any problematic numbers are visibly flagged for manual review.

**Why this priority**: Invalid or poorly formatted phone numbers render the WhatsApp links useless. Catching bad data early saves the administrator time and prevents failed message deliveries.

**Independent Test**: Can be tested by providing various phone number formats (with spaces, country codes, missing digits, etc.) and verifying that valid numbers are normalised and invalid ones are flagged with a `?` suffix.

**Acceptance Scenarios**:

1. **Given** a phone number with extra spaces or formatting characters, **When** it is processed, **Then** the output contains a clean, normalised phone number suitable for WhatsApp.
2. **Given** a phone number that fails validation rules, **When** it is processed, **Then** the number is kept in the output but suffixed with `?` so it is visible in the Excel without crashing the run.
3. **Given** there are flagged phone numbers in a run, **When** the run completes, **Then** a summary log entry lists all flagged numbers for human review.

---

### User Story 6 - Output Delivery to Cloud Storage (Priority: P3)

As a clinic administrator, I want the final Excel file to be automatically uploaded to a shared cloud storage folder so that I can access it from any device without needing to log into the automation system.

**Why this priority**: Uploading to cloud storage is the final delivery step. Without it, the administrator would need to manually retrieve the file from the automation environment, reducing the automation's value.

**Independent Test**: Can be tested by running the system and verifying that the output Excel file appears in the configured cloud storage folder with the correct naming convention.

**Acceptance Scenarios**:

1. **Given** the system has completed message generation and Excel creation, **When** the upload step runs, **Then** the Excel file is uploaded to the designated cloud storage folder.
2. **Given** a successful upload, **When** the administrator checks the cloud storage folder, **Then** the file is named with the pattern `WellSkin_Followup_YYYY-MM-DD_to_YYYY-MM-DD.xlsx` using the start and end dates of the 7-day window.

---

### User Story 7 - Structured Run Logging (Priority: P3)

As a clinic administrator, I want each automated run to produce a structured log with summary counts so that I can quickly verify whether the run succeeded and how many messages were generated.

**Why this priority**: Logging is essential for operational visibility and troubleshooting, but the system is still valuable without it in the short term.

**Independent Test**: Can be tested by triggering a run and inspecting the log output for key events: date range, appointment count, gender classification counts, flagged numbers, file creation, file upload, and completion status.

**Acceptance Scenarios**:

1. **Given** a successful run, **When** the log is reviewed, **Then** it contains entries for: date range computed, number of appointments fetched, number of genders resolved from CSV vs. AI, number of flagged phone numbers, Excel file name, upload confirmation, and a final completion message with total message count.
2. **Given** a step encounters an issue (e.g., no appointments found), **When** the log is reviewed, **Then** it clearly indicates what happened and at which step.

---

### Edge Cases

- What happens when there are zero appointments in the 7-day window? The system should still complete successfully, produce an empty Excel file (headers only), and log that zero appointments were found.
- What happens when the EHR system is unreachable or returns an error? The run should fail with a clear error message in the logs identifying the EHR connection as the failure point.
- What happens when the AI gender classification service is unavailable? The system should log the failure, leave the gender field empty for unclassified names, and still produce the Excel with as many complete rows as possible.
- What happens when the cloud-hosted gender CSV file is empty or missing headers? The system should treat all names as unknown and proceed with AI classification for the entire batch.
- What happens when a patient has no phone number in the EHR? The row should be included in the Excel with an empty phone number and no WhatsApp link, and logged as a flagged entry.
- What happens when a doctor's English name is not found in the translation dictionary? The system should use the original English name in the message and log a warning so that the dictionary can be updated.
- What happens when a patient has multiple appointments in the 7-day window? The system should deduplicate and keep only the earliest appointment, generating a single follow-up message per patient.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST automatically compute a rolling 7-day date window (today → today + 7 days) on each run with no hardcoded dates.
- **FR-002**: System MUST fetch all scheduled appointments from the EHR system for the computed date window using authenticated requests.
- **FR-003**: System MUST extract from each appointment record: patient name, appointment date, doctor name, and patient phone number.
- **FR-003a**: System MUST deduplicate appointments per patient within the date window, keeping only the earliest appointment when a patient has multiple visits scheduled.
- **FR-004**: System MUST normalise phone numbers by removing extraneous formatting characters, validating their structure, and prepending the Egypt country code (`+20`) when an international prefix is missing.
- **FR-005**: System MUST flag invalid or suspicious phone numbers with a `?` suffix rather than discarding them or stopping execution.
- **FR-006**: System MUST classify each patient's gender by first looking up the patient's first name in a cloud-hosted CSV of previously classified names.
- **FR-007**: System MUST use an AI service as a fallback to classify genders for any patient names not found in the CSV.
- **FR-008**: System MUST batch all unknown names into a single AI request to minimise external service calls and cost.
- **FR-009**: System MUST update the cloud-hosted CSV with newly classified names after each run, deduplicating and sorting entries.
- **FR-010**: System MUST translate doctor names from English to Arabic using a maintained dictionary of name mappings.
- **FR-011**: System MUST generate a personalised Arabic follow-up message for each appointment, using the correct gendered verb form based on the patient's classified gender.
- **FR-012**: System MUST suppress the doctor title prefix ("د/") for specific doctors as defined by business rules (e.g., doctor "آية").
- **FR-013**: System MUST produce an Excel file with columns: PhoneNumber, Message, Date, and WhatsApp Link (clickable hyperlink that opens WhatsApp Web pre-populated with the message).
- **FR-014**: System MUST name the output Excel file using the pattern `WellSkin_Followup_YYYY-MM-DD_to_YYYY-MM-DD.xlsx` where the dates represent the start and end of the 7-day appointment window.
- **FR-015**: System MUST upload the output Excel file to a designated cloud storage folder.
- **FR-016**: System MUST produce structured log entries at each processing step, including summary counts for appointments fetched, genders classified (from CSV vs. AI), phone numbers flagged, and a final completion message.
- **FR-017**: System MUST run on an automated weekly schedule (every Sunday at midnight Egypt time / 22:00 UTC Saturday) as well as support manual/on-demand triggering.

### Key Entities

- **Appointment**: A scheduled patient visit — key attributes: patient name, appointment date, doctor name, patient phone number.
- **Patient**: A person with a scheduled appointment — key attributes: first name (Arabic), gender (Male/Female), phone number.
- **Doctor**: A clinician — key attributes: English name (from EHR), Arabic translated name, title prefix rule.
- **Gender Classification Record**: A mapping of patient first name to gender — stored in the cloud CSV for persistence across runs.
- **Follow-Up Message**: The generated Arabic text for one appointment — composed from patient gender, doctor Arabic name, and appointment date.
- **Output File**: The Excel workbook containing all follow-up messages with WhatsApp links for the current run.

## Assumptions

- The EHR system provides a stable query interface to retrieve appointments by date range.
- The EHR authentication token is long-lived or can be managed externally; token refresh is out of scope for V1.
- The cloud storage service account has read/write access to both the gender CSV file and the output folder.
- The doctor name translation dictionary is maintained manually and updated via code changes when new doctors join.
- The AI gender classification model produces sufficiently accurate results for Arabic first names; manual correction in the CSV overrides AI results on subsequent runs.
- Only one clinic branch is supported in V1 (branch ID is static).
- WhatsApp messages are sent manually by the administrator using the generated links; automatic sending is out of scope.
- There is no user interface or dashboard; the system operates as a headless automated pipeline.
- Retry logic for external service failures is out of scope for V1.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The complete pipeline (fetch → classify → generate → upload) executes end-to-end without manual intervention on every scheduled run.
- **SC-002**: 100% of unique patients with appointments in the 7-day window appear as rows in the output Excel file (one row per patient, earliest appointment used).
- **SC-003**: Gender classification accuracy reaches 95%+, with the ability for humans to correct errors that persist on future runs.
- **SC-004**: The system reduces the administrator's weekly follow-up preparation time from approximately 30+ minutes of manual work to under 2 minutes (open file, review, click links).
- **SC-005**: The gender knowledge base (CSV) grows over time, reducing AI classification calls by at least 80% after the first month of operation.
- **SC-006**: Every generated WhatsApp link opens WhatsApp Web with the correct pre-populated Arabic message, ready to send.
- **SC-007**: Run logs provide enough information for an administrator to determine whether a run was successful and identify any issues within 30 seconds of reviewing the log.
