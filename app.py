import io
import json
import base64
from datetime import date, datetime

import streamlit as st
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether

st.set_page_config(
    page_title="Site Defect Report",
    page_icon="🔎",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Mobile-first styling
st.markdown(
    """
    <style>
      .block-container {max-width: 760px; padding-top: 0.75rem; padding-bottom: 5rem;}
      h1 {font-size: 1.65rem !important; line-height: 1.15 !important;}
      h2, h3 {line-height: 1.2 !important;}
      div[data-testid="stButton"] > button,
      div[data-testid="stDownloadButton"] > button,
      div[data-testid="stFormSubmitButton"] > button {
          min-height: 3.2rem;
          font-size: 1rem;
          font-weight: 700;
          border-radius: 12px;
          width: 100%;
      }
      div[data-testid="stTextInput"] input,
      div[data-testid="stTextArea"] textarea,
      div[data-baseweb="select"] > div {
          font-size: 16px !important;
      }
      div[data-testid="stCameraInput"] button {min-height: 3rem;}
      .site-card {
          border: 1px solid rgba(128,128,128,.28);
          border-radius: 14px;
          padding: 0.85rem 1rem;
          margin: 0.45rem 0 0.8rem 0;
      }
      .muted {opacity: .72; font-size: .92rem;}
      @media (max-width: 600px) {
        .block-container {padding-left: 0.75rem; padding-right: 0.75rem;}
        h1 {font-size: 1.5rem !important;}
      }
    </style>
    """,
    unsafe_allow_html=True,
)

if "findings" not in st.session_state:
    st.session_state.findings = []

# V1.1.1 hotfix: restore widget-backed state before the widgets are instantiated.
apply_pending_draft_restore()


def clean(value):
    return (value or "").strip()


def image_to_jpeg_bytes(uploaded_file):
    uploaded_file.seek(0)
    img = PILImage.open(uploaded_file)
    if img.mode in ("RGBA", "LA", "P"):
        if img.mode == "P":
            img = img.convert("RGBA")
        bg = PILImage.new("RGB", img.size, "white")
        if "A" in img.getbands():
            bg.paste(img, mask=img.getchannel("A"))
        else:
            bg.paste(img)
        img = bg
    else:
        img = img.convert("RGB")
    img.thumbnail((1800, 1800))
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=88, optimize=True)
    return out.getvalue()



def serialize_draft():
    """Create a portable JSON draft including finding photos."""
    payload = {
        "version": "1.1",
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "inspection": {
            "client": st.session_state.get("client", ""),
            "site": st.session_state.get("site", ""),
            "equipment": st.session_state.get("equipment", ""),
            "equipment_id": st.session_state.get("equipment_id", ""),
            "inspection_date": st.session_state.get("inspection_date", date.today()).isoformat(),
            "inspector": st.session_state.get("inspector", ""),
            "report_ref": st.session_state.get("report_ref", ""),
            "inspection_type": st.session_state.get("inspection_type", "Visual condition inspection"),
            "scope": st.session_state.get("scope", ""),
        },
        "findings": [],
    }
    for finding in st.session_state.findings:
        item = dict(finding)
        raw = item.pop("image_bytes", None)
        item["image_b64"] = base64.b64encode(raw).decode("ascii") if raw else None
        payload["findings"].append(item)
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def queue_restore_draft(uploaded_file):
    """Validate a V1.1 draft and queue it for restoration before widgets are created."""
    uploaded_file.seek(0)
    payload = json.loads(uploaded_file.read().decode("utf-8"))
    if str(payload.get("version")) != "1.1":
        raise ValueError("Unsupported draft version.")
    st.session_state["_pending_draft_restore"] = payload


