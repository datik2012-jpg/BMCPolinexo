# API contract

GET `/api/instance` returns `{ "instance_id": "process-random-uuid" }`.
The Windows packaged server additionally returns `desktop_mode: true`. Desktop
tabs clear their workspace on connection loss, since restarting the launcher
may select a different localhost port. Docker/native API behavior is unchanged.
POST `/api/import` takes multipart field `file` (one .xlsx). Responses have Cache-Control: no-store. Errors return `{ "detail": "Hebrew user-safe message" }`.

Success: `{instance_id: string, report_date: string | null, entries: Entry[], warnings: string[]}`.
Entry: `{id: string, source_sheet: string, source_row: number, original: Fields, values: Fields, issues: string[]}`.
Fields has string values (empty string for missing): `insured_id`, `category`, `subcategory`, `product_type`, `insurer`, `period`, `additional_details`, `premium`, `frequency`, `policy_number`, `classification`.
Premium is a normalized decimal string where valid; invalid source text is preserved and flagged. Frequency is `monthly`, `annual`, or original unknown/empty text. Original fields retain source display text, including Hebrew frequency. Source sheet/row provide provenance. Insured ID is not editable.

Frontend computes groups and totals using decimal.js; source totals use original fields with Hebrew frequency mapping. Excluded rows remain accessible, contribute no current premium, and remain in original totals. Duplicate warnings are provisional and retain both entries. Missing grouping fields yield a per-entry group. Recompute validation after edits. Identifiers are strings. Don't fabricate lost leading zeros.

Server limits: 5 MiB request body, 25 MiB total uncompressed ZIP contents, 2000 ZIP members, 10000 worksheet rows. Parse in memory without UploadFile spooling. Accept one data worksheet; reject multiple populated coverage worksheets rather than silently omit them. Generic errors must never echo source data.
Browser checks instance every 3 seconds and on focus; lock interaction on loss of availability and clear data when instance changes. Import response instance must match latest confirmed instance. No storage or service worker.

The browser supports multiple family customers with independent reports. Customer profile fields (relationship, first/last name, ID, birth date, gender, marital status and smoking status) remain in browser memory; they are sent to the API only for an explicit Excel export. Insurance age is derived at last birthday. Each import still contains one insured person. The browser validates the imported ID against the target customer before replacing that customer's report. Customer profiles, reports and corrections all clear together on refresh or instance change.

POST `/api/export` takes JSON containing all workspace customer details and complete reports, including baseline/original fields and entry copy/exclusion flags. It returns an XLSX attachment with `Cache-Control: no-store` and `X-Instance-Id`. Processing and output use memory only. All reports must match the active instance (otherwise 409); malformed payloads or unsupported Excel text return a generic 400 without echoing input. Requests over 5 MiB return 413. Limit 50 customers / 20,000 total coverages. No filter-based omission or automatic deduplication. Notes remain in their policy block; originals and source references remain separate from corrections. Per-customer current totals exclude excluded entries and separate monthly/annual premiums, with partial totals marked. The browser aborts export on unmount/loss of availability and checks the response instance before downloading.


## Compact family export (2026-10-04)

`POST /api/export` accepts all workspace customers (`report` may be null), the agent fields and optional `selected_customer_id`. Coverage entries preserve `baseline` and `copied`. Existing rows use baseline values; proposed rows use only copied entries and their saved values/exclusions. No automatic proposal population. Every attached report must match the running instance.

The workbook has one visible RTL presentation and two hidden supporting sheets: calculation inputs and full source/correction history. Native list validation and exact INDEX/MATCH formulas select actual owner premiums. Family totals remain independent of row selection; annual totals stay separate. Complete insurer/policy keys combine for presentation only; incomplete keys remain separate, ownership is retained, and no coverage is deduplicated. The visible seven-column layout keeps agent notes on the left and uses continuation rows for long text. All customer cards are included in the reference-order customer table. Print width is one page; height is automatic. Only catalog logo assets are packaged; reference workbooks and synthetic output artifacts are excluded.


The coverage column uses per-policy named-range list validation in both states. Default text is the category or a coverage-count heading; options contain coverage names and excluded markers. Coverage selection is presentation-only and is not a premium filter. Full source entries, dates and ownership remain in the hidden audit; only identical menu labels are collapsed. Ordinary policy rows are 32 points regardless of coverage count. Only long notes add continuation rows. Coverage and insured dropdowns use separate named ranges.
