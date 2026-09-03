import pytest
from app.extractor import (
    extract_patient_name,
    extract_report_date,
    extract_lab_name,
    parse_biomarkers_from_text,
    parse_medical_report
)

SAMPLE_TEXT = """
Apollo Diagnostics
Patient Name: John Doe
Date: 15/07/2024
Report Date: 16/07/2024

Lipid Profile:
Total Cholesterol : 220 mg/dL (125-200)
LDL Cholesterol : 145 mg/dL (0-100)
HDL Cholesterol : 42 mg/dL (40-60)
Triglycerides : 170 mg/dL (0-150)

Fasting Blood Sugar : 105 mg/dL (70-99)
HbA1c : 6.1 % (4.0-5.6)
Serum Creatinine : 1.1 mg/dL (0.7-1.3)
Uric Acid : 7.6 mg/dL (3.5-7.2)
Hemoglobin : 14.5 g/dL (13.0-17.5)
Vitamin D : 18.0 ng/mL (30-100)
Blood Pressure : 130/85 mmHg
"""

def test_extract_patient_name():
    name = extract_patient_name(SAMPLE_TEXT)
    assert name == "John Doe"

def test_extract_report_date():
    date_str, year = extract_report_date(SAMPLE_TEXT)
    assert year == 2024
    assert date_str == "2024-07-15" or date_str == "2024-07-16"

def test_extract_lab_name():
    lab = extract_lab_name(SAMPLE_TEXT)
    assert "Apollo" in lab

def test_parse_biomarkers():
    biomarkers = parse_biomarkers_from_text(SAMPLE_TEXT)
    b_map = {b["test_name"]: b for b in biomarkers}

    assert "Total Cholesterol" in b_map
    assert b_map["Total Cholesterol"]["result_value"] == 220.0
    assert b_map["Total Cholesterol"]["status"] == "HIGH"

    assert "LDL Cholesterol" in b_map
    assert b_map["LDL Cholesterol"]["result_value"] == 145.0
    assert b_map["LDL Cholesterol"]["status"] == "HIGH"

    assert "HbA1c" in b_map
    assert b_map["HbA1c"]["result_value"] == 6.1
    assert b_map["HbA1c"]["status"] == "HIGH"

    assert "Vitamin D (25-OH)" in b_map
    assert b_map["Vitamin D (25-OH)"]["result_value"] == 18.0
    assert b_map["Vitamin D (25-OH)"]["status"] == "LOW"

    assert "Systolic Blood Pressure" in b_map
    assert b_map["Systolic Blood Pressure"]["result_value"] == 130.0

def test_full_pipeline():
    result = parse_medical_report(SAMPLE_TEXT)
    assert result["patient_name"] == "John Doe"
    assert result["report_year"] == 2024
    assert len(result["biomarkers"]) >= 8


APOLLO_PROHEALTH_SAMPLE = """
NAME
Mrs. PUVIARASI MJ
UHID
AHA1.0000267193
ASSESSMENT DATE
18/08/2026
Apollo Speciality Hospitals, Vanagaram

Lab parameters needing attention
Hemoglobin (SLS) Reading
9.6
gm%
Ref range
12-15

Packed cell volume (Cumulative Pulse Height Detection) Reading
35
%
Ref range
36-46

Glycosylated Hemoglobin (HbA1c) Reading
5.9
%
Ref range
0-5.7

LDL Cholesterol (Direct LDL) Reading
172
mg/dL
Ref range
0-130

Vitamin D Total(250H vitD3 and 250H vitD2) Reading
19.8
ng/mL
Ref range
30-80

Diagnostic Summary
Total Cholesterol 223
mg/dL
0 239 0-239

Triglycerides - Serum 95
mg/dL
0 150 0-150

Creatinine - Serum 0.66
mg/dL
0.5 0.9 0.5-0.9
"""

