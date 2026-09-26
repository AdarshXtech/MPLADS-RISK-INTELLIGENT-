# Responsive UI verification

Verification on 2026-09-26 covers the six source-backed surfaces: sign-in, Command Centre, Investigation Queue, candidate evidence and duplicate comparison, Data Quality and Review Audit Trail. The full 66-test production-build run passed all Chromium and Firefox scenarios and 19 of 22 WebKit scenarios. The three affected WebKit workflows then passed focused reruns after a same-route retry correction and realistic budgets for long end-to-end flows. The responsive route suite covers the Audit Trail at every viewport below, including loading, empty, error, filtering and mobile-card states.

Publication merge on 2026-09-25: dedicated Data Quality navigation and pending-review ordering are retained with the Suchak AI design. The merged suite passed 63 browser checks and exposed a source-count selector collision in three browsers. After scoping the selector to the source section, all nine queue checks passed in the focused rerun. This covers the changed navigation, provenance text sizing, review submission, filtering, export and Data Quality active state alongside the passing map/responsive checks.

The 2026-09-25 Stitch adaptation is described in [design.md](design.md). The shared header, light navigation, sign-in, filters, source comparison and reviewer rail use the same responsive checks. `stitch-ui.spec.ts` additionally verifies password visibility with keyboard activation, side-by-side desktop evidence/review placement, stacked phone placement, pending review submission and truthful failed-service status.

Verification on 2026-09-25: all 51 tests passed across Chromium, Firefox and WebKit. A final distance-display consistency fix was followed by a successful production rebuild and six focused UI checks in all three browsers, including zero versus unavailable distance. Updated focused screenshots are under `output/stitch-ui/`; route/state captures are under `output/responsiveness/`. These remain synthetic test artifacts.

The Data Quality sidebar item now opens `/data-quality` with a distinct heading, active navigation state and loading, empty and service-error views. Route and state captures include this page on phone, tablet and desktop.

The 2026-09-13 readability pass uses the already-loaded Geist font, larger supporting labels and word-level wrapping for ordinary copy. Long source hashes, Work IDs and reviewer names still wrap safely. The Command Centre source panel no longer stretches to the neighbouring analysis rail, and its aggregate caption explains that report-row totals are not unique projects.

The existing application uses wrapping navigation, fluid filter columns, mobile candidate cards, responsive metric grids and wrapping evidence values. Desktop sidebars scroll when the available height is short. Buttons and primary action links have a minimum 44-pixel height.

The shared skip link is explicitly tabbable, including in WebKit's default keyboard mode. Its main-content destination has `tabIndex=-1` so activation transfers focus without adding a second stop to normal Tab navigation.

## Screens and states

The Suchak AI continuation adds `location-comparison.spec.ts`: actual logo loading and page titles, review workload navigation, India outline and map controls, exact A/B selection with Enter/Space support, co-located points, missing/invalid coordinates, larger groups, stale request cancellation, authenticated source membership, map/source failures and a delayed-map tablet layout regression. Labelled screenshots are written to `output/suchak-ui/<browser>/`; the actual local sign-in screenshots are `output/suchak-ui/login-desktop.png` and `login-phone.png`. No screenshot contains official review data.

Final continuation verification: the expanded 66-test suite passed in Chromium, Firefox and WebKit. A final street-layer cleanup was followed by a production rebuild and all 15 focused map tests passing again. Map loading retains a stable shell so it does not shift the review form during a click. Attribution removal, Enter/Space activation and failed-source retry are explicitly asserted.

The reproducible Playwright suite checks Chromium, Firefox and WebKit at these CSS viewport sizes:

| Size | Width x height |
| --- | --- |
| Small phone | 320 x 568 |
| Phone | 390 x 844 |
| Phone landscape | 844 x 390 |
| Tablet portrait | 768 x 1024 |
| Tablet landscape | 1024 x 768 |
| Small laptop | 1280 x 800 |
| Desktop | 1440 x 900 |
| Large desktop | 1920 x 1080 |

Every size covers sign-in, the populated queue, candidate evidence, a saved review, the Command Centre and Data Quality. Phone, tablet and desktop also cover invalid sign-in; empty and filtered queues; export pending, failure and success; failed review; missing and unavailable candidates; queue and Data Quality service failure/recovery; empty sources; both route loading states; second-page results; verification requested, resolved, reopened and dismissed review states.

A 640 x 450 case checks keyboard entry through the skip link, reduced-motion preference and long unbroken synthetic evidence. It approximates the CSS width available when zooming a 1280-pixel screen to 200%. It does not certify native browser zoom or physical mobile devices.

## Generate screenshots

Run from `frontend`:

```powershell
$env:CAPTURE_UI = '1'
npm run test:e2e
node e2e/build-gallery.mjs
```

Open `output/responsiveness/index.html` from the repository root. Choose a browser and screen size, then open any thumbnail for the full PNG. Use the browser's Save image action to retain an individual image. Screenshots are generated only when `CAPTURE_UI=1`; the layout assertions run during normal CI too.

All screenshots carry a synthetic-data label. Test-only response overrides in `frontend/e2e/mock-api.mjs` exercise server-rendered failure, delay and empty responses through the actual Next.js pages. The mock listens only on loopback, requires the generated test API key for scenario configuration and is never imported into the application. Review submissions update this mock only. No official records are changed.

The images are actual browser captures, not generated design mock-ups. The gallery covers the scenarios listed above, not every possible combination of data and device. Runtime values are synthetic, and database integration is tested separately by Pytest. This is responsive regression coverage, not a complete WCAG certification.
