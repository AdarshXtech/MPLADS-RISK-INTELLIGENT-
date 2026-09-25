# MPLADS Risk Intelligence: The Problem and the Solution

The proposed system should help an official move from a large collection of MPLADS records to a manageable set of cases requiring verification. Each case should explain the unusual observation, its administrative significance, the supporting records, the limits of the evidence and the next action. The intended public benefit is earlier corrective action and more effective use of review capacity. An alert is a reason to examine records or inspect a work; it does not establish wrongdoing.

The present repository implements a limited but relevant part of this approach: preserved source records, deterministic potential-duplicate screening, an evidence view and a persistent review workflow. It does not yet implement a validated predictive model, comprehensive compliance checking or a composite risk score. Its documented screening counts describe a supplied snapshot, not the prevalence of irregularities across MPLADS.[^11][^12]

**1. The SIH problem and the authority of the available statement.** The project identifies its problem as SIH26102. An explicitly unofficial community archive attributes the statement to MoSPI's Data Informatics & Innovation Division. Its scope covers analysis of sanctions, expenditure, estimates, progress, payments and assets; detection of unusual patterns, possible duplication, delays and deviations; and alerts, prediction and decision support for administrative stakeholders.[^1]

Direct authentication against the official SIH statement page remains incomplete. The repository records an earlier team-supplied statement and an unsuccessful official-page retrieval. Consequently, the identifier, sponsoring division and exact competition wording should be treated as provisional until checked against the official submission material. Government sources below independently establish the scheme's operation and monitoring context. The solution design in this report is an analytical recommendation, rather than a claim that every proposed feature is explicitly mandated by SIH.[^1][^11]

**2. MPLADS in plain English.** MPLADS means Members of Parliament Local Area Development Scheme. It supports locally needed development works, with an emphasis on durable community assets. The annual entitlement described in the July 2025 parliamentary answer is ₹5 crore per MP. The Tamil Nadu government's scheme page also states ₹5 crore and describes the local administrative sanction process. Entitlement should be understood as authority to recommend eligible works within the scheme, rather than money available for personal expenditure.[^2][^3]

The practical distinction between the main participants is straightforward. An MP recommends a work. The District Authority checks feasibility, sanctions it and designates an Implementing Agency. The agency executes the work and raises payment requests. State and Ministry oversight sit above these local processes. This allocation of responsibilities means that an unusual project record cannot, by itself, establish responsibility for a particular person's conduct.[^4]

Fund-flow descriptions also need dates. MoSPI's December 2025 review says the scheme moved to Model 1A-TSA (Hybrid) from April 2025, using a PMU-MPLADS RBI account. Agency demands on eSAKSHI are consolidated and vendor payments made through PFMS daily. A system designed around older descriptions of district bank-account transfers could therefore misinterpret newer records. The relevant fund-flow version should accompany any financial rule.[^5]

For example, a hypothetical local request might concern an additional classroom. The administrative record could contain a recommendation, sanction, payment entries and a completion update. These are related observations about a work. They are not interchangeable measures of money spent or benefit delivered. This example is illustrative and is not an official project record.

| Term | Interpretation needed by the proposed product | Common analytical mistake |
| --- | --- | --- |
| Annual entitlement or authorisation | The amount available for recommendations within the applicable period | Treating it as settled expenditure |
| Recommended amount | Amount earmarked through the recommendation process | Calling the entire amount a vendor payment |
| Sanctioned amount | Approved amount for the work | Treating approval as proof that work has started |
| Reported expenditure | Vendor payments released, according to the dashboard's definition | Combining unsuccessful or pending payment rows with released payments |
| Recorded completion | Completion status entered through the administrative process | Treating a status field as an independent physical inspection |
| Verified usable asset | A separate assessment of existence, specification, usability and public purpose | Assuming a photograph or financial total establishes all of these |

The portal specifically explains that MP-level utilisation refers to recommended amounts, while its expenditure measure refers to vendor payments released. It depends on stakeholder updates, and completed works appear after the agency marks them complete. The table's verification cautions are implications for analytical design, rather than additional official portal definitions.[^6]

