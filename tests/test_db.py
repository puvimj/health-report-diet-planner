import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Report, Biomarker, DietPlan

TEST_DB_URL = "sqlite:///:memory:"

@pytest.fixture
def db_session():
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()

def test_create_report_and_biomarkers(db_session):
    report = Report(
        patient_name="Pavithran",
        report_date=date(2025, 5, 10),
        report_year=2025,
        hospital_lab_name="Apollo Diagnostics",
        notes="Annual Health Assessment"
    )
    db_session.add(report)
    db_session.commit()
    db_session.refresh(report)

    assert report.id is not None
    assert report.patient_name == "Pavithran"
    assert report.report_year == 2025

    # Add biomarkers
    b1 = Biomarker(
        report_id=report.id,
        category="Lipid Profile",
        test_name="Total Cholesterol",
        result_value=195.0,
        unit="mg/dL",
        reference_min=125.0,
        reference_max=200.0,
        status="NORMAL"
    )
    b2 = Biomarker(
        report_id=report.id,
        category="Blood Sugar",
        test_name="HbA1c",
        result_value=6.0,
        unit="%",
        reference_min=4.0,
        reference_max=5.6,
        status="HIGH"
    )
    db_session.add_all([b1, b2])
    db_session.commit()

    db_session.refresh(report)
    assert len(report.biomarkers) == 2
    assert report.to_dict()["abnormal_biomarkers"] == 1

def test_query_filtering(db_session):
    # Create two reports in different years
    r1 = Report(patient_name="Pavithran", report_date=date(2023, 1, 1), report_year=2023)
    r2 = Report(patient_name="Pavithran", report_date=date(2024, 1, 1), report_year=2024)
    r3 = Report(patient_name="Alice", report_date=date(2024, 2, 1), report_year=2024)
    db_session.add_all([r1, r2, r3])
    db_session.commit()

    # Filter by year
    reports_2024 = db_session.query(Report).filter(Report.report_year == 2024).all()
    assert len(reports_2024) == 2

    # Filter by name
    pavi_reports = db_session.query(Report).filter(Report.patient_name == "Pavithran").all()
    assert len(pavi_reports) == 2

    # Filter by both name and year
    filtered = db_session.query(Report).filter(
        Report.patient_name == "Pavithran",
        Report.report_year == 2024
    ).all()
    assert len(filtered) == 1
    assert filtered[0].report_year == 2024

def test_cascade_delete(db_session):
    report = Report(patient_name="Bob", report_date=date(2025, 1, 1), report_year=2025)
    db_session.add(report)
    db_session.commit()

    b = Biomarker(report_id=report.id, category="Lipids", test_name="HDL", result_value=50.0, unit="mg/dL")
    db_session.add(b)
    db_session.commit()

    assert db_session.query(Biomarker).count() == 1

    # Delete report
    db_session.delete(report)
    db_session.commit()

    # Cascade should delete biomarker
    assert db_session.query(Biomarker).count() == 0
