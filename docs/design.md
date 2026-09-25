# Suchak AI frontend design system

Updated 2026-09-25. This document describes the implemented frontend and its unified route shell.

## Design references

The seven supplied `stitch_mplads_design_system` ZIP exports contain reviewer sign-in, dashboard, risk-triage, comparison and audit-ledger concepts. Their screenshots and HTML informed the layout. Embedded document instructions, scripts, sample records, credentials and legal claims were not adopted as project requirements or production data.

The implementation uses the dark identity header, light operational navigation, restrained indigo/teal accents, compact metrics, source comparison and reviewer rail. The same design applies to sign-in, Command Centre, Investigation Queue, candidate evidence and Data Quality. No external Stitch code or CDN script runs in the application.

## Implementation map

| Surface | Implementation |
| --- | --- |
| Shared colours, typography, spacing and responsive rules | `frontend/app/globals.css` |
| Header, session identity, sidebar and footer | `frontend/app/investigation-queue/shell.tsx` |
| Suchak AI logo and metadata | `frontend/app/brand.tsx`, `frontend/app/layout.tsx`, `frontend/public/brand/suchak-ai.png` |
| Sign-in layout | `frontend/app/login/page.tsx` |
| Password visibility | `frontend/app/login/password-field.tsx` |
| Sign-in and review pending states | `frontend/app/submit-button.tsx` |
| Cross-browser responsive route and state coverage | `frontend/e2e/responsiveness.spec.ts` |
| Source readiness and review workload | `frontend/app/command-centre/dashboard.tsx`, with route entry points in `command-centre/page.tsx` and `data-quality/page.tsx` |
| Review distribution and filtered workload links | `frontend/app/command-centre/review-overview.tsx` |
| Candidate filters, results and pagination | `frontend/app/investigation-queue/page.tsx` |
| CSV download with pending/error/success states | `frontend/app/investigation-queue/export-button.tsx` |
| Evidence, source comparison, review form and history | `frontend/app/investigation-queue/[id]/page.tsx` |
| India map, pair selection and fetched source details | `frontend/app/investigation-queue/location-comparison.tsx`, `location-map-canvas.tsx`, `location-types.ts` |
| Authenticated source detail request | `frontend/app/investigation-queue/[id]/source/route.ts` |
| UI interaction and layout checks | `frontend/e2e/stitch-ui.spec.ts`, existing queue and responsiveness suites |

## Visual tokens

| Token | Value | Purpose |
| --- | --- | --- |
| Canvas | `#f7f9fc` | Neutral workspace |
| Surface | `#ffffff` | Forms and readable evidence |
| Ink | `#17202d` | Body text |
| Muted | `#596575` | Supporting labels |
| Header | `#0b132b` | Product identity |
| Primary action | `#064d72` | Save and filter actions |
| Links | `#006c86` | Navigation and evidence actions |
| Border | `#dce3eb` | Section and table separators |
| Success | `#11734d` | Saved and resolved states |
| Caution | `#875400` on `#fffbeb` | Verification boundaries |
| Error | `#b4232c` on `#fff2f2` | Failed requests |

Use the already configured Geist font for body text and Geist Mono for identifiers and numeric totals. Font sizes are fixed within breakpoint layouts, with zero letter spacing. Controls have at least 44-pixel targets. Inputs/buttons use 5-pixel corners, repeated metrics/source items use 6 pixels and the authentication form uses 8 pixels. Page sections use borders and full-width surfaces rather than floating cards.

Lucide icons supplement visible labels. The password icon button has an accessible action name and tooltip. Status always includes text, not colour alone. Focus outlines, semantic forms, the authenticated skip link and reduced-motion support remain available.

## Responsive behaviour

- Below 1024 pixels, navigation wraps above the workspace; the desktop sidebar no longer consumes horizontal space.
- Below 672 pixels, candidate tables become readable cards. Filters stack on phones and use two columns from 768 pixels.
- At 1280 pixels and above, the evidence view places the working review form and audit history in a right rail. At smaller sizes, review follows evidence in document order.
- Source records and metrics use bounded grid tracks. Long identifiers and labels wrap instead of widening the page.
- The sign-in form remains centred on a subtle grid background, with wrapping header and footer content.

## Data and action boundaries

All counts, match confidence, severity and source records come from the existing API. Screening summary and supporting evidence use the same returned detector distance; zero is displayed as `0.0 m` and missing distances remain unavailable. The map separately calculates display-only straight-line separation for the selected pair using their returned verified coordinates. It does not modify detector evidence. Confidence is labelled as matching confidence, not probability of misuse. Source records are not labelled as proposed or historical sanctions unless the data establishes that relationship.

## Suchak AI identity and comparison map

The shared `Brand` renders the supplied PNG unchanged. CSS frames its transparent margins; the header uses a white backplate so the original dark wordmark remains readable. Sign-in, authenticated routes, footer, page titles and icon metadata share the Suchak AI identity. The Command Centre reference is adapted into actual review-state bars, three working filtered-queue links and a full-width source matrix. Its illustrative financial, state and trend values are not imported.

The locality section contains a client-only Leaflet map with a bundled India reference outline. Exactly the selected A/B pair is considered for markers. Only `VERIFIED_COORDINATES` records with finite, valid latitude/longitude produce a pin; administrative names and unverified addresses never produce substitute points. Opposite marker anchors keep co-located works selectable at their unchanged coordinates. Larger groups offer two distinct work selectors.

Clicking a marker or its source button fetches the record through the authenticated Next.js route. The detail panel displays available provenance, location/verification, cleaned values, derived values and validation issues. It includes loading, retry and expired-session states and cancels stale requests. Enter and Space activate markers. Missing coordinates do not prevent source detail inspection.

India view, fit locations, zoom and optional street tiles are implemented controls. The local outline works without a third-party map request. Enabling Street map requests OpenStreetMap tiles directly from the browser; failure leaves the outline and markers available. Attribution and a non-legal-boundary notice remain visible. See the [map asset provenance](../frontend/public/maps/README.md). The map is 400 pixels high, or 340 pixels on phones, with stacked source details on narrow screens.

`frontend/e2e/location-comparison.spec.ts` exercises branding, workload links, map controls, marker selection, pair changes, coincident/missing/invalid coordinates, authenticated membership, recovery and stale requests across all three browsers.

The design exports' invented financial exposure, live-sync timing, clearance levels, certification/legal assertions, demo credentials, notifications, support links, passkeys, hardware tokens and sanction-freezing actions are not displayed. The implemented sign-in, server-side filters, pagination, CSV export, review transitions and append-only history continue to use their existing handlers.

See [responsive-ui.md](responsive-ui.md) for reproducible screenshots and browser coverage. Synthetic fixtures are used only by the test suite.