def test_apollo_prohealth_extraction():
    res = parse_medical_report(APOLLO_PROHEALTH_SAMPLE)
    assert res["patient_name"] == "Mrs. PUVIARASI MJ"
    assert res["report_year"] == 2026
    assert res["report_date"] == "2026-08-18"
    assert "Apollo" in res["hospital_lab_name"]

    b_map = {b["test_name"]: b for b in res["biomarkers"]}
    assert "Hemoglobin" in b_map
    assert b_map["Hemoglobin"]["result_value"] == 9.6
    assert b_map["Hemoglobin"]["status"] == "LOW"

    assert "HbA1c" in b_map
    assert b_map["HbA1c"]["result_value"] == 5.9
    assert b_map["HbA1c"]["status"] == "HIGH"

    assert "LDL Cholesterol" in b_map
    assert b_map["LDL Cholesterol"]["result_value"] == 172.0
    assert b_map["LDL Cholesterol"]["status"] == "HIGH"

    assert "Vitamin D (25-OH)" in b_map
    assert b_map["Vitamin D (25-OH)"]["result_value"] == 19.8
    assert b_map["Vitamin D (25-OH)"]["status"] == "LOW"

def test_hdl_and_lipid_wholistic_extraction():
    # Test 1: Apollo 2026 Diagnostic Summary format
    sample_2026 = """
    Lab parameters needing attention
    Total Cholesterol / HDL Cholesterol Ratio (Calculated) Reading
    5.4
    Ref range
    0–4.5
    NON-HDL CHOLESTEROL Reading
    182
    mg/dL
    Ref range
    0–130
    Diagnostic Summary
    HDL Cholesterol 41
    mg/dL
    39 150 39-150
    Total Cholesterol 223
    mg/dL
    0 239 0-239
    Triglycerides - Serum 95
    mg/dL
    0 150 0-150
    """
    res_2026 = parse_medical_report(sample_2026)
    b_2026 = {b["test_name"]: b for b in res_2026["biomarkers"]}
    
    # Verify HDL is 41 and NORMAL (not 5.4, not HIGH)
    assert "HDL Cholesterol" in b_2026
    assert b_2026["HDL Cholesterol"]["result_value"] == 41.0
    assert b_2026["HDL Cholesterol"]["status"] == "NORMAL"
    assert b_2026["HDL Cholesterol"]["reference_min"] == 40.0
    assert b_2026["HDL Cholesterol"]["reference_max"] == 60.0

    # Verify Total Cholesterol / HDL Ratio is 5.4 and HIGH
    assert "Total Cholesterol / HDL Ratio" in b_2026
    assert b_2026["Total Cholesterol / HDL Ratio"]["result_value"] == 5.4
    assert b_2026["Total Cholesterol / HDL Ratio"]["status"] == "HIGH"

    # Verify Non-HDL is 182 and HIGH
    assert "Non-HDL Cholesterol" in b_2026
    assert b_2026["Non-HDL Cholesterol"]["result_value"] == 182.0
    assert b_2026["Non-HDL Cholesterol"]["status"] == "HIGH"

    # Test 2: Apollo 2025 Biochemistry format
    sample_2025 = """
    CHOLESTEROL - SERUM / PLASMA
    220 *CHOLESTEROL - SERUM / PLASMA
    mg/dLLow: <4044HDL CHOLESTEROL - SERUM / PLASMA
    150 *LDL CHOLESTEROL - SERUM / PLASMA (DIRECT LDL)
    119TRIGLYCERIDES - SERUM
    TOTAL CHOLESTEROL/HDL CHOLESTEROL RATIO(Calculated) 5.0 * < 4.5
    """
    res_2025 = parse_medical_report(sample_2025)
    b_2025 = {b["test_name"]: b for b in res_2025["biomarkers"]}

    assert "HDL Cholesterol" in b_2025
    assert b_2025["HDL Cholesterol"]["result_value"] == 44.0
    assert b_2025["HDL Cholesterol"]["status"] == "NORMAL"
    assert b_2025["HDL Cholesterol"]["reference_min"] == 40.0
    assert b_2025["HDL Cholesterol"]["reference_max"] == 60.0

    assert "Total Cholesterol" in b_2025
    assert b_2025["Total Cholesterol"]["result_value"] == 220.0
    assert b_2025["Total Cholesterol"]["status"] == "HIGH"

    assert "Total Cholesterol / HDL Ratio" in b_2025
    assert b_2025["Total Cholesterol / HDL Ratio"]["result_value"] == 5.0
    assert b_2025["Total Cholesterol / HDL Ratio"]["status"] == "HIGH"


