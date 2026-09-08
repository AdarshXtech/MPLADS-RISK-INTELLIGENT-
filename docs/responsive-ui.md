# Responsive UI verification

The existing application uses wrapping navigation, fluid filter columns, mobile candidate cards, responsive metric grids and wrapping evidence values. Desktop sidebars scroll when the available height is short. Buttons and primary action links have a minimum 44-pixel height.

The shared skip link is explicitly tabbable, including in WebKit's default keyboard mode. Its main-content destination has `tabIndex=-1` so activation transfers focus without adding a second stop to normal Tab navigation.

## Screens and states

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

Every size covers sign-in, the populated queue, candidate evidence, a saved review and the Command Centre. Phone, tablet and desktop also cover invalid sign-in; empty and filtered queues; export pending, failure and success; failed review; missing and unavailable candidates; queue and Command Centre service failure/recovery; empty sources; both route loading states; second-page results; verification requested, resolved, reopened and dismissed review states.

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
