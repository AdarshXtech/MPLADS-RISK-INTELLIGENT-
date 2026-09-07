# Deterministic detector rules and feasibility

Assessed and implemented where stated on 2026-09-07 against all six supplied CSV reports. The recorded export scope is All India, Lok Sabha. Coverage and snapshot completeness remain limited to the supplied exports. No composite risk score, fraud classification, compliance finding or predictive model is implemented. The active candidate rule is exposed only through the authenticated Investigation Queue API.

SUPPORTED: the stated check has the necessary verified fields. PARTIALLY SUPPORTED: only a restricted version is possible. NOT SUPPORTED: essential evidence is absent.

| Proposed detector | Classification | Available evidence | Missing evidence and limitations |
| --- | --- | --- | --- |
| Peer cost anomaly | PARTIALLY SUPPORTED, IMPLEMENTED FOR CALIBRATION BUT DISABLED | Sanction Amount, derived work type and category for 16,000 works | Missing quantities, unit costs, engineering scale and revisions. The measured rule produced 3,016 candidates and is not enabled for reviewable runs |
| Expenditure versus physical progress | NOT SUPPORTED | Dated payment amounts/status and Work ID; 620 IDs overlap sanctioned works | No physical-progress percentage, dated milestones or expected payment schedule. Completion markers cannot substitute for physical progress |
| Delay against expected duration | NOT SUPPORTED | Recommendation and sanction dates; completion dates link for 6,988 recommended works | No expected completion dates, actual starts, approved extensions or reasons. Observed duration can be described but does not establish overdue status. Absence from this completed export does not mean non-completion |
| Potential duplicate works | PARTIALLY SUPPORTED, ACTIVE CANDIDATE RULE | IDs, descriptions, work types, sanction/recommendation dates and amounts, State, constituency and IDA | Version 1 exact-match candidate screening is implemented against sanctioned works. Recommended-work linkage can provide additional evidence, but no verified asset IDs, precise locations/coordinates or quantities exist |
| Recommendation-to-sanction amount change | PARTIALLY SUPPORTED, NOT IMPLEMENTED | 15,963 normalised Work IDs overlap recommended and sanctioned exports, with recommended and sanction amounts available | No amendment history, approval reason, quantities or rule defining an unacceptable change. Differences may be legitimate and require descriptive analysis before any candidate rule |
| Statistical outlier screening | PARTIALLY SUPPORTED | Sanction amounts and contextual fields; payment amounts/dates/status/vendor labels; MP allocation limits; calamity consent amounts/types/dates | Comparability, report periods, complete transaction coverage and stable MP/recipient/event IDs are missing. Interpretable screening within reviewed groups may be feasible; no model trained or validated |
| MPLADS compliance rules | NOT SUPPORTED | Some dates, categories and financial fields, including allocation limits and calamity consent | Applicable clause-level guidelines/amendments, allocation periods and rule-specific fields such as eligibility, ownership and approvals are unverified. No invented limit or rule |
| Predictive early warning | NOT SUPPORTED | Single supplied snapshots and some dated events | No historical as-of snapshots, contractual deadlines, verified outcome labels or full payment histories. No defensible temporal validation or fraud probability |
| Export data-quality checks, not risk detectors | SUPPORTED | Actual headers, source rows, IDs, dates and footers | Implemented schema/type/missingness checks, exact duplicate counts, repeated IDs, date order, derived ID normalisation and reconciliation. These produce validation issues, never risk flags |

## Active rule: potential duplicate work candidate

- **Detector ID/version:** `duplicate_work_candidate` version 1, engine version 2.
- **Input:** detail records from `Works Sanctioned.csv` only.
- **Condition:** two or more records have different derived Work IDs and non-null exact matches after case, punctuation and whitespace normalisation across Work description, derived work type, State, constituency, IDA, Sanction Date and Sanction Amount.
- **Output:** one review candidate per matching group, with severity `review`, confidence `1`, matched values, all different Work IDs, source SHA-256/parser version/record number provenance, limitations, explanation and verification step.
- **Confidence meaning:** certainty that the deterministic predicate matched. It is not a probability of duplication, misuse or fraud.
- **Measured result:** 174 reviewable groups reference 1,281 source records. Group sizes range from 2 to 86; 60 groups contain exactly two records. Large groups demonstrate the known risk from repeated template descriptions.
- **Required verification:** compare underlying recommendations, physical locations, asset identities, quantities and sanction records before deciding whether records refer to separate or duplicate works.

## Disabled calibration rule: peer sanction cost

- **Detector ID/version:** `peer_sanction_cost` version 1.
- **Calibration condition:** sanctioned amount at least 2 times the median of a peer group containing at least 20 records with the same normalised work category and derived work type.
- **Measured result:** 3,016 candidates. This is too broad for administrative triage and confirms that category/type alone does not establish engineering comparability.
- **Disposition:** disabled in engine version 2. Its implementation remains directly tested for threshold behaviour, but reviewable runs do not execute or persist its results.
- **Reactivation gate:** add verified quantities, dimensions, unit rates, revisions or an approved narrower peer definition, then recalibrate and document the false-positive review.

The first engine-version-1 database run is retained with status `calibration` for auditability. Engine version 2 is the only `reviewable` run and contains the 174 duplicate-work candidate groups. Only that reviewable run is exposed through authenticated, server-side Investigation Queue endpoints.

