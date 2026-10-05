# BMCPolinexo

- Local, single-employee insurance portfolio review pilot for BMC in Israel.
- FastAPI API, React + TypeScript UI; Docker Compose or a per-user Windows 10/11 x64 installer with bundled runtimes and a browser launcher. No database.
- Natural Hebrew UI, RTL layout; English identifiers and technical documentation.
- Support an in-memory family workspace, initially one customer card. Each XLSX contains one insured person and belongs to a separate customer portfolio. Preserve every coverage, including zero premiums and suspected duplicates.
- Group by insured identifier, insurer, and policy number; incomplete keys remain separate. Preserve coverage-level dates and categories.
- Optional shared view groups selected customers by insurer and policy number for display only; preserve ownership, separate customer totals, and incomplete-key separation. Shared policy headers also show a combined monthly total without automatic deduplication.
- Monthly and annual premiums stay separate; use decimal arithmetic and never present annual amounts as monthly payments. Hide zero annual totals and differences in the UI; retain nonzero amounts, incomplete-data warnings, and source values.
- Keep original source values and row references alongside corrections. Support temporary edits, exclude/restore, and source reconciliation. Manual customer details are allowed; no manually created coverage entries. Insurance age uses age at last birthday.
- Data exists only in memory. Refresh clears browser state; server restart detection clears open portfolios. No browser persistence, upload files, database, or sensitive logs.
- Windows launcher uses an OS-assigned localhost port and one instance per Windows user. Closing it stops the server; desktop tabs clear data on connection loss because a restart can change the port.
- User-initiated Excel export uses one compact RTL worksheet, starting with BMC Select logo, agent first name, surname, and date. It downloads all family customer details and compact existing/proposed policy tables with compact coverage dropdowns, insured-person selectors and leftmost agent notes. Coverage selection changes display only; it does not filter premiums. Hidden sheets preserve calculation inputs and source/correction history. Family and selected-person totals are distinct; monthly/annual amounts remain separate. Generate in memory; no server-side files.
- Bind the pilot to localhost. Do not include real XLSX files, screenshots, client data, or source prompts in Git or container images.
- Use synthetic fixtures for tests. Test grouping, totals, bad inputs, correction effects, exclusions, RTL, and lifecycle clearing.
- First version excludes client summaries, standalone notes, recommendations, policy actions, and shared deployment. Coverage-level agent notes are temporary and exported separately for each state.
- Imported processed coverages appear read-only under מצב קיים — לפני השינויים. Explicitly copy a coverage into מצב חדש, חוסרים והמלצות before editing; preserve its owner and baseline. Proposed totals include copied coverages only; uncopied does not mean cancelled. This UI does not yet add recommendation fields or disk persistence.
- After every change, update the affected Markdown documentation, run relevant checks, and update the local Docker services. Rebuild affected images when source, dependencies, assets, or Docker configuration change, then rerun the affected services and verify localhost responds. For documentation-only changes outside the image context, ensure Compose is running; no image rebuild is needed. Avoid restarting unaffected services.
- Keep this file concise and update it only for durable approved decisions.