def test_puvi_2025_full_actual_report():
    actual_2025_text = """
DEPARTMENT OF BIOCHEMISTRY
Mrs. PUVIARASI MJ
Collected on 05-FEB-2025 08:10:03 AM
Apollo ProHealth Master Health Program
TEST NAME RESULT BIOLOGICAL REFERENCE INTERVALS UNITS
GLUCOSE - SERUM / PLASMA (FASTING) 85 Adult: 70 - 100 mg/dl mg/dL
(GOD/POD)
UREA - SERUM
(UREASE-GLDH-UV)
UREA - SERUM / PLASMA 18 Adult: 13 - 43 mg/dL
CREATININE - SERUM
(Jaffe Kinetic)
CREATININE - SERUM / PLASMA 0.7 Female: 0.6 - 1.1 mg/dL
Healthy adults: ≥ 90 ml/min/1.73 m2
Mild Decrease: 60 – 89 
Moderate Decrease: 30 – 59 
Severe Decrease: 15 – 29 
CKD: <15
eGFR(Calculated) 117
URIC ACID - SERUM 3.7 Adult Female: 2.6 - 6.0 mg/dL
(URICASE/PEROXIDASE)
CHOLESTEROL - SERUM
(Enzymatic Method)
Adult Desirable: <200 mg/dL
Borderline High: 200 - 239
High: >=240
CHOLESTEROL - SERUM / PLASMA 220 *
HDL CHOLESTEROL - SERUM
(Direct PEG)
HDL CHOLESTEROL - SERUM / PLASMA 44 Low: <40 mg/dL
Optimal: <100 mg/dL
Near/above optimal: 100 - 129
Borderline High: 130 - 159
High: 160 - 189
Very High: >=190
LDL CHOLESTEROL - SERUM / PLASMA (DIRECT 150 *
LDL)
Normal: <150 mg/dL
High: 150 - 199
Hypertriglyceridemic: 200 - 499
Very High: >=500
TRIGLYCERIDES - SERUM 119
(GLYCEROL 3 PHOSPHATE OXIDASE - GPO)
TOTAL CHOLESTEROL/HDL CHOLESTEROL 
RATIO(Calculated)
5.0 * < 4.5
BILIRUBIN, TOTAL - SERUM 0.3 Adult : Upto 1.0 mg/dL
(VANADATE OXIDATION)
BILIRUBIN CONJUGATED (DIRECT) - SERUM 0.1 0.0 - 0.2 mg/dL
(VANADATE OXIDATION)
BILIRUBIN UNCONJUGATED - 0.2 0.0 - 1.0 mg/dL
SERUM(Calculated)
PROTEIN TOTAL - SERUM
(Biuret)
PROTEIN TOTAL - SERUM / PLASMA 6.5 >2 Year: 6.0 - 8.0 g/dL
ALBUMIN - SERUM 3.7 Adult(20 - 60 Yr): 3.5 - 5.2 g/dL
(BCG)
GLOBULIN - SERUM:(Calculated) 2.8 Adult (2.0 - 3.5) g/dL
AST (SGOT) - SERUM 10 Adult Female: <31 U/L
(IFCC)
ALT(SGPT) - SERUM / PLASMA 12 Adult Female : <34 U/L
GGTP: GAMMA GLUTAMYL TRANSPEPTIDASE - 20 Female: < 38 U/L
SERUM
ALKALINE PHOSPHATASE - SERUM/PLASMA 80 Adult(Female): < 104 U/L
GLYCOSYLATED HEMOGLOBIN (HBA1C) - 6.1 * 4 - 6 % (NGSP) %
WHOLE BLOOD
HEMOGRAM : (Automation)
Hemoglobin(Optical/Impedance) 9.9 * 11.5 - 16.5 gm%
Packed cell volume(Calculated) 35 * 37 - 47 %
WBC Count(Optical/Impedance) 9.04 4 - 11 10³/mm³
Platelet Count(Optical/Impedance) 312 150 - 450 10³/mm³
ESR(Automated - Westergren method) 11 0 - 20 mm/hr
RBC COUNT(Optical/Impedance) 5.2 3.7 - 5.6 Million/ul
MCV(Optical/Impedance) 68 * 75 - 95 fl
MCH(Calculated) 19 * 26 - 32 pg
MCHC(Calculated) 28 * 31 - 36 g/dl
Neutrophils 64 40 - 80 %
Lymphocytes 29 20 - 40 %
Eosinophils 01 01 - 06 %
Monocytes 06 2 - 10 %
RDW (Derived from RBC histogram) 14.8 * 11.6 - 14.5
Child/Adult: 210 - 440 pg/dL
FREE T3 - SERUM 389
Adult(21 - 87 yrs): 0.8 - 2.7 ng/dL
FREE T4 - SERUM 1.3
Adults(21 - 54 Years): 0.4 - 4.2 µIU/mL
TSH: THYROID STIMULATING HORMONE - 4.3 *
SERUM
"""
    res = parse_medical_report(actual_2025_text)
    assert res["patient_name"] == "Mrs. PUVIARASI MJ"
    assert res["report_year"] == 2025
    assert res["report_date"] == "2025-02-05"

    b = {item["test_name"]: item for item in res["biomarkers"]}

    # Core Lipids
    assert b["Total Cholesterol"]["result_value"] == 220.0
    assert b["Total Cholesterol"]["status"] == "HIGH"

    assert b["HDL Cholesterol"]["result_value"] == 44.0
    assert b["HDL Cholesterol"]["status"] == "NORMAL"

    assert b["LDL Cholesterol"]["result_value"] == 150.0
    assert b["LDL Cholesterol"]["status"] == "HIGH"

    assert b["Triglycerides"]["result_value"] == 119.0
    assert b["Triglycerides"]["status"] == "NORMAL"

    assert b["Total Cholesterol / HDL Ratio"]["result_value"] == 5.0
    assert b["Total Cholesterol / HDL Ratio"]["status"] == "HIGH"

    # Sugar & HbA1c
    assert b["Fasting Blood Sugar"]["result_value"] == 85.0
    assert b["Fasting Blood Sugar"]["status"] == "NORMAL"

    assert b["HbA1c"]["result_value"] == 6.1
    assert b["HbA1c"]["status"] == "HIGH"

    # CBC
    assert b["Hemoglobin"]["result_value"] == 9.9
    assert b["Hemoglobin"]["status"] == "LOW"

    assert b["Packed Cell Volume (PCV)"]["result_value"] == 35.0
    assert b["Packed Cell Volume (PCV)"]["status"] == "LOW"

    assert b["Total WBC Count"]["result_value"] == 9.04
    assert b["Total WBC Count"]["status"] == "NORMAL"

    assert b["Platelet Count"]["result_value"] == 312.0
    assert b["Platelet Count"]["status"] == "NORMAL"

    assert b["ESR"]["result_value"] == 11.0
    assert b["ESR"]["status"] == "NORMAL"

    assert b["RBC Count"]["result_value"] == 5.2
    assert b["RBC Count"]["status"] == "NORMAL"

    assert b["MCV"]["result_value"] == 68.0
    assert b["MCV"]["status"] == "LOW"

    assert b["MCH"]["result_value"] == 19.0
    assert b["MCH"]["status"] == "LOW"

    assert b["MCHC"]["result_value"] == 28.0
    assert b["MCHC"]["status"] == "LOW"

    assert b["RDW"]["result_value"] == 14.8
    assert b["RDW"]["status"] == "HIGH"

    assert b["Neutrophils"]["result_value"] == 64.0
    assert b["Neutrophils"]["status"] == "NORMAL"

    assert b["Lymphocytes"]["result_value"] == 29.0
    assert b["Lymphocytes"]["status"] == "NORMAL"

    assert b["Eosinophils"]["result_value"] == 1.0
    assert b["Eosinophils"]["status"] == "NORMAL"

    assert b["Monocytes"]["result_value"] == 6.0
    assert b["Monocytes"]["status"] == "NORMAL"

    # Kidney / Electrolytes
    assert b["Serum Urea"]["result_value"] == 18.0
    assert b["Serum Urea"]["status"] == "NORMAL"

    assert b["Serum Creatinine"]["result_value"] == 0.7
    assert b["Serum Creatinine"]["status"] == "NORMAL"

    assert b["Uric Acid"]["result_value"] == 3.7
    assert b["Uric Acid"]["status"] == "NORMAL"

    assert b["eGFR"]["result_value"] == 117.0
    assert b["eGFR"]["status"] == "NORMAL"

    # Liver Function
    assert b["Bilirubin Total"]["result_value"] == 0.3
    assert b["Bilirubin Total"]["status"] == "NORMAL"

    assert b["Bilirubin Direct"]["result_value"] == 0.1
    assert b["Bilirubin Direct"]["status"] == "NORMAL"

    assert b["Bilirubin Indirect"]["result_value"] == 0.2
    assert b["Bilirubin Indirect"]["status"] == "NORMAL"

    assert b["Total Protein"]["result_value"] == 6.5
    assert b["Total Protein"]["status"] == "NORMAL"

    assert b["Serum Albumin"]["result_value"] == 3.7
    assert b["Serum Albumin"]["status"] == "NORMAL"

    assert b["Serum Globulin"]["result_value"] == 2.8
    assert b["Serum Globulin"]["status"] == "NORMAL"

    assert b["SGOT (AST)"]["result_value"] == 10.0
    assert b["SGOT (AST)"]["status"] == "NORMAL"

    assert b["SGPT (ALT)"]["result_value"] == 12.0
    assert b["SGPT (ALT)"]["status"] == "NORMAL"

    assert b["Alkaline Phosphatase"]["result_value"] == 80.0
    assert b["Alkaline Phosphatase"]["status"] == "NORMAL"

    assert b["GGTP"]["result_value"] == 20.0
    assert b["GGTP"]["status"] == "NORMAL"

    # Thyroid
    assert b["TSH"]["result_value"] == 4.3
    assert b["TSH"]["status"] == "HIGH"

    assert b["Free T3"]["result_value"] == 389.0
    assert b["Free T3"]["status"] == "NORMAL"

    assert b["Free T4"]["result_value"] == 1.3
    assert b["Free T4"]["status"] == "NORMAL"


