# Site Defect Report — Mobile-first MVP v1

A mobile-first Streamlit app for inspection engineers to capture defect photos on site, record findings, and generate a PDF report.

## Mobile-first improvements

- Narrow, single-column layout for phones
- Large touch-friendly action buttons
- Native phone camera capture using `st.camera_input`
- Existing photo upload as a fallback
- Inspection details kept in a collapsible section
- Equipment/site summary card remains visible in the workflow
- Saved findings displayed as compact expandable cards
- Phone-friendly image preview
- PDF generation remains available from the same browser session
- Deployment-ready Streamlit configuration included

## Current workflow

1. Open **Inspection details** and enter job information.
2. Under **New finding**, enter location and component.
3. Select severity and status.
4. Tap **Take photo** to use the phone camera, or choose an existing image.
5. Enter the factual observation and recommendation.
6. Tap **SAVE FINDING**.
7. Repeat for additional findings.
8. Tap **GENERATE & DOWNLOAD PDF**.

## Run locally

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

macOS / Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Important: using it on a phone at site

The app is now mobile-friendly, but `localhost:8501` only opens on the computer running Streamlit. For normal site use from a phone anywhere, deploy the project to an internet-accessible Streamlit host or your own server. Once deployed, the inspector simply opens the HTTPS URL in the phone browser.

Phone camera access normally requires a secure HTTPS deployment and browser permission for the camera.

## Engineering safeguard

The application must not automatically invent acceptance criteria, clauses or regulatory requirements. Acceptance decisions remain traceable to the correct standard, edition, clause, OEM requirement and inspection scope.
