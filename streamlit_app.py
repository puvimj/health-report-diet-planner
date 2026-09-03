import os
import io
import re
import base64
import shutil
from datetime import datetime, date
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Application modules
from app.database import SessionLocal, UPLOADS_DIR, engine, Base
from app.models import Report, Biomarker, DietPlan
from app.extractor import parse_medical_report, extract_text_from_pdf
from pypdf import PdfReader, PdfWriter
from app.diet_engine import create_diet_plan, analyze_health_findings
from app.main import strip_patient_title, get_canonical_patient_key, sync_and_upgrade_reports_data

# Ensure tables are created in SQLite
Base.metadata.create_all(bind=engine)

# Static serving configuration for Streamlit Cloud & local
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
STATIC_REPORTS_DIR = os.path.join(STATIC_DIR, "reports")
os.makedirs(STATIC_REPORTS_DIR, exist_ok=True)

# Pre-populate static reports from data/uploads if present
if os.path.exists(UPLOADS_DIR):
    for up_f in os.listdir(UPLOADS_DIR):
        if up_f.lower().endswith(".pdf") and not up_f.startswith("temp_"):
            clean_name = up_f
            if len(up_f) > 15 and up_f[:14].isdigit() and up_f[14] == "_":
                clean_name = up_f[15:]
            tgt = os.path.join(STATIC_REPORTS_DIR, clean_name)
            src = os.path.join(UPLOADS_DIR, up_f)
            if not os.path.exists(tgt) or os.path.getsize(tgt) != os.path.getsize(src):
                try:
                    shutil.copy2(src, tgt)
                except Exception:
                    pass

def sync_file_to_static(file_p: str, orig_filename: str) -> str:
    """Copies the report to the Streamlit static serving directory and returns the relative URL."""
    clean_name = re.sub(r'[^a-zA-Z0-9_\.-]', '_', orig_filename)
    if not clean_name.lower().endswith(".pdf"):
        clean_name += ".pdf"
    clean_lower = clean_name.lower()

    # 1. Check if an existing file matches in STATIC_REPORTS_DIR
    if os.path.exists(STATIC_REPORTS_DIR):
        for f in os.listdir(STATIC_REPORTS_DIR):
            f_lower = f.lower()
            if f_lower == clean_lower or f_lower.endswith(clean_lower) or clean_lower.endswith(f_lower):
                return f"/app/static/reports/{f}"

    # 2. If not found, copy from file_p
    if not file_p or not os.path.exists(file_p):
        return ""

    target_path = os.path.join(STATIC_REPORTS_DIR, clean_name)
    try:
        if not os.path.exists(target_path) or os.path.getsize(target_path) != os.path.getsize(file_p):
            shutil.copy2(file_p, target_path)
        return f"/app/static/reports/{clean_name}"
    except Exception:
        return ""

# -------------------------------------------------------------
# Page Configuration & CSS
# -------------------------------------------------------------

st.set_page_config(
    page_title="HealthTrack & DietRx",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="collapsed"
)

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=DM+Sans:wght@400;500;700&display=swap');

html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    font-family: 'Plus Jakarta Sans', 'DM Sans', sans-serif !important;
    background-color: #f8fafc !important;
    color: #0f172a !important;
}

.block-container {
    padding-top: 1.25rem !important;
    padding-bottom: 3rem !important;
    max-width: 1360px !important;
}

/* Header & Brand */
.header-bar {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 1.25rem 1.75rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.brand-title {
    font-size: 1.4rem;
    font-weight: 800;
    color: #0f172a;
    letter-spacing: -0.02em;
}

.brand-sub {
    font-size: 0.82rem;
    color: #64748b;
    font-weight: 500;
}

/* KPI Cards */
.kpi-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 1.15rem 1.25rem;
    box-shadow: 0 1px 2px rgba(0,0,0,0.02);
    transition: all 0.2s ease;
}
.kpi-card:hover {
    border-color: #38bdf8;
    box-shadow: 0 4px 12px rgba(0,0,0,0.04);
}
.kpi-val {
    font-size: 1.8rem;
    font-weight: 800;
    color: #0f172a;
    line-height: 1.2;
}
.kpi-lbl {
    font-size: 0.78rem;
    color: #64748b;
    font-weight: 600;
    margin-top: 2px;
}
.kpi-meta {
    font-size: 0.72rem;
    margin-top: 6px;
    font-weight: 600;
}

/* Badges */
.badge-high {
    background: #fef2f2;
    color: #dc2626;
    border: 1px solid #fecaca;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 0.72rem;
    font-weight: 700;
}
.badge-low {
    background: #eff6ff;
    color: #2563eb;
    border: 1px solid #bfdbfe;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 0.72rem;
    font-weight: 700;
}
.badge-normal {
    background: #f0fdf4;
    color: #16a34a;
    border: 1px solid #bbf7d0;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 0.72rem;
    font-weight: 700;
}

/* Patient Card */
.patient-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 1.25rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    margin-bottom: 1rem;
}