def test_puvi_2025_pypdf_raw_stream():
    raw_pypdf_text = """
DEPARTMENT OF BIOCHEMISTRY
Mrs. PUVIARASI  MJ
Collected on 05-FEB-2025 08:10:03 AM
Apollo ProHealth Master Health Program
TEST NAME RESULT BIOLOGICAL REFERENCE INTERVALS UNITS
mg/dLAdult: 70 - 100 mg/dl85GLUCOSE - SERUM / PLASMA (FASTING)
(GOD/POD)
UREA - SERUM
(UREASE-GLDH-UV)
mg/dLAdult: 13 - 4318UREA - SERUM / PLASMA
CREATININE - SERUM
(Jaffe Kinetic)
mg/dLFemale: 0.6 - 1.10.7CREATININE - SERUM / PLASMA
117eGFR(Calculated)
mg/dLAdult Female: 2.6 - 6.03.7URIC ACID - SERUM
(URICASE/PEROXIDASE)
CHOLESTEROL - SERUM
(Enzymatic Method)
220 *CHOLESTEROL - SERUM / PLASMA
HDL CHOLESTEROL - SERUM
(Direct PEG)
mg/dLLow: <4044HDL CHOLESTEROL - SERUM / PLASMA
150 *LDL CHOLESTEROL - SERUM / PLASMA (DIRECT
LDL)
119TRIGLYCERIDES - SERUM
(GLYCEROL 3 PHOSPHATE OXIDASE - GPO)
TOTAL CHOLESTEROL/HDL CHOLESTEROL
RATIO(Calculated)
5.0 * < 4.5
mg/dLAdult : Upto 1.00.3BILIRUBIN, TOTAL - SERUM
(VANADATE OXIDATION)
mg/dL0.0  -  0.20.1BILIRUBIN CONJUGATED (DIRECT) - SERUM
(VANADATE OXIDATION)
mg/dL0.0  -  1.00.2BILIRUBIN UNCONJUGATED -
SERUM(Calculated)
PROTEIN TOTAL - SERUM
(Biuret)
g/dL>2 Year: 6.0 - 8.06.5PROTEIN TOTAL - SERUM / PLASMA
g/dLAdult(20 - 60 Yr): 3.5 - 5.23.7ALBUMIN - SERUM
(BCG)
g/dLAdult (2.0 - 3.5)2.8GLOBULIN - SERUM:(Calculated)
U/LAdult Female: <3110AST (SGOT) - SERUM
(IFCC)
ALT(SGPT) - SERUM
(IFCC)
U/LAdult Female : <3412ALT(SGPT) - SERUM / PLASMA
U/LFemale: < 3820GGTP: GAMMA GLUTAMYL TRANSPEPTIDASE -
SERUM
(Modified IFCC Method)
ALKALINE PHOSPHATASE - SERUM
(IFCC Modified AMP buffer)
U/LAdult(Female): < 10480ALKALINE PHOSPHATASE - SERUM/PLASMA
%4 - 6 % (NGSP)6.1 *GLYCOSYLATED HEMOGLOBIN (HBA1C) -
WHOLE BLOOD
HEMOGRAM : (Automation)
Hemoglobin(Optical/Impedance) 11.5  -  16.5 gm%9.9 *
Packed cell volume(Calculated) 37  -  47 %35 *
WBC Count(Optical/Impedance) 4  -  11 10?/mm?9.04
Platelet Count(Optical/Impedance) 150  -  450 10?/mm?312
ESR(Automated - Westergren method) 0  -  20 mm/hr11
RBC COUNT(Optical/Impedance) 3.7  -  5.6 Million/ul5.2
MCV(Optical/Impedance) 75  -  95 fl68 *
MCH(Calculated) 26  -  32 pg19 *
MCHC(Calculated) 31  -  36 g/dl28 *
Differential Count(Optical/Impedance/Microscopy)
Neutrophils 40  -  80 %64
Lymphocytes 20 - 40 %29
Eosinophils 01  -  06 %01
Monocytes 2  -  10 %06
RDW (Derived from RBC histogram) 14.8 * 11.6  -  14.5
FREE T3 - SERUM 389
FREE T4 - SERUM 1.3
TSH: THYROID STIMULATING HORMONE - 4.3 *
"""
    res = parse_medical_report(raw_pypdf_text)
    b = {item["test_name"]: item for item in res["biomarkers"]}

    assert b["Alkaline Phosphatase"]["result_value"] == 80.0
    assert b["Alkaline Phosphatase"]["status"] == "NORMAL"

    assert b["SGPT (ALT)"]["result_value"] == 12.0
    assert b["SGPT (ALT)"]["status"] == "NORMAL"

    assert b["SGOT (AST)"]["result_value"] == 10.0
    assert b["SGOT (AST)"]["status"] == "NORMAL"

    assert b["GGTP"]["result_value"] == 20.0
    assert b["GGTP"]["status"] == "NORMAL"

    assert b["HDL Cholesterol"]["result_value"] == 44.0
    assert b["HDL Cholesterol"]["status"] == "NORMAL"

    assert b["Total Cholesterol"]["result_value"] == 220.0
    assert b["Total Cholesterol"]["status"] == "HIGH"

    assert b["LDL Cholesterol"]["result_value"] == 150.0
    assert b["LDL Cholesterol"]["status"] == "HIGH"

    assert b["Triglycerides"]["result_value"] == 119.0
    assert b["Triglycerides"]["status"] == "NORMAL"

    assert b["Total Cholesterol / HDL Ratio"]["result_value"] == 5.0
    assert b["Total Cholesterol / HDL Ratio"]["status"] == "HIGH"

    assert b["Fasting Blood Sugar"]["result_value"] == 85.0
    assert b["Fasting Blood Sugar"]["status"] == "NORMAL"

    assert b["HbA1c"]["result_value"] == 6.1
    assert b["HbA1c"]["status"] == "HIGH"

    assert b["Serum Urea"]["result_value"] == 18.0
    assert b["Serum Urea"]["status"] == "NORMAL"

    assert b["Serum Creatinine"]["result_value"] == 0.7
    assert b["Serum Creatinine"]["status"] == "NORMAL"

    assert b["Uric Acid"]["result_value"] == 3.7
    assert b["Uric Acid"]["status"] == "NORMAL"

    assert b["eGFR"]["result_value"] == 117.0
    assert b["eGFR"]["status"] == "NORMAL"

    assert b["Bilirubin Total"]["result_value"] == 0.3
    assert b["Bilirubin Direct"]["result_value"] == 0.1
    assert b["Bilirubin Indirect"]["result_value"] == 0.2

    assert b["Total Protein"]["result_value"] == 6.5
    assert b["Serum Albumin"]["result_value"] == 3.7
    assert b["Serum Globulin"]["result_value"] == 2.8

    assert b["Hemoglobin"]["result_value"] == 9.9
    assert b["Packed Cell Volume (PCV)"]["result_value"] == 35.0
    assert b["Total WBC Count"]["result_value"] == 9.04
    assert b["Platelet Count"]["result_value"] == 312.0
    assert b["ESR"]["result_value"] == 11.0
    assert b["RBC Count"]["result_value"] == 5.2
    assert b["MCV"]["result_value"] == 68.0
    assert b["MCH"]["result_value"] == 19.0
    assert b["MCHC"]["result_value"] == 28.0
    assert b["RDW"]["result_value"] == 14.8
    assert b["Neutrophils"]["result_value"] == 64.0
    assert b["Lymphocytes"]["result_value"] == 29.0
    assert b["Eosinophils"]["result_value"] == 1.0
    assert b["Monocytes"]["result_value"] == 6.0

    assert b["TSH"]["result_value"] == 4.3
    assert b["Free T3"]["result_value"] == 389.0
    assert b["Free T4"]["result_value"] == 1.3


