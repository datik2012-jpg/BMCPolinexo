# Version v1.2.0 — New Excel presentation — 2026-10-04

- GitHub checkpoint for the compact existing/proposed Excel presentation, coverage and insured dropdowns, proportional insurer logos, full family export, and hidden source/calculation sheets.
- Includes the follow-up UI fix that hides zero annual totals and differences while preserving nonzero annual amounts, warnings and source data.
- Validation recorded below: 25 backend tests, 33 frontend tests, production build, browser export/proposal checks, and native Excel dropdown/recalculation/save-reopen checks passed. Local Docker services are running and localhost responds.
- Customer workbooks, screenshots, source prompts and generated test artifacts are excluded from this version.

# Hide zero annual UI amounts — 2026-10-04

- Annual values of zero are hidden in current/proposed totals, filtered/source totals, shared-policy customer summaries and source-comparison differences. Nonzero amounts and incomplete-data warnings remain visible. Monthly amounts, coverage source values and Excel data are unchanged.
- Summary grids collapse the unused annual column on desktop and mobile. Recorded this display rule in AGENTS.md and README.
- Verified all 33 frontend tests, production build and browser proposal/export regressions, including changing a monthly premium to a nonzero annual premium and back, zero annual differences, and shared monthly-only policy headers.
- Rebuilt/recreated only web. Localhost responds successfully; API was not restarted.

# Coverage dropdowns — 2026-10-04

- Replaced the expanded coverage text in both Excel states with a native **כיסויים** dropdown per policy. The initial cell shows the category (or a coverage-count heading), with the policy's coverage names in its menu. Selection changes presentation only; the insured selector continues to control the premium.
- Coverage count no longer adds visible rows or increases policy-row height. Ordinary policy rows are 32 points; agent notes retain their wrapping/continuation behavior. Full coverage dates, categories, ownership and source rows remain in the hidden history. Repeated menu labels do not deduplicate coverage premiums.
- Verified 25 backend tests, including 40 coverages in one compact row per state, duplicate premiums and state-specific choices. Desktop Excel passed eight coverage choices and six insured choices, unchanged totals and save/reopen. Reviewed the native Excel print rendering and passed the real browser download regression with both dropdown types.
- Rebuilt/recreated only the API service; the web service was left running. Localhost export and page checks passed.

# Compact Excel export — 2026-10-04

- Implemented the requested two-state compact report based on the supplied text and the header/compact reference workbooks in Downloads. Reference files and their example data remain outside Git and Docker.
- All family customer cards are exported, including cards without uploads. Existing and explicitly copied proposed coverages have separate grouped tables, private/general sections and agent notes. Seven logical RTL columns preserve the specified order. Catalog logos retain their proportions.
- Native Excel list validation selects each row's family or individual premium. Family and selection totals are distinct, annual premiums remain separate, incomplete data is flagged, zero/duplicate/excluded rows remain traceable, and hidden inputs/history retain ownership and source references. Long notes use continuation rows.
- Verification: 23 backend tests and 33 frontend tests passed; the production build passed. Browser export regression verified real downloads, all customer cards, state/notes separation, single/shared initial selections, logos, responsive RTL, errors and refresh clearing. The proposal browser regression also passed.
- Desktop Excel verification passed all six selector choices across both states, unchanged family totals, no formula errors, and save/reopen preservation. Excel's two-page print rendering was inspected; coverage clipping found during review was fixed. The test dismisses an activation wizard only in its own automation instance. Failed test instances were cleaned up; the pre-existing user Excel window was left open.
- Rebuilt API and web Docker images and recreated their services. API is healthy; `http://127.0.0.1:8080` returns HTTP 200. All artifacts used for verification are synthetic and ignored.

# Latest update — 2026-10-04

## New features and UI — new status added

- GitHub checkpoint includes the existing/proposed-state workflow, explicit coverage copying and removal, insurance category display, compact RTL forms and totals, header logo positioning, and branded single-worksheet Excel export.
- Checkpoint verification: 20 backend tests, 33 frontend tests, and the synthetic proposal browser check passed. The web production build and desktop/mobile logo placement were verified; local Docker services remain available.

- Moved the header logo to the top-right corner with an 8px inset and natural image aspect ratio. Updated README; Docker production build passed, rebuilt/recreated only web, and browser checks at 1280px and 375px verified the inset and localhost HTTP 200.

