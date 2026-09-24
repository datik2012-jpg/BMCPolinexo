# Project checkpoint — 2026-09-24

The first-version pilot is published in [BMCPolinexo on GitHub](https://github.com/datik2012-jpg/BMCPolinexo).
The app is available at http://127.0.0.1:8080 while Compose is running.
First product version: `v1.0.0`, commit `528f7bd`, on branch `main`.

## Verified

- Backend: 17 tests passed (`..\.venv\Scripts\python -m pytest -q` from `backend`).
- Frontend: 19 tests passed (`npm test` from `frontend`).
- Production TypeScript/Vite build passed, including the final Docker build.
- `docker compose config --quiet` and `docker compose up --build -d` succeeded.
- Earlier baseline browser acceptance: `.\.venv\Scripts\python -u tests/browser_check.py`
  with `BMC_TEST_DOCKER_RESTART=1` passed before the latest branding/display changes.
- Synthetic import: 20 coverages, 8 groups, 763.32 ILS monthly and 5,642.00 ILS
  annually. Editing, exclusion/restoration, regrouping, incomplete totals,
  source comparison, filtering, RTL/mobile layout, refresh clearing, offline
  locking, and both simulated and actual API restart clearing passed.
- Latest logo browser check: all 26 logos loaded; unknown insurer name remained
  visible; RTL positioning and policy-card widths 1440, 768, 390 and 320 passed.
- Latest additional-details browser check: saving text displayed it under
  **בדיקה ומקור**; clearing the field removed the displayed text.
- Before publication, reran all 17 backend and 19 frontend tests successfully.
  Verified committed raster logos decode after metadata removal.

## Changes in this checkpoint

- Local catalog of 26 insurer/brand logos, with aliases and RTL policy-card placement.
- BMSelect header branding, including the user's size and position adjustments.
- Saved additional details appear in the expanded coverage row.
- Explicit accessible names on filters and edit fields.
- Explicit left-to-right isolation for numeric/date values, including collapsed
  policy date ranges; browser regression assertion added.
- Optional actual Docker API restart test and documented browser test commands.

## First publication

- Reviewed the 60 files in the initial commit for client data and credentials;
  none found in the committed content.
- Excluded real workbooks, screenshots, original prompts, environment files,
  private-key file types, caches, and local test artifacts from Git.
- Removed embedded EXIF/XMP/text metadata from affected raster logo assets.
- Used a GitHub no-reply commit email. Pushed `main` and the annotated `v1.0.0`
  tag and verified both remote references.
- Follow-up documentation updates belong on `main`; the `v1.0.0` tag remains
  the original first-version snapshot.

## Limits and next step

Verification used synthetic data only; the real workbook was not opened during
this checkpoint. The existing documented import limits and local-only scope
remain in effect. Automated checks do not replace an employee's Hebrew UX and
real-export acceptance review. That review is the next handoff step.

A synthetic portfolio screenshot is in the ignored `test-results/portfolio.png`.
Startup and verification commands are in README.md. Test runs emit a non-failing
Starlette/httpx deprecation warning. The npm install reported two moderate
dependency advisories; dependency audit/remediation was not part of this check.