def test_dr_lal_pathlabs_arun_2025():
    sample_text = """
Dr Lal PathLabs
Name : Mr. ARUN KUMAR
Age : 47 Years
Gender : Male
Reported : 1/10/2025 6:29:25PM
Test Name Results Units Bio. Ref. Interval
LIPID PROFILE, SCREEN
Cholesterol, Total 203.10
(CHO-POD)
mg/dL <200.00 
Triglycerides 110.40
(GPO-POD)
mg/dL <150.00 
HDL Cholesterol 47.70
(CHO-POD)
mg/dL >40.00 
LDL Cholesterol, Calculated 133.32
(Calculated)
mg/dL <100.00 
VLDL Cholesterol,Calculated 22.08
(Calculated)
mg/dL <30.00 
Non-HDL Cholesterol 155
(Calculated)
mg/dL <130 
GLUCOSE, FASTING
Glucose Fasting 92.00 mg/dL 70.00 - 100.00
HbA1c 6.4 % 4.00 - 5.60
"""
    res = parse_medical_report(sample_text)
    assert res["patient_name"] == "Mr. ARUN KUMAR"
    assert res["report_year"] == 2025
    assert "Lal" in res["hospital_lab_name"]

    b = {item["test_name"]: item for item in res["biomarkers"]}
    assert b["HDL Cholesterol"]["result_value"] == 47.70
    assert b["HDL Cholesterol"]["status"] == "NORMAL"
    assert b["HDL Cholesterol"]["reference_min"] == 40.0

    assert b["Total Cholesterol"]["result_value"] == 203.10
    assert b["Total Cholesterol"]["status"] == "HIGH"

    assert b["Triglycerides"]["result_value"] == 110.40
    assert b["Triglycerides"]["status"] == "NORMAL"

    assert b["LDL Cholesterol"]["result_value"] == 133.32
    assert b["LDL Cholesterol"]["status"] == "HIGH"

    assert b["Non-HDL Cholesterol"]["result_value"] == 155.0
    assert b["Non-HDL Cholesterol"]["status"] == "HIGH"

    assert b["Fasting Blood Sugar"]["result_value"] == 92.0
    assert b["Fasting Blood Sugar"]["status"] == "NORMAL"

    assert b["HbA1c"]["result_value"] == 6.4
    assert b["HbA1c"]["status"] == "HIGH"