- Agent date now defaults to the current local calendar date on opening/reset, while remaining editable. Reopening the form preserves the selected date. Updated README; all 33 frontend tests and Docker production build passed. Rebuilt/recreated only web and verified localhost HTTP 200.

- Removed the annual amount from individual policy headers in existing and proposed views. Annual data and totals remain preserved. Updated README; all 33 frontend tests and Docker production build passed. Recreated only web and verified localhost HTTP 200 and the updated served bundle.

- Removed the **תוקן** label from coverage actions while preserving correction tracking and source comparison. Docker production build passed; only web was recreated. Localhost returned HTTP 200 and the served JavaScript no longer contains the label.

- Aligned the return-to-policies button inside expanded source rows to the left in RTL. Updated README; Docker production build passed, only web was recreated, and localhost returned HTTP 200.

- Restored left alignment for the coverage action buttons and their column heading in both existing and proposed views, preserving RTL button order.
- Verified the production build in Docker and the synthetic proposal browser workflow on localhost, including computed alignment and button positioning in both views. Rebuilt and recreated only the web service.

- Follow-up: verified the instructions appear below the source line, start expanded, and close/reopen on click. All 33 frontend tests, production build, and the synthetic browser check passed. Rebuilt only the web service and verified localhost through the browser check.

- Removed the numeric Excel identifier warning while preserving explicit identifier zero-padding. Moved **הוראות הסוכן** into **בדיקה ומקור**, below the source row/sheet, with a bold heading and a collapsible section open by default.
- Verified 20 backend tests, 33 frontend tests, production build, and the synthetic proposal browser check including visible instructions in the source column. Rebuilt and updated API/web Docker services; localhost responded successfully.

- Added **הסרה מהמצב החדש** to proposed coverage rows. Removal clears the copy, temporary edits and exclusion, preserves the existing baseline/source/owner, updates proposed totals, and enables copying again.
- Verified all 33 frontend unit tests and the production build. Synthetic browser regression passed against Docker, including removal of an edited/excluded copy and copying again with the baseline premium. Shared ownership is covered by the unit regression.
- Rebuilt and recreated only the Docker web service; localhost browser check passed.

# Latest update — 2026-10-03

- Renamed the additional-details display label to **הוראות הסוכן** in the UI and Excel export; retained the original import header and internal field identifier for compatibility. Updated browser-check selectors.

- Combined the memory-only notice and upload/workspace status into one compact inline strip with a uniform 12px font, natural wrapping on narrow screens, and the status announcement preserved.

- Compacted both open forms: smaller inputs, buttons and spacing; five customer-field columns on wide screens with responsive layouts.
- Agent details use a compact row and a completion button that collapses to the agent name/date summary, with keyboard focus returned to the summary.
- Verified the frontend production build and all 32 frontend unit tests. No new browser visual verification was performed for this change.
- Rebuilt and recreated the local Docker web service successfully using `docker compose up -d --build --no-deps web`.
- Recorded the ongoing requirement in AGENTS.md and the commands in README.md: after each change, update documentation, run relevant checks, rebuild affected Docker images when needed, rerun affected services, and verify localhost.
- Documentation-only updates do not require an image rebuild because Markdown files are excluded from the Docker build context.

The checkpoint below is historical and its test counts describe earlier versions.

# Project checkpoint — 2026-09-24

The first-version pilot is published in [BMCPolinexo on GitHub](https://github.com/datik2012-jpg/BMCPolinexo).
The app is available at http://127.0.0.1:8080 while Compose is running.
First product version: `v1.0.0`, commit `528f7bd`, on branch `main`.

## Verified

Latest family-workspace update (after the `v1.0.0` snapshot): one initial customer
card, required name/ID/gender before upload (other details optional), age at last birthday, additional
family members, independent reports displayed directly below each customer form. Adding a customer appends a new section after the previous customer’s full portfolio. All 23 frontend
tests and the production/Docker build passed. `tests/family_check.py` verified
upload gating, duplicate/mismatched IDs, separate corrections and replacement,
responsive forms, no browser storage, and refresh/restart clearing with synthetic data.
The updated `tests/browser_check.py` also passed the full existing workflow,
including editing, exclusions/restoration, comparison, filtering, RTL/mobile,
offline locking, refresh and simulated restart detection.

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
