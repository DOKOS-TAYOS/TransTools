# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.1] - 2026-05-17

### Added

- Added repository Dependabot configuration for Python dependencies, Sphinx docs dependencies, and GitHub Actions.
- Added `pip-audit` to the development toolchain and CI workflow so known vulnerable Python packages fail automated checks.
- Added GitHub dependency review for pull requests.

### Fixed

- Local `.env` writing now flattens multiline values before saving, preventing accidental extra environment assignments from pasted config text.
- Newly generated local voice-metrics encryption keys now use private POSIX file permissions where supported.

## [0.2.0] - 2026-05-03

### Added

- Configuration dialog now includes full-profile export/import/delete actions for moving or fully resetting local user data, including profile/history JSON files, the local voice-metrics key, and saved audio when present; destructive deletion now also requires typing `BORRAR`.
- Adaptive habit checklist now includes seven extra low-friction micro-habits for basic routines and lightweight day planning.
- Companion Phase 1:
  - Main-menu quick summary panel with direct access to a new companion center.
  - Companion center with dashboard, editable roadmap, appointment preparation, and wellbeing tabs.
  - Typed companion domain models for roadmap items, appointment prep, wellbeing logs, milestones, and dashboard snapshots.
  - Companion datasets in local storage and export frames: roadmap, appointments, wellbeing, and milestones.
  - Automatic follow-up appointment preparation when a visit stores a next visit date.
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

### Changed

- The repo now exposes a `dev` extra for local quality tools, and GitHub Actions installs that extra so `pyright` runs together with Ruff and pytest in CI.
- The fake-history generator script now rebuilds `patient_history.json` with the current record schema, fills companion records such as roadmap items, appointment prep, wellbeing logs, and milestones, extends generated data through the current day, and still preserves existing voice rows that already point to saved audio files.
- Scroll-heavy primary windows now open slightly taller by default, and the main menu also starts a bit higher, giving the companion center, contacts directory, configuration dialog, and landing screen more vertical room so their scrollbars stay still more often on the current default UI size; the `Ver mis datos` window keeps a slightly shorter dedicated height to avoid feeling oversized.
- Collapsible information sections now use cleaner chevron icons for their open/closed state instead of plain `>` / `v` text.
- Night mode UI chrome now uses clearer shared surface separation and visible dark-mode borders across cards, buttons, inputs, tables, listboxes, collapsible headers, and the main menu hero so the interface no longer reads as one flat block in dark theme.
- Windows and Linux installer/setup/run scripts now share a typed Python bootstrap flow that reuses `.venv` directly, validates the installation more clearly, offers `run --check`, and gives more actionable recovery messages when setup or launch fails.
- Sphinx landing docs now reflect the current installation flow more clearly, including `.venv` reuse, one-step install scripts, and the `run --check` validation mode.
- Weekly voice trends are now hidden unless a week has voice samples on at least two distinct days, so single-day recordings do not produce weekly pitch analysis or exports.
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

### Fixed

- The remaining untyped helpers flagged during the public-release review now declare explicit parameter and return types in the other-records dialog and voice-privacy Fernet builder.
- Full profile deletion now also removes any legacy project-local profile copy in `output/`, preventing old data from being auto-migrated back after restart and making the reset behave like a true fresh start.
- Button copy and feedback are now more explicit in key dialogs: onboarding now uses a clearer `Cancelar y salir` action, configuration checkboxes explain their exact effect next to the toggle, and companion actions that require a selected row now tell the user what to select instead of failing silently.
- Profile import now validates exported JSON and the local voice-metrics key before replacing local data, so corrupt bundles fail fast instead of only breaking after restart.
- Profile import now stages and rolls back managed files/directories when a replacement fails, preventing mixed old/new local state after partial import errors.
- Configuration profile-transfer dialogs now handle optional Tk parents and their tests with stricter typing, which removes the remaining `pyright` errors in the config dialog flow.

### Changed