def test_squished_decimal_hdl():
    # Test that a decimal HDL value with or without space extracts 47.70 and NOT 70
    t1 = "47.70HDL CHOLESTEROL - SERUM"
    res1 = parse_medical_report(t1)
    b1 = {item["test_name"]: item for item in res1["biomarkers"]}
    assert b1["HDL Cholesterol"]["result_value"] == 47.70

    t2 = "47.70 HDL CHOLESTEROL - SERUM"
    res2 = parse_medical_report(t2)
    b2 = {item["test_name"]: item for item in res2["biomarkers"]}
    assert b2["HDL Cholesterol"]["result_value"] == 47.70


def test_physician_notes_extraction():
    # Test 1: Notes present
    t1 = """
CLINICAL IMPRESSION:
Patient shows borderline elevated LDL and mild microcytic anemia. Recommended iron-rich diet and Mediterranean lifestyle.
GLUCOSE Fasting 92 mg/dL
"""
    res1 = parse_medical_report(t1)
    assert "borderline elevated LDL" in res1["physician_notes"]

    # Test 2: No notes present
    t2 = """
CHOLESTEROL 220 mg/dL
HDL CHOLESTEROL 44 mg/dL
"""
    res2 = parse_medical_report(t2)
    assert res2["physician_notes"] == ""