**3. The operational problem.** An official can have substantial information and still lack a useful answer to what deserves attention today. Records may describe different stages, have different reporting periods, use inconsistent identifiers or omit the context needed for comparison. Reviewing every item with equal intensity consumes staff time. Looking only at aggregate totals can conceal individual problems or make ordinary differences look alarming.

The work to be done is therefore a chain of decisions. First determine what the available records actually represent. Then identify observations that are unusual within a defensible context. Next decide which observations warrant verification, gather their evidence and record what the review established. The last step matters: a system that produces alerts without tracking action can merely create a second backlog.

Historical audit evidence illustrates the significance of this distinction. CAG's Report No. 31 of 2010, tabled in March 2011, examined the period 2004–05 to 2008–09. Its chapter on execution described deficiencies in the age-wise information available about incomplete works. This supports the historical importance of usable monitoring information. It does not establish the quality of today's eSAKSHI system or a present-day irregularity rate.[^7][^8]

Current government monitoring also already includes ageing indicators. MoSPI's August 2025 parliamentary response describes regular pendency lists and monthly State/UT reviews. Therefore, the additional value proposed here is contextual prioritisation, connected evidence and recorded verification outcomes. A coloured list of old projects, on its own, would contribute relatively little to that existing process.[^9]

**4. How the proposed product fits alongside eSAKSHI.** MoSPI announced a revamped public dashboard in March 2026 with drill-down information on recommendations, sanctions, completion, expenditure and calamity consent, together with improvements for asset photographs. The official platform already provides an operational foundation for scheme reporting.[^4]

The proposed product should consume authorised information from that foundation and help reviewers use it. At the current stage, this means documented exports. A future departmental integration could use an approved API or agreed batch delivery if made available. Public dashboard access does not establish that a stable machine API, unrestricted document access or an integration agreement exists.

| Existing information or activity | Proposed additional decision support | Evidence of useful performance |
| --- | --- | --- |
| Lists of recommended and sanctioned works | Link records into a supported work history | Correctly linked records and explicit unmatched cases |
| Expenditure reports | Highlight supported payment exceptions with transaction context | Officials can reconstruct the relevant payment sequence |
| Progress and completion reporting | Identify documented milestone or deadline exceptions | Alerts use dated evidence and approved extensions |
| Aggregate dashboard totals | Prioritise actionable cases within a defined review capacity | Reviewed cases yield useful verification outcomes |
| Administrative documents and photographs | Present the exact evidence needed for a particular alert | Less time spent locating and reconciling records |
| Follow-up activity | Record review decisions, reasons and unresolved evidence requests | Cases have traceable outcomes and responsible owners |

These additions are proposed capabilities. Their value must be tested with actual reviewers. The research does not establish that no government system already has similar internal functionality; discovery with MoSPI and district users is required before making a uniqueness claim.

**5. What the system should detect.** There are several distinct analytical questions. They require different evidence, rules and verification actions. Combining all of them under one generic anomaly label would make results harder to interpret.

| Candidate concern | Defensible screening approach | Essential evidence | What an official should verify | Present repository status |
| --- | --- | --- | --- | --- |
| Potential duplicate work | Match distinct work identifiers using descriptive, administrative and financial context; later enrich with asset/location evidence | Source work records, asset identity, location, scope and phases | Whether the records describe separate assets, legitimate phases, corrections or the same work | Exact normalised candidate rule is active; asset-level confirmation is unavailable |
| Unusual cost | Compare equivalent quantities and specifications within suitable place/time groups | Quantities, dimensions, specification, approved estimate, rates and revisions | Whether scope, terrain, transport, quality or approved changes explain the difference | Broad peer-cost rule is disabled |
| Expenditure-progress mismatch | Compare dated payments with expected milestones and measured progress | Payment schedule, settled transactions, inspection/measurement dates and physical progress | Whether advances, materials or milestones explain the apparent mismatch | Required evidence is missing |
| Delay or stalled execution | Compare known process dates with applicable deadlines and extensions | Receipt, sanction, start, contractual completion, extensions and current status | Administrative pendency, approved exception, reporting lag or execution problem | Full deadline-aware detector is unavailable |
| Potential duplicate payment | Compare transaction/invoice identities and settlement histories | Invoice, transaction ID, recipient ID, amount, status and reversals | Whether entries are instalments, retries, reversals or repeated settlement | Not implemented; export lacks transaction identifiers |
| Compliance deviation | Apply a verified, dated clause to records satisfying its scope | Applicable guideline/amendment plus clause-specific facts | Eligibility, authorisation, exception and underlying documentation | Comprehensive clause-level engine is unavailable |

