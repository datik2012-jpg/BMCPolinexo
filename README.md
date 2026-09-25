# BMCPolinexo

Local Hebrew RTL insurance portfolio review for one employee. Import a Har HaBituach XLSX, inspect grouped policies, temporarily correct coverage fields, exclude or restore entries, and compare with the original source. Monthly and annual premiums remain separate. This pilot has no accounts or database.

First product version: [v1.0.0](https://github.com/datik2012-jpg/BMCPolinexo/tree/v1.0.0), published on 2026-09-24. See [STATUS.md](STATUS.md) for verification and handoff notes.

## Policy display and corrections

The workspace starts with one customer card. First name, last name, a nine-digit ID and gender are required to enable Excel upload. Relationship, birth date and smoking status are optional; a supplied birth date must be valid. Insurance age is calculated at the last birthday. Use **הוסף לקוח נוסף** for a spouse, child or another family member. Customer forms appear together above the insurance portfolios. **הוסף לקוח נוסף** sits below the first form; additional customer forms appear below that button, before all portfolio totals and coverage lists. Existing portfolios remain visible, and each customer has independent filters, edits and source reconciliation.

The imported ID must match the customer's ID (allowing leading zeros lost by Excel). Duplicate customer IDs are blocked. An unsuccessful upload preserves the previous portfolio; a successful replacement replaces only that customer's report and corrections. The ID is read-only once a report is attached. Removing a customer with a report requires confirmation. Refresh or server restart clears all customer details and portfolios. The one-insured-person import limit applies separately to each workbook.

The header uses the BMSelect logo. Policy cards show a matching insurer logo at the top-right. The local catalog covers 26 insurers and insurance brands, including names absent from the current workbook; Hebrew and English aliases affect display only, not policy grouping. Unknown names remain visible without a guessed logo. See [logo sources and maintenance](docs/INSURER_LOGOS.md).

To display additional coverage details, choose **עריכה**, enter text in **פרטים נוספים**, then choose **שמירת תיקונים**. The saved text appears under **בדיקה ומקור** in the expanded coverage row. Empty details are hidden. These corrections stay in memory; they do not modify the original Excel file and are cleared on refresh or server restart.

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

Select at least two customers with imported reports using the checkboxes above the customer forms, then choose **הצגת הלקוחות יחד**. Names and family names do not need to match. **חזרה לתצוגה נפרדת** returns to the individual portfolios.

The shared view places coverages with the same insurer and exact policy number in one policy card, while incomplete identification keys remain separate. It preserves every coverage, including zero premiums and suspected duplicates. Customer names identify coverage rows, additional details, source records, and editing dialogs. Edits and exclusions update only the owning customer's report. Each customer retains separate totals, including filtered totals and original-source totals. Shared policy headers also display a combined monthly total for the displayed, non-excluded coverages; annual premiums are not included in that monthly amount. Matching policy numbers do not trigger premium deduplication.

Selections and shared presentation exist only in memory. Removing customers updates the view, replacing a report refreshes its shared entries, and refresh or server restart clears the workspace. Run `.\.venv\Scripts\python tests/shared_check.py` against the local app to verify the shared workflow with synthetic data.

## Data handling and limits

### Excel export

Use **ייצוא ל־Excel** beside a customer's portfolio, or in the shared view to export all displayed customers. Export includes every coverage for those customers regardless of active filters, including excluded and zero-premium rows. Each coverage's **פרטים נוספים** stays in the same row as that coverage and its customer name.

The workbook contains Hebrew RTL sheets for customer details, current coverages, original/current values with source row references, and per-customer monthly and annual totals. Excluded rows are marked and omitted from current totals. Invalid amounts/frequencies remain visible and mark totals as partial. Text is stored literally, including text that starts with `=`, so notes cannot become Excel formulas. Totals use numeric monthly/annual snapshot columns and exclusion status; the exported workbook is a snapshot, not a round-trip import format.

Export is generated in memory and downloaded to the agent's computer. The server does not save it. The downloaded file remains after the browser workspace clears. Export requests are limited to 5 MiB, 50 customers, and 20,000 coverages; export individual customers if the combined request is too large. Excel cell text limits are checked rather than silently truncating notes.

Verification: run `.\.venv\Scripts\python tests/export_check.py` against the local app and the backend export unit tests with synthetic data.

Uploads and portfolios exist only in process/browser memory. There is no browser storage, saved upload, database, analytics, or request-content logging. Nginx access/error logs are disabled, proxy buffering is disabled, and its temporary filesystem is RAM-backed. API access logging is disabled. Both containers have read-only root filesystems and no persistent data volumes. Build contexts use an explicit allowlist; real workbooks, screenshots, and source prompts are excluded.

The entire multipart request is limited to 5 MiB, so the workbook must be slightly smaller. XLSX expansion is limited to 25 MiB and 2,000 ZIP members; worksheets are limited to 10,000 rows. Only one insured person and one populated coverage worksheet are supported. Unsupported or ambiguous inputs produce Hebrew messages. Unknown frequencies and invalid premiums make reconciliation incomplete; duplicate candidates remain included until explicitly excluded.

The pilot trusts the local operating-system account and local machine. It is not intended for shared/network deployment. Use an appropriately secured workstation; memory-only application handling does not control operating-system swap or crash dumps. Never commit client files, put raw spreadsheet values into debug output, or enable analytics/request-body tracing. Client summaries, recommendations, notes, policy actions, and manual entry creation are outside this version.

See `CONTRACT.md` for the import API and field conventions and `AGENTS.md` for durable project decisions.

The initial Git publication was reviewed for client data and credentials. Real workbooks, screenshots, source prompts, environment files, caches, and test artifacts are excluded from Git. Committed raster logos have personal/text metadata removed. Keep these exclusions in place when adding files.