def test_patient_canonicalization():
    from app.main import strip_patient_title, get_canonical_patient_key

    # Test title stripping
    assert strip_patient_title("Mrs. PUVIARASI MJ") == "PUVIARASI MJ"
    assert strip_patient_title("Ms. PUVIARASI") == "PUVIARASI"
    assert strip_patient_title("Mr. ARUN KUMAR") == "ARUN KUMAR"
    assert strip_patient_title("Dr. Rajesh Sharma") == "Rajesh Sharma"

    # Test canonical grouping (both map to same key)
    key1 = get_canonical_patient_key("Mrs. PUVIARASI MJ")
    key2 = get_canonical_patient_key("Ms. PUVIARASI")
    key3 = get_canonical_patient_key("Mr. ARUN KUMAR")

    assert key1 == key2 == "PUVIARASI"
    assert key3 == "ARUN KUMAR"
    assert key1 != key3


def test_apollo_2026_page18_glucose_extraction():
    sample = """
Diagnostic Summary
Diabetic Profile
Examination Reading Ref range
GLUCOSE - PLASMA
(RANDOM)
97
mg/dL
54 140 54-140
mg/dL
Glycosylated
Hemoglobin (HbA1c)
5.9
%
0 5.7 0-5.7
%
"""
    res = parse_medical_report(sample)
    b_map = {b["test_name"]: b for b in res["biomarkers"]}

    assert "Random Blood Sugar" in b_map
    assert b_map["Random Blood Sugar"]["result_value"] == 97.0
    assert b_map["Random Blood Sugar"]["status"] == "NORMAL"
    assert b_map["Random Blood Sugar"]["unit"] == "mg/dL"
    assert b_map["Random Blood Sugar"]["reference_min"] == 54.0
    assert b_map["Random Blood Sugar"]["reference_max"] == 140.0

    assert "HbA1c" in b_map
    assert b_map["HbA1c"]["result_value"] == 5.9
    assert b_map["HbA1c"]["status"] == "HIGH"


