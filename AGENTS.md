# SIH26102 permanent development rules

These rules are mandatory for all future work in this repository. They apply to code, tests, product copy, documentation and commit messages.

## 1. Product purpose and claims

This is an MPLADS Risk Intelligence and Early Warning System, not a normal dashboard. It is a decision-support product that must help officials answer:

1. What looks abnormal?
2. How serious is it?
3. Why was it flagged?
4. What evidence supports the alert?
5. What should an official verify next?

Do not make legal accusations or claim that anomaly detection proves fraud. Acceptable terms include "high-risk anomaly", "potential irregularity", "potential duplicate", "unusual expenditure pattern", "compliance deviation", "requires verification" and "potential misuse indicator".

Never state "fraud confirmed", "this MP committed fraud", "this contractor stole money", "proven corruption" or an equivalent accusation.

## 2. Working product, not dummy UI

Every visible interactive element must have a real purpose, working behaviour and relevant tests. Do not create dummy buttons, dead links, fake search, fake filters, fake export, fake notifications, fake profile menus, fake forms, placeholder modals, non-working pagination, decorative controls or controls that only announce "coming soon".

If functionality is not implemented, do not display its control. A visually correct page with dead interactions is incomplete. Optimise for a working product, not screenshots.

## 3. Language and content

- Use Indian English.
- Do not use emojis in UI, documentation, generated copy, code comments or commit messages unless technically necessary.
- Do not use em dashes.
- Use concise, professional and administrative wording.
- Avoid generic AI marketing language such as "powered by magic", "intelligent insights", "smart AI engine", "revolutionary AI", "awesome" and "supercharged".
- Do not exaggerate system capability.

## 4. Data integrity and provenance

- Never fabricate government data or invent missing MPLADS fields.
- Never silently replace missing values with assumptions.
- Keep original source data unchanged.
- Store raw data, cleaned data, derived features and model outputs separately.
- Preserve provenance from every risk result to its original source record.
- When required fields are missing, mark the detector unavailable, explain why, identify the missing fields and do not fabricate substitutes.
- Use synthetic data only for testing, label it clearly as synthetic and never present it as official MPLADS data.

## 5. Detection before generation

Generative AI must never determine whether a project is risky. Risk flags may come only from deterministic rules, statistical analysis, conventional machine-learning models or documented compliance logic.

Generative AI may explain evidence already produced by the system. It must not create, remove or modify risk scores, detector results, compliance results or severity levels. Detection and investigation must continue to work when the LLM is unavailable.

## 6. Explainability

Never show an unexplained risk score. Every detector result should include:

- detector ID
- detector name
- severity
- confidence
- evidence
- fields used
- human-readable explanation
- rule or model version

Composite risk scores must show their contributing factors. Show data confidence separately from risk. Poor data quality must not automatically increase risk.

Example presentation:

```text
Risk Score: 87 / 100

Cost deviation                  +23
Expenditure-progress mismatch   +26
Delay severity                  +18
Potential duplicate             +12
Compliance deviation             +8

Data Confidence: 91%
```

## 7. Architecture and dependencies

- Frontend: Next.js and TypeScript.
- Backend: FastAPI and Python 3.12.
- Python environment and packages: uv.
- Database: PostgreSQL.
- Tests: Pytest, Playwright and Vitest where appropriate.
- Prefer a simple, understandable architecture.
- Do not introduce microservices without a clear technical need.
- Do not use an AI agent framework for core application logic.
- Do not add a library because it is popular.
- Document every major dependency choice in `docs/decisions.md`.

## 8. Python and uv

- Use Python 3.12.
- Use `uv python install`, `uv python pin`, `uv add`, `uv remove`, `uv sync` and `uv run` as appropriate.
- Do not use pip directly unless a documented compatibility reason requires it.
- Treat `pyproject.toml` and `uv.lock` as the dependency sources of truth.
- Do not maintain `requirements.txt` unless a deployment target explicitly requires it.
- Never commit `.venv`.

## 9. UI and decision support

The product must feel like a serious government administrative tool: credible, calm, precise, evidence-focused, accessible and information-dense without clutter.

Avoid generic AI SaaS styling, glassmorphism, excessive gradients, neon glow, cryptocurrency-style dashboards, oversized hero sections, decorative 3D graphics, excessive rounded cards, random illustrations and clones of Notion, Linear or Google.

Every chart must support a real decision. Do not add charts to fill space. Each screen should make clear what requires attention, why, how serious it is and what the official should do next.

## 10. Responsive design

Support small phones, large phones, portrait and landscape tablets, small and large laptops, desktops and large desktops. Nothing may overlap. Do not merely shrink desktop tables on mobile; provide an appropriate mobile representation. Test multiple breakpoints.

## 11. Accessibility

Meet WCAG 2.1 AA. Use semantic HTML, complete keyboard navigation, visible focus states, proper labels, accessible tables, sufficient contrast, reduced-motion support, screen-reader-friendly controls and layouts usable at 200% zoom.

Do not communicate status through colour alone. Pair visual indicators with text labels.

## 12. Performance

Design for slow internet, low-end laptops and low-memory devices. Avoid unnecessary client-side processing and never load huge datasets directly into the browser.

Use pagination, lazy loading, code splitting, server-side filtering, cached analytics results and efficient API responses where they solve a measured or clear need.