The approaches in this table are recommendations. Present-status statements come from the repository's detector definitions and measured data dictionary.[^12][^13]

Cost analysis requires particular care. Two works described as a road can differ in length, width, drainage, ground conditions and specification. A higher total sanction amount does not establish an excessive unit cost. A difference between recommended and sanctioned amounts is also not automatically a cost overrun: the baseline, revisions, scope and timing must first be understood. These are comparability requirements for a useful detector.

Anomaly-detection research distinguishes contextual anomalies, where an observation is unusual only within a particular setting, from other anomaly types. Applying that principle here means that the peer group is part of the detector's reasoning. A statistical method cannot compensate for a peer group that compares different kinds of work.[^10]

**6. What the monitoring rules actually permit us to say.** The August 2025 response cites a 45-day sanction/rejection period from receipt by the Implementing District Authority. It also says the sanction letter should generally set completion within one year, with specific justification for exceptions. Its three-month no-payment list is a monitoring trigger. These are different concepts, and the receipt date is not necessarily the recommendation date available in an export.[^9]

Before implementing a rule, the product needs its authoritative text, effective dates, scope, required fields and exception handling. If the relevant receipt date or approved extension is absent, an alert must say what is unknown. An old sanction date may justify seeking an update; it does not by itself establish a breach. A missing completion row in a partial export cannot establish that a work remains incomplete.

The official guidelines listing identifies the 2023 guidelines, effective from 1 April 2023, but a complete clause-by-clause review of those guidelines and subsequent amendments has not been established here. MoSPI's January 2026 workshop discussed proposed revisions. That workshop announcement is not evidence that a specific replacement rule was enacted. Any production compliance catalogue needs departmental validation against the operative instruments.[^14][^15]

**7. The proposed end-to-end solution.** The intended flow is:

1. Receive an authorised export or data delivery and record its scope and time.
2. Preserve the original and validate the fields, units, identifiers and report grain.
3. Link supported records while retaining uncertainty and source references.
4. Run only detectors for which the necessary evidence is available.
5. Present a review queue with clear reasons and any defensible priority factors.
6. Let the official inspect evidence and request the missing documents or field checks.
7. Record the decision, reasons, reviewer and time without rewriting detector history.
8. Use reviewed outcomes to assess the rules and approve later revisions.

An alert should contain the detector ID and version, affected records, the matched condition or measured deviation, severity meaning, evidence quality, fields used, explanation, limitations and a specific verification action. When peers are used, show how they were selected, how many there are, which were excluded and the relevant comparison. A reviewer should be able to reconstruct the alert without asking a language model to justify it.

Risk, confidence and availability require separate treatment. Risk concerns the potential significance of an observed issue. Evidence confidence concerns how well the observation is supported. Availability concerns whether a detector could run at all. Missing physical progress should therefore produce an unavailable progress detector and a request for progress evidence. It should not create either a reassuring low-risk result or an elevated risk score.

A composite score is optional at first. If later introduced, its weights, thresholds, contributions and treatment of unavailable detectors must be documented and tested. Correlated alerts should not repeatedly count the same underlying fact. A score of 80 cannot be described as an 80% probability of misuse without an appropriate labelled dataset and demonstrated calibration. Ranking must also avoid mechanically favouring districts simply because their reporting is more complete.

The present architecture is suitable for a measured extension: Next.js and TypeScript for the interface, FastAPI and Python for ingestion and detection, and PostgreSQL for source records, detector outputs and review history. Proposed heavy analysis should run during ingestion or scheduled processing, with cached results and server-side filtering for page requests. The current implementation already uses database-backed pagination and a server-to-server application boundary; production identity and operational readiness remain separate work.[^16]

