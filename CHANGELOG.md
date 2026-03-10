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

- Configuration dialog now also edits profile and health fields.
- Voice analysis now computes heuristic mood scores from acoustic features.
- README updated to reflect full v1 scope and offline-first behavior.

## [0.1.0] - 2026-02-23

### Added

- Voice recording with pitch analysis (tone, energy, mood score)
- Historical record with table and evolution charts
- Data export to CSV and Excel
- Configuration via `.env` (language, paths, recording duration)
- Tkinter GUI
- Multilingual support (Spanish, English)
