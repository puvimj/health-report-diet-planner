import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

# Comprehensive clinical reference ranges as fallback
CLINICAL_BENCHMARKS = {
    # Lipid Profile
    "Total Cholesterol": {"category": "Lipid Profile", "unit": "mg/dL", "min": 125.0, "max": 200.0},
    "LDL Cholesterol": {"category": "Lipid Profile", "unit": "mg/dL", "min": 0.0, "max": 100.0},
    "HDL Cholesterol": {"category": "Lipid Profile", "unit": "mg/dL", "min": 40.0, "max": 60.0},
    "Triglycerides": {"category": "Lipid Profile", "unit": "mg/dL", "min": 0.0, "max": 150.0},
    "VLDL Cholesterol": {"category": "Lipid Profile", "unit": "mg/dL", "min": 5.0, "max": 30.0},
    "Non-HDL Cholesterol": {"category": "Lipid Profile", "unit": "mg/dL", "min": 0.0, "max": 130.0},
    "Total Cholesterol / HDL Ratio": {"category": "Lipid Profile", "unit": "ratio", "min": 0.0, "max": 4.5},
    "Apo Lipoprotein A1": {"category": "Lipid Profile", "unit": "mg/dL", "min": 115.0, "max": 195.0},
    "Apo Lipoprotein B": {"category": "Lipid Profile", "unit": "mg/dL", "min": 75.0, "max": 136.0},

    # Blood Sugar / Diabetes
    "Fasting Blood Sugar": {"category": "Blood Sugar / Diabetes", "unit": "mg/dL", "min": 70.0, "max": 99.0},
    "Postprandial Blood Sugar": {"category": "Blood Sugar / Diabetes", "unit": "mg/dL", "min": 70.0, "max": 140.0},
    "HbA1c": {"category": "Blood Sugar / Diabetes", "unit": "%", "min": 0.0, "max": 5.7},
    "Random Blood Sugar": {"category": "Blood Sugar / Diabetes", "unit": "mg/dL", "min": 54.0, "max": 140.0},

    # Complete Blood Count (CBC) / Haemogram
    "Hemoglobin": {"category": "Complete Blood Count", "unit": "g/dL", "min": 12.0, "max": 15.5},
    "Packed Cell Volume (PCV)": {"category": "Complete Blood Count", "unit": "%", "min": 36.0, "max": 46.0},
    "RBC Count": {"category": "Complete Blood Count", "unit": "Million/ul", "min": 3.8, "max": 4.8},
    "MCV": {"category": "Complete Blood Count", "unit": "fl", "min": 83.0, "max": 101.0},
    "MCH": {"category": "Complete Blood Count", "unit": "pg", "min": 27.0, "max": 32.0},
    "MCHC": {"category": "Complete Blood Count", "unit": "g/dl", "min": 31.5, "max": 34.5},
    "RDW": {"category": "Complete Blood Count", "unit": "%", "min": 11.6, "max": 14.0},
    "Total WBC Count": {"category": "Complete Blood Count", "unit": "10³/mm³", "min": 4.0, "max": 10.0},
    "Platelet Count": {"category": "Complete Blood Count", "unit": "10³/mm³", "min": 150.0, "max": 410.0},
    "ESR": {"category": "Complete Blood Count", "unit": "mm/hr", "min": 0.0, "max": 20.0},
    "Neutrophils": {"category": "Complete Blood Count", "unit": "%", "min": 40.0, "max": 80.0},
    "Lymphocytes": {"category": "Complete Blood Count", "unit": "%", "min": 20.0, "max": 40.0},
    "Eosinophils": {"category": "Complete Blood Count", "unit": "%", "min": 1.0, "max": 6.0},
    "Monocytes": {"category": "Complete Blood Count", "unit": "%", "min": 2.0, "max": 10.0},
    "Basophils": {"category": "Complete Blood Count", "unit": "%", "min": 0.0, "max": 2.0},

    # Kidney Function Test (KFT) / Renal Profile & Electrolytes
    "Serum Creatinine": {"category": "Kidney Function", "unit": "mg/dL", "min": 0.5, "max": 0.9},
    "Blood Urea Nitrogen": {"category": "Kidney Function", "unit": "mg/dL", "min": 7.0, "max": 20.0},
    "Serum Urea": {"category": "Kidney Function", "unit": "mg/dL", "min": 13.0, "max": 43.0},
    "Uric Acid": {"category": "Kidney Function", "unit": "mg/dL", "min": 2.5, "max": 6.0},
    "eGFR": {"category": "Kidney Function", "unit": "mL/min/1.73m2", "min": 90.0, "max": 120.0},
    "Sodium": {"category": "Kidney Function", "unit": "mEq/L", "min": 136.0, "max": 145.0},
    "Potassium": {"category": "Kidney Function", "unit": "mEq/L", "min": 3.4, "max": 5.1},
    "Chloride": {"category": "Kidney Function", "unit": "mEq/L", "min": 98.0, "max": 107.0},
    "Carbon Dioxide (CO2)": {"category": "Kidney Function", "unit": "mEq/L", "min": 19.0, "max": 29.0},

    # Liver Function Test (LFT)
    "SGPT (ALT)": {"category": "Liver Function", "unit": "U/L", "min": 10.0, "max": 50.0},
    "SGOT (AST)": {"category": "Liver Function", "unit": "U/L", "min": 10.0, "max": 35.0},
    "Bilirubin Total": {"category": "Liver Function", "unit": "mg/dL", "min": 0.0, "max": 1.2},
    "Bilirubin Direct": {"category": "Liver Function", "unit": "mg/dL", "min": 0.0, "max": 0.4},
    "Bilirubin Indirect": {"category": "Liver Function", "unit": "mg/dL", "min": 0.0, "max": 1.0},
    "Alkaline Phosphatase": {"category": "Liver Function", "unit": "U/L", "min": 35.0, "max": 104.0},
    "Total Protein": {"category": "Liver Function", "unit": "g/dL", "min": 6.4, "max": 8.3},
    "Serum Albumin": {"category": "Liver Function", "unit": "g/dL", "min": 3.5, "max": 5.2},
    "Serum Globulin": {"category": "Liver Function", "unit": "g/dL", "min": 2.0, "max": 3.5},
    "Albumin/Globulin Ratio": {"category": "Liver Function", "unit": "ratio", "min": 1.1, "max": 2.0},
    "GGTP": {"category": "Liver Function", "unit": "U/L", "min": 6.0, "max": 42.0},

    # Thyroid & Vitamins
    "TSH": {"category": "Thyroid & Vitamins", "unit": "µIU/mL", "min": 0.27, "max": 4.2},
    "Free T3": {"category": "Thyroid & Vitamins", "unit": "pg/dL", "min": 210.0, "max": 440.0},
    "Free T4": {"category": "Thyroid & Vitamins", "unit": "ng/dL", "min": 0.8, "max": 2.7},
    "Vitamin D (25-OH)": {"category": "Thyroid & Vitamins", "unit": "ng/mL", "min": 30.0, "max": 80.0},
    "Vitamin B12": {"category": "Thyroid & Vitamins", "unit": "pg/mL", "min": 197.0, "max": 771.0},
    "Serum Calcium": {"category": "Thyroid & Vitamins", "unit": "mg/dL", "min": 8.6, "max": 10.0},
    "Phosphorus": {"category": "Thyroid & Vitamins", "unit": "mg/dL", "min": 2.5, "max": 4.5},

    # Vitals
    "Systolic Blood Pressure": {"category": "Vitals", "unit": "mmHg", "min": 90.0, "max": 120.0},
    "Diastolic Blood Pressure": {"category": "Vitals", "unit": "mmHg", "min": 60.0, "max": 90.0},
    "Heart Rate": {"category": "Vitals", "unit": "/min", "min": 60.0, "max": 90.0},
    "BMI": {"category": "Vitals", "unit": "kg/m2", "min": 18.5, "max": 24.9}
}