**8. The role of AI and prediction.** For the proposed design, deterministic rules handle explicitly defined conditions, statistics identify interpretable deviations within valid peer groups, and conventional machine learning is considered when it improves measured results. Generative AI may turn existing evidence into a readable explanation. It must not create or alter the score, detector findings, severity or compliance decision. This is also the repository's declared product boundary.[^12][^16]

An Isolation Forest or another outlier method could be evaluated on suitable numerical features, but its output is not an independently established allegation. The scikit-learn documentation explains that outlier predictions use thresholds over scoring functions, with contamination controlling thresholds in relevant estimators. Selecting such a parameter is a modelling choice, rather than discovering the percentage of misconduct in a population.[^17]

Genuine prediction requires a target defined in advance. One possible future research target is whether a work will miss its approved deadline, evaluated using information that existed at the prediction date. This requires historical snapshots, deadline revisions and reliable outcomes. A dataset collected after completion can accidentally reveal the answer through fields that would not have existed earlier, producing misleading performance.

Early warning can begin without a predictive model if reliable updates identify an emerging exception soon enough for an official to act. The system must distinguish an observed current exception from a forecast. The current repository has neither the historical coverage nor outcome validation needed to claim a reliable delay forecast. The remaining AI-related scope is substantial even though the review workflow is already useful.[^12]

**9. The data currently available.** The repository source register records twelve original files and six staged CSV reports. The team confirmed an All India, Lok Sabha download context. Exact extraction times and export completeness are not established by the CSV files. The inventory below reports detail rows, not unique projects.[^11][^13]

| Supplied CSV report | Detail rows | Interpretation constraint |
| --- | ---: | --- |
| Allocated Limit for Honble MPs | 543 | MP-level allocation rows; period and stable MP identifiers are missing |
| Amount consented for Calamity | 12 | Consent entries; these do not establish disbursal to particular works |
| Expenditure on Completed and On-going Works as on Date | 11,000 | Payment-related entries with repeated work identifiers |
| Works Recommended | 107,156 | Recommendation records, including repeated or missing usable work identifiers |
| Works Sanctioned | 16,000 | Sanctioned-work records used by the current active detector |
| Works Completed | 7,000 | Exported completion records with unverified population coverage |

These rows must not be added together and advertised as distinct projects. CSV and XLSX row counts differ for expenditure and completion reports. The sanctioned, expenditure and completed CSV detail amounts also fail reconciliation with their footers. Those observations require investigation of export scope, pagination or source behaviour; they do not establish missing public funds.[^11][^13]

Cross-report joins reveal additional limits. The documented comparison finds only 620 shared normalised work IDs between expenditure and sanctioned exports, and only 17 between expenditure and completed exports. Those are properties of the supplied snapshots. Treating non-matches as evidence of unsanctioned payments or nonexistent completed works would assume a completeness and synchronisation that have not been established.[^13]

The payment export contains 11,000 rows but 8,210 distinct normalised work IDs, with 823 repeated IDs and 143 exact repeated detail rows when serial numbers are ignored. Instalments and reporting duplication are possible explanations. Because a transaction identifier is absent, the original rows are retained. A project identifier identifies a work, not a unique payment.[^12][^13]

Coverage limitations exist at the portal level as well. The official explanation excludes pre-2023–24 recommended and sanctioned work details from the specified eSAKSHI historical coverage. A multi-year comparison must therefore check which years and workflows it actually observes. Partial records should not be stretched into a complete parliamentary-term performance assessment.[^6]

**10. What the current project demonstrates.** The active detector groups records with different derived work IDs when seven configured fields match after normalisation: description, work type, State, constituency, implementing district authority, sanction date and sanction amount. It retains the matched values, source references, explanation and verification guidance. The current severity is a review label, and confidence represents whether the configured predicate matched, not the probability of an actual duplicate.[^12][^18]