def apply_pending_draft_restore():
    """Apply queued draft data early in a fresh rerun, before keyed widgets are instantiated."""
    payload = st.session_state.pop("_pending_draft_restore", None)
    if payload is None:
        return

    inspection = payload.get("inspection", {})
    for key in ("client", "site", "equipment", "equipment_id", "inspector",
                "report_ref", "inspection_type", "scope"):
        st.session_state[key] = inspection.get(key, "")

    date_text = inspection.get("inspection_date")
    st.session_state["inspection_date"] = (
        date.fromisoformat(date_text) if date_text else date.today()
    )

    restored = []
    for finding in payload.get("findings", []):
        item = dict(finding)
        encoded = item.pop("image_b64", None)
        item["image_bytes"] = base64.b64decode(encoded) if encoded else None
        restored.append(item)

    st.session_state.findings = restored
    st.session_state["draft_saved_at"] = payload.get("saved_at", "")
    st.session_state["_draft_restore_success"] = True


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.drawString(18 * mm, 10 * mm, "Inspection Defect Report")
    canvas.drawRightString(192 * mm, 10 * mm, f"Page {doc.page}")
    canvas.restoreState()


def build_pdf(report, findings):
    output = io.BytesIO()
    doc = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=15 * mm,
        bottomMargin=18 * mm,
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ReportTitleMobile", parent=styles["Title"], fontName="Helvetica-Bold",
        fontSize=18, leading=22, alignment=TA_CENTER, spaceAfter=12,
    ))
    styles.add(ParagraphStyle(
        name="FindingTitleMobile", parent=styles["Heading2"], fontName="Helvetica-Bold",
        fontSize=12, leading=15, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="SmallMobile", parent=styles["BodyText"], fontSize=8.5, leading=11,
    ))

    story = [Paragraph("INSPECTION DEFECT REPORT", styles["ReportTitleMobile"]), Spacer(1, 3 * mm)]
    details = [
        ["Client", report["client"], "Inspection Date", report["inspection_date"]],
        ["Site / Location", report["site"], "Inspector", report["inspector"]],
        ["Equipment", report["equipment"], "Equipment ID", report["equipment_id"]],
        ["Report Ref.", report["report_ref"], "Inspection Type", report["inspection_type"]],
    ]
    t = Table(details, colWidths=[30*mm, 58*mm, 32*mm, 58*mm])
    t.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#F0F0F0")),
        ("BACKGROUND", (2,0), (2,-1), colors.HexColor("#F0F0F0")),
        ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME", (2,0), (2,-1), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 5),
        ("RIGHTPADDING", (0,0), (-1,-1), 5),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    story += [t, Spacer(1, 6 * mm)]

    if report["scope"]:
        story += [
            Paragraph("<b>Scope / General Notes</b>", styles["Heading3"]),
            Paragraph(report["scope"].replace("\n", "<br/>"), styles["BodyText"]),
            Spacer(1, 5 * mm),
        ]

    story += [Paragraph(f"<b>Total Findings: {len(findings)}</b>", styles["Heading3"]), Spacer(1, 3 * mm)]

    for no, finding in enumerate(findings, start=1):
        blocks = [Paragraph(
            f"Finding {no:02d} — {finding['component'] or 'Unspecified component'}",
            styles["FindingTitleMobile"],
        )]
        meta = [
            ["Location", finding["location"], "Severity", finding["severity"]],
            ["Status", finding["status"], "Reference", finding["reference"]],
        ]
        mt = Table(meta, colWidths=[23*mm, 65*mm, 23*mm, 67*mm])
        mt.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 0.4, colors.grey),
            ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#F5F5F5")),
            ("BACKGROUND", (2,0), (2,-1), colors.HexColor("#F5F5F5")),
            ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
            ("FONTNAME", (2,0), (2,-1), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 8.5),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
        ]))
        blocks += [mt, Spacer(1, 3 * mm)]
        blocks += [
            Paragraph("<b>Observation</b>", styles["SmallMobile"]),
            Paragraph(finding["observation"].replace("\n", "<br/>"), styles["BodyText"]),
            Spacer(1, 2 * mm),
            Paragraph("<b>Recommendation</b>", styles["SmallMobile"]),
            Paragraph((finding["recommendation"] or "-").replace("\n", "<br/>"), styles["BodyText"]),
            Spacer(1, 3 * mm),
        ]
        if finding.get("image_bytes"):
            blocks.append(Image(io.BytesIO(finding["image_bytes"]), width=150*mm, height=95*mm, kind="proportional"))
            if finding.get("photo_caption"):
                blocks.append(Paragraph(f"<i>{finding['photo_caption']}</i>", styles["SmallMobile"]))
        blocks.append(Spacer(1, 7 * mm))
        story.append(KeepTogether(blocks))

    if not findings:
        story.append(Paragraph("No findings recorded.", styles["BodyText"]))

    story += [
        Spacer(1, 8 * mm),
        Paragraph("<b>Inspector Declaration</b>", styles["Heading3"]),
        Paragraph(
            "The observations in this report reflect the visible condition at the time of inspection "
            "and are subject to the stated inspection scope and limitations.",
            styles["SmallMobile"],
        ),
    ]
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    output.seek(0)
    return output


