# BMCPolinexo

Local Hebrew RTL insurance portfolio review for one employee. Import a Har HaBituach XLSX, inspect grouped policies, temporarily correct coverage fields, exclude or restore entries, and compare with the original source. Monthly and annual premiums remain separate. This pilot has no accounts or database.

Current version: [v1.2.0 — New Excel presentation](https://github.com/datik2012-jpg/BMCPolinexo/tree/v1.2.0), tagged 2026-10-04. Includes compact coverage dropdowns, family/person premium selection, separate current/proposed states, and hidden zero annual UI totals.

First product version: [v1.0.0](https://github.com/datik2012-jpg/BMCPolinexo/tree/v1.0.0), published on 2026-09-24. See [STATUS.md](STATUS.md) for verification and handoff notes.

## Policy display and corrections

Edited coverage rows do not display a **תוקן** label in the actions column. Correction tracking and source comparison remain available. Zero annual totals are hidden in the UI, including shared-policy customer summaries and zero annual differences in source comparison. Nonzero annual amounts and incomplete-data warnings remain visible; source premiums and Excel data remain preserved.

The workspace starts with one customer card. First name, last name, a nine-digit ID and gender are required to enable Excel upload. Relationship, birth date and smoking status are optional; a supplied birth date must be valid. Insurance age is calculated at the last birthday. Use **הוסף לקוח נוסף** for a spouse, child or another family member. Customer forms appear together above the insurance portfolios. **הוסף לקוח נוסף** follows the most recently added remaining customer form. New customers are appended in creation order. Selecting בן/בת זוג places that customer second in forms, selection lists and portfolios; other customers retain creation order and the first customer stays in place. Changing the relationship restores creation order. If multiple spouses are selected, the earliest added spouse takes the second position. Existing portfolios remain visible, and each customer has independent filters, edits and source reconciliation.

The imported ID must match the customer's ID (allowing leading zeros lost by Excel). Duplicate customer IDs are blocked. An unsuccessful upload preserves the previous portfolio; a successful replacement replaces only that customer's report and corrections. The ID is read-only once a report is attached. Removing a customer with a report requires confirmation. Refresh or server restart clears all customer details and portfolios. The one-insured-person import limit applies separately to each workbook.

The header places the BMSelect logo in the top-right corner with an 8px inset at desktop and mobile widths, preserving its aspect ratio. Policy cards show a matching insurer logo at the top-right. The local catalog covers 26 insurers and insurance brands, including names absent from the current workbook; Hebrew and English aliases affect display only, not policy grouping. Unknown names remain visible without a guessed logo. See [logo sources and maintenance](docs/INSURER_LOGOS.md).

To display additional coverage details, choose **עריכה**, enter text in **הוראות הסוכן**, then choose **שמירת תיקונים**. The saved text appears below the source row/sheet under **בדיקה ומקור**, with a bold **הוראות הסוכן** heading. This section is open by default and can be collapsed. Numeric Excel identifiers no longer produce a leading-zero warning; explicit zero-padding formats are still preserved. Empty details are hidden. These corrections stay in memory; they do not modify the original Excel file and are cleared on refresh or server restart.

## Docker Desktop

Install Docker Desktop with Linux containers, then run from the repository root:

```powershell
docker compose config --quiet
docker compose up --build -d
docker compose ps
```

Open http://127.0.0.1:8080. Only the web service is published, bound to IPv4 localhost; the API is private to the Compose network. No persistent volumes are created.

```powershell
# Verify restart clearing with an open portfolio.
docker compose restart api
# Stop and remove the pilot containers.
docker compose down
```

An open page checks server identity every three seconds and on focus. A changed identity clears the portfolio; loss of connectivity locks interaction until availability is known. Browser refresh immediately clears all imported data and corrections.

## Workflow after each change

Update the relevant Markdown documentation and run checks appropriate to the change. Keep the local Docker app synchronized with the source before handing off:

```powershell
# Frontend changes: rebuild and rerun only the web service.
docker compose up -d --build --no-deps web
# Backend changes: rebuild and rerun only the API service.
docker compose up -d --build --no-deps api
# Changes affecting both services or Compose configuration.
docker compose up -d --build
# Documentation-only changes outside the image context: ensure services are running.
docker compose up -d
# Verify service status and the local page.
docker compose ps
(Invoke-WebRequest http://127.0.0.1:8080 -UseBasicParsing).StatusCode
```

A local `npm run build` does not update the running Docker image. Rebuild the affected service as shown above. Avoid restarting unaffected services. Browser refresh loads the new UI and clears temporary customer data; API replacement also clears open portfolios through restart detection.

### Compact agent and customer forms

The agent date defaults to today's local calendar date when the app opens or the workspace resets. It remains editable, and reopening the agent form preserves the selected date.

The memory-only notice and the current workspace status share one compact line at a uniform font size. Text wraps naturally on narrow screens; error alerts remain separate.

Agent fields use one compact row on wide screens. Choose **סיום עריכה** to collapse them to a summary containing the agent name and date; select the summary to edit again. Customer fields use five columns on wide screens, with smaller controls and spacing. Narrow screens use fewer columns. Customer **סיום עריכה** hides the details while keeping the customer header and upload controls available.

## Native development and checks

Use Python 3.12 and Node.js 22. In a terminal at the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r backend/requirements-dev.txt
Set-Location backend
..\.venv\Scripts\python -m pytest -q
..\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

In another terminal at the repository root:

```powershell
Set-Location frontend
npm ci
npm test
npm run build
npm run dev -- --host 127.0.0.1
```

Open the local address printed by Vite. Tests use synthetic data, never the supplied real workbook. Review the main workflow at desktop and narrow widths: import, expand policies, filters, edits, undo, exclusion/restoration, source comparison, refresh, offline locking, and API restart.

## Browser acceptance checks

With Docker Compose running, execute from the repository root:

```powershell
.\.venv\Scripts\python -m pip install -r tests/requirements.txt
.\.venv\Scripts\python -m playwright install chromium
$env:BMC_TEST_DOCKER_RESTART = '1'
.\.venv\Scripts\python tests/browser_check.py
Remove-Item Env:BMC_TEST_DOCKER_RESTART
```

The check imports an in-memory synthetic workbook and verifies 20 source entries,
8 policy groups, monthly premiums of 763.32 ILS and annual premiums of 5,642.00 ILS,
corrections, exclusions/restoration, regrouping, source comparison, filters,
RTL/mobile layout, refresh clearing, offline locking, and restart clearing.
The optional environment variable also restarts the actual Compose API; omit it
when testing against a native development server. Set `BMC_URL` to override the
default `http://127.0.0.1:8080`. A synthetic-data screenshot is written to the
ignored `test-results` folder. No uploaded workbook is saved.

To check all 26 logos and RTL policy-card layout at desktop and narrow widths against the default Docker address:

```powershell
.\.venv\Scripts\python tests/insurer_logos_check.py
.\.venv\Scripts\python tests/family_check.py
```

## Shared customer view

The compact **הצגת לקוחות יחד** bar appears immediately below **+ הוסף לקוח נוסף** when the workspace has more than one customer. Its heading, customer checkboxes and actions share a row on wide screens and wrap on narrow screens; the active-view indicator also uses compact spacing. Select at least two customers with imported reports, then choose **הצגת הלקוחות יחד**. Names and family names do not need to match. **חזרה לתצוגה נפרדת** returns to the individual portfolios.

The shared view places coverages with the same insurer and exact policy number in one policy card, while incomplete identification keys remain separate. It preserves every coverage, including zero premiums and suspected duplicates. Customer names identify coverage rows, additional details, source records, and editing dialogs. Edits and exclusions update only the owning customer's report. Each customer retains separate totals, including filtered totals and original-source totals. Shared policy headers also display a combined monthly total for the displayed, non-excluded coverages; annual premiums are not included in that monthly amount. Matching policy numbers do not trigger premium deduplication.

Selections and shared presentation exist only in memory. Removing customers updates the view, replacing a report refreshes its shared entries, and refresh or server restart clears the workspace. Run `.\.venv\Scripts\python tests/shared_check.py` against the local app to verify the shared workflow with synthetic data.

## Data handling and limits

### Excel export

Use **ייצוא ל־Excel** from either state to download every customer in the family workspace, including customer cards without an uploaded report. Both **מצב קיים** and **מצב חדש** appear in the same report. Export from a single customer's view initially selects that person on applicable policy rows; shared-view exports select **כל המשפחה**, including a proposal in which only one family member has copied coverages. Policies belonging only to other family members retain the family selection.

The visible Hebrew RTL worksheet retains the logo, agent fields and customer-column order from the reference. Seven compact insurance columns run right to left: insurer logo, insurer name, policy number, coverages, insured selector, monthly premium, agent notes. Each state separates private and general insurance. **כיסויים** is a native Excel dropdown: the cell initially shows the insurance category (or a coverage-count heading), and the list contains that policy’s coverage names. Selecting a coverage only changes the displayed name; the policy premium still follows **מבוטחים**. Repeated display names share one menu option, while every underlying coverage and premium remains preserved. Coverage count no longer increases the policy row’s height; ordinary rows are 32 points. Complete insurer/policy keys group for display across owners; incomplete keys remain separate. Every coverage is counted once, including zero premiums and suspected duplicates; there is no guessed allocation or automatic deduplication. Excluded coverages remain labelled but contribute no premium.

Current state uses the processed import baseline; new state includes only explicitly copied coverages with their saved edits and exclusions. Uncopied coverage is not cancelled. Notes remain separate by state and are shown in the leftmost column, with continuation rows for long text. Dates, categories, originals, corrections, exclusions and source row references remain available in the hidden **מקור ושינויים** sheet. The hidden **נתוני חישוב** sheet contains each policy's family and individual amounts and separate per-customer totals for each state.

Native Excel dropdowns and exact-match formulas update each row's monthly premium. **סה"כ בחודש למשפחה** always counts the entire family; **סה"כ חודשי לפי הבחירה** follows the selectors. Annual premiums have a separately labelled total and are never divided into or shown as monthly payments. Missing/invalid premiums are identified and totals are marked partial. Policy/identity numbers retain leading zeros; source strings beginning with `=` remain literal text. Print layout fits one page across with unrestricted pages down.

Export is generated in memory and downloaded to the agent's computer. The server does not save it. Downloads remain after the browser workspace clears. Requests are limited to 5 MiB, 50 customers and 20,000 coverages. Unsupported Excel cell text is rejected instead of silently truncated. Refresh and server restart still clear the workspace.

Verification: run `.\.venv\Scripts\python tests/export_check.py` against the local app and the backend export unit tests with synthetic data. For native Windows Excel verification, install the optional test dependency `pywin32`, run `tests/export_fixture.py`, then `tests/excel_recalc_check.py` with the same Python environment. The latter uses a separate hidden Excel instance, verifies all selector choices and stable family totals, saves/reopens the workbook, and renders a print preview under ignored `test-results/`. It closes an Office activation startup dialog only in its own test process; it does not change activation settings. Normal export requires neither desktop Excel nor these test dependencies.

Uploads and portfolios exist only in process/browser memory. There is no browser storage, saved upload, database, analytics, or request-content logging. Nginx access/error logs are disabled, proxy buffering is disabled, and its temporary filesystem is RAM-backed. API access logging is disabled. Both containers have read-only root filesystems and no persistent data volumes. Build contexts use an explicit allowlist; real workbooks, screenshots, and source prompts are excluded.

The entire multipart request is limited to 5 MiB, so the workbook must be slightly smaller. XLSX expansion is limited to 25 MiB and 2,000 ZIP members; worksheets are limited to 10,000 rows. Only one insured person and one populated coverage worksheet are supported. Unsupported or ambiguous inputs produce Hebrew messages. Unknown frequencies and invalid premiums make reconciliation incomplete; duplicate candidates remain included until explicitly excluded.

The pilot trusts the local operating-system account and local machine. It is not intended for shared/network deployment. Use an appropriately secured workstation; memory-only application handling does not control operating-system swap or crash dumps. Never commit client files, put raw spreadsheet values into debug output, or enable analytics/request-body tracing. Client summaries, recommendations, notes, policy actions, and manual entry creation are outside this version.

See `CONTRACT.md` for the import API and field conventions and `AGENTS.md` for durable project decisions.

The initial Git publication was reviewed for client data and credentials. Real workbooks, screenshots, source prompts, environment files, caches, and test artifacts are excluded from Git. Committed raster logos have personal/text metadata removed. Keep these exclusions in place when adding files.

Source comparison includes **חזרה לפוליסות** beside the source introduction and inside each expanded source row, so users can return directly to the policy list from the inspected source. The button inside each expanded source row is aligned to the left in the RTL layout. Returning preserves filters and corrections and clears the focused source row.

Individual policy headers display the monthly amount only in both existing and proposed views. Annual premiums remain available in coverage details, portfolio totals, and Excel export. Portfolio summaries use compact per-customer premium rows with monthly and annual amounts kept separate. Import review details expand on demand while the review count remains visible. Source comparison and Excel export buttons align along their top edge, with export guidance below the button.

In the proposed state, **הסרה מהמצב החדש** removes the copied coverage and discards its temporary edits/exclusion. The existing-state coverage, source values, and ownership remain intact; it can be copied again from its imported baseline. Proposed totals immediately omit the removed copy. This also applies in the shared view.

### Existing and new states

Imported coverages are read-only under **מצב קיים — לפני השינויים**. Explicitly copy a coverage into **מצב חדש, חוסרים והמלצות** before editing it. Copies preserve customer ownership and the imported baseline. Proposed totals include copied coverages only; an uncopied coverage does not imply cancellation. Recommendation fields and disk persistence are not included.