The documented run over the supplied 16,000 sanctioned records produced 174 candidate groups referencing 1,281 source records. Group sizes range from two to 86. Those numbers come from the repository's recorded analysis; this report does not represent a fresh run against the deployed database. Large groups are especially important to inspect because standard template descriptions may describe legitimate separate works.[^12]

An earlier cost-screening calibration used at least twice the median sanction amount within category/type groups of at least 20 records. It generated 3,016 candidates and was disabled. The issue is that the available grouping fields do not establish comparable engineering scope. The count alone cannot measure its false-positive rate, because adjudicated outcomes are not supplied.[^12][^18]

| Capability | Current position | Implication for the demonstration |
| --- | --- | --- |
| Source ingestion and provenance | Implemented for the six supplied CSV reports | Explain how a displayed result traces to its original record |
| Exact potential-duplicate screening | Implemented | Demonstrate a candidate and its limitations |
| Investigation Queue and evidence | Implemented | Show real search, filters, pagination, export and evidence inspection |
| Review history | Implemented as append-only events | Record a reasoned review decision and show its history |
| Composite risk score and contribution model | Not implemented | Do not present an invented score |
| Context-rich cost and progress analysis | Missing required evidence; broad cost rule disabled | Explain the data dependencies |
| Predictive early warning | Not validated or implemented | Present as a defined future evaluation task |
| Departmental identity, roles and ownership | Current local reviewer mechanism is limited | Treat the application as a prototype requiring production work |

The queue supports moving a new case into review, requesting verification, resolving or dismissing it, and reopening where appropriate. The event history is separate from detector evidence. A verification-request status does not itself establish that an external agency was notified or that an inspection occurred. Such operational integrations must be demonstrated separately.[^12][^19]

**11. A clear demonstration story.** Start with the source snapshot and its coverage, then open one actual candidate group. Show the different work identifiers and the fields that caused the match. Open the source references, explain that exact matching does not establish asset identity, and show the documents or location details the official should request. Finally, record a review action with a reason and show that it persists.

For explanation only, consider two hypothetical records describing a community hall with matching date and amount. They might refer to the same asset, or to separate phases or sites recorded with a standard description. A useful alert asks the official to compare the sanction orders, site identifiers and scope. If those documents are unavailable, insufficient evidence is a valid outcome. The hypothetical records must not be inserted into the official-data demonstration as if they were real.

The strongest claim supported by this flow is that the prototype can turn a documented matching condition into a traceable verification case. The full intended system would add several validated detectors and help allocate review attention across them. That broader claim requires additional data, evaluation and implementation.

**12. How success should be measured.** The objective is useful official action with acceptable review effort. The number of alerts alone is a poor success measure: excessive low-value alerts can make monitoring less effective. The following are proposed evaluation measures, not achieved results.

| Measure | Suggested definition | Interpretation limit |
| --- | --- | --- |
| Useful-case rate in the first k cases | Reviewer-adjudicated actionable cases divided by the k reviewed cases, using a predefined outcome definition | Does not measure all missed cases |
| Review preparation time | Time needed to assemble the evidence for equivalent cases | Compare equivalent tasks and experienced reviewers |
| Time to first action | Time from alert availability to a recorded substantive review step | A status click without review is not meaningful action |
| Unresolved evidence burden | Cases blocked by missing evidence and the age of those requests | Helps identify data-access needs separately from detector quality |
| Detector coverage | Eligible, successfully evaluated records divided by records in the declared relevant population | Requires an explicit denominator and exclusion reasons |
| Dismissal and insufficiency rates | Reviewed outcomes by detector, source and context | Dismissal is not always a modelling error; reasons matter |
| Reproducibility | Same source and processing version produce the same evidence and results | Determinism does not prove the rule is useful |
| Lead time for a future predictive model | Time between the forecast and a subsequently verified outcome | Requires historical as-of data and an appropriate comparison model |

Review samples should include flagged records and a random sample of unflagged records, with diversity across work types and geography. Evaluating only flagged cases hides misses. Related records should be kept together when splitting development and evaluation data so near-duplicates do not leak between them. Predictive evaluation should hold out later time periods and record the information available at each cutoff.

