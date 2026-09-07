# Reproducible inspection and ingestion

Phase 2 file staging and live PostgreSQL persistence are implemented and verified. No detector, score, dashboard or project-risk tables exist.

## Sources and outputs

Twelve unchanged files are present under `data/raw/`: CSV/XLSX/PDF for sanctioned works, completed works and expenditure, plus the supplied allocation, calamity and recommended-work CSVs. Every Downloads-to-raw SHA-256 pair was verified when copied. Allocation, calamity and recommended-work XLSX/PDF counterparts were not supplied and are recorded as missing rather than reconstructed. The recorded portal scope is All India, Lok Sabha.

CSV is the staging source because it preserves strings and has at least as many rows as the available workbook. This does not establish completeness. XLSX is inspected independently, never appended. PDFs are retained as reference only; first-page renders show right-edge clipping. No missing CSV observations are manufactured from PDFs.

Each source-hash/parser-version directory under `data/processed/` contains:

- `report.json`: source filename/hash, parser version, exact headers, column profiles, validation issues, totals and coverage limits.
- `records.jsonl`: every original row, separate cleaned/derived values, issues, kind, one-based record ordinal and physical line start/end. Summary and malformed-width rows are retained. The adjacent report supplies file provenance.

`inspection.json` adds file sizes/hashes, XLSX measurements, missing-file inventory and ID overlap. Raw and processed observations are Git-ignored. Generated dictionary examples need team review before publication. No files were committed or pushed.

## Reproduce from backend/

```powershell
uv sync --frozen
uv run --frozen python -m backend.inspect_exports --raw ../data/raw --output ../data/processed --dictionary ../docs/data-dictionary.md
uv run --frozen python -m backend.ingest "../data/raw/Works Sanctioned.csv" --output ../data/processed
uv run --frozen pytest -q
uv run --frozen ruff check --no-cache src/backend/ingest.py src/backend/inspect_exports.py src/backend/staging.py tests
```

Python 3.12 and the uv lock are required. `inspect_exports` regenerates the dictionary and inspection report. Its successful execution does not approve data quality. Single-file ingestion returns 0 for staging without detected issues, 2 for staging requiring review, and 1 for fatal input/schema/I/O failure. The current command runner sometimes reports non-zero Python exits as 1; unit tests assert the entry point returns 2. All current CSVs require review.

Identical input/version reruns compare output bytes and change nothing. Different or incomplete existing outputs are refused, not overwritten. After interruption, retain the partial output for diagnosis and use a new output root. Behaviour changes require incrementing the parser version. Results do not depend on current time or randomness.

## Parsing contract

- Exact supported filenames and header order; strict UTF-8 CSV parsing including quoted multiline cells. Unknown schemas and malformed CSV syntax abort before output creation.
- Logical row ordinal, physical line number and source Sr. No. are distinct. Preserve them; serials are not cross-report identifiers.
- Trim outer whitespace only in cleaned values. Empty/whitespace becomes null. Image's N/A marker additionally means missing. No missing amount becomes zero.
- Dates use English dd-MMM-yyyy independent of system locale. Reject invalid dates; flag sanction before recommendation.
- In the recommended-work export, literal `NA` in Sanction Date is a reported missing value. `NA-<work type>` in WORK means no Work ID is available; the type is retained separately and no identifier is fabricated.
- Money uses Decimal and JSON decimal strings, not floats. Accept plain, Indian-grouped and international-grouped non-negative INR amounts with at most two fractional digits; reject invalid grouping, negative amounts, exponents and non-finite values for review, preserving originals.
- Sanctioned/completed Work strings are split into derived work ID/type. Expenditure has its own ID field. Only whitespace in the matched ID is removed, with an explicit validation record. Names and descriptions are not fuzzy-normalised or merged.
- Grand Total is a separate summary, excluded from detail totals. Sanctioned CSV puts this amount under Work Status; the final footer cell is parsed independently.
- Row-width/type/missingness issues, ID parsing, unknown payment status and date order are reported. Duplicate serials/rows, repeated IDs and total reconciliation are measured. No automatic deduplication.
- Status-separated expenditure sums are retained. The combined sum is for reconciliation only, not verified settled expenditure or a risk feature.

## PostgreSQL staging

The verified local development service is PostgreSQL 17.11 from the official Windows x86-64 binary archive. It is project-local under ignored `.local/`, listens only on `127.0.0.1:55432`, and uses SCRAM password authentication. It is not a system service and does not start automatically.

