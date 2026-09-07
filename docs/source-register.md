# Source register

Updated 2026-09-07. The user confirmed that the exports were downloaded from the official MoSPI eSAKSHI portal with All India and Lok Sabha selected. Twelve available originals were copied unchanged into data/raw and hash-verified. All six CSV reports are staged locally; available XLSX files are independently inspected and PDFs are retained as reference.

## Supplied export inventory

Source: user-downloaded files from the official MPLADS eSAKSHI portal. Recorded filter scope is All India, Lok Sabha. Exact extraction time and any additional portal state are not embedded in the CSVs. The user confirmation and supplied portal screenshot establish the delivery context, but no digital signature is available. Raw/processed files are Git-ignored. The twelve-file SHA-256 and size inventory is reproducibly generated in `data/processed/inspection.json`; CSV hashes are also recorded in the measured dictionary.

| Report | CSV detail rows | XLSX detail rows | CSV SHA-256 |
| --- | --- | --- | --- |
| Allocated Limit for Honble MPs | 543 | Not supplied | db419a582d351bdd54cb3c14310287fbab385907f803f9287fa8875bbd43dcd3 |
| Amount consented for Calamity | 12 | Not supplied | 7f75cf2105b1084ac47ba5e4c6a794a3c878edea5d66bf47fdf6c9c26762e4d6 |
| Expenditure on Completed and On-going Works as on Date | 11,000 | 7,000 | 5a5c900266f604a3f605443f9fcb85c079c543ea367200284b154dd844584b72 |
| Works Recommended | 107,156 | Not supplied | f9ceb495b8a211da2bdac423c19d1690aa2a2e5845062f7adc71232f4dc204b4 |
| Works Sanctioned | 16,000 | 16,000 | d7737beb69a961cbf071cc4d3ae256b37afbb5151db6e7cac4ef899f461b7cbf |
| Works Completed | 7,000 | 4,000 | bb231ab991d93a5f4125bec1b04d30719afd8da9920fa3af9a2f9b8de4616e20 |

The allocation, calamity and recommended-work CSV listed-amount sums reconcile with their Grand Totals. The sanctioned, completed and expenditure detail sums do not. Do not assume a reconciled footer establishes export completeness. Allocation, calamity and recommended-work XLSX/PDF counterparts were not supplied, so only their CSVs are included.

The portal screenshot showed 107,135 recommended works and INR 5,735.81 crore. The supplied CSV contains 107,156 detail rows and INR 5,739.85 crore, indicating a later or otherwise different portal snapshot. The CSV is processed as its own immutable snapshot; screenshot totals are not substituted.

PDF metadata reports 1,775 pages for sanctioned works, 981 for completed and 1,496 for expenditure. First pages were rendered and visually inspected with existing Poppler: columns extend beyond the right page boundary. Whole-document row equivalence is not verified; no PDF observations are ingested. Creation timestamps indicate file creation, not data freshness. The CSV/XLSX mismatch is not repaired using clipped PDFs.

The official problem statement text was subsequently supplied by the user in chat. It is usable as a team-provided reference; direct SIH-page authentication remains unverified. No further statement attachment is necessary for this ingestion task.