Money associated with an alert is neither money lost nor money saved. Multiple alerts may concern the same work or payment, so even exposure totals need deduplication and precise definitions. Financial benefit should be reported only where a documented administrative outcome supports attribution. There is no verified accuracy percentage, loss estimate or realised saving established by this research.

**13. Recommended next steps.** First secure the authoritative SIH statement and the operative guideline/amendment set. Agree with at least a small number of intended reviewers which decisions are difficult, what evidence they need and which outcomes count as useful. Validate the existing duplicate rule using a structured review sample, including large groups and ordinary unflagged records. This can expose problems in descriptions, identifiers or normalisation before more detector types are added.

Next define a reliable work history. Obtain export coverage, consistent extraction times, stable work/asset identifiers and explicit relationships between recommendation, sanction, payment and completion records. Preserve one-to-many relationships rather than flattening all observations into one row. Reconcile report scope before drawing conclusions from unmatched records or totals.

Then request the minimum evidence for the next detector: engineering quantities and specifications for cost comparison; receipt, deadlines and extensions for delay; and transaction identities plus dated progress for payment analysis. Choose the detector according to the evidence that can actually be supplied. A narrowly supported rule can be evaluated sooner than a broad detector that relies on imputed facts.

After that, complete a controlled departmental pilot with individual identities, appropriate access boundaries, case ownership, evidence handling, backups, review of security and responsiveness on realistic devices. Confirm that the current public demonstration environment and deployed versions match the approved pilot configuration. The repository's deployment documentation itself treats organisational production readiness as unfinished.[^20]

Finally, evaluate statistical or predictive methods against the validated rule-based baseline. Add them when they provide measurable additional value. Maintain a record of model/rule changes and their effects on reviewer workload. This sequence is a recommendation based on the current evidence constraints, not a claim that the full SIH objective can be achieved from the existing public exports alone.

**Source notes and limitations.** External sources and repository material were assessed through 10 September 2026. Current scheme operation is supported by government publications; the SIH wording is supported only by the provisional references described above. The historical CAG evidence is explicitly period-limited. No current nationwide misconduct prevalence, field validation, complete government integration or certified detector accuracy is established. Repository counts are documented snapshot measurements, and implementation statements are based on the inspected files rather than a new production acceptance test.

**Sources**

| No. | Publisher or record | Date and use |
| --- | --- | --- |
| 1 | Community SIH 2026 archive, SIH26102; official SIH statement index as the pending authority | Undated archive; provisional problem scope only |
| 2 | MoSPI, Lok Sabha Unstarred Question 501, Increase in MPLADS Fund | 23 July 2025; annual entitlement and policy context |
| 3 | Tamil Nadu Rural Development and Panchayat Raj Department, MPLADS scheme page | Page displays update 7 September 2026; scheme purpose and allocation corroboration; not a source for national current totals |
| 4 | PIB/MoSPI, Revamped public dashboard of MPLADS eSAKSHI portal | 6 March 2026; institutional responsibilities and existing portal capabilities |
| 5 | PIB/MoSPI, Year-end review 2025, MPLADS section | 24 December 2025; April 2025 fund-flow transition and PFMS |
| 6 | MoSPI, eSAKSHI public dashboard process explanation | Accessed 10 September 2026; utilisation/expenditure definitions and coverage |
| 7 | CAG, Report No. 31 of 2010 landing page | Tabled 18 March 2011; historical audit identity and period |
| 8 | CAG, same report, chapter 4, Execution of Works | Historical period 2004–05 to 2008–09; age-wise monitoring information |
| 9 | PIB/MoSPI, eSAKSHI Portal | 6 August 2025; quoted guideline provisions and existing pendency reviews |
| 10 | Chandola, Banerjee and Kumar, Anomaly Detection: A Survey, ACM Computing Surveys 41(3) | July 2009; contextual anomaly methodology |
| 11 | Repository source register | Updated 7 September 2026; delivery context, report inventory and authenticity limits |
| 12 | Repository detection rules | Inspected 10 September 2026; active/disabled rules, documented measurements and review constraints |
| 13 | Repository data dictionary | Inspected 10 September 2026; measured fields, report grain and overlap |
| 14 | MoSPI, MPLADS Guidelines listing and linked English 2023 document | Effective 1 April 2023; full clause/amendment validation remains incomplete |
| 15 | PIB/MoSPI, National Level Brainstorming Workshop for revision of guidelines and portal | 23 January 2026; proposed revisions, not an enacted replacement rule |
| 16 | Repository architecture and PRD | Inspected 10 September 2026; implemented versus intended boundaries |
| 17 | scikit-learn, Novelty and Outlier Detection documentation | Accessed 10 September 2026; outlier scores and thresholds |
| 18 | Repository backend detector implementation | Inspected 10 September 2026; actual configured matching and disabled cost rule |
| 19 | Repository backend investigation implementation | Inspected 10 September 2026; persisted review transitions |
| 20 | Repository deployment readiness | Updated 8 September 2026; documented staging/production limitations |

