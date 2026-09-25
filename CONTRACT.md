# API contract

GET `/api/instance` returns `{ "instance_id": "process-random-uuid" }`.
POST `/api/import` takes multipart field `file` (one .xlsx). Responses have Cache-Control: no-store. Errors return `{ "detail": "Hebrew user-safe message" }`.

Success: `{instance_id: string, report_date: string | null, entries: Entry[], warnings: string[]}`.
Entry: `{id: string, source_sheet: string, source_row: number, original: Fields, values: Fields, issues: string[]}`.
Fields has string values (empty string for missing): `insured_id`, `category`, `subcategory`, `product_type`, `insurer`, `period`, `additional_details`, `premium`, `frequency`, `policy_number`, `classification`.
Premium is a normalized decimal string where valid; invalid source text is preserved and flagged. Frequency is `monthly`, `annual`, or original unknown/empty text. Original fields retain source display text, including Hebrew frequency. Source sheet/row provide provenance. Insured ID is not editable.

Frontend computes groups and totals using decimal.js; source totals use original fields with Hebrew frequency mapping. Excluded rows remain accessible, contribute no current premium, and remain in original totals. Duplicate warnings are provisional and retain both entries. Missing grouping fields yield a per-entry group. Recompute validation after edits. Identifiers are strings. Don't fabricate lost leading zeros.

Server limits: 5 MiB request body, 25 MiB total uncompressed ZIP contents, 2000 ZIP members, 10000 worksheet rows. Parse in memory without UploadFile spooling. Accept one data worksheet; reject multiple populated coverage worksheets rather than silently omit them. Generic errors must never echo source data.
Browser checks instance every 3 seconds and on focus; lock interaction on loss of availability and clear data when instance changes. Import response instance must match latest confirmed instance. No storage or service worker.

The browser supports multiple family customers with independent reports. Customer profile fields (relationship, first/last name, ID, birth date, gender, marital status and smoking status) remain in browser memory; they are sent to the API only for an explicit Excel export. Insurance age is derived at last birthday. Each import still contains one insured person. The browser validates the imported ID against the target customer before replacing that customer's report. Customer profiles, reports and corrections all clear together on refresh or instance change.

POST `/api/export` takes JSON `{customers: Customer[]}` containing selected customers' details and complete current reports, including original fields and optional entry `excluded` flags. It returns an XLSX attachment with `Cache-Control: no-store` and `X-Instance-Id`. Processing and output use memory only. All reports must match the active instance (otherwise 409); malformed payloads or unsupported Excel text return a generic 400 without echoing input. Requests over 5 MiB return 413. Limit 50 customers / 20,000 total coverages. No filter-based omission or automatic deduplication. Notes remain coverage columns; originals and source references remain separate from corrections. Per-customer current totals exclude excluded entries and separate monthly/annual premiums, with partial totals marked. The browser aborts export on unmount/loss of availability and checks the response instance before downloading.