st.title("🔎 Site Defect Report")
if st.session_state.pop("_draft_restore_success", False):
    st.success("Draft restored successfully — inspection details, findings and photos have been recovered.")
st.markdown('<div class="muted">Mobile-first V1.1.1 • capture photo → record finding → save draft → generate PDF</div>', unsafe_allow_html=True)

with st.expander("📋 Inspection details", expanded=not bool(st.session_state.findings)):
    client = st.text_input("Client", key="client")
    site = st.text_input("Site / location", key="site")
    equipment = st.text_input("Equipment", placeholder="Passenger Lift / Overhead Crane", key="equipment")
    equipment_id = st.text_input("Equipment ID / Asset No.", key="equipment_id")
    inspection_date = st.date_input("Inspection date", value=date.today(), key="inspection_date")
    inspector = st.text_input("Inspector", key="inspector")
    report_ref = st.text_input("Report reference", key="report_ref")
    inspection_type = st.text_input("Inspection type", value="Visual condition inspection", key="inspection_type")
    scope = st.text_area("Scope / general notes", height=90, key="scope")

if equipment or equipment_id or site:
    st.markdown(
        f'<div class="site-card"><b>{clean(equipment) or "Equipment not set"}</b><br>'
        f'<span class="muted">{clean(equipment_id) or "No asset ID"} • {clean(site) or "Site not set"}</span></div>',
        unsafe_allow_html=True,
    )

st.subheader("📸 New finding")
with st.form("finding_form", clear_on_submit=True):
    location = st.text_input("Finding location", placeholder="Hoistway / Machine room / Boom section")
    component = st.text_input("Component", placeholder="Suspension belt / Wire rope / Guardrail")
    severity = st.selectbox("Severity", ["Observation", "Minor", "Major", "Critical"])
    status = st.selectbox("Action status", ["Open", "Monitor", "Rectification required", "Closed"])

    st.markdown("**Photo**")
    camera_photo = st.camera_input("Take photo", label_visibility="collapsed")
    uploaded_photo = st.file_uploader(
        "Or choose an existing photo",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=False,
    )

    observation = st.text_area(
        "Observation / finding *",
        height=120,
        placeholder="Describe what was observed. Keep it factual and measurable where possible.",
    )
    recommendation = st.text_area(
        "Recommendation",
        height=100,
        placeholder="Recommended action / further assessment / rectification.",
    )
    reference = st.text_input("Standard / clause / OEM reference (optional)")
    photo_caption = st.text_input("Photo caption (optional)")

    submitted = st.form_submit_button("➕ SAVE FINDING", use_container_width=True)
    if submitted:
        if not clean(observation):
            st.error("Observation / finding is required.")
        else:
            source_photo = camera_photo if camera_photo is not None else uploaded_photo
            image_bytes = image_to_jpeg_bytes(source_photo) if source_photo is not None else None
            st.session_state.findings.append({
                "location": clean(location),
                "component": clean(component),
                "severity": severity,
                "status": status,
                "reference": clean(reference),
                "observation": clean(observation),
                "recommendation": clean(recommendation),
                "photo_caption": clean(photo_caption),
                "image_bytes": image_bytes,
            })
            st.success(f"Finding {len(st.session_state.findings):02d} saved.")

