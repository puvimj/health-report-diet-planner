from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    patient_name = Column(String(120), nullable=False, index=True)
    report_date = Column(Date, nullable=False)
    report_year = Column(Integer, nullable=False, index=True)
    hospital_lab_name = Column(String(200), default="", nullable=True)
    original_filename = Column(String(255), default="", nullable=True)
    file_path = Column(String(500), default="", nullable=True)
    notes = Column(Text, default="", nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    biomarkers = relationship(
        "Biomarker",
        back_populates="report",
        cascade="all, delete-orphan",
        order_by="Biomarker.category, Biomarker.test_name"
    )
    diet_plans = relationship(
        "DietPlan",
        back_populates="report",
        cascade="all, delete-orphan",
        order_by="DietPlan.created_at.desc()"
    )

    def to_dict(self):
        abnormal_count = sum(1 for b in self.biomarkers if b.status in ("HIGH", "LOW"))
        return {
            "id": self.id,
            "patient_name": self.patient_name,
            "report_date": self.report_date.isoformat() if self.report_date else None,
            "report_year": self.report_year,
            "hospital_lab_name": self.hospital_lab_name,
            "original_filename": self.original_filename,
            "file_path": self.file_path,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "total_biomarkers": len(self.biomarkers),
            "abnormal_biomarkers": abnormal_count,
        }


class Biomarker(Base):
    __tablename__ = "biomarkers"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    test_name = Column(String(120), nullable=False, index=True)
    result_value = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False, default="")
    reference_min = Column(Float, nullable=True)
    reference_max = Column(Float, nullable=True)
    status = Column(String(20), default="NORMAL", nullable=False)  # "NORMAL", "HIGH", "LOW"
    clinical_summary = Column(Text, default="", nullable=True)

    report = relationship("Report", back_populates="biomarkers")

    def to_dict(self):
        return {
            "id": self.id,
            "report_id": self.report_id,
            "category": self.category,
            "test_name": self.test_name,
            "result_value": self.result_value,
            "unit": self.unit,
            "reference_min": self.reference_min,
            "reference_max": self.reference_max,
            "status": self.status,
            "clinical_summary": self.clinical_summary,
        }


class DietPlan(Base):
    __tablename__ = "diet_plans"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_name = Column(String(120), nullable=False)
    diet_preference = Column(String(50), default="Vegetarian")
    cuisine_preference = Column(String(50), default="Indian")
    calorie_target = Column(Integer, default=2000)
    primary_health_goals = Column(Text, default="[]")  # JSON string
    foods_to_prioritize = Column(Text, default="[]")   # JSON string
    foods_to_avoid = Column(Text, default="[]")        # JSON string
    weekly_meal_plan = Column(Text, default="{}")       # JSON string
    lifestyle_recommendations = Column(Text, default="[]") # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)

    report = relationship("Report", back_populates="diet_plans")
