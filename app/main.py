import os
import re
import json
import shutil
from datetime import datetime, date
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Query, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc

from pydantic import BaseModel

from app.database import engine, Base, get_db, UPLOADS_DIR

def strip_patient_title(name: Optional[str]) -> str:
    """Strips honorific titles/salutations (Mr., Mrs., Ms., Dr., Miss, Master, etc.)"""
    if not name:
        return "Unknown Patient"
    cleaned = re.sub(r'^(?:mr|mrs|ms|miss|dr|prof|shri|smt|master|baby|m/s)\.?\s+', '', name.strip(), flags=re.IGNORECASE)
    return cleaned.strip() or name.strip()

def get_canonical_patient_key(name: Optional[str]) -> str:
    """
    Groups patient names by ignoring titles and matching the root name:
    'Mrs. PUVIARASI MJ', 'Ms. PUVIARASI', 'PUVIARASI' -> 'PUVIARASI'
    'Mr. ARUN KUMAR' -> 'ARUN KUMAR'
    """
    clean = strip_patient_title(name).upper()
    tokens = [t for t in re.split(r'[\s\.\-_]+', clean) if t]
    if not tokens:
        return "UNKNOWN"
    sig_tokens = [t for t in tokens if len(t) > 2]
    if sig_tokens:
        return " ".join(sig_tokens)
    return " ".join(tokens)
from app.models import Report, Biomarker, DietPlan
from app.schemas import (
    ReportCreate, ReportSummaryResponse, ReportDetailResponse,
    ExtractedReportData, DietPlanGenerateRequest, DietPlanResponse,
    TrendSeries, TrendPoint, BiomarkerCreate
)
from app.extractor import extract_text_from_pdf, parse_medical_report
from app.diet_engine import create_diet_plan, analyze_health_findings

# Initialize SQLite database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Personal Health Report Manager & Diet Planner",
    description="Upload yearly medical checkup reports, store in SQL, filter by name/year, and generate clinical diet plans.",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def read_root():
    """Serves the main HTML dashboard."""
    index_file = os.path.join(STATIC_DIR, "index.html")
    return FileResponse(index_file)


# -------------------------------------------------------------
# Report Ingestion & Upload Endpoints
# -------------------------------------------------------------

@app.post("/api/reports/upload", response_model=ExtractedReportData)
async def upload_and_parse_report(file: UploadFile = File(...)):
    """
    Accepts an uploaded medical report (PDF or TXT), extracts text and biomarkers,
    and returns parsed data so the user can review and edit before saving to SQL.
    """
    filename = file.filename or "uploaded_report.pdf"
    file_ext = os.path.splitext(filename)[1].lower()

    # Save temp file
    temp_path = os.path.join(UPLOADS_DIR, f"temp_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}")
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        import importlib
        import app.extractor
        importlib.reload(app.extractor)

        raw_text = ""
        if file_ext == ".pdf":
            raw_text = app.extractor.extract_text_from_pdf(temp_path)
        else:
            # Attempt to read as text file
            with open(temp_path, "r", encoding="utf-8", errors="ignore") as f:
                raw_text = f.read()

        if not raw_text.strip():
            # If PDF text was empty or scanned without text layer
            parsed_data = {
                "patient_name": "Self / Patient",
                "report_date": datetime.now().strftime("%Y-%m-%d"),
                "report_year": datetime.now().year,
                "hospital_lab_name": "Diagnostic Center",
                "extracted_text_preview": "Note: Scanned PDF contains no extractable text layer. You can manually enter or adjust biomarkers in the form below.",
                "biomarkers": []
            }
        else:
            parsed_data = app.extractor.parse_medical_report(raw_text)

        parsed_data["file_path"] = temp_path
        return parsed_data
    finally:
        pass