This workstation used the archive linked from the [official PostgreSQL Windows downloads page](https://www.postgresql.org/download/windows/) and [EDB binary archive](https://www.enterprisedb.com/download-postgresql-binaries). The downloaded PostgreSQL 17.11 archive SHA-256 was `4B8DB0930C38F6EF845DB919551DEDDA3B6B845AEB0927B3D79A6E8E9E4537CF`. Verify the checksum before extraction. The archive is not tracked.

Manage the installed service from the repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\postgres.ps1 start
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\postgres.ps1 status
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\postgres.ps1 stop
```

Psycopg was already declared but failed on Windows with `libpq library not found`. Its official binary extra was added using uv after consulting Context7. No ORM or additional database library was added.

`DATABASE_URL` and `TEST_DATABASE_URL` are stored in Windows user environment variables on this workstation. Passwords are stored separately as `MPLADS_DB_PASSWORD`, `MPLADS_TEST_DB_PASSWORD` and `SIH_POSTGRES_ADMIN_PASSWORD`. `SIH_POSTGRES_BIN` optionally overrides the default local binary directory. Never place their values in source, documentation or command-line history. A new terminal may be required after changing user environment variables.

```powershell
uv run --frozen python -m backend.staging "../data/raw/Works Sanctioned.csv"
```

The local tables already exist. Use `--create-tables` only during authorised initialisation with a role that has schema CREATE. It creates `mplads_ingest_batch` and `mplads_source_record` if absent. Batch identity is source SHA-256 plus parser version; record identity additionally includes the source record ordinal. Original/cleaned/derived/issues data occupies separate JSONB columns. JSON monetary strings retain precision. This is lossless staging, not a typed analytics model.

The connection transaction commits the whole batch or rolls back on failure. An existing identical batch is checked by metadata and row count and is not reinserted. Inconsistent batches are refused. There is no UPDATE, DELETE, DROP or reset operation. Error messages do not print driver connection details.

Routine permissions: database CONNECT, schema USAGE, table SELECT and INSERT. Initial creation additionally needs schema CREATE. Use a dedicated project database and remove creation privilege for routine imports.

The Investigation Queue adds the append-only `mplads_review_event` table. Initialise it once with an authorised owner or administrator connection:

```powershell
uv run --frozen python -m backend.investigations --create-table
```

After creation, the routine application role needs `SELECT, INSERT` on `mplads_review_event` and `USAGE, SELECT` on `mplads_review_event_event_id_seq`. It must not receive UPDATE or DELETE on review events or detector results.

`mplads_owner` owns the application tables but cannot log in. `mplads_app` can connect to `mplads` and SELECT/INSERT the staging tables, but cannot create schema objects, update or delete records. `mplads_test` owns the separate `mplads_test` database. Public database CONNECT is revoked for both databases.

Set `TEST_DATABASE_URL` only for a dedicated test database. The integration test creates an isolated random schema inside a rollback-only transaction, checks real row persistence, idempotency and failed-batch rollback, then verifies schema rollback. Without that variable it is skipped, not passed. With the configured local test database, the complete suite passes 29 tests without skips.

All six CSV sources have been staged in `mplads`: six batches, 141,717 retained records, including 141,711 detail and six summary records. There are 32,839 records with one or more validation issues. The recommended-work batch contains 107,156 details; 28,237 lack a sanction date and two lack a work description. A repeated import reported the new batch as identical and inserted nothing.

## Remaining limits

The local PostgreSQL archive, cluster and credentials are workstation state and are intentionally Git-ignored. Other team members must install PostgreSQL 17, create equivalent least-privilege roles/databases, set the documented environment variables and run the integration suite. The management script only operates an already installed project-local runtime at the documented path.

The read-only XLSX inspector supports only the supplied static, single-sheet inline-string/numeric representation; it rejects formulas, shared strings, extra sheets and DTD/entities. It is not a general Excel importer. The spreadsheet authoring runtime was unavailable; no workbook was authored.

Processing is in memory for the supplied bounded exports. Larger inputs need measured memory limits and streaming improvements. No performance SLA claimed. No totals from different snapshots should be summed as independent spending.

Confirm exact extraction time, allocation period, calamity report scope and Grand Total semantics. Supply allocation/calamity/recommended-work XLSX or PDF only if independent format comparison is required. No expected deadlines, extensions, physical-progress percentages, quantities, coordinates or historical snapshots were supplied. No next phase starts automatically.
