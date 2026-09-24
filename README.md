# BMCPolinexo

Local Hebrew RTL insurance portfolio review for one employee. Import a Har HaBituach XLSX, inspect grouped policies, temporarily correct coverage fields, exclude or restore entries, and compare with the original source. Monthly and annual premiums remain separate. This pilot has no accounts or database.

First product version: [v1.0.0](https://github.com/datik2012-jpg/BMCPolinexo/tree/v1.0.0), published on 2026-09-24. See [STATUS.md](STATUS.md) for verification and handoff notes.

## Policy display and corrections

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
```

## Data handling and limits

Uploads and portfolios exist only in process/browser memory. There is no browser storage, saved upload, database, analytics, or request-content logging. Nginx access/error logs are disabled, proxy buffering is disabled, and its temporary filesystem is RAM-backed. API access logging is disabled. Both containers have read-only root filesystems and no persistent data volumes. Build contexts use an explicit allowlist; real workbooks, screenshots, and source prompts are excluded.

The entire multipart request is limited to 5 MiB, so the workbook must be slightly smaller. XLSX expansion is limited to 25 MiB and 2,000 ZIP members; worksheets are limited to 10,000 rows. Only one insured person and one populated coverage worksheet are supported. Unsupported or ambiguous inputs produce Hebrew messages. Unknown frequencies and invalid premiums make reconciliation incomplete; duplicate candidates remain included until explicitly excluded.

The pilot trusts the local operating-system account and local machine. It is not intended for shared/network deployment. Use an appropriately secured workstation; memory-only application handling does not control operating-system swap or crash dumps. Never commit client files, put raw spreadsheet values into debug output, or enable analytics/request-body tracing. Client summaries, recommendations, notes, policy actions, and manual entry creation are outside this version.

See `CONTRACT.md` for the import API and field conventions and `AGENTS.md` for durable project decisions.

The initial Git publication was reviewed for client data and credentials. Real workbooks, screenshots, source prompts, environment files, caches, and test artifacts are excluded from Git. Committed raster logos have personal/text metadata removed. Keep these exclusions in place when adding files.