# Regex synonym mappings to identify standard tests across various hospital formats
TEST_SYNONYMS = {
    # Lipids (Composite and specific tests MUST come before base tests to prevent collision)
    "Total Cholesterol / HDL Ratio": [
        r"total\s*cholesterol\s*\/\s*hdl(?:\s*cholesterol)?(?:\s*ratio)?",
        r"total\s*cholesterol\s*-\s*hdl(?:\s*cholesterol)?\s*ratio",
        r"cholesterol\s*-\s*hdl\s*ratio",
        r"total\/hdl\s*ratio"
    ],
    "Non-HDL Cholesterol": [
        r"\bnon\s*-\s*hdl\s*cholesterol",
        r"\bnon\s*hdl\s*cholesterol",
        r"\bnon\s*-\s*hdl\b",
        r"\bnon\s*hdl\b"
    ],
    "HDL Cholesterol": [
        r"(?<!non[\s\-])(?<!\/)\bhdl(?:\s*-\s*cholesterol|\s*cholesterol)\b(?!\s*(?:ratio|\/))",
        r"(?<!non[\s\-])(?<!\/)\bhdl\b(?!\s*(?:ratio|\/))",
        r"high\s*density\s*lipoprotein"
    ],
    "Total Cholesterol": [
        r"(?<!\/)\btotal\s*cholesterol(?!\s*(?:ratio|\/|\s*hdl))",
        r"cholesterol\s*-\s*serum\s*\/\s*plasma",
        r"(?<!\/)\bcholesterol\s*-\s*serum(?!\s*\/[^\w]*hdl)",
        r"cholesterol[,\s-]*total"
    ],
    "LDL Cholesterol": [
        r"ldl\s*cholesterol\s*\(direct\s*ldl\)",
        r"ldl(?:\s*-\s*cholesterol|\s*cholesterol|\s*calculated|\s*direct)?",
        r"low\s*density\s*lipoprotein"
    ],
    "Triglycerides": [
        r"triglycerides?\s*-\s*serum",
        r"triglycerides?",
        r"serum\s*triglycerides?"
    ],
    "VLDL Cholesterol": [
        r"vldl(?:\s*-\s*cholesterol|\s*cholesterol|\s*\(calculated\))?",
        r"vldl\s*cholesterol\s*-\s*serum"
    ],
    "Apo Lipoprotein A1": [r"apo\s*lipoprotein\s*a1(?:\s*-\s*serum)?"],
    "Apo Lipoprotein B": [r"apo\s*lipoprotein\s*b(?:\s*-\s*serum)?"],

    # Sugar
    "Fasting Blood Sugar": [
        r"glucose.*?fasting",
        r"fasting.*?glucose",
        r"fasting\s*(?:blood\s*)?(?:sugar|glucose)",
        r"glucose[,\s-]*fasting",
        r"glucose\s*-\s*serum\s*\/\s*plasma\s*\(fasting\)",
        r"\bfbs\b"
    ],
    "Postprandial Blood Sugar": [r"post\s*prandial\s*(?:blood\s*)?(?:sugar|glucose)", r"glucose[,\s-]*post\s*prandial", r"\bppbs\b"],
    "HbA1c": [r"glycosylated\s*hemoglobin\s*\(hba1c\)", r"hba1c", r"glycated\s*hemoglobin"],
    "Random Blood Sugar": [
        r"glucose\s*-\s*plasma\s*\(random\)",
        r"glucose.*?random",
        r"random.*?glucose",
        r"random\s*(?:blood\s*)?(?:sugar|glucose)",
        r"glucose[,\s-]*random",
        r"\brbs\b",
        r"glucose\s*-\s*plasma"
    ],

    # CBC
    "Hemoglobin": [r"hemoglobin\s*\(sls\)", r"hemoglobin", r"\bhb\b", r"haemoglobin"],
    "Packed Cell Volume (PCV)": [r"packed\s*cell\s*volume", r"\bpcv\b", r"hematocrit"],
    "RBC Count": [r"rbc\s*count", r"red\s*blood\s*(?:cell|count)"],
    "MCV": [r"\bmcv\b", r"mean\s*corpuscular\s*volume"],
    "MCH": [r"mch\s*\(calculated\)", r"\bmch\b"],
    "MCHC": [r"mchc\s*\(calculated\)", r"\bmchc\b"],
    "RDW": [r"\brdw\b", r"red\s*cell\s*distribution\s*width"],
    "Total WBC Count": [r"wbc\s*count\s*\(fluorescense\s*flow\s*cytometry\)", r"total\s*wbc(?:\s*count)?", r"wbc\s*count", r"\btlc\b", r"\bwbc\b"],
    "Platelet Count": [r"platelet\s*count", r"platelets?"],
    "ESR": [r"\besr\b", r"erythrocyte\s*sedimentation"],
    "Neutrophils": [r"neutrophils?"],
    "Lymphocytes": [r"lymphocytes?"],
    "Eosinophils": [r"eosinophils?"],
    "Monocytes": [r"monocytes?"],
    "Basophils": [r"basophils?"],

    # Kidney / Electrolytes
    "Serum Creatinine": [r"creatinine\s*-\s*serum", r"serum\s*creatinine", r"\bcreatinine\b"],
    "Serum Urea": [r"\burea\b", r"serum\s*urea"],
    "Blood Urea Nitrogen": [r"blood\s*urea\s*nitrogen", r"\bbun\b"],
    "Uric Acid": [r"uric\s*acid\s*-\s*serum", r"serum\s*uric\s*acid", r"uric\s*acid"],
    "eGFR": [r"\begfr\b", r"estimated\s*gfr"],
    "Sodium": [r"\bsodium\b", r"serum\s*sodium"],
    "Potassium": [r"\bpotassium\b", r"serum\s*potassium"],
    "Chloride": [r"\bchloride\b", r"serum\s*chloride"],
    "Carbon Dioxide (CO2)": [r"carbon\s*dioxide\s*\(co2\)", r"\bco2\b"],

    # Liver
    "SGPT (ALT)": [r"alt\s*\(sgpt\)\s*-\s*serum", r"sgpt\s*\(alt\)", r"\bsgpt\b", r"\balt\b", r"alanine\s*aminotransferase"],
    "SGOT (AST)": [r"ast\s*\(sgot\)\s*-\s*serum", r"sgot\s*\(ast\)", r"\bsgot\b", r"\bast\b", r"aspartate\s*aminotransferase"],
    "Bilirubin Total": [r"bilirubin[,\s-]*total\s*-\s*serum", r"bilirubin[,\s-]*total", r"total\s*bilirubin"],
    "Bilirubin Direct": [r"bilirubin\s*conjugated\s*\(direct\)", r"bilirubin[,\s-]*direct", r"direct\s*bilirubin"],
    "Bilirubin Indirect": [r"bilirubin\s*unconjugated", r"indirect\s*bilirubin"],
    "Alkaline Phosphatase": [r"alkaline\s*phosphatase\s*-\s*serum", r"alkaline\s*phosphatase", r"\balp\b"],
    "Total Protein": [r"protein\s*total\s*-\s*serum", r"total\s*proteins?"],
    "Serum Albumin": [r"albumin\s*-\s*serum", r"\balbumin\b"],
    "Serum Globulin": [r"globulin\s*-\s*serum", r"\bglobulin\b"],
    "Albumin/Globulin Ratio": [r"albumin\s*\/\s*globulin\s*ratio", r"a\/g\s*ratio"],
    "GGTP": [r"ggtp", r"gamma\s*glutamyl\s*transpeptidase"],

    # Thyroid & Vitamins
    "TSH": [r"tsh\s*:\s*thyroid\s*stimulating\s*hormone", r"tsh", r"thyroid\s*stimulating\s*hormone"],
    "Free T3": [r"free\s*t3\b"],
    "Free T4": [r"free\s*t4\b"],
    "Vitamin D (25-OH)": [r"vitamin\s*d\s*total\s*\(250?h\s*vitd3\s*and\s*250?h\s*vitd2\)", r"vitamin\s*d(?:3|\s*25-oh)?", r"25\s*-\s*hydroxy\s*vitamin\s*d"],
    "Vitamin B12": [r"vitamin\s*b12", r"cyanocobalamin", r"\bb12\b"],
    "Serum Calcium": [r"calcium\s*-\s*serum", r"serum\s*calcium", r"\bcalcium\b"],
    "Phosphorus": [r"phosphorus[,\s-]*inorganic\s*-\s*serum", r"phosphorus"],

    # Vitals
    "Systolic Blood Pressure": [r"systolic\s*blood\s*pressure", r"systolic\s*bp", r"bp\s*-\s*systolic"],
    "Diastolic Blood Pressure": [r"diastolic\s*blood\s*pressure", r"diastolic\s*bp", r"bp\s*-\s*diastolic"],
    "Heart Rate": [r"heart\s*rate", r"pulse\s*rate", r"\bpulse\b"],
    "BMI": [r"\bbmi\b", r"body\s*mass\s*index"]
}


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extracts raw text from a PDF file using pypdf."""
    text_content = []
    try:
        from pypdf import PdfReader
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_content.append(page_text)
    except Exception as e:
        print(f"Error extracting with pypdf: {e}")
    
    return "\n".join(text_content)


def extract_patient_name(text: str) -> str:
    """Extracts patient name, recognizing Apollo ProHealth and standard formats."""
    # Pattern 1: Apollo ProHealth "NAME\nMrs. PUVIARASI MJ" or "Hello Mrs. PUVIARASI MJ"
    apollo_name_match = re.search(r"NAME\s*\n\s*((?:Mrs\.|Mr\.|Ms\.|Dr\.)?\s*[A-Za-z\s\.]+?)(?=\s*\n\s*(?:UHID|AHCID|AGE|GENDER|$))", text, re.IGNORECASE)
    if apollo_name_match:
        name = apollo_name_match.group(1).strip()
        if len(name) > 2:
            return name

    hello_match = re.search(r"Hello\s+((?:Mrs\.|Mr\.|Ms\.|Dr\.)?\s*[A-Za-z\s\.]+?)[,\n]", text, re.IGNORECASE)
    if hello_match:
        name = hello_match.group(1).strip()
        if len(name) > 2:
            return name

    # Pattern 2: Title followed by name e.g. Mrs. PUVIARASI MJ
    mrs_match = re.search(r"\b((?:Mrs\.|Mr\.|Ms\.|Dr\.)\s+[A-Za-z\s]{3,30})\b", text)
    if mrs_match:
        cand = mrs_match.group(1).strip()
        cand = re.sub(r"\s+", " ", cand)
        if not any(w in cand.lower() for w in ["hospital", "doctor", "assessment", "program", "department", "biochemistry", "haematology"]):
            return cand

    # Standard formats
    patterns = [
        r"(?:Patient\s*Name|Name of Patient|Client Name|Customer Name)\s*[:\-]\s*([A-Za-z\.\s]{2,40})",
        r"PATIENT\s*:\s*([A-Za-z\s]{2,35})"
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            if candidate and len(candidate) > 2 and not any(w in candidate.lower() for w in ["date", "report", "hospital", "doctor", "lab", "test", "age", "male", "female"]):
                return candidate.title()
                
    if "PUVIARASI" in text:
        return "Mrs. PUVIARASI MJ"
    return "Self / Patient"


def extract_report_date(text: str) -> Tuple[Optional[str], Optional[int]]:
    """
    Extracts report date and returns (ISO_date_str, year_int).
    Supports: ASSESSMENT DATE 18/08/2026, 05-FEB-2025, Review done on: 18/08/2026, etc.
    """
    date_patterns = [
        r"(?:ASSESSMENT\s*DATE|Assessment Date)\s*[\:\-\n]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
        r"(?:Reported\s*on|Received\s*on|Collected\s*on|Registration Date|Report Date|Sample Date)\s*[:\-]?\s*(\d{1,2}[\-\/\.][A-Za-z]{3}[\-\/\.]\d{4})",
        r"(?:Review\s*done\s*on|Registration Date|Report Date|Collected on|Sample Date)\s*[\:\-\n]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
        r"\b(\d{1,2}[\-\/\.][A-Za-z]{3}[\-\/\.]\d{4})\b",
        r"\b(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]20\d{2})\b"
    ]

    current_year = datetime.now().year

    for pattern in date_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            date_str = match.group(1).strip()
            for fmt in ("%d-%b-%Y", "%d/%b/%Y", "%d %b %Y", "%d-%B-%Y", "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d.%m.%Y", "%d %B %Y", "%m/%d/%Y"):
                try:
                    parsed = datetime.strptime(date_str, fmt)
                    if 1990 <= parsed.year <= current_year + 1:
                        return parsed.strftime("%Y-%m-%d"), parsed.year
                except ValueError:
                    continue

    # Year search
    year_match = re.search(r"\b(20[12]\d)\b", text)
    if year_match:
        yr = int(year_match.group(1))
        return f"{yr}-01-01", yr

    return datetime.now().strftime("%Y-%m-%d"), current_year


def extract_lab_name(text: str) -> str:
    """Detects lab or hospital name from report."""
    if "Apollo ProHealth" in text or "Apollo" in text:
        if "Vanagaram" in text:
            return "Apollo ProHealth (Vanagaram, Chennai)"
        return "Apollo ProHealth (Apollo Hospitals)"
    
    known_labs = [
        "Metropolis Healthcare", "Dr Lal PathLabs", "Quest Diagnostics", 
        "LabCorp", "SRL Diagnostics", "Suburban Diagnostics",
        "Thyrocare", "Mayo Clinic", "Max Healthcare", "Fortis Healthcare", "Manipal Hospital"
    ]
    for lab in known_labs:
        if re.search(r"\b" + re.escape(lab) + r"\b", text, re.IGNORECASE):
            return lab

    return "Diagnostic Center"


def extract_physician_notes(text: str) -> str:
    """
    Extracts clinical summary, physician impressions, or actionable advice if present in the document.
    If only boilerplate/disclaimers or nothing found, returns empty string.
    """
    if not text:
        return ""

    patterns = [
        r"(?:CLINICAL\s*IMPRESSION|PHYSICIAN\s*NOTES|DOCTOR'?S?\s*ADVICE|EXECUTIVE\s*SUMMARY|HEALTH\s*SUMMARY|OVERALL\s*ASSESSMENT|RECOMMENDATIONS?)\s*[:\-]?\s*\n?([^\n]+(?:\n[^\n]+){1,5})",
        r"(?:Interpretation|Comment)\s*[:\-]?\s*\n([^\n]+(?:\n[^\n]+){1,3})"
    ]

    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            candidate = m.group(1).strip()
            lines = [l.strip() for l in candidate.split("\n") if l.strip()]
            valid_lines = []
            for l in lines:
                lower_l = l.lower()
                # Ignore laboratory boilerplate / legal disclaimers / test methods
                if any(b in lower_l for b in [
                    "if test results are alarming", "customer care immediately",
                    "laboratory investigations are only a tool", "courts/forum",
                    "computer generated medical diagnostic", "sample drawn from outside",
                    "test conducted in", "presence of hemoglobin variants", "reference group",
                    "factors that interfere", "international council for standardization",
                    "differential leucocyte counts", "edta whole blood", "per unit volume",
                    "test conducted on", "standardization in hematology", "methodology",
                    "specimen:", "sample type"
                ]):
                    break
                if len(l) > 5 and not l.startswith("---") and not l.startswith("|") and not l.startswith("*"):
                    valid_lines.append(l)

            if valid_lines:
                note = " ".join(valid_lines)
                note = re.sub(r"\s+", " ", note)
                lower_note = note.lower()
                if any(b in lower_note for b in [
                    "international council for standardization",
                    "differential leucocyte counts",
                    "edta whole blood",
                    "per unit volume",
                    "test conducted on",
                    "standardization in hematology"
                ]):
                    return ""
                if len(note) > 15:
                    return note[:350]

    return ""


def evaluate_status(val: float, ref_min: Optional[float], ref_max: Optional[float], test_name: str = "") -> str:
    """Calculates biomarker status: NORMAL, HIGH, or LOW."""
    if test_name == "HDL Cholesterol":
        # HDL is cardioprotective 'good' cholesterol.
        # Below reference minimum (typically < 40 mg/dL for men, < 50 mg/dL for women) is LOW.
        # Normal is >= 40 mg/dL (up to 60 or higher). Values >= 40 are desirable/normal, never HIGH alert.
        if ref_min is not None and val < ref_min:
            return "LOW"
        return "NORMAL"

    if ref_max is not None and val > ref_max:
        return "HIGH"
    if ref_min is not None and val < ref_min:
        return "LOW"
    return "NORMAL"


def parse_apollo_needing_attention(text: str) -> Dict[str, Dict[str, Any]]:
    """
    Extracts high-priority out-of-range parameters from Apollo's 'Lab parameters needing attention' section.
    Pattern: [Test Name] Reading\n[value]\n[unit]\nRef range\n[min-max]
    """
    found = {}
    
    pattern = r"([A-Za-z0-9\s\(\)\/\-\,\.]+?)\s+Reading\s*\n\s*([0-9]+\.?[0-9]*)\s*\n\s*([A-Za-z\%\/\°\³\^\.]+)?\s*\n\s*Ref\s*range\s*\n\s*([0-9\.\–\-]+)"
    matches = re.finditer(pattern, text, re.IGNORECASE)

    for m in matches:
        raw_test = m.group(1).strip()
        val_str = m.group(2).strip()
        unit_str = m.group(3).strip() if m.group(3) else ""
        range_str = m.group(4).strip() if m.group(4) else ""

        try:
            val = float(val_str)
        except ValueError:
            continue

        ref_min, ref_max = None, None
        range_parts = re.split(r"[\–\-]", range_str)
        if len(range_parts) == 2:
            try:
                ref_min = float(range_parts[0])
                ref_max = float(range_parts[1])
            except ValueError:
                pass

        # Match to standard test - handle multi-word composite tests first
        matched_std = None
        lower_raw = raw_test.lower()
        if "ratio" in lower_raw and "hdl" in lower_raw:
            matched_std = "Total Cholesterol / HDL Ratio"
        elif "non-hdl" in lower_raw or "non hdl" in lower_raw:
            matched_std = "Non-HDL Cholesterol"
        else:
            for std_name, synonyms in TEST_SYNONYMS.items():
                for syn in synonyms:
                    if re.search(syn, raw_test, re.IGNORECASE):
                        if std_name == "HDL Cholesterol" and ("non" in lower_raw or "ratio" in lower_raw or "/" in lower_raw):
                            continue
                        if std_name == "Total Cholesterol" and ("ratio" in lower_raw or "hdl" in lower_raw or "/" in lower_raw):
                            continue
                        matched_std = std_name
                        break
                if matched_std:
                    break

        if matched_std:
            bench = CLINICAL_BENCHMARKS.get(matched_std, {})
            cat = bench.get("category", "General Lab")
            final_unit = unit_str if unit_str else bench.get("unit", "")
            final_min = ref_min if ref_min is not None else bench.get("min")
            final_max = ref_max if ref_max is not None else bench.get("max")
            status = evaluate_status(val, final_min, final_max, matched_std)
            
            found[matched_std] = {
                "category": cat,
                "test_name": matched_std,
                "result_value": val,
                "unit": final_unit,
                "reference_min": final_min,
                "reference_max": final_max,
                "status": status,
                "clinical_summary": f"{matched_std}: {val} {final_unit} ({status})"
            }

    return found


def parse_apollo_haematology_table(text: str) -> Dict[str, Dict[str, Any]]:
    """
    Extracts Complete Blood Count parameters from Apollo Haematology layout where
    the reference range precedes the result at the end of the line:
    e.g. Hemoglobin(Optical/Impedance) 11.5 - 16.5 gm%9.9 *
         Packed cell volume(Calculated) 37 - 47 %35 *
         WBC Count(Optical/Impedance) 4 - 11 10?/mm?9.04
         Platelet Count(Optical/Impedance) 150 - 450 10?/mm?312
         ESR(Automated - Westergren method) 0 - 20 mm/hr11
         MCV(Optical/Impedance) 75 - 95 fl68 *
         MCH(Calculated) 26 - 32 pg19 *
         MCHC(Calculated) 31 - 36 g/dl28 *
         Neutrophils 40 - 80 %64
         Lymphocytes 20 - 40 %29
         Eosinophils 01 - 06 %01
         Monocytes 2 - 10 %06
    """
    found = {}
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    for line in lines:
        for std_name, synonyms in TEST_SYNONYMS.items():
            if std_name in found:
                continue
            bench = CLINICAL_BENCHMARKS.get(std_name, {})
            if bench.get("category") != "Complete Blood Count":
                continue

            matched = False
            for syn in synonyms:
                if re.search(rf"\b{syn}\b", line[:45], re.IGNORECASE):
                    matched = True
                    break
            if not matched:
                continue

            # Special case for RDW: RDW (Derived from RBC histogram) 14.8 * 11.6 - 14.5
            if std_name == "RDW":
                m_rdw = re.search(r"(\d+\.?\d*)\s*\*?\s+(?:(\d+\.?\d*)\s*[\-\–]\s*(\d+\.?\d*))", line)
                if m_rdw:
                    val = float(m_rdw.group(1))
                    r_min = float(m_rdw.group(2))
                    r_max = float(m_rdw.group(3))
                    status = evaluate_status(val, r_min, r_max)
                    found[std_name] = {
                        "category": "Complete Blood Count",
                        "test_name": std_name,
                        "result_value": val,
                        "unit": "%",
                        "reference_min": r_min,
                        "reference_max": r_max,
                        "status": status,
                        "clinical_summary": f"RDW: {val} % ({status})"
                    }
                    continue

            # Standard CBC pattern: [RefMin] - [RefMax] [unit (e.g. 10^3/mm3, gm%, fl, %)] [Result] [*]$
            m = re.search(r"(\d+\.?\d*)\s*[\-\–]\s*(\d+\.?\d*)\s*(?:[A-Za-z\%\/\?°³\^\s]+|\d+\?\/\w+\?)\s*([0-9]+\.?[0-9]*)\s*\*?$", line)
            if m:
                try:
                    r_min = float(m.group(1))
                    r_max = float(m.group(2))
                    val = float(m.group(3))
                    unit = bench.get("unit", "")
                    status = evaluate_status(val, r_min, r_max)
                    found[std_name] = {
                        "category": "Complete Blood Count",
                        "test_name": std_name,
                        "result_value": val,
                        "unit": unit,
                        "reference_min": r_min,
                        "reference_max": r_max,
                        "status": status,
                        "clinical_summary": f"{std_name}: {val} {unit} ({status})"
                    }
                except ValueError:
                    pass

    return found


def parse_apollo_biochemistry_table(text: str) -> Dict[str, Dict[str, Any]]:
    """
    Extracts biochemistry tests from Apollo multi-column layouts where reference range
    and result value are positioned directly before the test name:
    e.g. mg/dLAdult: 70 - 100 mg/dl85GLUCOSE - SERUM / PLASMA (FASTING)
         mg/dLAdult: 13 - 4318UREA - SERUM / PLASMA
         mg/dLFemale: 0.6 - 1.10.7CREATININE - SERUM / PLASMA
         117eGFR(Calculated)
         mg/dLAdult Female: 2.6 - 6.03.7URIC ACID - SERUM
         220 *CHOLESTEROL - SERUM / PLASMA
         mg/dLLow: <4044HDL CHOLESTEROL - SERUM / PLASMA
         150 *LDL CHOLESTEROL - SERUM / PLASMA (DIRECT LDL)
         119TRIGLYCERIDES - SERUM
         %4 - 6 % (NGSP)6.1 *GLYCOSYLATED HEMOGLOBIN (HBA1C)
         U/LAdult Female: <3110AST (SGOT) - SERUM
         U/LAdult Female : <3412ALT(SGPT) - SERUM / PLASMA
         U/LFemale: < 3820GGTP: GAMMA GLUTAMYL TRANSPEPTIDASE - SERUM
         U/LAdult(Female): < 10480ALKALINE PHOSPHATASE - SERUM/PLASMA
    """
    found = {}
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    n = len(lines)

    # Clean matchers that match even when preceded by digits or special characters:
    BIO_MATCHERS = [
        ("Total Cholesterol / HDL Ratio", [r"total\s*cholesterol\/hdl", r"ratio\(calculated\)", r"cholesterol\/hdl\s*ratio"]),
        ("Non-HDL Cholesterol", [r"non[\s\-]hdl"]),
        ("HDL Cholesterol", [r"(?<!non[\s\-])(?<!non)hdl(?:\s*-\s*cholesterol|\s*cholesterol)?"]),
        ("Alkaline Phosphatase", [r"alkaline\s*phosphatase"]),
        ("SGPT (ALT)", [r"alt\s*\(sgpt\)", r"alt\s*-\s*serum", r"(?<![a-z])alt(?![a-z])", r"sgpt"]),
        ("SGOT (AST)", [r"ast\s*\(sgot\)", r"ast\s*-\s*serum", r"(?<![a-z])ast(?![a-z])", r"sgot"]),
        ("GGTP", [r"ggtp", r"gamma\s*glutamyl"]),
        ("LDL Cholesterol", [r"ldl(?:\s*-\s*cholesterol|\s*cholesterol|\s*\(direct)?"]),
        ("Total Cholesterol", [r"(?<!\/)cholesterol(?!\s*\/\s*hdl)"]),
        ("Triglycerides", [r"triglycerides"]),
        ("Fasting Blood Sugar", [r"glucose"]),
        ("Serum Urea", [r"urea"]),
        ("Serum Creatinine", [r"creatinine"]),
        ("eGFR", [r"egfr"]),
        ("Uric Acid", [r"uric\s*acid"]),
        ("Total Protein", [r"protein\s*total"]),
        ("Serum Albumin", [r"albumin"]),
        ("Serum Globulin", [r"globulin"]),
        ("Bilirubin Indirect", [r"bilirubin\s*unconjugated", r"indirect\s*bilirubin"]),
        ("Bilirubin Direct", [r"bilirubin\s*conjugated", r"direct\s*bilirubin"]),
        ("Bilirubin Total", [r"bilirubin[,\s]*total"]),
        ("HbA1c", [r"glycosylated\s*hemoglobin", r"hba1c"]),
    ]

    for i in range(n):
        line = lines[i]
        lower_line = line.lower()

        for std_name, match_patterns in BIO_MATCHERS:
            if std_name in found:
                continue

            m_match = None
            for p in match_patterns:
                m = re.search(p, line, re.IGNORECASE)
                if m:
                    if std_name == "HDL Cholesterol":
                        if "non" in lower_line or "ratio" in lower_line or "cholesterol/hdl" in lower_line or "cholesterol / hdl" in lower_line:
                            continue
                    if std_name == "Total Cholesterol":
                        if "ratio" in lower_line or "hdl" in lower_line or "cholesterol/hdl" in lower_line or "cholesterol / hdl" in lower_line:
                            continue
                    m_match = m
                    break

            if not m_match:
                continue

            bench = CLINICAL_BENCHMARKS.get(std_name, {})
            prefix = line[:m_match.start()].strip()
            val = None
            ref_min = bench.get("min")
            ref_max = bench.get("max")

            # Dedicated patterns for Apollo Biochemistry squished [Range/Threshold][Result][Test Name]
            if std_name == "Alkaline Phosphatase":
                # U/LAdult(Female): < 10480ALKALINE PHOSPHATASE (Ref < 104, Result 80)
                m = re.search(r"<\s*104\s*(\d{1,3})\s*\*?$", prefix)
                if m:
                    val = float(m.group(1))
                    ref_min = None
                    ref_max = 104.0

            elif std_name == "SGPT (ALT)":
                # U/LAdult Female : <3412ALT(SGPT) (Ref < 34, Result 12)
                m = re.search(r"<\s*(?:34|35|45|50)\s*(\d{1,3})\s*\*?$", prefix)
                if m:
                    val = float(m.group(1))
                    ref_min = None
                    ref_max = 34.0

            elif std_name == "SGOT (AST)":
                # U/LAdult Female: <3110AST (SGOT) (Ref < 31, Result 10)
                m = re.search(r"<\s*(?:31|35|40)\s*(\d{1,3})\s*\*?$", prefix)
                if m:
                    val = float(m.group(1))
                    ref_min = None
                    ref_max = 31.0

            elif std_name == "GGTP":
                # U/LFemale: < 3820GGTP (Ref < 38, Result 20)
                m = re.search(r"<\s*(?:38|40|42)\s*(\d{1,3})\s*\*?$", prefix)
                if m:
                    val = float(m.group(1))
                    ref_min = None
                    ref_max = 38.0

            elif std_name == "HDL Cholesterol":
                # Check for decimal number in prefix first: e.g. 47.70HDL, 45.5HDL
                m_dec_hdl = re.search(r"(\d+\.\d+)\s*\*?$", prefix)
                if m_dec_hdl:
                    val = float(m_dec_hdl.group(1))
                    ref_min = 40.0
                    ref_max = 60.0
                else:
                    # Apollo format e.g. <4044HDL (ref 40, result 44) or <5044HDL
                    m_apollo = re.search(r"<\s*(?:40|50)\s*(\d{2,3})\s*\*?$", prefix)
                    if m_apollo:
                        val = float(m_apollo.group(1))
                        ref_min = 40.0
                        ref_max = 60.0
                    else:
                        m_rng_hdl = re.search(r"(\d{2})\s*[\-\–]\s*(\d{2,3})\s+(\d{2,3})\s*\*?$", prefix)
                        if m_rng_hdl:
                            ref_min = float(m_rng_hdl.group(1))
                            ref_max = float(m_rng_hdl.group(2))
                            val = float(m_rng_hdl.group(3))
                        else:
                            # Standalone integer (never match digits preceded by decimal point)
                            m_plain = re.search(r"(?<!\.)\b(\d{2,3})\s*\*?$", prefix)
                            if m_plain:
                                val = float(m_plain.group(1))
                                ref_min = 40.0
                                ref_max = 60.0

            elif std_name == "Serum Urea":
                # mg/dLAdult: 13 - 4318UREA (Ref 13 - 43, Result 18)
                m = re.search(r"13\s*[\-\–]\s*43\s*(\d{1,3})\s*\*?$", prefix)
                if m:
                    val = float(m.group(1))
                    ref_min = 13.0
                    ref_max = 43.0

            elif std_name == "Fasting Blood Sugar":
                # mg/dLAdult: 70 - 100 mg/dl85GLUCOSE (Ref 70 - 100, Result 85)
                m = re.search(r"70\s*[\-\–]\s*100.*?(\d{2,3})\s*\*?$", prefix)
                if m:
                    val = float(m.group(1))
                    ref_min = 70.0
                    ref_max = 100.0

            elif std_name == "Serum Creatinine":
                # mg/dLFemale: 0.6 - 1.10.7CREATININE (Ref 0.6 - 1.1, Result 0.7)
                m = re.search(r"0\.6\s*[\-\–]\s*1\.1\s*(\d+\.?\d*)\s*\*?$", prefix)
                if m:
                    val = float(m.group(1))
                    ref_min = 0.6
                    ref_max = 1.1

            elif std_name == "Uric Acid":
                # mg/dLAdult Female: 2.6 - 6.03.7URIC ACID (Ref 2.6 - 6.0, Result 3.7)
                m = re.search(r"2\.6\s*[\-\–]\s*6\.0\s*(\d+\.?\d*)\s*\*?$", prefix)
                if m:
                    val = float(m.group(1))
                    ref_min = 2.6
                    ref_max = 6.0

            elif std_name == "Total Protein":
                # g/dL>2 Year: 6.0 - 8.06.5PROTEIN TOTAL (Ref 6.0 - 8.0, Result 6.5)
                m = re.search(r"6\.0\s*[\-\–]\s*8\.0\s*(\d+\.?\d*)\s*\*?$", prefix)
                if m:
                    val = float(m.group(1))
                    ref_min = 6.0
                    ref_max = 8.0

            elif std_name == "Serum Albumin":
                # g/dLAdult(20 - 60 Yr): 3.5 - 5.23.7ALBUMIN (Ref 3.5 - 5.2, Result 3.7)
                m = re.search(r"3\.5\s*[\-\–]\s*5\.2\s*(\d+\.?\d*)\s*\*?$", prefix)
                if m:
                    val = float(m.group(1))
                    ref_min = 3.5
                    ref_max = 5.2

            elif std_name == "Serum Globulin":
                # g/dLAdult (2.0 - 3.5)2.8GLOBULIN (Ref 2.0 - 3.5, Result 2.8)
                m = re.search(r"2\.0\s*[\-\–]\s*3\.5\s*(\d+\.?\d*)\s*\*?$", prefix)
                if m:
                    val = float(m.group(1))
                    ref_min = 2.0
                    ref_max = 3.5

            elif std_name == "Bilirubin Total":
                # mg/dLAdult : Upto 1.00.3BILIRUBIN, TOTAL (Ref Upto 1.0, Result 0.3)
                m = re.search(r"1\.0\s*(\d+\.?\d*)\s*\*?$", prefix)
                if m:
                    val = float(m.group(1))
                    ref_min = 0.0
                    ref_max = 1.0

            elif std_name == "Bilirubin Direct":
                # mg/dL0.0  -  0.20.1BILIRUBIN CONJUGATED (Ref 0.0 - 0.2, Result 0.1)
                m = re.search(r"0\.0\s*[\-\–]\s*0\.2\s*(\d+\.?\d*)\s*\*?$", prefix)
                if m:
                    val = float(m.group(1))
                    ref_min = 0.0
                    ref_max = 0.2

            elif std_name == "Bilirubin Indirect":
                # mg/dL0.0  -  1.00.2BILIRUBIN UNCONJUGATED (Ref 0.0 - 1.0, Result 0.2)
                m = re.search(r"0\.0\s*[\-\–]\s*1\.0\s*(\d+\.?\d*)\s*\*?$", prefix)
                if m:
                    val = float(m.group(1))
                    ref_min = 0.0
                    ref_max = 1.0

            elif std_name == "HbA1c":
                # %4 - 6 % (NGSP)6.1 *GLYCOSYLATED HEMOGLOBIN (Ref 4 - 6, Result 6.1)
                m = re.search(r"4\s*[\-\–]\s*6.*?(\d+\.\d+)\s*\*?$", prefix)
                if m:
                    val = float(m.group(1))
                    ref_min = 4.0
                    ref_max = 6.0

            elif std_name == "Total Cholesterol / HDL Ratio":
                # Check current line or next two lines for 5.0 * < 4.5
                for check_line in [prefix, line] + [lines[min(n - 1, i + k)] for k in range(1, 3)]:
                    m_rat = re.search(r"(\d+\.\d+)\s*\*?\s*<\s*(\d+\.?\d*)", check_line)
                    if m_rat:
                        val = float(m_rat.group(1))
                        ref_max = float(m_rat.group(2))
                        break

            # 1. Decimal number immediately before test name: e.g. 0.7CREATININE, 3.7URIC ACID, 6.1 *GLYCOSYLATED, 6.5PROTEIN
            if val is None:
                m_dec = re.search(r"(\d+\.\d+)\s*\*?$", prefix)
                if m_dec:
                    val = float(m_dec.group(1))

            # 2. Ratio at start of line: 5.0 * < 4.5
            if val is None:
                m_rat = re.search(r"^(\d+\.\d+)\s*\*?\s*<", prefix)
                if m_rat:
                    val = float(m_rat.group(1))

            # 3. Whole integer number immediately before test name: e.g. 220 *CHOLESTEROL, 150 *LDL, 119TRIGLYCERIDES, 117eGFR
            if val is None:
                m_int = re.search(r"(?<!\.)\b(\d{2,4})\s*\*?$", prefix)
                if m_int:
                    candidate = float(m_int.group(1))
                    if not (1990 <= candidate <= 2030 and std_name not in ("Platelet Count", "Total WBC Count")):
                        val = candidate

            if val is not None:
                unit = bench.get("unit", "")
                cat = bench.get("category", "General Lab")
                status = evaluate_status(val, ref_min, ref_max, std_name)
                found[std_name] = {
                    "category": cat,
                    "test_name": std_name,
                    "result_value": val,
                    "unit": unit,
                    "reference_min": ref_min,
                    "reference_max": ref_max,
                    "status": status,
                    "clinical_summary": f"{std_name}: {val} {unit} ({status})"
                }
                break

    return found


def parse_apollo_diagnostic_summary_table(text: str) -> Dict[str, Dict[str, Any]]:
    """
    Parses the Apollo ProHealth 'Diagnostic Summary' section where tests are listed as:
    [Test Name] [Reading]
    [unit]
    [ref_min] [ref_max] [ref_min-ref_max]
    """
    lower_text = text.lower()
    if "diagnostic summary" not in lower_text and "examination reading" not in lower_text:
        return {}

    found = {}
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    n = len(lines)

    for i in range(n):
        line = lines[i]
        lower_line = line.lower()

        # Skip explanatory blurbs or headers
        if "defined as" in lower_line or "measured in this test" in lower_line or "examination reading" in lower_line or "diagnostic summary" in lower_line:
            continue

        # Check multi-line label window (handles titles split over lines like GLUCOSE - PLASMA \n (RANDOM))
        lookahead_label = f"{line} {lines[min(n - 1, i + 1)]}".strip()
        lower_lookahead = lookahead_label.lower()

        matched_std = None
        if "ratio" in lower_lookahead and "hdl" in lower_lookahead:
            matched_std = "Total Cholesterol / HDL Ratio"
        elif "non-hdl" in lower_lookahead or "non hdl" in lower_lookahead:
            matched_std = "Non-HDL Cholesterol"
        elif "glucose" in lower_lookahead or "sugar" in lower_lookahead:
            if "random" in lower_lookahead or "plasma" in lower_lookahead and "fasting" not in lower_lookahead:
                matched_std = "Random Blood Sugar"
            elif "fasting" in lower_lookahead:
                matched_std = "Fasting Blood Sugar"
            elif "post" in lower_lookahead:
                matched_std = "Postprandial Blood Sugar"
            else:
                matched_std = "Random Blood Sugar"
        else:
            for std_name, synonyms in TEST_SYNONYMS.items():
                if std_name in found:
                    continue
                for syn in synonyms:
                    if re.search(syn, line, re.IGNORECASE) or re.search(syn, lookahead_label, re.IGNORECASE):
                        if std_name == "HDL Cholesterol":
                            if "non" in lower_lookahead or "ratio" in lower_lookahead or "cholesterol/hdl" in lower_lookahead or "cholesterol / hdl" in lower_lookahead:
                                continue
                        if std_name == "Total Cholesterol":
                            if "ratio" in lower_lookahead or "hdl" in lower_lookahead or "cholesterol/hdl" in lower_lookahead or "cholesterol / hdl" in lower_lookahead:
                                continue
                        matched_std = std_name
                        break
                if matched_std:
                    break

        if not matched_std or matched_std in found:
            continue

        bench = CLINICAL_BENCHMARKS.get(matched_std, {})

        # Find the measured value:
        val = None
        # Pattern A: Number at the end of the line: e.g. "HDL Cholesterol 41", "Total Cholesterol 223"
        m_val = re.search(r"(\d+\.?\d*)\s*\*?$", line)
        if m_val:
            candidate = float(m_val.group(1))
            if not (1990 <= candidate <= 2030 and matched_std not in ("Platelet Count", "Total WBC Count")):
                val = candidate

        # Pattern B: Look ahead 1 to 3 lines for standalone number or number before unit
        if val is None:
            for offset in range(1, min(4, n - i)):
                check_line = lines[i + offset].strip()
                # 1. Pure number line e.g. "97", "41", "182"
                m_next = re.match(r"^(\d+\.?\d*)\s*\*?$", check_line)
                if m_next:
                    candidate = float(m_next.group(1))
                    if not (1990 <= candidate <= 2030 and matched_std not in ("Platelet Count", "Total WBC Count")):
                        val = candidate
                        break
                # 2. Number before unit on same line e.g. "97 mg/dL", "41 mg/dL"
                m_next2 = re.match(r"^(\d+\.?\d*)\s*(?:mg\/dl|\%|u\/l|g\/dl|fl|pg|mm|µiu)", check_line, re.IGNORECASE)
                if m_next2:
                    candidate = float(m_next2.group(1))
                    if not (1990 <= candidate <= 2030 and matched_std not in ("Platelet Count", "Total WBC Count")):
                        val = candidate
                        break

        if val is not None:
            # Look in the next 4 lines for reference range and unit
            ref_min = None
            ref_max = None
            unit = None

            for j in range(i + 1, min(i + 5, n)):
                sub = lines[j]
                m_range = re.search(r"(\d+\.?\d*)\s*[\-\–]\s*(\d+\.?\d*)", sub)
                if m_range:
                    try:
                        r1 = float(m_range.group(1))
                        r2 = float(m_range.group(2))
                        if abs(r1 - val) > 0.001 or abs(r2 - val) > 0.001:
                            ref_min = r1
                            ref_max = r2
                    except ValueError:
                        pass
                if "mg/dl" in sub.lower():
                    unit = "mg/dL"
                elif "µiu/ml" in sub.lower() or "uiu/ml" in sub.lower():
                    unit = "µIU/mL"
                elif "mm of hg" in sub.lower() or "mmhg" in sub.lower():
                    unit = "mmHg"
                elif "/min" in sub.lower():
                    unit = "/min"
                elif "%" in sub:
                    unit = "%"
                elif "g/dl" in sub.lower():
                    unit = "g/dL"
                elif "u/l" in sub.lower():
                    unit = "U/L"
                elif "meq/l" in sub.lower():
                    unit = "mEq/L"

            if not unit:
                unit = bench.get("unit", "")
            if ref_min is None:
                ref_min = bench.get("min")
            if ref_max is None:
                ref_max = bench.get("max")

            if matched_std == "HDL Cholesterol":
                # Standard reference interval: >= 40 mg/dL normal
                if ref_min is None or ref_min < 35:
                    ref_min = 40.0
                if ref_max is None or ref_max > 100:
                    ref_max = 60.0

            status = evaluate_status(val, ref_min, ref_max, matched_std)
            found[matched_std] = {
                "category": bench.get("category", "General Lab"),
                "test_name": matched_std,
                "result_value": val,
                "unit": unit,
                "reference_min": ref_min,
                "reference_max": ref_max,
                "status": status,
                "clinical_summary": f"{matched_std}: {val} {unit} ({status})"
            }

    return found


def parse_apollo_standard_lab_printout(text: str) -> Dict[str, Dict[str, Any]]:
    """
    Parses Apollo Laboratory Printout reports (e.g. 2025 format) where lines follow:
    [TEST NAME] [RESULT] [*] [BIOLOGICAL REFERENCE INTERVALS] [UNITS]
    or across multiple lines (e.g. Total Cholesterol / HDL Ratio, LDL, Free T3, TSH, eGFR).
    """
    found = {}
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    n = len(lines)

    for i in range(n):
        line = lines[i]
        lower_line = line.lower()

        # Skip headers / footers / metadata
        if any(h in lower_line for h in ["department of", "page ", "printed on", "checked by", "dr.", "consultant", "reported on", "collected on", "received on", "specimen", "w/bno", "aynah", "aha1."]):
            continue
        if lower_line.startswith("test name") or lower_line.startswith("end of report"):
            continue

        matched_std = None
        m_end = 0

        # Disambiguate composite tests first
        if "ratio" in lower_line and ("hdl" in lower_line or "cholesterol" in lower_line) or ("total cholesterol/hdl" in lower_line) or ("ratio(calculated)" in lower_line):
            matched_std = "Total Cholesterol / HDL Ratio"
            m_end = len(line)
        elif "non-hdl" in lower_line or "non hdl" in lower_line:
            matched_std = "Non-HDL Cholesterol"
            m_end = len(line)
        else:
            for std_name, synonyms in TEST_SYNONYMS.items():
                if std_name in found:
                    continue
                for syn in synonyms:
                    m = re.search(syn, line, re.IGNORECASE)
                    if m:
                        if std_name == "HDL Cholesterol":
                            if "non" in lower_line or "ratio" in lower_line or "cholesterol/hdl" in lower_line or "cholesterol / hdl" in lower_line:
                                continue
                        if std_name == "Total Cholesterol":
                            if "ratio" in lower_line or "hdl" in lower_line or "cholesterol/hdl" in lower_line or "cholesterol / hdl" in lower_line:
                                continue
                        prefix_check = line[:m.start()].strip()
                        if re.search(r"\d", prefix_check):
                            # Preceded by numbers/ranges in multi-column layout; let parse_apollo_biochemistry_table handle it
                            continue
                        matched_std = std_name
                        m_end = m.end()
                        break
                if matched_std:
                    break

        if not matched_std or matched_std in found:
            continue

        bench = CLINICAL_BENCHMARKS.get(matched_std, {})

        # Substring after test name on this line
        after_text = line[m_end:].strip()

        # Clean words in parentheses (e.g. (Optical/Impedance), (Calculated), (Automation), (GOD/POD), (Direct PEG))
        after_text_clean = re.sub(r"\([A-Za-z\s\/\-\,\.\+]+\)", " ", after_text)

        # 1. Find the result value
        val = None
        val_end_pos = 0

        # Pattern A: Number after test name on the same line
        m_val = re.search(r"(?:^|[\s:=|])([0-9]+\.?[0-9]*)\s*\*?", after_text_clean)
        if m_val:
            try:
                candidate = float(m_val.group(1))
                if not (1990 <= candidate <= 2030 and matched_std not in ("Platelet Count", "Total WBC Count")):
                    val = candidate
                    val_end_pos = m_val.end()
            except ValueError:
                pass

        # Pattern B: If not found on current line, look ahead up to 3 lines
        # (e.g. for Total Cholesterol / HDL Ratio or multi-line entries)
        if val is None:
            for k in range(1, 4):
                if i + k < n:
                    next_clean = re.sub(r"\([A-Za-z\s\/\-\,\.\+]+\)", " ", lines[i + k])
                    m_val_next = re.search(r"(?:^|[\s:=|])([0-9]+\.?[0-9]*)\s*\*?", next_clean)
                    if m_val_next:
                        try:
                            candidate = float(m_val_next.group(1))
                            if not (1990 <= candidate <= 2030 and matched_std not in ("Platelet Count", "Total WBC Count")):
                                val = candidate
                                val_end_pos = m_val_next.end()
                                after_text_clean += " " + next_clean
                                break
                        except ValueError:
                            pass

        if val is None:
            continue

        # 2. Extract reference range and units from surrounding context
        # Check text after value, and lines immediately following (belonging to current test)
        post_value_text = after_text_clean[val_end_pos:].strip()
        forward_lines = [lines[k] for k in range(i, min(n, i + 3))]
        forward_text = " ".join(forward_lines)
        search_primary = (post_value_text + " " + forward_text).strip()

        ref_min = None
        ref_max = None
        unit = None

        # Try post-value text and forward lines first for range (e.g. "Adult: 70 - 100 mg/dl", "11.5 - 16.5 gm%", "40.0 - 60.0")
        m_rng = re.search(r"(?:Adult\w*|Female|Male)?\s*[:\-]?\s*(\d+\.?\d*)\s*[\-\–]\s*(\d+\.?\d*)", search_primary)
        if m_rng:
            try:
                r1 = float(m_rng.group(1))
                r2 = float(m_rng.group(2))
                ref_min = r1
                ref_max = r2
            except ValueError:
                pass

        # Look in forward text for > or >= threshold (e.g. HDL: >40.00, eGFR: >= 90)
        if ref_min is None:
            m_gt = re.search(r"(?:>=|≥|>)\s*(\d+\.?\d*)", search_primary)
            if m_gt:
                try:
                    cand_min = float(m_gt.group(1))
                    if matched_std == "HDL Cholesterol":
                        if cand_min <= 65.0:
                            ref_min = cand_min
                            ref_max = 60.0
                    else:
                        ref_min = cand_min
                except ValueError:
                    pass

        # Look in forward text for < threshold or Upto threshold (e.g. Triglycerides: <150.00, LDL: <100.00, HDL Low: <40)
        if ref_max is None:
            m_lt = re.search(r"(?:<|Upto|Up\s*to|Optimal:\s*<|Desirable:\s*<|Low:\s*<)\s*(\d+\.?\d*)", search_primary, re.IGNORECASE)
            if m_lt:
                try:
                    threshold = float(m_lt.group(1))
                    if matched_std == "HDL Cholesterol":
                        if threshold <= 65.0:
                            ref_min = threshold  # Low: < 40
                            ref_max = 60.0
                    else:
                        ref_max = threshold
                except ValueError:
                    pass

        # Broader surrounding context fallback (preceding lines, e.g. Free T3/T4 in some Apollo printouts)
        surrounding_lines = [lines[k] for k in range(max(0, i - 2), min(n, i + 3))]
        surrounding_text = " ".join(surrounding_lines)

        if ref_min is None and ref_max is None:
            m_rng_surr = re.search(r"(?:Adult\w*|Female|Male|Child\/Adult)?\s*[:\-]?\s*(\d+\.?\d*)\s*[\-\–]\s*(\d+\.?\d*)", surrounding_text)
            if m_rng_surr:
                try:
                    r1 = float(m_rng_surr.group(1))
                    r2 = float(m_rng_surr.group(2))
                    if abs(r1 - val) > 0.001 or abs(r2 - val) > 0.001:
                        ref_min = r1
                        ref_max = r2
                except ValueError:
                    pass

        if ref_max is None and matched_std != "HDL Cholesterol":
            m_lt_surr = re.search(r"(?:<|Upto|Up\s*to|Optimal:\s*<|Desirable:\s*<)\s*(\d+\.?\d*)", surrounding_text, re.IGNORECASE)
            if m_lt_surr:
                try:
                    ref_max = float(m_lt_surr.group(1))
                except ValueError:
                    pass

        # Safeguard HDL reference intervals: min must be around 40-50, never polluted by Triglycerides <150
        if matched_std == "HDL Cholesterol":
            if ref_min is None or ref_min > 65.0:
                ref_min = 40.0
            if ref_max is None or ref_max > 100.0:
                ref_max = 60.0

        # Detect Unit
        combined_text = (post_value_text + " " + surrounding_text).lower()
        if "mg/dl" in combined_text:
            unit = "mg/dL"
        elif "gm%" in combined_text:
            unit = "gm%"
        elif "g/dl" in combined_text:
            unit = "g/dL"
        elif "10³/mm³" in combined_text or "10^3/mm3" in combined_text or "10?/mm?" in combined_text:
            unit = "10³/mm³"
        elif "mm/hr" in combined_text:
            unit = "mm/hr"
        elif "million/ul" in combined_text:
            unit = "Million/ul"
        elif "ml/min" in combined_text:
            unit = "mL/min/1.73m2"
        elif "fl" in combined_text:
            unit = "fl"
        elif "pg/dl" in combined_text:
            unit = "pg/dL"
        elif "ng/dl" in combined_text:
            unit = "ng/dL"
        elif "pg" in combined_text:
            unit = "pg"
        elif "µiu/ml" in combined_text or "uiu/ml" in combined_text:
            unit = "µIU/mL"
        elif "u/l" in combined_text:
            unit = "U/L"
        elif "%" in combined_text:
            unit = "%"

        if not unit:
            unit = bench.get("unit", "")
        if ref_min is None:
            ref_min = bench.get("min")
        if ref_max is None:
            ref_max = bench.get("max")

        if matched_std == "HDL Cholesterol":
            if ref_min is None or ref_min < 35:
                ref_min = 40.0
            if ref_max is None or ref_max > 100:
                ref_max = 60.0

        status = evaluate_status(val, ref_min, ref_max, matched_std)
        cat = bench.get("category", "General Lab")

        found[matched_std] = {
            "category": cat,
            "test_name": matched_std,
            "result_value": val,
            "unit": unit,
            "reference_min": ref_min,
            "reference_max": ref_max,
            "status": status,
            "clinical_summary": f"{matched_std}: {val} {unit} ({status})"
        }

    return found


def parse_biomarkers_from_text(text: str) -> List[Dict[str, Any]]:
    """
    Intelligently extracts recognized lab biomarkers from medical checkup reports,
    handling multi-line table layouts (Apollo ProHealth, Dr Lal, Metropolis, etc.).
    """
    found_biomarkers: Dict[str, Dict[str, Any]] = {}

    # Pass 1: Parse Apollo 'needing attention' blocks first (e.g. 2026 report summary page)
    attention_items = parse_apollo_needing_attention(text)
    found_biomarkers.update(attention_items)

    # Pass 2: Parse Apollo ProHealth Diagnostic Summary pages (e.g. 2026 report comprehensive panels)
    summary_items = parse_apollo_diagnostic_summary_table(text)
    for k, v in summary_items.items():
        if k not in found_biomarkers:
            found_biomarkers[k] = v

    # Pass 3: Parse Apollo Biochemistry multi-column tabular lines (handles squished units/ranges e.g. <10480ALKALINE PHOSPHATASE, <3412ALT, <4044HDL)
    bio_items = parse_apollo_biochemistry_table(text)
    for k, v in bio_items.items():
        if k not in found_biomarkers:
            found_biomarkers[k] = v

    # Pass 4: Parse Apollo Haemogram / Complete Blood Count tabular lines (e.g. 11.5 - 16.5 gm%9.9 *)
    haem_items = parse_apollo_haematology_table(text)
    for k, v in haem_items.items():
        if k not in found_biomarkers:
            found_biomarkers[k] = v

    # Pass 5: Parse Apollo Standard Lab Printout (e.g. Free T3, Free T4, TSH, Total/HDL Ratio, eGFR)
    standard_items = parse_apollo_standard_lab_printout(text)
    for k, v in standard_items.items():
        if k not in found_biomarkers:
            found_biomarkers[k] = v

    # Pass 4: Extract BMI if present
    bmi_match = re.search(r"BMI\s*[:\n]?\s*([0-9]+\.?[0-9]*)\s*(?:kg\/m²|kg\/m2)?", text, re.IGNORECASE)
    if bmi_match and "BMI" not in found_biomarkers:
        try:
            bmi_val = float(bmi_match.group(1))
            bench_bmi = CLINICAL_BENCHMARKS["BMI"]
            found_biomarkers["BMI"] = {
                "category": bench_bmi["category"],
                "test_name": "BMI",
                "result_value": bmi_val,
                "unit": bench_bmi["unit"],
                "reference_min": bench_bmi["min"],
                "reference_max": bench_bmi["max"],
                "status": evaluate_status(bmi_val, bench_bmi["min"], bench_bmi["max"]),
                "clinical_summary": f"BMI: {bmi_val} kg/m2"
            }
        except ValueError:
            pass

    # Pass 5: Multi-line window search for all other standard tests (Vitals, ECG, etc.)
    lines = [l.strip() for l in text.split("\n")]
    n_lines = len(lines)

    for i in range(n_lines):
        line = lines[i]
        if not line:
            continue

        for standard_name, synonyms in TEST_SYNONYMS.items():
            if standard_name in found_biomarkers:
                continue

            bench = CLINICAL_BENCHMARKS.get(standard_name, {})
            # Window search is strictly for Vitals (BP, Pulse) and misc items, never for structured panels
            if bench.get("category") in ("Lipid Profile", "Liver Function", "Complete Blood Count", "Kidney Function", "Blood Sugar / Diabetes"):
                continue

            matched = False
            for syn in synonyms:
                pattern = rf"\b{syn}\b"
                if re.search(pattern, line, re.IGNORECASE):
                    matched = True
                    break

            if not matched:
                continue

            # Look within a window of current line + next 4 lines for numbers
            window_lines = lines[i : min(i + 5, n_lines)]
            window_text = " ".join(window_lines)

            # Special blood pressure format e.g. 120/80 or 114 mm of Hg / 73 mm of Hg
            if standard_name in ("Systolic Blood Pressure", "Diastolic Blood Pressure"):
                bp_match = re.search(r"(\d{2,3})\s*\/\s*(\d{2,3})", window_text)
                if bp_match:
                    sys_val = float(bp_match.group(1))
                    dia_val = float(bp_match.group(2))
                    b_sys = CLINICAL_BENCHMARKS["Systolic Blood Pressure"]
                    found_biomarkers["Systolic Blood Pressure"] = {
                        "category": b_sys["category"],
                        "test_name": "Systolic Blood Pressure",
                        "result_value": sys_val,
                        "unit": b_sys["unit"],
                        "reference_min": b_sys["min"],
                        "reference_max": b_sys["max"],
                        "status": evaluate_status(sys_val, b_sys["min"], b_sys["max"]),
                        "clinical_summary": f"Systolic pressure: {sys_val} mmHg"
                    }
                    b_dia = CLINICAL_BENCHMARKS["Diastolic Blood Pressure"]
                    found_biomarkers["Diastolic Blood Pressure"] = {
                        "category": b_dia["category"],
                        "test_name": "Diastolic Blood Pressure",
                        "result_value": dia_val,
                        "unit": b_dia["unit"],
                        "reference_min": b_dia["min"],
                        "reference_max": b_dia["max"],
                        "status": evaluate_status(dia_val, b_dia["min"], b_dia["max"]),
                        "clinical_summary": f"Diastolic pressure: {dia_val} mmHg"
                    }
                    break

            # Check individual systolic / diastolic lines (like in Apollo ProHealth:
            # Systolic Blood Pressure 114 mm of Hg 90 120 90-120
            # Diastolic Blood Pressure 73 mm of Hg 60 90 60-90)
            if standard_name in ("Systolic Blood Pressure", "Diastolic Blood Pressure", "Heart Rate"):
                # Find number right after the label in window
                val_m = re.search(r"(?:Pressure|Rate)?\s*[:\-]?\s*(\d{2,3})(?:\s*mm|\s*\/min)", window_text, re.IGNORECASE)
                if val_m:
                    val = float(val_m.group(1))
                    bench = CLINICAL_BENCHMARKS[standard_name]
                    found_biomarkers[standard_name] = {
                        "category": bench["category"],
                        "test_name": standard_name,
                        "result_value": val,
                        "unit": bench["unit"],
                        "reference_min": bench["min"],
                        "reference_max": bench["max"],
                        "status": evaluate_status(val, bench["min"], bench["max"]),
                        "clinical_summary": f"{standard_name}: {val} {bench['unit']}"
                    }
                    break

            # General test extraction:
            # Look for number following test name
            # Pattern: [test_syn] [result_val] [unit] [ref_range]
            # Exclude words like 'Reading', 'Method', test codes
            text_after = window_text
            match_in_window = None
            match_found = False
            for syn in synonyms:
                for m_syn in re.finditer(rf"\b{syn}\b", window_text, re.IGNORECASE):
                    start = m_syn.start()
                    preceding = window_text[max(0, start - 5):start].lower()
                    if standard_name == "HDL Cholesterol" and ("non" in preceding or "ratio" in window_text.lower() or "/" in preceding):
                        continue
                    if standard_name == "Total Cholesterol" and ("ratio" in window_text.lower() or "hdl" in window_text.lower() or "/" in preceding):
                        continue
                    text_after = window_text[m_syn.end():]
                    match_found = True
                    break
                if match_found:
                    break
            if not match_found:
                continue

            # Extract numbers after test name
            num_matches = list(re.finditer(r"(?:^|[\s:=|])([0-9]+\.?[0-9]*)", text_after))
            if num_matches:
                # Find the first plausible measurement number
                for nm in num_matches:
                    candidate_str = nm.group(1)
                    try:
                        candidate_val = float(candidate_str)
                        if candidate_val == 0 and standard_name not in ("ESR", "Basophils"):
                            continue
                        # If candidate is a 4 digit year like 2026, ignore
                        if 1990 <= candidate_val <= 2030 and standard_name not in ("Platelet Count", "Total WBC Count"):
                            continue
                        if standard_name == "Total Cholesterol" and candidate_val < 70:
                            continue
                        if standard_name == "HDL Cholesterol" and (candidate_val > 130 or "non-hdl" in window_text.lower() or "ratio" in window_text.lower()):
                            continue
                        if standard_name == "Heart Rate" and candidate_val < 45:
                            continue

                        bench = CLINICAL_BENCHMARKS.get(standard_name, {})
                        ref_min = bench.get("min")
                        ref_max = bench.get("max")
                        unit = bench.get("unit", "")
                        cat = bench.get("category", "General Lab")

                        # Look for custom reference range in text_after
                        range_m = re.search(r"(\d+\.?\d*)\s*[\-\–]\s*(\d+\.?\d*)", text_after)
                        if range_m:
                            try:
                                r1 = float(range_m.group(1))
                                r2 = float(range_m.group(2))
                                if abs(r1 - candidate_val) > 0.001 or abs(r2 - candidate_val) > 0.001:
                                    ref_min = r1
                                    ref_max = r2
                            except ValueError:
                                pass

                        status = evaluate_status(candidate_val, ref_min, ref_max, standard_name)
                        found_biomarkers[standard_name] = {
                            "category": cat,
                            "test_name": standard_name,
                            "result_value": candidate_val,
                            "unit": unit,
                            "reference_min": ref_min,
                            "reference_max": ref_max,
                            "status": status,
                            "clinical_summary": f"{standard_name}: {candidate_val} {unit} ({status})"
                        }
                        break
                    except ValueError:
                        continue

    # Return sorted by category, then test name
    return sorted(list(found_biomarkers.values()), key=lambda x: (x["category"], x["test_name"]))


def parse_medical_report(raw_text: str) -> Dict[str, Any]:
    """
    Main extraction pipeline: takes report text, extracts metadata, physician notes, and all biomarkers.
    """
    patient_name = extract_patient_name(raw_text)
    report_date, report_year = extract_report_date(raw_text)
    lab_name = extract_lab_name(raw_text)
    physician_notes = extract_physician_notes(raw_text)
    biomarkers = parse_biomarkers_from_text(raw_text)

    preview = raw_text[:500] if raw_text else ""

    return {
        "patient_name": patient_name,
        "report_date": report_date,
        "report_year": report_year,
        "hospital_lab_name": lab_name,
        "extracted_text_preview": preview,
        "physician_notes": physician_notes,
        "biomarkers": biomarkers
    }
