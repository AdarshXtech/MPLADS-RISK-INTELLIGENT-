# SIH26102 presentation source and handover notes

Date: 10 September 2026

## Template-matched revision

Current local output: `output/presentations/Innospark-SIH26102-template-matched-v3.pptx`.

The user subsequently supplied `SIH26102_MPLADS_Risk_Intelligence_Official_Template_Edited.pdf`. This now takes precedence over the earlier generic visual direction. All six source pages were inspected. The presentation retains the SIH 2026 logos, Innospark badge, serif headings, pastel panels, source diagram arrangement, blue footer and six-slide order. The PDF's 960 x 540 point canvas maps to the same 16:9 PowerPoint dimensions.

Source outlines were reconstructed as editable native shapes, with editable text and a native risk-response table. Original logo images were extracted rather than redrawn. This is a reconstruction from PDF, not preservation of an original PowerPoint master. Curve sampling, shadows, table borders and some text wraps can differ slightly. The PDF remains unchanged.

The old deck's proposed score, risk fusion, NLP/geospatial matching and additional detector families are retained as proposals. Actual seven-field matching and the implemented stack are distinguished from future work. The source does not provide a Team ID, which still needs to be filled before submission. Source content did not include specific CAG report or research paper citations, so none were fabricated.

The final six slides were rendered and compared with the reference pages. Package integrity, slide count, geometry, source-derived font policy and re-import checks passed. No desktop PowerPoint verification, application change or Git push was performed. The earlier draft and its research record below are historical, not the current template choice.

## Earlier draft

Local output: `output/presentations/mplads-sih26102-pitch-draft-v5.pptx`.

Six slides: title, idea and uniqueness, technical approach, feasibility and risks, impact and benefits, references. The flow diagram, text and risk-response table are editable. References and speaking guidance appear in slide notes. The screenshot is a labelled synthetic browser-test capture, not official work data.

The output is a draft because the supplied OneDrive presentation could not be retrieved. The link returned an access error during inspection. No matching MPLADS deck was found among the PowerPoint files in Downloads. The local `PPT TEMPLATE .pdf` belongs to a different hackathon. No content or team metadata has been claimed as recovered from the old deck. Upload the original PPTX before preparing the submission version.

## Reference presentation

[Ourobonics / Kritrim, team-published SIH 2025 deck](https://github.com/Baksheeshs/ourobonics-kritrim_SIH_2025_Winner/blob/main/ourobonics_SIH2025.pptx).

The repository identifies the team as a winner. The [Galgotias robotics club post](https://www.linkedin.com/posts/robotics-club-galgotias-university-greater-noida_sih2025-sih2024-smartindiahackathon-activity-7405847542690742272-59c5) also reports the team's SIH 2025 win. This is team and institutional reporting, not an independently inspected official result certificate.

The reference deck was downloaded and imported. Its technical and feasibility slides were visually inspected. Useful patterns adopted: six-part section order, separate technical approach, concrete prototype evidence, and explicit risk-response pairing. Its text, images, unrelated metrics and team identifiers were not reused. This reference does not establish that its layout caused the competition result.

## Content sources

- [Official eSAKSHI dashboard](https://mplads.mospi.gov.in/digigov/dashboard.html): source portal for the team's exports.
- [PIB, 6 March 2026](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2235932): current digital monitoring context and public dashboard scope.
- [PIB, 6 August 2025](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2153066): existing end-to-end monitoring and review processes.
- [Detection rules](../detection-rules.md): documented 174 groups referencing 1,281 source records, seven matching fields, limitations and disabled peer-cost calibration rule.
- [Pitch preparation](sih26102-pitch-and-judge-preparation.md): 16,000 sanctioned-work records screened and defensible judge answers.
- [Architecture](../architecture.md) and [execution flow](../flow.md): implementation and persistence.

These are documented snapshot measurements, not a new database run. Records and groups are different units. Neither fraud detection accuracy nor financial savings have been established.

## Design sources and choices

- [Microsoft presentation guidance](https://support.microsoft.com/en-us/powerpoint/tips-for-creating-and-delivering-an-effective-presentation): legible sans-serif typography and short text.
- [Microsoft accessible presentations](https://support.microsoft.com/en-us/accessibility/powerpoint/make-your-powerpoint-presentations-accessible-to-people-with-disabilities): clear titles, meaningful reading order, image descriptions and text labels.
- [Historical SIH 2024 template, college-hosted copy](https://www.cmrit.ac.in/wp-content/uploads/2024/10/SIH2024_IDEA_Presentation_Format.pdf): six-slide sequence. Confirm current submission requirements with the SPOC.

Selected design: 16:9, Arial, navy and teal, flat layouts, large headings and labelled numbers. No fabricated charts or comparisons. A native flow diagram explains the processing sequence, and a native table pairs each risk with a response.

## Verification and remaining work

All six final slides were rendered and visually inspected. Package integrity, six-slide count, geometry, Arial policy, native table presence and re-import checks passed. The file was not opened in desktop PowerPoint. Application tests were not rerun because application code did not change.

The dependency-loading tool named by the presentation skill was unavailable. The matching installed bundled runtime was located locally and used without adding dependencies. Ponytail kept the authoring to a single build script using existing packages. Temporary sources and validation records remain private under `.tmp/sih-pitch/`.

Before submission: upload and reconcile the old deck, add verified team and institution details, confirm the applicable SIH template, test the demo with authorised credentials and review the PPTX in PowerPoint. Generated output is ignored by the repository's existing Git rules and has not been pushed.