/* Panel Header */
.panel-header {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 0.75rem 1.25rem;
    margin-top: 1rem;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# -------------------------------------------------------------
# Database Session & Data Loading
# -------------------------------------------------------------

def get_db():
    return SessionLocal()

# Perform synchronization once per app session to avoid disk overhead on reruns
if "db_synced" not in st.session_state:
    with get_db() as sync_db:
        try:
            sync_and_upgrade_reports_data(sync_db)
            st.session_state.db_synced = True
        except Exception as e:
            st.session_state.db_synced = True

def is_meaningful_clinical_note(note: str) -> bool:
    """Checks whether text is a genuine clinical physician note vs lab methodology boilerplate."""
    if not note or not str(note).strip():
        return False
    lower = str(note).lower()
    boilerplate = [
        "international council for standardization",
        "differential leucocyte counts",
        "edta whole blood",
        "per unit volume",
        "test conducted on",
        "laboratory investigations are only a tool",
        "standardization in hematology",
        "methodology",
        "sample type",
        "specimen:"
    ]
    return not any(b in lower for b in boilerplate)

def render_dataframe(df, **kwargs):
    """Renders a dataframe using width='stretch' to eliminate Streamlit 2025 deprecation warnings."""
    try:
        st.dataframe(df, width="stretch", **kwargs)
    except TypeError:
        st.dataframe(df, use_container_width=True, **kwargs)

def render_plotly(fig, **kwargs):
    """Renders a plotly chart using width='stretch' to eliminate Streamlit 2025 deprecation warnings."""
    try:
        st.plotly_chart(fig, width="stretch", **kwargs)
    except TypeError:
        st.plotly_chart(fig, use_container_width=True, **kwargs)

def get_embeddable_pdf_bytes(file_bytes: bytes, max_pages: int = 10):
    """
    If PDF is <= 2MB, returns original bytes.
    If PDF is > 2MB (which Chrome blocks in data: URIs), creates a fast in-memory
    preview of the primary clinical checkup pages (< 1MB) so Chrome renders it without failing.
    Returns: (pdf_bytes_to_render, is_preview, pages_shown, total_pages)
    """
    if len(file_bytes) <= 2 * 1024 * 1024:
        return file_bytes, False, 0, 0
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        total_pages = len(reader.pages)
        pages_to_take = min(total_pages, max_pages)
        writer = PdfWriter()
        for p in reader.pages[:pages_to_take]:
            writer.add_page(p)
        buf = io.BytesIO()
        writer.write(buf)
        res = buf.getvalue()
        if len(res) <= 2 * 1024 * 1024:
            return res, True, pages_to_take, total_pages
        # Further reduce to first 5 pages if needed
        writer2 = PdfWriter()
        for p in reader.pages[:5]:
            writer2.add_page(p)
        buf2 = io.BytesIO()
        writer2.write(buf2)
        return buf2.getvalue(), True, 5, total_pages
    except Exception:
        return file_bytes, False, 0, 0

def render_pdf_viewer(file_bytes: bytes, filename: str, file_path: str = ""):
    """Renders PDF using static HTTP URL (avoids Chrome data-URI iframe blocks) with direct new tab and download options."""
    static_url = sync_file_to_static(file_path, filename) if file_path else ""

    if static_url:
        st.markdown(f'''
        <div style="display: flex; gap: 0.75rem; align-items: center; margin-top: 0.5rem; margin-bottom: 0.5rem;">
            <a href="{static_url}" target="_blank" style="display: inline-flex; align-items: center; gap: 0.4rem; background-color: #0284c7; color: white; padding: 0.45rem 1.1rem; font-size: 0.85rem; font-weight: 600; text-decoration: none; border-radius: 6px;">
                🔍 Open Full PDF in New Tab
            </a>
        </div>
        <div style="margin-top: 0.25rem;">
            <iframe src="{static_url}#toolbar=1" width="100%" height="750px" type="application/pdf" style="border: 1px solid #cbd5e1; border-radius: 8px; background: white;">
                <p style="padding: 1rem; color: #64748b;">If your browser does not render the in-line frame, please use the <strong>Open Full PDF in New Tab</strong> or <strong>Download Original File</strong> button above.</p>
            </iframe>
        </div>
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px 12px; margin-top: 6px; font-size: 12px; color: #64748b;">
            📱 <strong>Mobile Note:</strong> Mobile browsers (Android Chrome & iPhone Safari) do not render PDFs inside web frames. Tap <strong>Open Full PDF in New Tab</strong> or <strong>Download Original File</strong> above to open the complete document on your phone.
        </div>
        ''', unsafe_allow_html=True)
    else:
        render_bytes, is_preview, p_count, total_count = get_embeddable_pdf_bytes(file_bytes)
        base64_pdf = base64.b64encode(render_bytes).decode("utf-8")
        if is_preview:
            st.caption(f"ℹ️ *Showing in-line document preview of the primary clinical checkup pages (Pages 1 to {p_count} of {total_count}). Use the primary button above to download/open the full {round(len(file_bytes)/(1024*1024), 1)} MB scan file.*")
        st.markdown(f'''
        <div style="margin-top: 0.5rem;">
            <iframe src="data:application/pdf;base64,{base64_pdf}#toolbar=1" width="100%" height="750px" type="application/pdf" style="border: 1px solid #cbd5e1; border-radius: 8px; background: white;"></iframe>
        </div>
        ''', unsafe_allow_html=True)

def resolve_report_file_path(r: dict) -> str:
    """Finds the actual file path on disk for a report, cross-platform (Windows & Linux Streamlit Cloud)."""
    file_p = r.get("file_path", "")
    if file_p and os.path.exists(file_p):
        return file_p

    orig_name = r.get("original_filename", "")
    orig_lower = orig_name.lower().strip() if orig_name else ""

    # Potential search folders on local Windows or Streamlit Cloud Linux containers
    base_dir = os.path.dirname(os.path.abspath(__file__))
    search_dirs = [
        UPLOADS_DIR,
        os.path.join(base_dir, "data", "uploads"),
        os.path.join(base_dir, "data"),
        os.path.join(base_dir, "uploads"),
        base_dir
    ]

    for s_dir in search_dirs:
        if not (s_dir and os.path.exists(s_dir)):
            continue

        # 1. Exact match
        if orig_name:
            exact = os.path.join(s_dir, orig_name)
            if os.path.exists(exact) and os.path.isfile(exact):
                return exact

        # 2. Case-insensitive scan
        all_files = [os.path.join(s_dir, f) for f in os.listdir(s_dir) if os.path.isfile(os.path.join(s_dir, f))]
        all_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)

        for f in all_files:
            bname = os.path.basename(f).lower()
            if orig_lower and (bname.endswith(orig_lower) or orig_lower.endswith(bname)):
                return f

        pname_clean = strip_patient_title(r.get("patient_name", "")).lower()
        pname_token = pname_clean.split()[0] if pname_clean else ""
        year_str = str(r.get("report_year", ""))
        for f in all_files:
            bname = os.path.basename(f).lower()
            if pname_token and pname_token in bname and year_str and year_str in bname:
                return f

    return ""

