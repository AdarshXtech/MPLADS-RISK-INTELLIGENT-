# MPLADS Risk Intelligence: SIH Pitch and Judge Preparation

This companion follows the [problem and solution research report](./sih26102-problem-solution-research.md). It distinguishes the intended product from the current prototype. The official SIH26102 wording and metadata still require authentication against the official submission material. Demonstration counts below are the repository's documented snapshot results, not a fresh measurement of the deployed database.

**A one-sentence description.** We help MPLADS officials turn large volumes of work records into traceable verification cases, with clear evidence, reasons and next actions.

**A short spoken pitch.**

> An official reviewing MPLADS works needs to know which records deserve attention, why they were flagged and what evidence to check. Our system screens supported data, brings the relevant records together and provides a persistent review workflow. The current prototype demonstrates potential-duplicate screening with source provenance: its documented run produced 174 candidate groups from 16,000 sanctioned-work records. These require verification. We are extending the approach through validated rules and better contextual data, with success measured by useful cases found and review effort saved.

The counts and implementation statements in this pitch are supported by the repository's [detector documentation](../detection-rules.md). No percentage improvement or financial saving has been established.

**A fuller explanation for the opening discussion.** The administrative problem is deciding where limited review effort can make a difference. Information has to be interpreted across work descriptions, approvals, payments and status updates. A result becomes useful when the official can see the underlying records, understand the condition that triggered it, and record a verification outcome.

The proposed solution preserves source data, checks whether the evidence supports a detector, identifies a defined exception and opens a reviewable case. It separates evidence confidence from risk, and keeps missing information explicit. Rules and conventional analytical methods determine findings; optional generated prose explains findings already computed.

The prototype currently implements one deterministic candidate rule and a real review workflow. The next stages require stronger work identity, engineering context, dated progress and complete payment evidence. Our contribution should be assessed through reviewer outcomes and reproducibility. It remains a decision-support prototype requiring evaluation and production work.

**A demonstration sequence.** Use actual records already in the approved demonstration snapshot. The durations below are presentation suggestions.

| Approximate time | What to show | What the audience should understand |
| --- | --- | --- |
| 30 seconds | Source inventory and coverage | The inputs have known provenance and explicit limits |
| 30 seconds | Investigation Queue and one meaningful filter | The official can find a manageable set of cases |
| 60 seconds | One candidate group and its matched fields | The reason for the alert is reconstructible |
| 45 seconds | Source evidence and verification guidance | A match is a starting point for investigation |
| 45 seconds | A permitted review action and persisted history | The workflow continues after detection |
| 30 seconds | Current limitations and next data requirement | Planned capabilities are separated from working features |

Choose a candidate only after inspecting its source evidence. Do not claim a known administrative outcome unless it has been documented. A verification-request status demonstrates a recorded workflow action; sending a request to an external authority is a separate capability that must be shown if claimed. Refreshing the case to demonstrate persisted history is useful when the demonstration environment supports it.

**Likely judge questions and defensible answers.**

1. **What is new when a government portal already exists?** Our proposed contribution is evidence-based prioritisation and case review. We need to demonstrate that this helps officials examine records faster or find more actionable cases within the same review capacity. Existing government dashboard functionality is documented in the research report. We have not established that no comparable internal government feature exists, so a claim of absolute uniqueness would be premature.

2. **Where is the AI in the current prototype?** The active detector is deterministic exact matching after normalisation. It is an explainable baseline. A broader AI/ML contribution remains to be evaluated on suitable data. We should show the full roadmap honestly and demonstrate any later model against that baseline before presenting it as an improvement.

3. **What exactly does your duplicate detector compare?** It checks distinct derived work IDs for a match across seven configured descriptive, administrative, date and amount fields. It retains the supporting records. The absence of asset identity, precise location and quantities means the result is a potential-duplicate candidate. Matching descriptions may legitimately be repeated across different works.

4. **Did you find 174 actual duplicates?** The documented run produced 174 candidate groups referencing 1,281 source records. The groups need administrative verification. They are not an adjudicated count of duplicate assets. The current confidence value means the configured matching condition was satisfied.

