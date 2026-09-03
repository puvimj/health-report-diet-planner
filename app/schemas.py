from datetime import date, datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# --- Biomarker Schemas ---

class BiomarkerBase(BaseModel):
    category: str = Field(..., description="Category, e.g., Lipid Profile, Diabetes, Liver, Kidney")
    test_name: str = Field(..., description="Name of test, e.g. Total Cholesterol, HbA1c")
    result_value: float = Field(..., description="Numeric result value")
    unit: str = Field("", description="Unit, e.g. mg/dL, %")
    reference_min: Optional[float] = Field(None, description="Minimum normal reference range")
    reference_max: Optional[float] = Field(None, description="Maximum normal reference range")
    status: Optional[str] = Field("NORMAL", description="NORMAL, HIGH, or LOW")
    clinical_summary: Optional[str] = Field("", description="Brief explanation or risk indicator")

class BiomarkerCreate(BiomarkerBase):
    pass

class BiomarkerResponse(BiomarkerBase):
    id: int
    report_id: int

    class Config:
        from_attributes = True


# --- Report Schemas ---

class ReportBase(BaseModel):
    patient_name: str
    report_date: date
    report_year: Optional[int] = None
    hospital_lab_name: Optional[str] = ""
    notes: Optional[str] = ""

class ReportCreate(ReportBase):
    original_filename: Optional[str] = ""
    file_path: Optional[str] = ""
    biomarkers: List[BiomarkerCreate] = []

class ReportSummaryResponse(BaseModel):
    id: int
    patient_name: str
    report_date: date
    report_year: int
    hospital_lab_name: Optional[str]
    original_filename: Optional[str]
    file_path: Optional[str]
    notes: Optional[str]
    created_at: datetime
    total_biomarkers: int
    abnormal_biomarkers: int

    class Config:
        from_attributes = True

class ReportDetailResponse(ReportBase):
    id: int
    report_year: int
    original_filename: Optional[str]
    file_path: Optional[str]
    created_at: datetime
    biomarkers: List[BiomarkerResponse] = []

    class Config:
        from_attributes = True


# --- Extraction Schemas ---

class ExtractedReportData(BaseModel):
    patient_name: str
    report_date: Optional[str] = None
    report_year: Optional[int] = None
    hospital_lab_name: Optional[str] = ""
    file_path: Optional[str] = ""
    extracted_text_preview: Optional[str] = ""
    physician_notes: Optional[str] = ""
    biomarkers: List[BiomarkerCreate] = []


# --- Diet Plan Schemas ---

class DietPlanGenerateRequest(BaseModel):
    report_id: int
    diet_preference: str = Field("Vegetarian", description="Vegetarian, Non-Vegetarian, Eggetarian, Vegan")
    cuisine_preference: str = Field("Indian", description="Indian, Mediterranean, Western")
    calorie_target: Optional[int] = Field(2000, description="Approximate daily calorie target")
    allergies: Optional[List[str]] = Field(default=[], description="Food allergies or intolerances")

class FoodItemRationale(BaseModel):
    food: str
    rationale: str
    target_markers: List[str]

class MealItem(BaseModel):
    meal_type: str  # Breakfast, Mid-Morning, Lunch, Evening Snack, Dinner
    menu: str
    portion_guide: str
    nutrition_focus: str

class DayMealPlan(BaseModel):
    day: str
    meals: List[MealItem]

class DietPlanResponse(BaseModel):
    id: Optional[int] = None
    report_id: int
    patient_name: str
    diet_preference: str
    cuisine_preference: str
    calorie_target: int
    primary_health_goals: List[str]
    foods_to_prioritize: List[FoodItemRationale]
    foods_to_avoid: List[FoodItemRationale]
    weekly_meal_plan: List[DayMealPlan]
    lifestyle_recommendations: List[str]
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# --- Trends / Analytics Schemas ---

class TrendPoint(BaseModel):
    year: int
    date: str
    value: float
    status: str
    report_id: int

class TrendSeries(BaseModel):
    test_name: str
    category: str
    unit: str
    reference_min: Optional[float]
    reference_max: Optional[float]
    points: List[TrendPoint]