def test_diet_planner_alcohol_avoidance():
    from app.diet_engine import create_diet_plan

    # Case 1: Report with high triglycerides and high HbA1c (alcohol avoidance required)
    biomarkers_alert = [
        {"category": "Lipid Profile", "test_name": "Triglycerides", "result_value": 210.0, "status": "HIGH"},
        {"category": "Blood Sugar / Diabetes", "test_name": "HbA1c", "result_value": 6.2, "status": "HIGH"}
    ]
    plan1 = create_diet_plan(1, "Test Patient", biomarkers_alert)
    avoid_foods1 = [item["food"] for item in plan1["foods_to_avoid"]]
    assert any("Alcohol" in f for f in avoid_foods1)
    assert any("Alcohol" in tip for tip in plan1["lifestyle_recommendations"])

    # Case 2: Clean report with normal markers (alcohol avoidance not artificially flagged)
    biomarkers_clean = [
        {"category": "Lipid Profile", "test_name": "Triglycerides", "result_value": 110.0, "status": "NORMAL"},
        {"category": "Blood Sugar / Diabetes", "test_name": "HbA1c", "result_value": 5.2, "status": "NORMAL"}
    ]
    plan2 = create_diet_plan(2, "Healthy Patient", biomarkers_clean)
    avoid_foods2 = [item["food"] for item in plan2["foods_to_avoid"]]
    assert not any("Alcohol & Alcoholic" in f for f in avoid_foods2)


def test_reject_lab_methodology_notes():
    from app.extractor import extract_physician_notes
    sample_text = """
    Comment :
    As per the recommendations of International council for Standardization in Hematology, the differential leucocyte counts are additionally being reported as absolute numbers of each cell in per unit volume of 2. Test conducted on EDTA whole blood
    """
    note = extract_physician_notes(sample_text)
    assert note == ""
