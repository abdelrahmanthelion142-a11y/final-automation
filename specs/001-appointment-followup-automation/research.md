# Research: Automated Weekly Appointment Follow-Up Tool

**Branch**: `001-appointment-followup-automation`  
**Date**: 2026-03-20

## Summary

All technology choices were pre-determined by the user's project description.
No NEEDS CLARIFICATION items were found in the Technical Context. This
research document records the decisions and rationale for each choice.

## Decisions

### D1: HTTP Client — httpx

- **Decision**: Use `httpx` for EHR GraphQL API calls.
- **Rationale**: Lightweight async-capable HTTP client, already specified by
  the user. Supports custom headers for bearer token authentication. Simpler
  than `requests` for GraphQL POST payloads.
- **Alternatives considered**: `requests` (heavier, no async), `aiohttp`
  (overkill for synchronous pipeline).

### D2: Data Processing — pandas

- **Decision**: Use `pandas` for in-memory data manipulation.
- **Rationale**: Natural fit for tabular appointment data. Provides built-in
  deduplication (`drop_duplicates`), sorting, merging with gender CSV, and
  column transformations. Widely used and well-documented.
- **Alternatives considered**: Pure Python dicts/lists (less expressive for
  dedup + merge operations).

### D3: AI Gender Classification — OpenAI (gpt-4o-mini)

- **Decision**: Use OpenAI `gpt-4o-mini` with structured output (Pydantic
  response model) for gender classification of unknown Arabic first names.
- **Rationale**: Cheapest capable model (~20x cheaper than gpt-4o). Structured
  output ensures deterministic Male/Female responses. Batch all unknowns in a
  single call to minimise cost.
- **Alternatives considered**: `gpt-4o` (more expensive, marginal accuracy
  gain for this simple task), rule-based heuristics (insufficient for Arabic
  name diversity).

### D4: Excel Generation — openpyxl

- **Decision**: Use `openpyxl` for Excel file creation.
- **Rationale**: Supports HYPERLINK formulas, cell styling (blue underlined
  link text), and `.xlsx` format. Proven library for programmatic Excel
  generation.
- **Alternatives considered**: `xlsxwriter` (similar capabilities but
  openpyxl more commonly paired with pandas), CSV output (lacks clickable
  links).

### D5: Google Drive Integration — Service Account + Drive API v3

- **Decision**: Use Google Service Account authentication with Drive API v3
  for both CSV download/upload and Excel upload.
- **Rationale**: Service Accounts work headlessly in CI/CD — no OAuth consent
  flow required. JSON key stored as a GitHub Secret. Only requires sharing
  target files/folders with the service account email.
- **Alternatives considered**: OAuth2 user flow (requires interactive consent,
  incompatible with headless CI), Google Drive direct link download (read-only,
  can't upload).

### D6: Phone Number Normalisation — Custom Module

- **Decision**: Implement phone normalisation as a custom module (no external
  library).
- **Rationale**: Rules are simple and Egypt-specific: strip spaces/dashes,
  prepend `+20` if no international prefix, validate digit count. A dedicated
  library like `phonenumbers` adds dependency weight for a narrow use case.
- **Alternatives considered**: `phonenumbers` library (full-featured but
  heavy for one country code).

### D7: CI/CD — GitHub Actions

- **Decision**: Use GitHub Actions with daily cron schedule.
- **Rationale**: Repository already hosted on GitHub. Native cron support,
  built-in secrets management, ubuntu-latest runners with Python 3.12. Manual
  `workflow_dispatch` trigger also supported.
- **Alternatives considered**: None — GitHub Actions was specified by the user.

### D8: Configuration — Environment Variables + python-dotenv

- **Decision**: All runtime configuration via environment variables; use
  `python-dotenv` for local development convenience.
- **Rationale**: GitHub Actions injects secrets as env vars. `python-dotenv`
  lets developers run locally with a `.env` file. No config files to manage.
- **Alternatives considered**: YAML/JSON config files (unnecessary complexity
  for 5 secrets).
