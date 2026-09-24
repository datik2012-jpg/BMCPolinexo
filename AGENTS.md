# BMCPolinexo

- Local, single-employee insurance portfolio review pilot for BMC in Israel.
- FastAPI API, React + TypeScript UI, Docker Compose for Docker Desktop. No database.
- Natural Hebrew UI, RTL layout; English identifiers and technical documentation.
- Import one XLSX for one insured person. Preserve every coverage, including zero premiums and suspected duplicates.
- Group by insured identifier, insurer, and policy number; incomplete keys remain separate. Preserve coverage-level dates and categories.
- Monthly and annual premiums stay separate; use decimal arithmetic and never present annual amounts as monthly payments.
- Keep original source values and row references alongside corrections. Support temporary edits, exclude/restore, and source reconciliation. No new manual entries.
- Data exists only in memory. Refresh clears browser state; server restart detection clears open portfolios. No browser persistence, upload files, database, or sensitive logs.
- Bind the pilot to localhost. Do not include real XLSX files, screenshots, client data, or source prompts in Git or container images.
- Use synthetic fixtures for tests. Test grouping, totals, bad inputs, correction effects, exclusions, RTL, and lifecycle clearing.
- First version excludes client summaries, notes, recommendations, policy actions, and shared deployment.
- Keep this file concise and update it only for durable approved decisions.
