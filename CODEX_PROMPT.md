
You are working on an Inspection Defect & Photo Report Generator for a professional lifting-equipment inspection engineer.

Current stack:
- Python
- Streamlit
- ReportLab
- Pillow

Main workflow:
1. Inspector enters report information.
2. Inspector records multiple findings.
3. Each finding contains location, component, severity, status, optional standard/OEM reference, observation, recommendation, photo and caption.
4. App generates a professional PDF defect report.

Engineering rules:
- Never invent an acceptance criterion, standard clause, or regulatory requirement.
- A standard reference entered by the inspector must be treated as inspector-supplied data.
- Do not automatically mark equipment PASS/FAIL based only on AI-generated wording.
- Keep calculations and engineering acceptance logic auditable and traceable.
- Preserve original inspection photographs; image compression should only affect the PDF copy.
- The UI must work well on a phone as well as desktop.

Your next task:
Upgrade the current MVP without breaking existing features.

Priority backlog:
1. Allow editing an existing finding.
2. Allow more than one photo per finding.
3. Allow drag/reorder or reliable manual reorder of findings.
4. Add company logo and report header/footer configuration.
5. Add inspector signature image.
6. Add Save Project / Open Project using JSON plus a folder containing photos.
7. Add reusable observation/recommendation templates.
8. Add a report preview page before final PDF generation.
9. Add validation so report reference, equipment and inspector can optionally be required via settings.
10. Add automated tests for the PDF-generation functions.

Before changing code:
- Inspect the existing files.
- Explain the proposed file structure.
- Make changes incrementally.
- Run the app or tests after meaningful changes.
- Avoid unnecessary framework changes.