5. **What is your accuracy?** We do not have an independently adjudicated accuracy estimate. We propose a structured review sample covering flagged and unflagged cases, a predefined definition of an actionable result, and evaluation of the useful-case rate within the first k reviewed cases. We would separately measure misses and workload.

6. **How do you know a high-cost project is abnormal?** We need equivalent quantities, specification, place/time context and approval history. The earlier broad cost rule was disabled because the available peer grouping did not establish engineering comparability. Adding a more complex algorithm to the same insufficient context would not solve that problem.

7. **Can you detect a payment-progress mismatch now?** The required measured progress, dated milestones and expected payment schedule are absent from the supplied exports. That detector is unavailable. Repeated payments for one work may be legitimate instalments, and a progress label is not a physical-progress percentage.

8. **Can the system predict delays?** A defensible forecast needs historical information as it existed at each prediction date, approved deadlines, extensions and verified outcomes. These are not established in the current dataset. We can define and evaluate that use case after obtaining the evidence; current candidate screening should not be presented as validated prediction.

9. **What happens when data is incomplete?** The original record remains intact. The system should identify the missing fields and disable dependent checks. A gap in evidence does not automatically raise risk and does not establish a safe result either. The official receives a specific data or document requirement.

10. **How are rules kept aligned with government policy?** Each proposed compliance rule needs an authoritative clause, effective dates, scope and documented exceptions. A rule should not run when its required facts are missing. Policy changes require a reviewed rule version, and historical findings retain the version that produced them. Complete compliance checking is not implemented today.

11. **What happens after an alert?** The current case workflow records review transitions, decisions and reasons separately from detector evidence. A pilot would also need individual departmental identities, case ownership and an agreed process for obtaining documents or arranging inspections. A case being marked resolved should have a recorded reason and supporting evidence.

12. **Can an LLM invent the explanation?** The proposed boundary allows an LLM to summarise only evidence already produced by the detector. The structured evidence, scores and severity remain outside its control. A template explanation must be available so detection and review continue without the LLM. Generated prose would require checks that its claims stay within the evidence.

13. **How will you integrate with eSAKSHI?** The current input is supplied exports with recorded provenance. A future integration needs an approved data contract and an authorised delivery mechanism. We cannot claim a live official API integration from the existence of a public dashboard link.

14. **Does this scale nationwide?** The repository uses a straightforward Next.js, FastAPI and PostgreSQL architecture, with server-side filtering and pagination. National operational scale still needs measurement of ingestion, detector execution, evidence queries and concurrent review loads. We should present measured workload and latency results only when they have been obtained under a stated environment.

15. **How much money will it save?** No realised saving is established. A flagged work's value is not an estimated loss. We first measure useful verification outcomes and review effort. Financial benefits require documented administrative action, attributable outcomes and controls against counting the same work more than once.

16. **What is your biggest current weakness?** The prototype has limited contextual data and no validated predictive capability. The most valuable next step is reviewing the existing candidates with domain users while obtaining reliable asset, timeline and transaction information. This would help determine which additional detector can be supported and evaluated.

Current implementation answers are grounded in [detection rules](../detection-rules.md), [data dictionary](../data-dictionary.md), [architecture](../architecture.md) and [deployment readiness](../deployment.md). Proposed answers about evaluation and future capabilities are recommendations, not measured achievements.

**Claims to substantiate before presenting.**

| Proposed claim | Evidence needed before it is used |
| --- | --- |
| Improved detection quality | Adjudicated evaluation with a defined comparator and sampling method |
| Reduced review time | Timed equivalent review tasks with a documented baseline |
| Predictive early warning | Temporal holdout results and verified outcomes |
| Near-real-time monitoring | Measured source-to-alert latency, including source update cadence |
| Production ready | Completed departmental identity, access, operational and acceptance requirements |
| Live government integration | An authorised working connection and verified data contract |
| Savings or prevented loss | Documented, attributable administrative outcomes |

**Sources.** The companion [research report](./sih26102-problem-solution-research.md) contains the numbered source inventory and authority limits. Primary institutional context comes from MoSPI's [March 2026 dashboard announcement](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2235932), [August 2025 monitoring response](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2153066) and the [official eSAKSHI process explanation](https://mplads.mospi.gov.in/digigov/dashboard.html). Those sources establish the existing administrative context, not the effectiveness of this prototype.