def fetch_all_reports():
    with get_db() as db:
        # Load reports and eager-load biomarkers
        reps = db.query(Report).order_by(Report.report_date.asc()).all()
        data = []
        for r in reps:
            # Heal file_path if missing or moved
            if not r.file_path or not os.path.exists(r.file_path):
                r_dict = {"file_path": r.file_path, "original_filename": r.original_filename, "patient_name": r.patient_name, "report_year": r.report_year}
                found_p = resolve_report_file_path(r_dict)
                if found_p:
                    r.file_path = found_p
                    db.commit()

            b_list = [{
                "id": b.id,
                "category": b.category,
                "test_name": b.test_name,
                "result_value": b.result_value,
                "unit": b.unit,
                "reference_min": b.reference_min,
                "reference_max": b.reference_max,
                "status": b.status,
                "clinical_summary": b.clinical_summary
            } for b in r.biomarkers]
            data.append({
                "id": r.id,
                "patient_name": r.patient_name,
                "report_date": r.report_date,
                "report_year": r.report_year,
                "hospital_lab_name": r.hospital_lab_name,
                "original_filename": r.original_filename,
                "file_path": r.file_path,
                "notes": r.notes,
                "biomarkers": b_list
            })
        return data

reports = fetch_all_reports()

# Build Canonical Patient Groups
patients_map = {}
for r in reports:
    k = get_canonical_patient_key(r["patient_name"])
    title_free = strip_patient_title(r["patient_name"])
    if k not in patients_map:
        patients_map[k] = {"key": k, "display_name": title_free, "reports": []}
    else:
        if len(title_free) > len(patients_map[k]["display_name"]):
            patients_map[k]["display_name"] = title_free
    patients_map[k]["reports"].append(r)

family_list = list(patients_map.values())

# -------------------------------------------------------------
# Brand Header
# -------------------------------------------------------------

