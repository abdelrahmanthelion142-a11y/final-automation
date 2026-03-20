# Data Model: Automated Weekly Appointment Follow-Up Tool

**Branch**: `001-appointment-followup-automation`  
**Date**: 2026-03-20

## Entities

### Appointment (from EHR API)

Raw record fetched from the EHR GraphQL API.

| Field       | Type   | Source        | Notes |
|-------------|--------|---------------|-------|
| Patient     | string | EHR response  | Full name (Arabic) |
| Date        | string | EHR response  | ISO 8601 datetime |
| Doctor      | string | EHR response  | English full name |
| PhoneNumber | string | EHR response  | Raw, unformatted |

**Deduplication rule**: When a patient has multiple appointments in the 7-day
window, keep only the row with the **earliest** Date value. Deduplication key:
patient first name + phone number.

---

### Gender Classification Record (Google Drive CSV)

Persistent store that grows over time.

| Field   | Type   | Constraints |
|---------|--------|-------------|
| Patient | string | First name only (Arabic), unique, sorted alphabetically |
| Gender  | string | Enum: `Male` or `Female` |

**Source of truth**: Manual edits in the CSV override AI classifications.
**Update cycle**: After each run, newly classified names are merged, the CSV
is deduplicated by `Patient`, sorted, and re-uploaded.

---

### Doctor Translation Entry (in-code dictionary)

Static mapping maintained by developers.

| Field         | Type    | Notes |
|---------------|---------|-------|
| english_key   | string  | Lookup key — usually first name; full name for `eman`, `mohamed` |
| arabic_name   | string  | Arabic translation |
| suppress_title| boolean | If `true`, omit "د/" prefix (e.g., for doctor "آية") |

**Disambiguation rule**: Doctors named "eman" or "mohamed" use full English
name as lookup key to distinguish from other doctors sharing the same first name.

---

### Follow-Up Message (generated, in-memory)

One row per unique patient in the output.

| Field         | Type   | Notes |
|---------------|--------|-------|
| PhoneNumber   | string | Normalised (Egypt +20 prefix), or flagged with `?` |
| Message       | string | Arabic text with gendered verb + doctor Arabic name |
| Date          | string | Appointment date (human-readable) |
| WhatsAppLink  | string | `https://wa.me/{phone}?text={encoded_message}` |

---

### Output Excel File

Final deliverable uploaded to Google Drive.

| Column        | Type          | Notes |
|---------------|---------------|-------|
| PhoneNumber   | text          | Normalised Egyptian number |
| Message       | text          | Full Arabic follow-up message |
| Date          | text          | Appointment date |
| WhatsApp Link | HYPERLINK     | Clickable "Send" link with blue styling |

**File naming**: `WellSkin_Followup_YYYY-MM-DD_to_YYYY-MM-DD.xlsx`
(start and end of the 7-day window).

## Data Flow

```text
EHR GraphQL API
    │
    ▼
[Raw Appointments DataFrame]
    │  columns: Patient, Date, Doctor, PhoneNumber
    │
    ├─── Phone Normalizer ──► PhoneNumber cleaned, ?-flagged
    │
    ├─── Deduplicate ──► One row per patient (earliest Date)
    │
    ├─── Gender Classifier
    │       ├─ CSV lookup (first name → Gender)
    │       ├─ OpenAI fallback (unknown names → Gender)
    │       └─ CSV update (merge + dedup + sort + upload)
    │       ▼
    │    DataFrame gains: Gender column
    │
    ├─── Doctor Translator ──► Doctor column → Arabic name
    │
    ├─── Message Generator ──► Message column (gendered Arabic)
    │
    └─── Excel Exporter ──► .xlsx with HYPERLINK formulas
              │
              ▼
       Google Drive Upload
```

## State Transitions

This pipeline has no persistent application state beyond the gender CSV.
Each run is idempotent: the same input date range will always produce the
same output (assuming EHR data hasn't changed).

The gender CSV is the only stateful artifact:

```
Empty CSV → names classified → CSV grows → manual corrections applied → next run uses updated CSV
```