@app.post("/api/reports", response_model=ReportDetailResponse, status_code=status.HTTP_201_CREATED)
def save_report(report_in: ReportCreate, db: Session = Depends(get_db)):
    """
    Saves a confirmed medical report with all its biomarkers into the SQL database.
    """
    # Determine year from date if not provided
    report_year = report_in.report_year or report_in.report_date.year

    db_report = Report(
        patient_name=report_in.patient_name.strip(),
        report_date=report_in.report_date,
        report_year=report_year,
        hospital_lab_name=report_in.hospital_lab_name,
        original_filename=report_in.original_filename,
        file_path=report_in.file_path,
        notes=report_in.notes
    )
    db.add(db_report)
    db.flush()  # populate db_report.id

    # Add biomarkers
    for b in report_in.biomarkers:
        db_biomarker = Biomarker(
            report_id=db_report.id,
            category=b.category,
            test_name=b.test_name,
            result_value=b.result_value,
            unit=b.unit,
            reference_min=b.reference_min,
            reference_max=b.reference_max,
            status=b.status or "NORMAL",
            clinical_summary=b.clinical_summary or ""
        )
        db.add(db_biomarker)

    db.commit()
    db.refresh(db_report)
    return db_report


# -------------------------------------------------------------
# Report Search, Filtering & Retrieval
# -------------------------------------------------------------

@app.get("/api/reports", response_model=List[ReportSummaryResponse])
def get_reports(
    patient_name: Optional[str] = Query(None, description="Filter by patient name"),
    year: Optional[int] = Query(None, description="Filter by checkup year"),
    abnormal_only: bool = Query(False, description="Filter to only reports with abnormal biomarkers"),
    search: Optional[str] = Query(None, description="Keyword search in lab name, notes, or patient"),
    db: Session = Depends(get_db)
):
    """
    Retrieves reports with flexible filters:
    - Patient Name
    - Year
    - Abnormal status
    - Keyword search
    """
    query = db.query(Report)

    if year and year > 1900:
        query = query.filter(Report.report_year == year)

    if search and search.strip():
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            (Report.patient_name.ilike(search_pattern)) |
            (Report.hospital_lab_name.ilike(search_pattern)) |
            (Report.notes.ilike(search_pattern))
        )

    all_reports = query.all()
    if patient_name and patient_name.strip():
        target_key = get_canonical_patient_key(patient_name)
        reports = [
            r for r in all_reports 
            if get_canonical_patient_key(r.patient_name) == target_key or patient_name.strip().lower() in (r.patient_name or "").lower()
        ]
    else:
        reports = all_reports

    # Group by canonical patient key, then order by year descending
    reports.sort(key=lambda r: (
        get_canonical_patient_key(r.patient_name),
        -(r.report_year or 0),
        -(r.report_date.toordinal() if r.report_date else 0)
    ))

    results = []
    for r in reports:
        summary_dict = r.to_dict()
        if abnormal_only and summary_dict["abnormal_biomarkers"] == 0:
            continue
        results.append(ReportSummaryResponse(**summary_dict))

    return results


@app.get("/api/reports/{report_id}", response_model=ReportDetailResponse)
def get_report_detail(report_id: int, db: Session = Depends(get_db)):
    """Retrieves full details of a specific report including all biomarkers."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Medical report not found")
    return report


@app.delete("/api/reports/{report_id}")
def delete_report(report_id: int, db: Session = Depends(get_db)):
    """Deletes a report and associated biomarkers/diet plans from the SQL database."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Medical report not found")
    
    # Delete uploaded file if exists
    if report.file_path and os.path.exists(report.file_path):
        try:
            os.remove(report.file_path)
        except Exception:
            pass

    db.delete(report)
    db.commit()
    return {"status": "success", "message": f"Report {report_id} successfully deleted"}