## 13. Feature completeness and testing

A feature is complete only when its UI, backend and required persistence work, and its loading, empty, error, success, mobile and keyboard states work. Relevant automated tests must exist.

Test every visible button, link, filter, form and action. Use Playwright for real browser interaction tests. Test every implemented route and click every visible interactive control. Test Chromium, Firefox and WebKit where practical. Do not declare completion without running relevant tests.

## 14. Error handling

- Never hide important errors silently.
- Important actions need loading, success and error states, plus retry or recovery where appropriate.
- Do not expose raw backend stack traces to normal users.
- Log technical errors appropriately for development without leaking secrets.

## 15. Documentation sources of truth

Maintain these files as implementation evolves:

- `docs/PRD.md`
- `docs/techstack.md`
- `docs/architecture.md`
- `docs/data-dictionary.md`
- `docs/detection-rules.md`
- `docs/source-register.md`
- `docs/decisions.md`
- `docs/flow.md`
- `docs/CODEX_LOG.md`

Update documentation when implementation changes. Documentation must describe actual code and data, not planned or imaginary behaviour.

## 16. Decision records

For every meaningful technical or architectural decision, update `docs/decisions.md` with:

- date
- decision
- problem being solved
- alternatives considered
- selected approach and reason
- library selection and reason, or "not applicable"
- trade-offs
- performance impact
- maintainability impact
- security impact where relevant
- affected files

Do not silently reverse an earlier decision. Record what changed and why.

## 17. Execution flow record

Keep `docs/flow.md` aligned with the real application. Document the frontend and backend entry points, request and API flow, authentication if present, ingestion, detector order, risk aggregation, persistence, function call relationships and files changed in the current session.

Update `docs/flow.md` whenever execution flow changes. Mark unimplemented flows as unimplemented rather than inventing them.

## 18. Session log

After every meaningful coding session, update `docs/CODEX_LOG.md` with the date, task, files created, files modified, implementation decisions, tests executed, results, known limitations, required manual review and unresolved issues. Use concrete descriptions, never vague entries such as "improved backend".

## 19. Change scope

Keep focused tasks focused. Inspect related code, change only what is necessary, avoid unrelated refactors and document unavoidable wider changes. Do not redesign the application while fixing a small issue.

## 20. Code quality

Prefer readable code, clear names, small focused functions, explicit types, predictable folders and reusable components where appropriate. Avoid giant files, deep nesting, duplicated business logic, magic numbers, unexplained constants and unnecessary abstractions.

Centralise and document configuration such as detector thresholds.

## 21. Security

- Never commit `.env` files, API keys, tokens, passwords, database credentials, private certificates or service-account files.
- Use environment variables and provide `.env.example` with safe variable names or placeholders only.
- Validate inputs at trust boundaries and never rely only on frontend validation.
- Do not perform destructive database, file, deployment or repository actions without explicit approval.

## 22. MCP usage

Approved project MCPs are Context7, Playwright, GitHub after a repository exists, and Google Stitch for UI exploration.

- Use Context7 for important current, version-specific documentation. Prefer official documentation and skip it for trivial code.
- Use Playwright for browser QA under the testing rules above.
- Use GitHub MCP only after the repository exists. Start read-only with minimum toolsets and permissions.
- Use Stitch only for UI/UX exploration and design references. Reimplement useful ideas in the project design system with accessibility, responsiveness and real behaviour. Generated Stitch output is not production code.
- Do not install MCP servers speculatively.
- Prefer official or well-maintained implementations and minimum permissions.
- Never expose secrets through MCP configuration.
- Report unavailable or misconfigured MCPs exactly instead of silently substituting another tool.

Never let an MCP perform destructive file, repository, deployment or database operations without explicit approval. Never force-push, delete branches, close issues or merge pull requests automatically.

## 23. Git

Prefer small, logical commits with meaningful messages, for example:

- `feat: add project risk profile API`
- `fix: correct expenditure progress detector`
- `docs: add detection rule definitions`
- `test: add investigation queue e2e tests`
- `refactor: simplify risk aggregation service`

Do not use vague messages such as `update`, `changes`, `final`, `stuff` or `working`. Do not force-push or delete branches without explicit approval.

## 24. Before implementing a major feature

1. Read this file.
2. Read the relevant documentation.
3. Inspect the current implementation.
4. Identify dependencies and affected files.
5. Review `docs/decisions.md`.
6. Plan the smallest complete change.
7. Then implement.

## 25. Before declaring a task complete

Where relevant to the task:

- run the application and relevant tests
- inspect frontend console and backend errors
- verify visible controls, responsive layout and keyboard interaction
- verify no fabricated data was introduced
- verify there is no unexplained risk score or prohibited accusation language
- update `docs/decisions.md`, `docs/flow.md` and `docs/CODEX_LOG.md`

Only then report completion. If a check cannot be run, state exactly why.

## 26. Target demonstration flow

All implementation should move towards this working demonstration without pretending that unimplemented stages exist:

```text
Thousands of MPLADS projects
-> system identifies a small number requiring attention
-> official opens a project
-> system explains exactly why it was flagged
-> evidence and peer comparison are visible
-> official receives a verification recommendation
-> case enters a real review workflow
```