- The shared ttk theme now passes combobox popup fonts to Tk using a font tuple instead of a plain string, which fixes configuration dropdowns when the system font family contains spaces (for example `Segoe UI` on Windows).
- Light theme shared widget borders now derive from a darker stroke color instead of a lighter one, and day-mode cards/buttons now use visible outlined chrome so panels and actions no longer disappear into the pale background.
- The main menu no longer duplicates the `Mi acompañamiento` shortcut inside the quick-summary card; that entry now lives only in the `Seguimiento y apoyo` section.
- The main-menu quick-summary card now keeps the `Mostrar` / `Ocultar` toggle inline at the right of the `Resumen rápido` title instead of placing a longer button underneath the heading.
- Contacts tables now reserve more row height per wrapped line, which prevents clipped entries in long-description rows such as the `Nacionales` and `Castilla-La Mancha` contact lists.
- The configuration dialog now limits appearance settings to a fixed day/night theme mode plus one global font-size control, with the rest of the UI styling derived automatically and older visual `.env` keys retired.
- Reviewed the adaptive habit catalog so extreme, overly medical, clinical, unusually niche, overly normative/social-pressure, or strongly resource-dependent entries were removed from the base catalog and locale habit labels, and older saved profiles/logs are pruned to the same safer set during migration.
- Voice recording now always registers the sample for the current day, and the recording dialog no longer mixes in self-reported emotional scoring because that check-in belongs in a separate flow.
- Scrollable Tk panels now react to the mouse wheel from any child control inside the panel, appointment writing areas were tightened so the `Citas` form fits more often without needing its scrollbar, and screen-fit sizing now leaves a larger vertical safety margin on Windows so dialogs are less likely to extend off-screen.
- Companion appointments and contacts dialogs now fit dense Spanish content better: the appointments form has more writing space plus internal scrolling so its lower actions/status never get cut off, the related tables use clearer column sizing/borders, and the contacts directory adds taller rows together with a horizontal scrollbar so long description/email/web columns stay usable instead of clipping.
- The contacts directory now sizes each table's row height from the longest wrapped description in that dataset, so the national contacts view no longer truncates multi-line rows just because regional rows are shorter.
- The `Proceso` tab in the unified data view now stacks the roadmap and appointments tables vertically instead of squeezing them side by side, and each table has its own horizontal and vertical scrollbars for more comfortable reading.
- Voice dialog imports no longer require `sounddevice`/PortAudio during module loading, so pytest collection works in environments where the recording backend is unavailable.
- Dynamic Tkinter dialogs that compute their size from the current form layout now preserve Tk's full requested height instead of undersizing by a few pixels on some screens, avoiding cramped footer buttons and making the recording, medication, onboarding, and other-records windows more comfortable to use.
- Tkinter UI now uses a more polished "dark premium" visual system: richer derived surfaces, stronger control hierarchy across buttons/tabs/tables/inputs, upgraded note and info panel styling, and a redesigned main menu landing page with a hero header, grouped action cards, a more prominent quick-summary panel, tighter menu sizing so long Spanish labels fit without clipping, and a vertical scrollbar when the menu content exceeds the available screen height.
- UI density and oversized dialogs are now better balanced: default `.env` UI font/padding are more compact, shared ttk button/tab/table sizing was tightened, requested window sizes are clamped to the available screen, and the companion dashboard now gives long summaries full-width sections with responsive wrapping instead of squeezing them into narrow side-by-side blocks.
- Contacts/resources dataset reviewed, expanded and normalized with current public sources: refreshed outdated emails and phones, updated Trànsit coverage and direct contact, clarified mixed entity/service entries such as Kattalingorri / Kattalingune and Gehitu, added new verified associations and public services across Spain, harmonized directory copy plus per-region contact ordering, added a visible `Tipo` column for faster scanning, and completed additional missing public contact data where official general details were available.
- Main menu quick summary now starts collapsed as a real expandable section, with a centered auto-sized toggle, smaller toggle text, and no extra heading text, and shared ttk theming now keeps notebooks, tables, dropdowns, and grouped panels on dark non-white surfaces across the newer dialogs.
- Medication and visit logs can now optionally save a same-day wellbeing check-in from their existing dialogs.
- Unified data view now includes companion process and wellbeing summary tabs.
- README and Sphinx landing docs now explain the current product scope, user flows, privacy model, storage layout, exports, and profile-transfer behavior more clearly for end users.
- Repository defaults and migrations now initialize `journey_stage` plus companion collections for existing users without losing previous data.
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