Technical references used via Context7: [Psycopg transactions](https://www.psycopg.org/psycopg3/docs/basic/transactions.html), [JSON adaptation](https://www.psycopg.org/psycopg3/docs/basic/adapt.html), [binary installation](https://www.psycopg.org/psycopg3/docs/basic/install.html), [PostgreSQL role attributes](https://www.postgresql.org/docs/17/role-attributes.html) and [password authentication](https://www.postgresql.org/docs/17/auth-password.html). The binary extra resolves the observed Windows missing-libpq error; it does not install a PostgreSQL server. The local server came from the [official PostgreSQL Windows downloads page](https://www.postgresql.org/download/windows/) and linked [EDB binary archive](https://www.enterprisedb.com/download-postgresql-binaries); its exact archive checksum is recorded in `docs/ingestion.md`.

Frontend implementation references: bundled documentation from the installed Next.js 16.3.4 package for App Router pages/layouts, Server Components, data fetching, error handling, accessibility and Turbopack root configuration. Context7's closest indexed official version, Next.js 16.2.9, confirmed request-time Server Component fetching and runtime environment handling. FastAPI's official current documentation confirmed yield dependencies, response models and test dependency overrides. The installed code and bundled Next.js 16.3.4 documentation took precedence where versions differed.

## Earlier web research and source roles

| ID | Source | Verification and permitted use | Limitations / next step |
| --- | --- | --- | --- |
| USER-01 | Latest team-supplied SIH26102 product brief in the conversation attachment | Read in full; authority for requested product requirements and phase order | Not an independently verified official SIH statement; illustrative numbers are not data |
| LOCAL-01 | Repository data/raw | Twelve hash-verified source copies now present; six CSVs inspected and staged | Scope recorded as All India, Lok Sabha; exact extraction timestamp and three XLSX/PDF counterparts are not supplied |
| SIH-01 | [Official SIH 2026 statements](https://sih.gov.in/sih2026PS) | Fetch attempted; returned HTTP 403 Forbidden | Official SIH26102 statement not verified. Team should supply the official statement export/PDF or an accessible official link |
| LEAD-01 | [Community SIH26102 archive](https://sih2026.vuce.in/ps/SIH26102) | Explicitly unofficial. Used only to discover links to SIH and the official MPLADS portal | Its labelled dataset link leads to a dashboard, not a supplied dataset. Do not treat its interpretation or metadata as official requirements |
| MPLADS-01 | [Official eSAKSHI public dashboard](https://mplads.mospi.gov.in/digigov/dashboard.html) | Accessible; MoSPI ownership displayed. Process guidance and visible filter labels inspected | No record-level schema/export obtained. Dynamic totals not retained as observations; extraction freshness and completeness unverified |
| MOSPI-01 | [MoSPI Programme Implementation Wing](https://mospi.gov.in/programme-implementation-pi-wing) | Official indexed page describes MPLADS administration and the role of District Authorities | Background context, not a clause-level compliance specification |
| MPLADS-02 | [Legacy complete work report](https://mplads.gov.in/mplads/AuthenticatedPages/Reports/Citizen/rptCitizenCompleteWorkDetails.aspx) and [legacy delayed work report](https://www.mplads.gov.in/mplads/AuthenticatedPages/Reports/Citizen/rptCitizenMisc.aspx) | Search indexed report titles; direct retrieval returned tool Internal Error | No rows or columns verified; do not infer access restrictions or schema from the retrieval failure |

## Verified portal interpretation constraints

MPLADS-01 states that the eSAKSHI process began on 1 April 2023 and identifies missing earlier recommended/sanctioned-work coverage. Expenditure on that dashboard represents vendor payments released for ongoing/completed work. A work appears completed only after the implementing agency records completion. Data depends on stakeholder updates. These are reporting semantics, not proof of project conditions or wrongdoing.

Visible selectors include Tenure, State, Constituency and MP Name, with Lok Sabha/Rajya Sabha controls. These are UI labels, not confirmed export column names. No assumption is made about the supplied dataset having physical progress, coordinates, dates, contractor identities or payment histories.

The portal describes a general completion expectation, but no compliance threshold is approved from that summary. Obtain applicable official guidelines, amendments, clause/page references and effective dates before implementing any compliance rule. Current clause-level regulatory research remains incomplete.

## Registration required for actual inputs

Record source owner, official URL/delivery reference, retrieval date, coverage period, access/usage restrictions, file checksum, file/sheet identity, row grain and known omissions. Avoid credentials and private identifiers in shared logs. Retain immutable original files and clearly separate local inspection facts from source claims and engineering inferences.
