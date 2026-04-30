# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- New modular core services with split JSON storage:
  - `patient_profile.json` (output): static patient data (name, health config, appointments, habit catalog).
  - `patient_history.json` (output): historical records (voice, medication, visits, events, habits).
  - `contacts.json` (src/data): support contacts (app-level, not in output).
- First-run onboarding wizard (3 steps) with optional health setup fields.
- New main menu structure with dedicated modules:
  - Voice log
  - Medication log
  - Other logs (visits + free events)
  - Adaptive habit checklist
  - Contacts/resources
  - App information
  - Unified data view
  - Configuration
- Voice privacy workflow:
  - Local encryption for sensitive tone metrics.
  - Weekly-only tone visibility policy in UI and exports.
- Medication/visit reminders for due or overdue items at app startup.
- Unified data view with calendar, daily non-sensitive summary, and weekly chart.
- Export support for CSV, Excel, PDF, and PNG.
- Linux scripts: `setup.sh`, `install.sh`, `bin/run.sh`.
- Third-party license inventory (`THIRD_PARTY_LICENSES.md`).
- Contacts dataset (`src/data/contacts.json`).
- New dependencies: `tkcalendar`, `reportlab`, `cryptography`.

### Changed

- Default data storage now uses a user-scoped directory on Windows and Linux instead of the project-local `output/`, with one-time migration from legacy files when needed.
- Settings restart now relaunches the app through the resolved `src/main.py` path instead of depending on `sys.argv[0]`.
- Medication startup reminders now stay compact by showing today's due warning plus one aggregated overdue summary.
- Legacy data migration is now file-by-file, so existing destination files are preserved while any missing legacy files are still copied across.
- Habit IDs with legacy mojibake or accents are now normalized to a stable ASCII form, with compatible migration for saved catalogs and checklist records.
- Configuration dialog now also edits profile and health fields.
- Obsolete `FILE_DATA_FORMAT` config is no longer emitted or treated as a supported setting.
- Optional health dates in the unified data view no longer auto-save as "today" when left blank, and they can be cleared safely.
- Configuration numeric fields now use narrower error handling instead of broad fallback catches.
- Locale loading now repairs mojibake text at runtime and aligns habit-name translation keys with normalized IDs.
- Pytest cacheprovider is now disabled in project config to avoid Windows permission warnings in this workspace.
- Deprecated `meta.help_shown` is no longer emitted in new saved state, while older data remains readable.
- Voice analysis now computes heuristic mood scores from acoustic features.
- Voice recording can again be registered for a user-selected past date instead of always using the current day.
- README updated to reflect full v1 scope and offline-first behavior.

## [0.1.0] - 2026-02-23

### Added

- Voice recording with pitch analysis (tone, energy, mood score)
- Historical record with table and evolution charts
- Data export to CSV and Excel
- Configuration via `.env` (language, paths, recording duration)
- Tkinter GUI
- Multilingual support (Spanish, English)
