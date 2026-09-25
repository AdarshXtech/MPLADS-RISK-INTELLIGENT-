# Architecture

Updated 2026-09-25. Distinguish the existing implementation from the intended design.

## Existing system

Next.js renders a data-readiness Command Centre and a separate authenticated Data Quality route using shared source-data presentation. Data Quality requests aggregate ingestion metadata from FastAPI without requiring the investigation summary. FastAPI returns status JSON from `/` and `/health`, and reads the two PostgreSQL staging tables for `/data-overview`. The `backend` console entry point still prints a greeting and does not start the ASGI server. See [flow.md](flow.md) for actual function calls.

Standalone CSV inspection and lossless staging cover six supplied reports. PostgreSQL stores original, cleaned and derived records with source identity. Deterministic detector runs/results remain immutable; review transitions are persisted separately as append-only events. Persistence and idempotency are verified against PostgreSQL 17.11. No typed project model or risk aggregation exists. See [ingestion.md](ingestion.md) and [detection-rules.md](detection-rules.md).

The ingestion API exposes only aggregate source metadata. The Next.js Command Centre and Investigation Queue require a signed local reviewer session; the protected backend workload endpoint also requires the review API key. Search, filtering and a closed set of sort orders execute in PostgreSQL before pagination. The CSV route validates the session before calling the key-protected backend export endpoint and preserves the selected order. Database credentials and the review API key stay server-side. See [deployment readiness](deployment.md) for the private staging boundary and production blockers.

## Implemented frontend design

The supplied Stitch references are reimplemented in the existing Next.js routes. `QueueShell` owns the dark product/session header and light navigation. CSS reflows the evidence view between a wide evidence/review split and a single column. The new `PasswordField` manages visibility locally; `SubmitButton` reads React form pending state without changing the login/review Server Actions. Lucide provides navigation/action icons. All metrics and source comparisons retain the existing API boundary. See [design.md](design.md) for tokens, page ownership and excluded illustrative reference content.

The current Suchak AI identity is shared by `Brand`, page metadata and the authenticated shell. `ReviewOverview` uses the existing investigation summary, without a new analytics endpoint. `LocationComparison` dynamically loads a browser-only Leaflet canvas and local India reference GeoJSON. Only verified source coordinates create A/B markers. The Next.js source route checks the signed session and candidate/source membership before returning a private, no-store record from the existing protected candidate API. The detail payload contains the available provenance, cleaned/derived values, validation and location fields, not an invented project model. Optional OpenStreetMap tiles are browser requests; the default map requires no third-party request. No detector, database schema or review persistence changes are introduced by this map.

## Intended design, not implemented


Use one Next.js frontend, one FastAPI/analytics backend and PostgreSQL. Keep ingestion and analysis in the Python project rather than introducing services or agent frameworks. Choose tables, source mappings and validation schemas only after inspecting actual input files.

Required processing order: official input, schema validation, normalisation, data quality assessment, feature engineering, supported detectors, risk aggregation, evidence-based explanation and ranked investigation queue. Persist source provenance, processing versions, validation results, detector evidence and case history. Do not persist credentials in source records or logs.

## Implemented ingestion contract

- Never overwrite or repair the raw file. Compute and retain its cryptographic checksum and source identity.
- Preserve file/sheet/record position as applicable, including records without a unique project identifier. Determine the dataset's actual record grain before deduplication or joins.
- Store original values independently from cleaned/derived values. Report every invalid value with its source position and reason. Do not silently impute, drop rows, coerce units or interpret ambiguous dates.
- Make parsing options, encoding, date conventions, units, validation rules and code version explicit. A repeat run with identical input and configuration must produce equivalent data outputs without duplicate persisted records.
- Transaction rollback, rejected-record retention and idempotency are implemented and verified against the staging schema.
- Treat unsupported detectors as unavailable, not negative findings. Separate data-quality problems from risk findings.

## Analysis and review contract

Prefer interpretable rules and peer statistics before optional ML. Fix and version randomness where applicable. Preserve peer selection, exclusions and sample sizes. Historical models need temporal validation and leakage checks. Review decisions must not rewrite original observations or historical detector evidence.

Composite risk weights, score thresholds and probability calibration remain undecided pending data analysis and human review. Project and score schemas do not exist. Future score contributions must be reconstructible. The current review slice uses one local reviewer role, defined transitions and append-only events. It must move to approved organisational identity and role mapping before production. Optional generated prose cannot affect the detection path.

## Implemented investigation boundary

Next.js owns the signed reviewer session and makes protected server-to-server calls to FastAPI. The browser never receives the review API key or PostgreSQL connection string. FastAPI validates its API key, queries only the latest reviewable detector run and appends review events after checking permitted transitions and current state. Review state is derived from history, and detector output remains immutable. The development database grants the application role SELECT/INSERT on review events and no UPDATE on review events or detector results.

## Implemented detector contract

- Engine version, detector configuration and ordered source-batch identities form a deterministic run ID.
- Each result records rule ID/name/version, `review` severity, predicate confidence, exact evidence, fields used, verification guidance, limitations and source-row provenance.
- The active rule creates potential duplicate candidates only when seven available fields match after deterministic normalisation and Work IDs differ.
- Data-quality issues remain in staging records and do not increase severity or create detector results.
- Unsupported detectors are recorded with missing inputs. The peer-cost implementation is disabled after measured calibration produced an unusably broad result set.
- The application role may select and insert detector data but cannot update or delete it. Initial table creation requires an administrative connection.

## Reviewed location and locality-screening contract

`mplads_work_location` is an append-only, provenance-linked snapshot table. It stores reviewed State, district, constituency, block/tehsil, ward/village, verified address text, coordinates, source, status and verification timestamp alongside separate original, cleaned and derived JSON values. It references a staged source record rather than replacing source data. A location correction produces a new content-addressed snapshot; selecting the latest verified timestamp never changes earlier snapshots.

The location import CLI accepts only a documented CSV contract and validates source provenance, coordinate pairs, geographic bounds, status rules and timezone-aware verification timestamps. It does not call an external geocoder. PostgreSQL built-in numeric columns and a deterministic Haversine fallback are used because the project-local PostgreSQL deployment has no verified PostGIS extension. The radius is configuration, not a factual boundary.

Engine version 3 executes the retained exact-context detector version 1 and a separate locality-aware detector version 1. The latter indexes administrative locality and description tokens before checking candidate pairs, then requires same work type, locality, meaningful description similarity and corroboration. Detector runs/results remain immutable. Investigation responses add location details without changing detector evidence; queue order remains unchanged unless a filter or existing sort is selected.

## Verification gates

Test parsing failures, nulls, units, date ambiguity, duplicate identifiers, provenance, unchanged raw hashes, deterministic reruns and transaction failure. Later test detector boundaries and unavailable inputs, score contributions, API validation and persistence, case history and complete UI flows. Synthetic edge cases are permitted only in tests. No runtime, security or performance guarantee is claimed by this design document.
