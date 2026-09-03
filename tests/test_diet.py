import pytest
from app.diet_engine import analyze_health_findings, create_diet_plan

def test_analyze_health_findings_abnormal():
    biomarkers = [
        {"test_name": "LDL Cholesterol", "result_value": 150.0, "status": "HIGH", "unit": "mg/dL"},
        {"test_name": "HbA1c", "result_value": 6.2, "status": "HIGH", "unit": "%"},
        {"test_name": "Uric Acid", "result_value": 7.8, "status": "HIGH", "unit": "mg/dL"},
        {"test_name": "Vitamin D (25-OH)", "result_value": 16.0, "status": "LOW", "unit": "ng/mL"}
    ]
    findings = analyze_health_findings(biomarkers)
    assert findings["high_cholesterol"] is True
    assert findings["high_hba1c"] is True
    assert findings["high_uric_acid"] is True
    assert findings["low_vit_d"] is True
    assert len(findings["abnormal_list"]) == 4

def test_diet_plan_generation():
    biomarkers = [
        {"test_name": "LDL Cholesterol", "result_value": 150.0, "status": "HIGH", "unit": "mg/dL"},
        {"test_name": "Triglycerides", "result_value": 190.0, "status": "HIGH", "unit": "mg/dL"},
        {"test_name": "Fasting Blood Sugar", "result_value": 112.0, "status": "HIGH", "unit": "mg/dL"}
    ]
    plan = create_diet_plan(
        report_id=1,
        patient_name="Pavithran",
        biomarkers=biomarkers,
        diet_pref="Vegetarian",
        cuisine_pref="Indian",
        calorie_target=1900
    )

    assert plan["report_id"] == 1
    assert plan["patient_name"] == "Pavithran"
    assert len(plan["primary_health_goals"]) >= 2
    assert any("Lipid" in g or "LDL" in g for g in plan["primary_health_goals"])
    assert any("Glycemic" in g or "glucose" in g for g in plan["primary_health_goals"])

    # Verify prioritization and avoid lists
    assert len(plan["foods_to_prioritize"]) >= 2
    assert len(plan["foods_to_avoid"]) >= 2

    # Verify 7-day weekly schedule
    assert len(plan["weekly_meal_plan"]) == 7
    monday = plan["weekly_meal_plan"][0]
    assert monday["day"] == "Monday"
    assert len(monday["meals"]) == 5  # 5 meal structure
