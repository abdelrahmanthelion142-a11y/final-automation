# Implementation Plan: Automated Weekly Appointment Follow-Up Tool

**Branch**: `001-appointment-followup-automation` | **Date**: 2026-03-20 | **Spec**: [spec.md](file:///home/user/projects/final%20automation/specs/001-appointment-followup-automation/spec.md)
**Input**: Feature specification from `/specs/001-appointment-followup-automation/spec.md`

## Summary

Build a headless Python automation pipeline that runs weekly (every Sunday at
midnight Egypt time) on GitHub Actions. It fetches a 7-day appointment window
from the EHR GraphQL API, normalises Egyptian phone numbers, classifies
patient genders via a Google Drive CSV + OpenAI fallback, translates doctor
names to Arabic, generates gender-aware Arabic WhatsApp follow-up messages,
exports them to a clickable Excel file, and uploads to Google Drive. One
message per unique patient (deduplicated by earliest appointment).

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: httpx, pandas, openai, pydantic, openpyxl, google-api-python-client, google-auth, python-dotenv  
**Storage**: Google Drive (CSV for gender classifications, folder for Excel output) — no database  
**Testing**: pytest (unit tests for each module)  
**Target Platform**: GitHub Actions (ubuntu-latest), triggered via cron and manual dispatch  
**Project Type**: Headless automation pipeline (CLI/script)  
**Performance Goals**: Complete full pipeline in under 5 minutes for up to 200 appointments  
**Constraints**: Single weekly run (Sunday midnight Egypt time); no retry logic in V1; single clinic branch  
**Scale/Scope**: ~50-200 appointments per 7-day window; ~100-500 unique patient names in gender CSV over time

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Modular Pipeline Steps | ✅ Pass | Each step is a separate module in `src/` with explicit function interfaces |
| II. Fail-Forward Resilience | ✅ Pass | Bad phone numbers flagged with `?`; AI failure degrades gracefully; only EHR/auth failures halt |
| III. Secrets & Security | ✅ Pass | All credentials via env vars from GitHub Secrets; no hardcoded tokens |
| IV. Structured Logging | ✅ Pass | Python `logging` at each step; summary counts in final log entry |
| V. Data Integrity | ✅ Pass | Phone normalisation (+20 prefix); first-name canonicalisation; CSV dedup+sort; CSV overrides AI |
| VI. Simplicity (YAGNI) | ✅ Pass | No UI, no auto-send, no retry, no multi-branch; hardcoded doctor dictionary |
| External Service Boundaries | ✅ Pass | EHR via `appointments.py`, Google Drive via `drive_handler.py`, OpenAI via `gender_classifier.py` |
| Code Quality Standards | ✅ Pass | Consistent formatting; docstrings; pinned `requirements.txt`; each module independently importable |

**Gate result: PASS** — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/001-appointment-followup-automation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/
├── appointments.py        # EHR GraphQL fetch + response parsing (Step 2)
├── phone_normalizer.py    # Phone cleaning, +20 prefix, validation (Step 3)
├── gender_classifier.py   # CSV lookup + OpenAI fallback + CSV update (Step 4)
├── doctor_translator.py   # English→Arabic dictionary + title rules (Step 5)
├── message_generator.py   # Gender-aware Arabic template composition (Step 6)
├── excel_exporter.py      # openpyxl writer + WA HYPERLINK formula (Step 7)
└── drive_handler.py       # Google Drive upload/download via Service Account (Step 8)

main.py                    # Orchestrator: Steps 1-9 in sequence
requirements.txt           # Pinned direct dependencies
.github/
└── workflows/
    └── daily_run.yml      # Cron trigger + secrets injection

tests/
└── unit/
    ├── test_phone_normalizer.py
    ├── test_gender_classifier.py
    ├── test_doctor_translator.py
    ├── test_message_generator.py
    └── test_excel_exporter.py
```

**Structure Decision**: Single-project flat `src/` layout. This is a simple
pipeline with 7 modules and an orchestrator — no need for nested packages,
services layers, or separate frontend/backend. Aligns with Constitution
Principle VI (Simplicity).

## Complexity Tracking

> No Constitution Check violations — this section is intentionally empty.