@app.get("/api/reports/{report_id}/file")
def get_report_file(report_id: int, db: Session = Depends(get_db)):
    """Serves the actual uploaded PDF/DOC directly so it opens in the browser."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Medical report not found")
    
    file_path = report.file_path
    if not file_path or not os.path.exists(file_path):
        # Look for matching file in UPLOADS_DIR
        if os.path.exists(UPLOADS_DIR):
            candidates = [
                os.path.join(UPLOADS_DIR, f) for f in os.listdir(UPLOADS_DIR)
                if os.path.isfile(os.path.join(UPLOADS_DIR, f))
            ]
            if candidates:
                candidates.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                matched = [c for c in candidates if report.original_filename and os.path.basename(c).lower().endswith(report.original_filename.lower())]
                file_path = matched[0] if matched else candidates[0]
                report.file_path = file_path
                if not report.original_filename:
                    clean_name = os.path.basename(file_path)
                    if clean_name.startswith("temp_"):
                        clean_name = clean_name.split("_", 2)[-1]
                    report.original_filename = clean_name
                db.commit()

    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Medical document file not found on disk")
    
    filename = report.original_filename or os.path.basename(file_path)
    ext = os.path.splitext(filename)[1].lower()
    
    media_types = {
        ".pdf": "application/pdf",
        ".doc": "application/msword",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".txt": "text/plain"
    }
    media_type = media_types.get(ext, "application/pdf")
    
    return FileResponse(
        file_path,
        media_type=media_type,
        headers={
            "Content-Disposition": f"inline; filename=\"{filename}\"",
            "Content-Type": media_type
        }
    )


@app.post("/api/reports/direct-upload")
async def direct_upload_report(
    file: Optional[UploadFile] = File(None),
    patient_name: str = Form(...),
    report_date: str = Form(...),
    report_year: Optional[int] = Form(None),
    hospital_lab_name: Optional[str] = Form(""),
    notes: Optional[str] = Form(""),
    findings_json: Optional[str] = Form("[]"),
    db: Session = Depends(get_db)
):
    """
    Directly uploads and archives medical PDF/DOC to SQL database without forcing automatic text parsing.
    Saves the file to disk and records metadata & health findings in SQLite.
    """
    try:
        parsed_date = datetime.strptime(report_date, "%Y-%m-%d").date()
    except ValueError:
        parsed_date = date.today()

    year = report_year or parsed_date.year
    saved_file_path = ""
    orig_filename = ""

    if file and file.filename:
        orig_filename = file.filename
        safe_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{orig_filename.replace(' ', '_')}"
        saved_file_path = os.path.join(UPLOADS_DIR, safe_name)
        with open(saved_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

    db_report = Report(
        patient_name=patient_name.strip(),
        report_date=parsed_date,
        report_year=year,
        hospital_lab_name=hospital_lab_name.strip() if hospital_lab_name else "Diagnostic Center",
        original_filename=orig_filename,
        file_path=saved_file_path,
        notes=notes.strip() if notes else ""
    )
    db.add(db_report)
    db.flush()

    # Save any health condition flags selected for diet planning
    try:
        findings = json.loads(findings_json or "[]")
        for f in findings:
            b = Biomarker(
                report_id=db_report.id,
                category=f.get("category", "Health Finding"),
                test_name=f.get("test_name", "Finding"),
                result_value=float(f.get("result_value", 1.0)),
                unit=f.get("unit", ""),
                reference_min=f.get("reference_min"),
                reference_max=f.get("reference_max"),
                status=f.get("status", "HIGH"),
                clinical_summary=f.get("clinical_summary", "")
            )
            db.add(b)
    except Exception as e:
        print(f"Error parsing findings: {e}")

    db.commit()
    db.refresh(db_report)
    return db_report.to_dict()


@app.post("/api/reports/reset-database")
def reset_database_records(db: Session = Depends(get_db)):
    """Deletes all reports, biomarkers, and diet plans to reset to a completely clean database."""
    db.query(DietPlan).delete()
    db.query(Biomarker).delete()
    db.query(Report).delete()
    db.commit()
    return {"status": "success", "message": "All records cleared. Database is now completely empty."}


@app.get("/api/reports/filter/years")
def get_available_years(db: Session = Depends(get_db)):
    """Returns a list of all distinct report years stored in the database."""
    years = db.query(Report.report_year).distinct().order_by(desc(Report.report_year)).all()
    return [y[0] for y in years if y[0] is not None]


@app.get("/api/reports/filter/patients")
def get_available_patients(db: Session = Depends(get_db)):
    """Returns a list of all distinct patient names stored in the database, normalized without titles."""
    patients = db.query(Report.patient_name).distinct().order_by(Report.patient_name).all()
    canonical_map = {}
    for p in patients:
        raw_name = p[0]
        if not raw_name:
            continue
        key = get_canonical_patient_key(raw_name)
        title_free = strip_patient_title(raw_name)
        if key not in canonical_map or len(title_free) > len(canonical_map[key]):
            canonical_map[key] = title_free
    return sorted(list(canonical_map.values()))


# -------------------------------------------------------------
# Trend Analytics Endpoints (Multi-Year Tracking)
# -------------------------------------------------------------

def sync_and_upgrade_reports_data(db: Session):
    """
    Checks all reports on disk and upgrades extracted biomarkers if needed.
    Ensures reports extracted with earlier versions get updated with complete biomarkers.
    """
    reports = db.query(Report).all()
    for report in reports:
        # Clean boilerplate lab disclaimers from physician notes
        if report.notes:
            lower_notes = report.notes.lower()
            if any(b in lower_notes for b in [
                "international council for standardization",
                "differential leucocyte counts",
                "edta whole blood",
                "per unit volume",
                "test conducted on",
                "laboratory investigations are only a tool"
            ]):
                report.notes = ""
                db.commit()

        # Heal broken or timestamp-shifted file paths
        if not report.file_path or not os.path.exists(report.file_path):
            if os.path.exists(UPLOADS_DIR):
                files = [os.path.join(UPLOADS_DIR, f) for f in os.listdir(UPLOADS_DIR) if os.path.isfile(os.path.join(UPLOADS_DIR, f))]
                files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                orig_lower = (report.original_filename or "").lower().strip()
                pname_token = strip_patient_title(report.patient_name or "").lower().split()[0] if report.patient_name else ""
                matched_path = None
                for f in files:
                    bname = os.path.basename(f).lower()
                    if orig_lower and (bname.endswith(orig_lower) or orig_lower.endswith(bname)):
                        matched_path = f
                        break
                    if pname_token and pname_token in bname and str(report.report_year) in bname:
                        matched_path = f
                        break
                if matched_path:
                    report.file_path = matched_path
                    db.commit()

        if not report.file_path or not os.path.exists(report.file_path):
            continue
        
        b_map = {b.test_name: b for b in report.biomarkers}
        needs_refresh = False

        # 1. HDL out-of-range bug in earlier Apollo parser (e.g. 182 instead of 41)
        if "HDL Cholesterol" in b_map and b_map["HDL Cholesterol"].result_value > 130:
            needs_refresh = True
        # 2. Triglycerides out-of-range bug in earlier Apollo parser (e.g. 19 instead of 95)
        if "Triglycerides" in b_map and b_map["Triglycerides"].result_value < 25 and report.report_year == 2026:
            needs_refresh = True
        # 3. Missing glucose in a comprehensive panel report
        if not any("sugar" in n.lower() or "glucose" in n.lower() for n in b_map) and report.report_year == 2026:
            needs_refresh = True

        if needs_refresh:
            try:
                from app.extractor import extract_text_from_pdf, parse_medical_report
                text = extract_text_from_pdf(report.file_path)
                parsed = parse_medical_report(text)
                
                # Delete outdated biomarkers
                db.query(Biomarker).filter(Biomarker.report_id == report.id).delete()
                
                # Insert fresh biomarkers
                for b_data in parsed.get("biomarkers", []):
                    new_b = Biomarker(
                        report_id=report.id,
                        category=b_data.get("category", "General Lab"),
                        test_name=b_data.get("test_name", "Test"),
                        result_value=b_data.get("result_value", 0.0),
                        unit=b_data.get("unit", ""),
                        reference_min=b_data.get("reference_min"),
                        reference_max=b_data.get("reference_max"),
                        status=b_data.get("status", "NORMAL"),
                        clinical_summary=b_data.get("clinical_summary", "")
                    )
                    db.add(new_b)
                
                if parsed.get("physician_notes") and not report.notes:
                    report.notes = parsed["physician_notes"]
                
                db.commit()
            except Exception as e:
                db.rollback()
                print(f"Error refreshing report {report.id}: {e}")


@app.get("/api/analytics/trends")
def get_trends(
    patient_name: Optional[str] = Query(None, description="Patient name for trends"),
    db: Session = Depends(get_db)
):
    """
    Returns time-series biomarker values across years for graphing (Chart.js),
    strictly isolated to a single patient (matching canonical name ignoring titles).
    Harmonizes multi-year lab tests (e.g. Fasting & Random Blood Glucose, Lipids, KFT, LFT)
    so patients can track continuous trends across different labs and years without missing records.
    """
    # Auto-upgrade any earlier report extractions
    sync_and_upgrade_reports_data(db)

    reports_all = db.query(Report).order_by(Report.report_date.asc()).all()
    if not reports_all:
        return []

    if patient_name and patient_name.strip() and patient_name.upper() != "ALL":
        target_key = get_canonical_patient_key(patient_name)
    else:
        target_key = get_canonical_patient_key(reports_all[-1].patient_name)

    reports = [r for r in reports_all if get_canonical_patient_key(r.patient_name) == target_key]

    # Aggregate by test name
    trends_by_test = {}
    glucose_points = []

    for r in reports:
        for b in r.biomarkers:
            name = b.test_name
            if name not in trends_by_test:
                trends_by_test[name] = {
                    "test_name": name,
                    "category": b.category,
                    "unit": b.unit,
                    "reference_min": b.reference_min,
                    "reference_max": b.reference_max,
                    "points": []
                }
            point_data = {
                "year": r.report_year,
                "date": r.report_date.isoformat(),
                "value": b.result_value,
                "status": b.status,
                "report_id": r.id,
                "test_name": b.test_name
            }
            trends_by_test[name]["points"].append(point_data)

            # Collect all blood sugar / glucose tests for comprehensive trajectory
            if "sugar" in name.lower() or "glucose" in name.lower():
                glucose_points.append({
                    "year": r.report_year,
                    "date": r.report_date.isoformat(),
                    "value": b.result_value,
                    "status": b.status,
                    "report_id": r.id,
                    "test_name": b.test_name,
                    "is_fasting": "fasting" in name.lower()
                })

    # Harmonize Blood Glucose / Sugar across all years
    if glucose_points:
        # Keep one representative glucose point per checkup report (prefer fasting if multiple)
        rep_map = {}
        for p in glucose_points:
            rid = p["report_id"]
            if rid not in rep_map or (p.get("is_fasting") and not rep_map[rid].get("is_fasting")):
                rep_map[rid] = p

        sorted_glucose_points = sorted(list(rep_map.values()), key=lambda x: x["date"])

        # Unified series: Blood Glucose / Sugar (covers Fasting, Random, Plasma Glucose across all checkup years)
        trends_by_test["Blood Glucose / Sugar"] = {
            "test_name": "Blood Glucose / Sugar",
            "category": "Blood Sugar / Diabetes",
            "unit": "mg/dL",
            "reference_min": 70.0,
            "reference_max": 99.0,
            "points": sorted_glucose_points
        }

        # If Fasting Blood Sugar exists, also bridge any missing checkup year with the available blood glucose reading
        if "Fasting Blood Sugar" in trends_by_test:
            fbs_years = {p["year"] for p in trends_by_test["Fasting Blood Sugar"]["points"]}
            for p in sorted_glucose_points:
                if p["year"] not in fbs_years:
                    p_copy = dict(p)
                    trends_by_test["Fasting Blood Sugar"]["points"].append(p_copy)
            trends_by_test["Fasting Blood Sugar"]["points"].sort(key=lambda x: x["date"])

    return list(trends_by_test.values())


@app.get("/api/analytics/summary")
def get_analytics_summary(
    patient_name: Optional[str] = Query(None, description="Optional patient name filter"),
    db: Session = Depends(get_db)
):
    """Summary metrics for the dashboard cards, optionally filtered by patient canonical name."""
    all_reports = db.query(Report).all()
    if patient_name and patient_name.strip() and patient_name.upper() != "ALL":
        target_key = get_canonical_patient_key(patient_name)
        reports = [
            r for r in all_reports 
            if get_canonical_patient_key(r.patient_name) == target_key or patient_name.strip().lower() in (r.patient_name or "").lower()
        ]
    else:
        reports = all_reports

    total_reports = len(reports)
    distinct_years = len(set(r.report_year for r in reports if r.report_year))
    years_list = sorted(list(set(r.report_year for r in reports if r.report_year)))
    report_ids = [r.id for r in reports]

    if report_ids:
        total_biomarkers = db.query(Biomarker).filter(Biomarker.report_id.in_(report_ids)).count()
        abnormal_count = db.query(Biomarker).filter(
            Biomarker.report_id.in_(report_ids),
            Biomarker.status.in_(["HIGH", "LOW"])
        ).count()
        latest_report = max(reports, key=lambda r: r.report_date) if reports else None
    else:
        total_biomarkers = 0
        abnormal_count = 0
        latest_report = None

    # Calculate per-patient breakdown across family
    patients_map = {}
    for r in all_reports:
        key = get_canonical_patient_key(r.patient_name)
        title_free = strip_patient_title(r.patient_name)
        if key not in patients_map:
            patients_map[key] = {
                "name": title_free,
                "reports_count": 0,
                "years": set(),
                "report_ids": []
            }
        else:
            if len(title_free) > len(patients_map[key]["name"]):
                patients_map[key]["name"] = title_free
        patients_map[key]["reports_count"] += 1
        if r.report_year:
            patients_map[key]["years"].add(r.report_year)
        patients_map[key]["report_ids"].append(r.id)

    breakdown = []
    for k, info in patients_map.items():
        ab_cnt = db.query(Biomarker).filter(
            Biomarker.report_id.in_(info["report_ids"]),
            Biomarker.status.in_(["HIGH", "LOW"])
        ).count()
        breakdown.append({
            "patient_name": info["name"],
            "reports_count": info["reports_count"],
            "years": sorted(list(info["years"])),
            "abnormal_count": ab_cnt
        })

    active_name = strip_patient_title(patient_name) if (patient_name and patient_name.strip() and patient_name.upper() != "ALL") else "All Family Members"

    return {
        "active_patient": active_name,
        "total_reports": total_reports,
        "distinct_years": distinct_years,
        "years_list": years_list,
        "total_biomarkers": total_biomarkers,
        "abnormal_findings_count": abnormal_count,
        "latest_report_date": latest_report.report_date.isoformat() if latest_report else None,
        "latest_patient": strip_patient_title(latest_report.patient_name) if latest_report else None,
        "breakdown": breakdown
    }


@app.get("/api/analytics/patients")
def get_patients_summary(db: Session = Depends(get_db)):
    """Returns aggregated multi-patient health summary for the Family Health Hub, grouped by canonical name (ignoring titles)."""
    reports = db.query(Report).order_by(desc(Report.report_date)).all()
    
    # Group reports by canonical patient key (ignoring titles like Mr./Mrs./Ms.)
    patients_map = {}
    canonical_names = {}
    for r in reports:
        key = get_canonical_patient_key(r.patient_name)
        title_free = strip_patient_title(r.patient_name)
        if key not in patients_map:
            patients_map[key] = []
            canonical_names[key] = title_free
        else:
            if len(title_free) > len(canonical_names[key]):
                canonical_names[key] = title_free
        patients_map[key].append(r)

    patient_summaries = []
    for key, p_reports in patients_map.items():
        display_name = canonical_names[key]
        latest_r = p_reports[0]  # Already ordered by desc report_date
        rep_ids = [r.id for r in p_reports]
        years = sorted(list(set(r.report_year for r in p_reports if r.report_year)), reverse=True)
        
        # Get latest report's abnormal biomarkers
        latest_abnormal = []
        for b in latest_r.biomarkers:
            if b.status in ["HIGH", "LOW"]:
                latest_abnormal.append({
                    "test_name": b.test_name,
                    "result_value": b.result_value,
                    "unit": b.unit,
                    "status": b.status
                })

        # Total abnormal count across all reports
        all_abnormal_count = db.query(Biomarker).filter(
            Biomarker.report_id.in_(rep_ids),
            Biomarker.status.in_(["HIGH", "LOW"])
        ).count()

        patient_summaries.append({
            "patient_name": display_name,
            "total_reports": len(p_reports),
            "years_tracked": years,
            "latest_year": latest_r.report_year,
            "latest_report_date": latest_r.report_date.isoformat(),
            "latest_lab": latest_r.hospital_lab_name or "Diagnostic Center",
            "latest_report_id": latest_r.id,
            "latest_notes": latest_r.notes or "",
            "abnormal_findings_count": len(latest_abnormal),
            "all_time_abnormal_count": all_abnormal_count,
            "latest_abnormal_markers": latest_abnormal,
            "overall_status": "ATTENTION_NEEDED" if latest_abnormal else "ALL_NORMAL"
        })

    return patient_summaries


# -------------------------------------------------------------
# Diet Planning Endpoints
# -------------------------------------------------------------

class DietPreviewRequest(BaseModel):
    biomarkers: List[BiomarkerCreate] = []
    diet_preference: str = "Vegetarian"
    cuisine_preference: str = "Indian"
    calorie_target: Optional[int] = 2000

@app.post("/api/diet/preview")
def preview_diet_from_biomarkers(req: DietPreviewRequest):
    """Generates an instant tailored diet plan and clinical improvement areas from raw biomarkers."""
    biomarker_dicts = [b.dict() for b in req.biomarkers]
    plan_data = create_diet_plan(
        report_id=0,
        patient_name="Patient",
        biomarkers=biomarker_dicts,
        diet_pref=req.diet_preference,
        cuisine_pref=req.cuisine_preference,
        calorie_target=req.calorie_target or 2000
    )
    findings = analyze_health_findings(biomarker_dicts)
    return {
        "findings": findings,
        "diet_plan": plan_data
    }


@app.post("/api/diet/generate", response_model=DietPlanResponse)
def generate_diet_plan(req: DietPlanGenerateRequest, db: Session = Depends(get_db)):
    """
    Generates a personalized clinical diet plan based on the findings of a specific health report,
    and saves it to the SQL database.
    """
    report = db.query(Report).filter(Report.id == req.report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Medical report not found")

    biomarker_dicts = [b.to_dict() for b in report.biomarkers]

    # Generate plan
    plan_data = create_diet_plan(
        report_id=report.id,
        patient_name=report.patient_name,
        biomarkers=biomarker_dicts,
        diet_pref=req.diet_preference,
        cuisine_pref=req.cuisine_preference,
        calorie_target=req.calorie_target or 2000
    )

    # Save or update in database
    db_diet = DietPlan(
        report_id=report.id,
        patient_name=report.patient_name,
        diet_preference=req.diet_preference,
        cuisine_preference=req.cuisine_preference,
        calorie_target=req.calorie_target or 2000,
        primary_health_goals=json.dumps(plan_data["primary_health_goals"]),
        foods_to_prioritize=json.dumps(plan_data["foods_to_prioritize"]),
        foods_to_avoid=json.dumps(plan_data["foods_to_avoid"]),
        weekly_meal_plan=json.dumps(plan_data["weekly_meal_plan"]),
        lifestyle_recommendations=json.dumps(plan_data["lifestyle_recommendations"])
    )
    db.add(db_diet)
    db.commit()
    db.refresh(db_diet)

    plan_data["id"] = db_diet.id
    plan_data["created_at"] = db_diet.created_at

    return plan_data


@app.get("/api/diet/{report_id}")
def get_saved_diet_plan(report_id: int, db: Session = Depends(get_db)):
    """Retrieves the latest saved diet plan for a report."""
    db_diet = db.query(DietPlan).filter(DietPlan.report_id == report_id).order_by(desc(DietPlan.created_at)).first()
    if not db_diet:
        raise HTTPException(status_code=404, detail="No diet plan found for this report")

    return {
        "id": db_diet.id,
        "report_id": db_diet.report_id,
        "patient_name": db_diet.patient_name,
        "diet_preference": db_diet.diet_preference,
        "cuisine_preference": db_diet.cuisine_preference,
        "calorie_target": db_diet.calorie_target,
        "primary_health_goals": json.loads(db_diet.primary_health_goals or "[]"),
        "foods_to_prioritize": json.loads(db_diet.foods_to_prioritize or "[]"),
        "foods_to_avoid": json.loads(db_diet.foods_to_avoid or "[]"),
        "weekly_meal_plan": json.loads(db_diet.weekly_meal_plan or "[]"),
        "lifestyle_recommendations": json.loads(db_diet.lifestyle_recommendations or "[]"),
        "created_at": db_diet.created_at.isoformat()
    }
