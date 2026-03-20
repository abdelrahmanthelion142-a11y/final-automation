<!--
  Sync Impact Report
  ==================
  Version change: (none) → 1.0.0
  Modified principles: N/A (initial creation)
  Added sections:
    - Core Principles (6 principles)
    - External Service Boundaries
    - Code Quality Standards
    - Governance
  Removed sections: N/A
  Templates requiring updates:
    - plan-template.md: ✅ No changes required (Constitution Check section is generic)
    - spec-template.md: ✅ No changes required
    - tasks-template.md: ✅ No changes required
  Follow-up TODOs: None
-->

# WellSkin Follow-Up Automation Constitution

## Core Principles

### I. Modular Pipeline Steps

Every processing stage (date range, fetch, normalise, classify, translate,
generate, export, upload) MUST be implemented as an independent, self-contained
module with a clear single responsibility.

- Each module MUST expose a well-defined function interface that accepts
  explicit inputs and returns explicit outputs — no hidden side effects.
- Modules MUST NOT depend on each other's internal implementation details;
  they communicate only through data (DataFrames, dicts, file paths).
- Adding, replacing, or reordering a step MUST NOT require changes to
  unrelated modules.

### II. Fail-Forward Resilience

The pipeline MUST continue processing and produce output even when individual
records contain bad or incomplete data.

- Invalid data (e.g., malformed phone numbers, unclassifiable names) MUST be
  flagged visibly in the output (e.g., `?` suffix) rather than silently
  dropped or causing the run to abort.
- Partial failures (e.g., AI service unavailable) MUST degrade gracefully:
  produce the best possible output with available data and log what was
  skipped.
- Only infrastructure-level failures (e.g., EHR unreachable, authentication
  invalid) are allowed to halt the run entirely, and MUST produce a clear
  error log identifying the failure point.

### III. Secrets & Security

All credentials, tokens, and service account keys MUST be managed through
environment variables injected at runtime — never hardcoded, committed, or
logged.

- Secrets MUST be stored in the CI/CD platform's secret management and
  injected via environment variables.
- Log output MUST NOT contain tokens, API keys, or any credential material.
- Service account access MUST follow the principle of least privilege: only
  the specific files and folders required for operation should be shared.

### IV. Structured Logging

Every pipeline step MUST emit structured log entries that enable an
administrator to verify run success and diagnose issues without reading code.

- Logs MUST include: timestamp, severity level, and a human-readable message.
- Each step MUST log at least one entry on entry and one on completion,
  including relevant counts (e.g., records fetched, records classified,
  records flagged).
- The final log entry of a successful run MUST include a summary count of
  total messages generated.
- Warnings (flagged data, missing dictionary entries) MUST be logged at
  WARNING level so they are easily filterable.

### V. Data Integrity

All external data entering the pipeline MUST be validated and normalised
before being used in downstream steps.

- Phone numbers MUST be normalised into a consistent format before generating
  WhatsApp links.
- Patient names MUST be reduced to a canonical form (first name extraction)
  before gender lookup.
- The gender classification CSV MUST be deduplicated and sorted after every
  update to prevent data drift.
- Manual corrections in the CSV MUST always take precedence over AI
  classifications — the CSV is the source of truth for gender data.

### VI. Simplicity (YAGNI)

The system MUST remain as simple as possible for V1. Features not explicitly
required MUST NOT be implemented.

- No UI, dashboard, or web interface.
- No automatic WhatsApp sending — manual click-to-send via Excel links.
- No multi-branch support — single branch ID is acceptable.
- No retry/backoff logic for external API failures in V1.
- No dynamic doctor name resolution — a hardcoded translation dictionary
  updated via code commits is sufficient.
- Complexity MUST be justified in writing if it deviates from these
  constraints.

## External Service Boundaries

All interactions with external services (EHR API, AI classification service,
cloud storage) MUST be isolated behind dedicated handler modules.

- Each external service MUST be accessed through a single module that
  encapsulates authentication, request formation, and response parsing.
- External service calls MUST NOT be scattered across business logic modules.
- The handler modules MUST be the only code that imports external service
  client libraries.
- If an external service changes its API, only the corresponding handler
  module should need to be updated.

## Code Quality Standards

- All Python code MUST follow consistent formatting (one formatter, applied
  project-wide).
- Functions MUST have clear docstrings describing inputs, outputs, and any
  side effects.
- The `requirements.txt` MUST pin all direct dependencies to avoid
  environment drift between runs.
- Every module MUST be importable and callable independently for manual
  testing and debugging.

## Governance

This constitution is the authoritative source of development principles for
this project. All implementation decisions, code reviews, and plan approvals
MUST be checked against these principles.

- **Amendment procedure**: Any change to this constitution MUST be documented
  with a version bump, rationale, and migration plan for affected code.
- **Versioning**: MAJOR.MINOR.PATCH — MAJOR for principle removals or
  redefinitions, MINOR for new principles or material expansions, PATCH for
  clarifications and wording fixes.
- **Compliance review**: Before merging any feature, verify that the
  implementation does not violate the principles listed above. The plan
  template's "Constitution Check" section MUST reference these principles by
  number (I–VI).

**Version**: 1.0.0 | **Ratified**: 2026-03-20 | **Last Amended**: 2026-03-20