[^1]: Community archive, [SIH26102](https://sih2026.vuce.in/ps/SIH26102). Explicitly unofficial. Pending authority: [official SIH 2026 statements](https://sih.gov.in/sih2026PS), not authenticated in the available material.
[^2]: MoSPI, [Lok Sabha Question 501: Increase in MPLADS Fund](https://sansad.in/getFile/loksabhaquestions/annex/185/AU501_Df6JX9.pdf?source=pqals), 23 July 2025, pp. 1–2.
[^3]: Tamil Nadu government, [Member of Parliament Local Area Development Scheme](https://tnrd.tn.gov.in/rdweb_newsite/project/reports/Public/public_page_table_content_details_view.php?page_id=Nw%3D%3D&tabular_content_id=MTc%3D).
[^4]: PIB/MoSPI, [Revamped public dashboard of MPLADS eSAKSHI portal](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2235932), 6 March 2026.
[^5]: PIB/MoSPI, [Year-end review 2025](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2208162&lang=2&reg=48), 24 December 2025, section 12.
[^6]: MoSPI, [eSAKSHI dashboard and process explanation](https://mplads.mospi.gov.in/digigov/dashboard.html).
[^7]: CAG, [Report No. 31 of 2010: MPLADS performance audit](https://cag.gov.in/en/audit-report/details/2341), tabled 18 March 2011.
[^8]: CAG, [Execution of Works, chapter 4](https://cag.gov.in/webroot/uploads/download_audit_report/2010/Union_Performance_Local_area_Development_Scheme_31_2010_chapter_4.pdf), section 4.1, printed p. 17.
[^9]: PIB/MoSPI, [eSAKSHI Portal](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2153066), 6 August 2025, provisions 3.2.4 and 3.2.12 and the monitoring paragraph.
[^10]: V. Chandola, A. Banerjee and V. Kumar, [Anomaly Detection: A Survey](https://arindam.cs.illinois.edu/papers/09/anomaly.pdf), July 2009, section 2.2.2.
[^11]: Repository [source register](../source-register.md). Local project record; not independently certified government data.
[^12]: Repository [detection rules](../detection-rules.md).
[^13]: Repository [data dictionary](../data-dictionary.md).
[^14]: MoSPI, [guidelines listing](https://www.mplads.gov.in/MPLADS/En/2010-mplads-guidelines.aspx) and [English Guidelines 2023](https://www.mplads.gov.in/MPLADS/UploadedFiles/MPLADSGuidelines2023_English_.pdf). Full PDF retrieval was incomplete; specific timeline statements in this report rely on source 9.
[^15]: PIB/MoSPI, [National Level Brainstorming Workshop for the revision of MPLADS guidelines and eSAKSHI Portal](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2217813&lang=1&reg=3), 23 January 2026.
[^16]: Repository [architecture](../architecture.md) and [PRD](../PRD.md).
[^17]: scikit-learn, [Novelty and Outlier Detection](https://scikit-learn.org/stable/modules/outlier_detection.html), sections 2.7 and 2.7.3.
[^18]: Repository [detectors.py](../../backend/src/backend/detectors.py).
[^19]: Repository [investigations.py](../../backend/src/backend/investigations.py).
[^20]: Repository [deployment readiness](../deployment.md).