st.subheader(f"🧾 Saved findings ({len(st.session_state.findings)})")
if not st.session_state.findings:
    st.info("No finding saved yet. Add your first finding above.")
else:
    for i, item in enumerate(st.session_state.findings):
        title = f"#{i+1:02d} • {item['component'] or 'Unspecified component'} • {item['severity']}"
        with st.expander(title, expanded=(i == len(st.session_state.findings)-1)):
            if item.get("image_bytes"):
                st.image(item["image_bytes"], use_container_width=True)
            st.markdown(f"**Location:** {item['location'] or '-'}")
            st.markdown(f"**Status:** {item['status']}")
            st.markdown("**Observation**")
            st.write(item["observation"])
            st.markdown("**Recommendation**")
            st.write(item["recommendation"] or "-")
            if item["reference"]:
                st.markdown(f"**Reference:** {item['reference']}")
            if st.form(f"delete_form_{i}", clear_on_submit=False).form_submit_button("🗑️ Delete this finding"):
                st.session_state.findings.pop(i)
                st.rerun()


st.divider()
st.subheader("💾 Persistent draft")
st.caption(
    "Save a portable draft to your phone. It includes inspection details, findings and compressed photos. "
    "After a browser refresh or Streamlit session restart, upload this JSON file to restore the inspection."
)

draft_bytes = serialize_draft()
draft_name_base = clean(st.session_state.get("report_ref", "")) or clean(
    st.session_state.get("equipment_id", "")
) or "inspection_draft"
draft_name_base = "".join(c if c.isalnum() or c in "-_" else "_" for c in draft_name_base)

st.download_button(
    "💾 SAVE DRAFT TO PHONE",
    data=draft_bytes,
    file_name=f"{draft_name_base}.inspection.json",
    mime="application/json",
    use_container_width=True,
)
st.caption("Save the draft after every few findings, especially before moving to an area with weak coverage.")

draft_upload = st.file_uploader(
    "Restore saved draft",
    type=["json"],
    key="draft_restore_file",
    help="Select a .inspection.json draft previously saved from this app.",
)
if draft_upload is not None:
    if st.button("♻️ RESTORE THIS DRAFT", use_container_width=True):
        try:
            queue_restore_draft(draft_upload)
            st.rerun()
        except Exception as exc:
            st.error(f"Could not restore draft: {exc}")

if st.session_state.get("draft_saved_at"):
    st.caption(f"Restored draft saved at: {st.session_state['draft_saved_at']}")

st.divider()
st.subheader("📄 Report")
report = {
    "client": clean(client),
    "site": clean(site),
    "equipment": clean(equipment),
    "equipment_id": clean(equipment_id),
    "inspection_date": inspection_date.strftime("%d %b %Y"),
    "inspector": clean(inspector),
    "report_ref": clean(report_ref),
    "inspection_type": clean(inspection_type),
    "scope": clean(scope),
}

if st.session_state.findings:
    pdf = build_pdf(report, st.session_state.findings)
    filename_base = clean(report_ref) or clean(equipment_id) or "inspection_defect_report"
    filename_base = "".join(c if c.isalnum() or c in "-_" else "_" for c in filename_base)
    st.download_button(
        "📄 GENERATE & DOWNLOAD PDF",
        data=pdf,
        file_name=f"{filename_base}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )
else:
    st.warning("Add at least one finding before generating the PDF.")

with st.expander("⚙️ Session controls"):
    st.caption("Reset removes findings from the current Streamlit session. Saved JSON draft files on your phone are not deleted.")
    if st.button("Reset all findings", use_container_width=True):
        st.session_state.findings = []
        st.rerun()

st.caption(
    "Engineering safeguard: the app does not invent acceptance criteria or automatically declare equipment safe/unsafe. "
    "Applicable standards, clauses and acceptance decisions remain under the inspector's control."
)