## Investigation review workflow

The queue does not modify detector evidence. `NEW` is implicit until the first reviewer event. Permitted transitions are `NEW` to `UNDER_REVIEW`; `UNDER_REVIEW` to `VERIFICATION_REQUESTED`, `RESOLVED` or `DISMISSED`; verification requests to resume, resolve or dismiss; and resolved/dismissed cases to reopen. Resolution and dismissal require a decision. Dismissal also requires a reason code.

Every action appends reviewer identity, timestamp, transition and supplied supporting notes to `mplads_review_event`. Existing events and detector results are not updated. `POTENTIAL_DUPLICATE` remains a human review decision requiring verification, not a confirmed fraud or misuse finding.

## Human-review CSV

Run the following from `backend/` with `DATABASE_URL` available:

```powershell
uv run --frozen python -m backend.review_export --output ../data/review/duplicate-candidate-review.csv
```

The command selects the latest reviewable run unless `--run-id` is supplied. It emits one row per duplicate-work candidate group and enriches exact Work IDs with available recommended-work source references, dates and amounts. It does not alter detector results or write to PostgreSQL.

Reviewers must choose one of `SEPARATE_WORKS`, `POTENTIAL_DUPLICATE`, `INSUFFICIENT_EVIDENCE` or `DATA_ERROR`, and record a supplied reason code, documents checked, evidence references, reviewer name, review date and notes. These are guidance values in a CSV, not enforced dropdowns. A candidate must not be recorded as a potential duplicate without supporting administrative evidence. Use `INSUFFICIENT_EVIDENCE` when the required records cannot be verified.

The baseline export is UTF-8 with a byte-order mark for spreadsheet compatibility. Formula-like cell prefixes are neutralised. The exporter permits byte-identical reruns and refuses to overwrite changed content at an existing path, protecting completed human review from accidental regeneration.

## Reproduce the detector run

From `backend/`, with `DATABASE_URL` supplied through the process environment:

```powershell
uv run --frozen python -m backend.detectors
```

Use `--create-tables` only for authorised initial setup with schema-creation permission. Routine execution requires SELECT on the two ingestion tables and SELECT/INSERT on `mplads_detector_run` and `mplads_detector_result`. The project application role has no UPDATE or DELETE permission on detector tables. The command uses one transaction, reports a generic failure without printing connection details and refuses inconsistent existing runs.

## Findings affecting later implementation

- Expenditure CSV: 11,000 rows, 8,210 normalised Work IDs, 823 repeated IDs and 143 exact duplicate rows ignoring serial. No transaction identifier exists, so all are retained, not automatically deduplicated or called duplicate payments.
- Payment Success rows sum to INR 3,042,342,331; Payment In-Progress rows sum to INR 794,317,473. These are status-separated sums of exported records, not independently verified settled balances.
- Completed CSV has four missing disbursal amounts and 2,658 Image values marked N/A. Images is an availability label, not a URL or verified evidence of asset existence.
- Allocation CSV has 543 MP-level rows and one missing allocation amount. Its INR 83,336,673,298.01 listed sum reconciles with its footer, but the allocation period and stable MP identifiers are absent. Do not compare or join allocation values by display name alone.
- Calamity CSV has 12 consent rows covering two reported calamity types and six exact calamity-name strings. Its INR 40,567,400 listed sum reconciles with its footer. Consent is not disbursal, the export has no stable event ID and it does not identify recipient works.
- Recommended-work CSV has 107,156 detail rows and a reconciled INR 57,398,544,852.41 total. It reports 78,919 distinct Work IDs; 28,237 rows have no sanction date, and two descriptions are missing. An absent sanction date is not evidence of delay or non-compliance.
- Recommended-to-sanctioned linkage finds 15,963 shared normalised Work IDs, 62,956 IDs only in the recommended export and 37 only in the supplied sanctioned export. These are snapshot coverage facts, not workflow outcomes.
- Expenditure links to 8,166 recommended Work IDs, while completed works link to 6,988. Missing matches must not be interpreted as missing payments or completion because export coverage and timing differ.
- The allocation and calamity files do not make a new risk detector fully supported. A restricted descriptive or outlier screen may be possible after period, coverage, entity-matching and peer-definition review.
- The three work/payment CSV detail sums fail reconciliation with Grand Total. Expenditure XLSX has 7,000 rows versus CSV 11,000; completed XLSX has 4,000 versus CSV 7,000. Sanctioned versions both have 16,000, with some raw text differences.
- Only 17 normalised Work IDs overlap between expenditure and completed CSVs. Do not blindly join by MP/constituency or interpret missing matches as irregularities.

See [data-dictionary.md](data-dictionary.md) for every field and [ingestion.md](ingestion.md) for processing behaviour.

## Result contract

Implemented results expose ID/name, severity, confidence, source-file hash and record-number evidence, fields used, explanation, verification step, limitations and rule version. The deterministic run identity is derived from engine version, configuration and source batches. Results have their own content hash and immutable database identity. Unavailable detectors retain missing-input reasons, not zero or Low scores.

Composite weights, risk thresholds and probability calibration remain undecided and unimplemented. Data-quality issues stay separate from detector results. Generative AI does not participate in detection. An anomaly does not prove fraud.