st.markdown("""
<div class="header-bar">
    <div>
        <div class="brand-title">🩺 HealthTrack <span style="color: #0d9488;">& DietRx</span></div>
        <div class="brand-sub">Multi-Patient Medical Archive, Multi-Year Biomarker Trajectory & Clinical Diet Planner</div>
    </div>
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# Navigation Tabs
# -------------------------------------------------------------

tab_dashboard, tab_archive, tab_upload, tab_diet = st.tabs([
    "📊 Dashboard & Trends",
    "📁 Reports Archive",
    "☁️ Upload Report",
    "🥗 Clinical Diet Planner"
])

# =============================================================
# TAB 1: DASHBOARD, TRAJECTORY & EXTRACTED BIOMARKERS TABLE
# =============================================================

with tab_dashboard:
    # 1. Patient Selector Scope
    st.markdown("##### 👥 Select Family Member Scope")
    patient_options = ["All Family Members"] + [p["display_name"] for p in family_list]
    
    if "selected_patient_scope" not in st.session_state:
        st.session_state.selected_patient_scope = "All Family Members"

    selected_scope = st.radio(
        "Family Scope:",
        options=patient_options,
        horizontal=True,
        key="patient_scope_radio",
        label_visibility="collapsed"
    )
    st.session_state.selected_patient_scope = selected_scope

    is_all = (selected_scope == "All Family Members")
    
    # Filter reports for active patient
    if is_all:
        active_reports = reports
        active_patient_title = "All Family Members"
        active_canonical_key = None
    else:
        active_patient_title = selected_scope
        active_canonical_key = get_canonical_patient_key(selected_scope)
        active_reports = [r for r in reports if get_canonical_patient_key(r["patient_name"]) == active_canonical_key]

    # Calculate KPIs
    total_reps = len(active_reports)
    distinct_years = len(set(r["report_year"] for r in active_reports if r.get("report_year")))
    years_str = ", ".join(str(y) for y in sorted(list(set(r["report_year"] for r in active_reports if r.get("report_year"))))) or "None"
    
    total_tests = sum(len(r["biomarkers"]) for r in active_reports)
    abnormal_count = sum(sum(1 for b in r["biomarkers"] if b["status"] in ("HIGH", "LOW")) for r in active_reports)
    latest_rep = max(active_reports, key=lambda r: r["report_date"]) if active_reports else None

    # Scope Header Badge
    st.markdown(f"""
    <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 0.5rem; margin-bottom: 0.75rem;">
        <span style="font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: #64748b; letter-spacing: 0.05em;">Key Health Indicators (KPIs)</span>
        <span style="font-size: 0.75rem; font-weight: 700; background: #f0f9ff; color: #0369a1; border: 1px solid #bae6fd; padding: 3px 12px; border-radius: 9999px;">
            {'👥 Scope: All Family Members (' + str(total_reps) + ' checkups)' if is_all else '👤 Patient: ' + active_patient_title}
        </span>
    </div>
    """, unsafe_allow_html=True)

    # Render 4 KPI Cards
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-val">{total_reps}</div>
            <div class="kpi-lbl">Checkup Reports Saved</div>
            <div class="kpi-meta" style="color: #0284c7;">
                {active_patient_title}: Latest {latest_rep['report_date'] if latest_rep else 'N/A'}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with kpi2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-val">{distinct_years}</div>
            <div class="kpi-lbl">Years of Health Tracked</div>
            <div class="kpi-meta" style="color: #4f46e5;">
                {active_patient_title}: {years_str}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with kpi3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-val">{total_tests}</div>
            <div class="kpi-lbl">Lab Biomarkers Stored</div>
            <div class="kpi-meta" style="color: #0d9488;">
                {active_patient_title}: Monitored Lab Parameters
            </div>
        </div>
        """, unsafe_allow_html=True)

    with kpi4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-val" style="color: #dc2626;">{abnormal_count}</div>
            <div class="kpi-lbl">Active Health Flags</div>
            <div class="kpi-meta" style="color: #dc2626;">
                {active_patient_title}: {abnormal_count} Attention Needed
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)

    # 2. Family Overview Cards
    if is_all and family_list:
        st.markdown("##### 🏡 Family Health Overview")
        card_cols = st.columns(min(len(family_list), 3))
        for i, fam in enumerate(family_list):
            p_reps = fam["reports"]
            p_latest = p_reps[-1]
            p_years = ", ".join(str(y) for y in sorted(list(set(r["report_year"] for r in p_reps if r.get("report_year")))))
            p_ab_count = sum(1 for b in p_latest["biomarkers"] if b["status"] in ("HIGH", "LOW"))
            badge_cls = "badge-high" if p_ab_count > 0 else "badge-normal"
            badge_txt = f"{p_ab_count} Flags Attention Needed" if p_ab_count > 0 else "All Key Markers Normal"

            with card_cols[i % len(card_cols)]:
                st.markdown(f"""
                <div class="patient-card">
                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.5rem;">
                        <div>
                            <strong style="font-size: 1rem; color: #0f172a;">{fam['display_name']}</strong>
                            <div style="font-size: 0.75rem; color: #64748b;">Latest: {p_latest['report_year']} • {p_latest['hospital_lab_name']}</div>
                        </div>
                        <span class="{badge_cls}">{badge_txt}</span>
                    </div>
                    <div style="font-size: 0.8rem; color: #334155; margin-top: 0.5rem; background: #f8fafc; padding: 0.5rem; border-radius: 8px;">
                        <div><strong>Total Checkups:</strong> {len(p_reps)} Records</div>
                        <div><strong>Timeline:</strong> {p_years}</div>
                        <div><strong>Total Tests:</strong> {sum(len(r['biomarkers']) for r in p_reps)} Biomarkers</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    # 3. Multi-Year Biomarker Trajectory Chart
    st.markdown("##### 📈 Multi-Year Biomarker Trajectory")
    
    target_patient_name = selected_scope if not is_all else (family_list[0]["display_name"] if family_list else "")
    target_key = get_canonical_patient_key(target_patient_name)
    target_reports = [r for r in reports if get_canonical_patient_key(r["patient_name"]) == target_key]

    if not target_reports:
        st.info("No medical checkup reports available for trajectory tracking. Upload a report in the 'Upload Report' tab.")
    else:
        trends_by_test = {}
        glucose_points = []

        for r in target_reports:
            for b in r["biomarkers"]:
                name = b["test_name"]
                if name not in trends_by_test:
                    trends_by_test[name] = {
                        "test_name": name,
                        "category": b["category"],
                        "unit": b["unit"],
                        "reference_min": b["reference_min"],
                        "reference_max": b["reference_max"],
                        "points": []
                    }
                pt = {
                    "year": r["report_year"],
                    "date": r["report_date"].isoformat() if hasattr(r["report_date"], "isoformat") else str(r["report_date"]),
                    "value": b["result_value"],
                    "status": b["status"],
                    "report_id": r["id"],
                    "test_name": b["test_name"]
                }
                trends_by_test[name]["points"].append(pt)

                if "sugar" in name.lower() or "glucose" in name.lower():
                    glucose_points.append({
                        "year": r["report_year"],
                        "date": r["report_date"].isoformat() if hasattr(r["report_date"], "isoformat") else str(r["report_date"]),
                        "value": b["result_value"],
                        "status": b["status"],
                        "report_id": r["id"],
                        "test_name": b["test_name"],
                        "is_fasting": "fasting" in name.lower()
                    })

        # Harmonize Blood Glucose / Sugar across all 3 years
        if glucose_points:
            rep_map = {}
            for p in glucose_points:
                rid = p["report_id"]
                if rid not in rep_map or (p.get("is_fasting") and not rep_map[rid].get("is_fasting")):
                    rep_map[rid] = p

            sorted_pts = sorted(list(rep_map.values()), key=lambda x: x["date"])
            trends_by_test["Blood Glucose / Sugar"] = {
                "test_name": "Blood Glucose / Sugar",
                "category": "Blood Sugar / Diabetes",
                "unit": "mg/dL",
                "reference_min": 70.0,
                "reference_max": 99.0,
                "points": sorted_pts
            }

            if "Fasting Blood Sugar" in trends_by_test:
                fbs_years = {p["year"] for p in trends_by_test["Fasting Blood Sugar"]["points"]}
                for p in sorted_pts:
                    if p["year"] not in fbs_years:
                        trends_by_test["Fasting Blood Sugar"]["points"].append(dict(p))
                trends_by_test["Fasting Blood Sugar"]["points"].sort(key=lambda x: x["date"])

        pref_order = ["Blood Glucose / Sugar", "Fasting Blood Sugar", "HbA1c", "Total Cholesterol", "LDL Cholesterol", "HDL Cholesterol", "Triglycerides", "Hemoglobin", "Serum Creatinine", "TSH"]
        all_metrics = list(trends_by_test.keys())
        all_metrics.sort(key=lambda x: pref_order.index(x) if x in pref_order else 999)

        chart_col1, chart_col2 = st.columns([1, 2])
        with chart_col1:
            chosen_patient = st.selectbox(
                "Patient:",
                options=[p["display_name"] for p in family_list],
                index=[p["display_name"] for p in family_list].index(target_patient_name) if target_patient_name in [p["display_name"] for p in family_list] else 0,
                key="chart_patient_select"
            )
        with chart_col2:
            metric_labels = [f"{m} ({trends_by_test[m]['category']}) [{len(trends_by_test[m]['points'])} records]" for m in all_metrics]
            chosen_label = st.selectbox("Biomarker:", options=metric_labels, index=0, key="chart_metric_select")
            chosen_test = all_metrics[metric_labels.index(chosen_label)]

        # Render Plotly Chart
        series = trends_by_test[chosen_test]
        pts = sorted(series["points"], key=lambda x: x["date"])

        df = pd.DataFrame(pts)
        df["label"] = df.apply(lambda row: f"{row['year']} ({row['date'][5:]})", axis=1)

        fig = go.Figure()
        color_map = {"HIGH": "#ef4444", "LOW": "#3b82f6", "NORMAL": "#10b981"}
        marker_colors = [color_map.get(s, "#10b981") for s in df["status"]]

        custom_text = [
            f"<b>{row['year']}</b>: {row['value']} {series['unit']}<br>Status: <b>{row['status']}</b><br>Test: {row.get('test_name', series['test_name'])}<br>Ref: {series.get('reference_min', '—')} - {series.get('reference_max', '—')} {series['unit']}"
            for _, row in df.iterrows()
        ]

        fig.add_trace(go.Scatter(
            x=df["label"],
            y=df["value"],
            mode="lines+markers",
            name=f"{series['test_name']} ({series['unit']})",
            line=dict(color="#0284c7", width=3),
            marker=dict(size=10, color=marker_colors, line=dict(color="white", width=2)),
            hoverinfo="text",
            hovertext=custom_text
        ))

        if series.get("reference_max") is not None:
            fig.add_trace(go.Scatter(
                x=df["label"],
                y=[series["reference_max"]] * len(df),
                mode="lines",
                name=f"Max Normal ({series['reference_max']} {series['unit']})",
                line=dict(color="#ef4444", width=1.5, dash="dash")
            ))

        if series.get("reference_min") is not None:
            fig.add_trace(go.Scatter(
                x=df["label"],
                y=[series["reference_min"]] * len(df),
                mode="lines",
                name=f"Min Normal ({series['reference_min']} {series['unit']})",
                line=dict(color="#3b82f6", width=1.5, dash="dash")
            ))

        fig.update_layout(
            paper_bgcolor="white",
            plot_bgcolor="white",
            margin=dict(l=20, r=20, t=20, b=20),
            height=360,
            xaxis=dict(title="Year of Checkup", showgrid=True, gridcolor="#f1f5f9"),
            yaxis=dict(title=f"{series['test_name']} ({series['unit']})", showgrid=True, gridcolor="#f1f5f9"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        render_plotly(fig, config={"displayModeBar": False})

        latest_pt = pts[-1]
        st_badge = "badge-high" if latest_pt["status"] == "HIGH" else ("badge-low" if latest_pt["status"] == "LOW" else "badge-normal")
        sub_info = f" ({latest_pt['test_name']})" if latest_pt.get("test_name") and latest_pt["test_name"] != series["test_name"] else ""
        st.markdown(f"""
        <div style="background: white; border: 1px solid #e2e8f0; border-radius: 10px; padding: 0.6rem 1rem; font-size: 0.82rem; display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem;">
            <div>
                <span style="font-weight: 700; color: #0284c7;">👤 Patient: {chosen_patient}</span> &nbsp;|&nbsp;
                Latest reading: <strong>{latest_pt['value']} {series['unit']}</strong> in {latest_pt['year']}{sub_info}
                <span class="{st_badge}" style="margin-left: 0.5rem;">{latest_pt['status']}</span>
            </div>
            <div style="color: #64748b; font-size: 0.75rem;">
                Normal Ref: {series.get('reference_min', '—')} - {series.get('reference_max', '—')} {series['unit']}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 4. Extracted Biomarkers & Full Lab Panel (Directly on Dashboard)
    st.markdown("---")
    st.markdown("### 📋 Extracted Lab Biomarkers & Clinical Panel")
    st.caption("Inspect every extracted laboratory parameter, reference boundaries, and clinical flags across any checkup report.")

    if target_reports:
        # Selector for checkup report
        report_options = [
            f"{r['patient_name']} — Year {r['report_year']} ({r['hospital_lab_name']} • {r['report_date']}) [{len(r['biomarkers'])} tests, {sum(1 for b in r['biomarkers'] if b['status'] in ('HIGH', 'LOW'))} alerts]"
            for r in target_reports
        ]
        selected_rep_idx = st.selectbox(
            "Select Checkup Report to View Extracted Data:",
            options=range(len(target_reports)),
            format_func=lambda i: report_options[i],
            key="dash_table_report_select"
        )
        view_rep = target_reports[selected_rep_idx]

        # Summary Chips
        tot_b = len(view_rep["biomarkers"])
        hi_b = sum(1 for b in view_rep["biomarkers"] if b["status"] == "HIGH")
        lo_b = sum(1 for b in view_rep["biomarkers"] if b["status"] == "LOW")
        norm_b = sum(1 for b in view_rep["biomarkers"] if b["status"] == "NORMAL")

        c_s1, c_s2, c_s3, c_s4 = st.columns(4)
        with c_s1:
            st.metric("Total Parameters Extracted", tot_b)
        with c_s2:
            st.metric("Normal Lab Readings", norm_b)
        with c_s3:
            st.metric("Elevated (HIGH) Flags", hi_b)
        with c_s4:
            st.metric("Sub-optimal (LOW) Flags", lo_b)

        # Filter Controls
        all_cats = ["All Categories"] + sorted(list(set(b["category"] for b in view_rep["biomarkers"])))
        col_f1, col_f2, col_f3 = st.columns([1.5, 1.5, 1])
        with col_f1:
            chosen_cat = st.selectbox("Filter by Category:", options=all_cats, index=0, key="cat_filter")
        with col_f2:
            search_query = st.text_input("Search Biomarker:", placeholder="e.g. Glucose, HDL, Creatinine...", key="bio_search")
        with col_f3:
            only_abnormal = st.checkbox("⚠️ Active Flags Only", value=False, key="only_abnormal_toggle")

        # Filter list
        display_biomarkers = view_rep["biomarkers"]
        if chosen_cat != "All Categories":
            display_biomarkers = [b for b in display_biomarkers if b["category"] == chosen_cat]
        if search_query.strip():
            sq = search_query.strip().lower()
            display_biomarkers = [b for b in display_biomarkers if sq in b["test_name"].lower() or sq in b["category"].lower()]
        if only_abnormal:
            display_biomarkers = [b for b in display_biomarkers if b["status"] in ("HIGH", "LOW")]

        # Render Table
        if not display_biomarkers:
            st.info("No biomarkers matching your search or filters.")
        else:
            table_rows = []
            for b in display_biomarkers:
                min_str = f"{b['reference_min']}" if b["reference_min"] is not None else "—"
                max_str = f"{b['reference_max']}" if b["reference_max"] is not None else "—"
                ref_interval = f"{min_str} - {max_str} {b['unit']}" if min_str != "—" or max_str != "—" else "—"
                table_rows.append({
                    "Category": b["category"],
                    "Biomarker Test": b["test_name"],
                    "Result Value": f"{b['result_value']} {b['unit']}".strip(),
                    "Normal Reference Range": ref_interval,
                    "Clinical Status": f"🔴 {b['status']}" if b["status"] == "HIGH" else (f"🔵 {b['status']}" if b["status"] == "LOW" else f"🟢 {b['status']}"),
                    "Interpretation": b.get("clinical_summary") or f"{b['test_name']} is {b['status']}"
                })

            df_table = pd.DataFrame(table_rows)
            render_dataframe(df_table, hide_index=True)

        if is_meaningful_clinical_note(view_rep.get("notes")):
            st.info(f"👨‍⚕️ **Physician Clinical Assessment / Notes:** {view_rep['notes']}")

# =============================================================
# TAB 2: REPORTS ARCHIVE
# =============================================================

with tab_archive:
    st.markdown("##### 📁 Medical Checkup Reports Archive")
    st.caption("Ordered strictly by Patient Name and Year Descending. View and download the actual original medical checkup documents.")

    if not reports:
        st.info("No reports found in the archive. Upload your reports in the 'Upload Report' tab.")
    else:
        for fam in family_list:
            p_reps = sorted(fam["reports"], key=lambda r: (r["report_year"], r["report_date"]), reverse=True)
            st.markdown(f"#### 👤 {fam['display_name']} ({len(p_reps)} Checkup Reports)")

            for r in p_reps:
                ab_count = sum(1 for b in r["biomarkers"] if b["status"] in ("HIGH", "LOW"))
                with st.expander(f"📄 Year {r['report_year']} Checkup Document — {r['hospital_lab_name']} ({r['report_date']}) • [{r.get('original_filename', 'Document')}]"):
                    col_meta1, col_meta2 = st.columns(2)
                    with col_meta1:
                        st.write(f"**Patient:** {r['patient_name']}")
                        st.write(f"**Checkup Date:** {r['report_date']}")
                        st.write(f"**Hospital / Lab:** {r['hospital_lab_name']}")
                    with col_meta2:
                        st.write(f"**Original File:** `{r.get('original_filename', 'Medical_Report.pdf')}`")
                        st.write(f"**Total Biomarkers Monitored:** {len(r['biomarkers'])} parameters")
                        if is_meaningful_clinical_note(r.get("notes")):
                            st.write(f"**Physician Notes:** {r['notes']}")

                    # Locate original file on disk
                    file_p = resolve_report_file_path(r)
                    disp_filename = r.get("original_filename") or (os.path.basename(file_p) if file_p else "Medical_Report.pdf")
                    if disp_filename.startswith("temp_"):
                        disp_filename = disp_filename.split("_", 2)[-1]
                    if re.match(r"^\d{14}_", disp_filename):
                        disp_filename = disp_filename[15:]

                    if file_p and os.path.exists(file_p):
                        with open(file_p, "rb") as f_in:
                            file_bytes = f_in.read()

                        st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
                        st.download_button(
                            label=f"📥 Download / Open Original File ({disp_filename})",
                            data=file_bytes,
                            file_name=disp_filename,
                            mime="application/pdf" if file_p.lower().endswith(".pdf") else "text/plain",
                            key=f"dl_{r['id']}",
                            type="primary"
                        )

                        if file_p.lower().endswith(".pdf"):
                            render_pdf_viewer(file_bytes, disp_filename, file_p)
                        else:
                            st.text_area("Document Content", value=file_bytes.decode("utf-8", errors="ignore"), height=400, disabled=True, key=f"txt_{r['id']}")
                    else:
                        st.warning(f"Original file '{disp_filename}' was not found on local disk storage.")

# =============================================================
# TAB 3: UPLOAD REPORT & LIVE EXTRACTION REVIEW
# =============================================================

with tab_upload:
    st.markdown("##### ☁️ Upload Medical Checkup Report (PDF / Document)")
    st.caption("Upload your annual health checkup or family members' reports. The clinical engine extracts patient details, dates, and all lab parameters automatically.")

    uploaded_file = st.file_uploader("Choose PDF or Document", type=["pdf", "txt"], key="doc_uploader")

    # Preserve extracted data in session state across reruns
    if "uploaded_preview" not in st.session_state:
        st.session_state.uploaded_preview = None
    if "uploaded_filename" not in st.session_state:
        st.session_state.uploaded_filename = ""

    if uploaded_file is not None:
        if st.session_state.uploaded_filename != uploaded_file.name:
            with st.spinner("Analyzing medical document & extracting biomarkers..."):
                temp_path = os.path.join(UPLOADS_DIR, f"temp_{uploaded_file.name}")
                file_bytes = uploaded_file.getvalue()
                with open(temp_path, "wb") as f:
                    f.write(file_bytes)

                try:
                    if uploaded_file.name.lower().endswith(".pdf"):
                        extracted_text = extract_text_from_pdf(temp_path)
                    else:
                        extracted_text = file_bytes.decode("utf-8", errors="ignore")

                    parsed = parse_medical_report(extracted_text)
                    st.session_state.uploaded_preview = parsed
                    st.session_state.uploaded_filename = uploaded_file.name
                    st.session_state.uploaded_raw_text = extracted_text
                except Exception as e:
                    st.error(f"Error extracting document: {e}")

    # If document has been parsed and is in session state, render the extracted review view
    if st.session_state.uploaded_preview is not None:
        parsed = st.session_state.uploaded_preview
        b_count = len(parsed.get("biomarkers", []))
        
        st.success(f"✅ Medical report analyzed! Extracted **{b_count} lab biomarkers**.")

        with st.expander("📄 View Extracted Document Text Preview"):
            st.text_area("Document Text", value=st.session_state.get("uploaded_raw_text", "")[:3000], height=200, disabled=True)

        st.markdown("### 📝 Review Extracted Metadata & Lab Parameters")
        
        col_e1, col_e2, col_e3 = st.columns(3)
        with col_e1:
            edit_name = st.text_input("Patient Name:", value=parsed.get("patient_name") or "Self")
        with col_e2:
            edit_date = st.text_input("Report Date (YYYY-MM-DD):", value=parsed.get("report_date") or str(date.today()))
        with col_e3:
            edit_year = st.number_input("Report Year:", value=parsed.get("report_year") or date.today().year, step=1)

        edit_lab = st.text_input("Diagnostic Lab / Hospital:", value=parsed.get("hospital_lab_name") or "Diagnostic Center")
        edit_notes = st.text_area("Physician Notes:", value=parsed.get("physician_notes") or "")

        st.markdown(f"#### 🧪 Extracted Clinical Biomarkers ({b_count} parameters detected)")
        
        if parsed.get("biomarkers"):
            df_bio = pd.DataFrame([{
                "Category": b["category"],
                "Test Name": b["test_name"],
                "Result Value": b["result_value"],
                "Unit": b["unit"],
                "Ref Min": b.get("reference_min"),
                "Ref Max": b.get("reference_max"),
                "Status": f"🔴 HIGH" if b["status"] == "HIGH" else (f"🔵 LOW" if b["status"] == "LOW" else "🟢 NORMAL")
            } for b in parsed["biomarkers"]])
            render_dataframe(df_bio, hide_index=True)
        else:
            st.warning("No standard biomarker rows were matched. If this is a scanned document without a text layer, you can use the web interface or check the text preview.")

        if st.button("💾 Confirm & Save Report to Medical Archive", type="primary"):
            try:
                try:
                    p_date = datetime.strptime(edit_date.strip(), "%Y-%m-%d").date()
                except ValueError:
                    p_date = date.today()

                permanent_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{st.session_state.uploaded_filename.replace(' ', '_')}"
                permanent_path = os.path.join(UPLOADS_DIR, permanent_filename)
                
                # Copy file to permanent storage
                temp_p = os.path.join(UPLOADS_DIR, f"temp_{st.session_state.uploaded_filename}")
                if os.path.exists(temp_p):
                    with open(temp_p, "rb") as sf, open(permanent_path, "wb") as df_out:
                        df_out.write(sf.read())

                with get_db() as save_db:
                    new_rep = Report(
                        patient_name=edit_name.strip(),
                        report_date=p_date,
                        report_year=int(edit_year),
                        hospital_lab_name=edit_lab.strip(),
                        original_filename=st.session_state.uploaded_filename,
                        file_path=permanent_path,
                        notes=edit_notes.strip()
                    )
                    save_db.add(new_rep)
                    save_db.flush()

                    for b in parsed.get("biomarkers", []):
                        db_b = Biomarker(
                            report_id=new_rep.id,
                            category=b.get("category", "General Lab"),
                            test_name=b.get("test_name", "Test"),
                            result_value=b.get("result_value", 0.0),
                            unit=b.get("unit", ""),
                            reference_min=b.get("reference_min"),
                            reference_max=b.get("reference_max"),
                            status=b.get("status", "NORMAL"),
                            clinical_summary=b.get("clinical_summary", "")
                        )
                        save_db.add(db_b)

                    save_db.commit()

                st.session_state.uploaded_preview = None
                st.session_state.uploaded_filename = ""
                st.success("🎉 Medical report saved successfully to database! View it in the Dashboard and Archive.")
                st.rerun()

            except Exception as save_err:
                st.error(f"Save failed: {save_err}")

# =============================================================
# TAB 4: CLINICAL DIET PLANNER
# =============================================================

with tab_diet:
    st.markdown("##### 🥗 Biomarker-Driven Clinical Diet Planner")
    st.caption("Personalized nutrition protocol and 7-day structured meal schedule tailored directly to your clinical lab findings.")

    if reports:
        report_choices = [f"{r['patient_name']} — Year {r['report_year']} ({r['hospital_lab_name']} • {len(r['biomarkers'])} tests)" for r in reports]
        selected_rep_idx = st.selectbox("Select Checkup Report for Clinical Profile:", options=range(len(reports)), format_func=lambda i: report_choices[i], key="diet_rep_select")
        chosen_rep = reports[selected_rep_idx]
        biomarkers_for_diet = chosen_rep["biomarkers"]
        diet_patient_name = chosen_rep["patient_name"]
    else:
        chosen_rep = None
        biomarkers_for_diet = []
        diet_patient_name = "Self"

    col_d1, col_d2, col_d3 = st.columns(3)
    with col_d1:
        chosen_diet_pref = st.selectbox("Diet Preference:", ["Vegetarian", "Non-Vegetarian", "Eggetarian", "Vegan"], index=0)
    with col_d2:
        chosen_cuisine = st.selectbox("Cuisine Style:", ["Indian", "Mediterranean"], index=0)
    with col_d3:
        chosen_calories = st.selectbox("Calorie Target:", [1800, 2000, 2200], index=1)

    if st.button("✨ Generate Personalized Nutrition Protocol", type="primary"):
        with st.spinner("Generating clinical diet plan..."):
            diet_plan = create_diet_plan(
                report_id=chosen_rep["id"] if chosen_rep else 0,
                patient_name=diet_patient_name,
                biomarkers=biomarkers_for_diet,
                diet_pref=chosen_diet_pref,
                cuisine_pref=chosen_cuisine,
                calorie_target=chosen_calories
            )

            st.markdown(f"""
            <div style="background: linear-gradient(to right, #059669, #0d9488); border-radius: 12px; padding: 1.25rem 1.5rem; color: white; margin-top: 1rem; margin-bottom: 1.25rem;">
                <span style="font-size: 0.72rem; font-weight: 700; background: rgba(255,255,255,0.2); padding: 3px 8px; border-radius: 4px; text-transform: uppercase;">
                    {diet_plan['diet_preference']} • {diet_plan['cuisine_preference']} Cuisine
                </span>
                <h3 style="margin-top: 0.5rem; margin-bottom: 0.2rem; font-weight: 800; color: white;">Biomarker-Driven Nutrition Protocol</h3>
                <div style="font-size: 0.85rem; opacity: 0.9;">Formulated specifically for <strong>{diet_plan['patient_name']}</strong></div>
            </div>
            """, unsafe_allow_html=True)

            # 1. Primary Objectives
            st.markdown("###### 🎯 Targeted Clinical Objectives")
            for g in diet_plan["primary_health_goals"]:
                st.markdown(f"- ✅ **{g}**")

            st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

            # 2. Foods Matrix
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                st.markdown("###### 👍 Foods to Prioritize")
                for f in diet_plan["foods_to_prioritize"]:
                    st.markdown(f"""
                    <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 0.75rem; margin-bottom: 0.5rem;">
                        <strong style="color: #166534; font-size: 0.85rem;">{f['food']}</strong>
                        <div style="color: #14532d; font-size: 0.75rem; margin-top: 2px;">{f['rationale']}</div>
                        <div style="color: #059669; font-size: 0.7rem; font-weight: 600; margin-top: 4px;">Targets: {', '.join(f['target_markers'])}</div>
                    </div>
                    """, unsafe_allow_html=True)

            with f_col2:
                st.markdown("###### ⚠️ Foods to Avoid / Limit")
                for f in diet_plan["foods_to_avoid"]:
                    is_alcohol = "Alcohol" in f["food"]
                    bg_col = "#fff1f2" if is_alcohol else "#fef2f2"
                    border_col = "#fda4af" if is_alcohol else "#fecaca"
                    st.markdown(f"""
                    <div style="background: {bg_col}; border: 1px solid {border_col}; border-radius: 8px; padding: 0.75rem; margin-bottom: 0.5rem;">
                        <strong style="color: #991b1b; font-size: 0.85rem;">{'🚫 ' if is_alcohol else ''}{f['food']}</strong>
                        <div style="color: #7f1d1d; font-size: 0.75rem; margin-top: 2px;">{f['rationale']}</div>
                        <div style="color: #dc2626; font-size: 0.7rem; font-weight: 600; margin-top: 4px;">Avoid due to: {', '.join(f['target_markers'])}</div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)

            # 3. 7-Day Meal Schedule
            st.markdown("###### 📅 7-Day Structured Meal Schedule")
            day_tabs = st.tabs([d["day"] for d in diet_plan["weekly_meal_plan"]])
            for i, d in enumerate(diet_plan["weekly_meal_plan"]):
                with day_tabs[i]:
                    for m in d["meals"]:
                        st.markdown(f"""
                        <div style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 0.6rem 0.9rem; margin-bottom: 0.4rem; display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <span style="font-size: 0.7rem; font-weight: 700; color: #0284c7; text-transform: uppercase;">{m['meal_type']}</span>
                                <div style="font-weight: 600; font-size: 0.85rem; color: #0f172a; margin-top: 1px;">{m['menu']}</div>
                                <div style="font-size: 0.72rem; color: #059669; font-weight: 500; margin-top: 2px;">✨ {m['nutrition_focus']}</div>
                            </div>
                            <div style="font-size: 0.72rem; color: #64748b; font-weight: 600; text-align: right; background: #f8fafc; padding: 4px 8px; border-radius: 6px;">
                                {m['portion_guide']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

            st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)

            # 4. Lifestyle Protocols
            st.markdown("###### 🏃 Physiological & Lifestyle Protocols")
            for tip in diet_plan["lifestyle_recommendations"]:
                st.markdown(f"- 💡 {tip}")
