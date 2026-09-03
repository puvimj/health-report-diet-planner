import json
from typing import List, Dict, Any, Optional, Tuple

def analyze_health_findings(biomarkers: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Evaluates report biomarkers and classifies clinical risks.
    """
    findings = {
        "high_cholesterol": False,
        "high_triglycerides": False,
        "low_hdl": False,
        "high_sugar": False,
        "high_hba1c": False,
        "high_uric_acid": False,
        "high_bp": False,
        "elevated_liver": False,
        "elevated_kidney": False,
        "low_hemoglobin": False,
        "low_vit_d": False,
        "low_vit_b12": False,
        "low_hdl": False,
        "high_bmi": False,
        "abnormal_list": []
    }

    for b in biomarkers:
        name = b.get("test_name", "")
        val = float(b.get("result_value", 0))
        status = b.get("status", "NORMAL")

        if status in ("HIGH", "LOW"):
            findings["abnormal_list"].append({
                "test_name": name,
                "value": val,
                "unit": b.get("unit", ""),
                "status": status,
                "ref_min": b.get("reference_min"),
                "ref_max": b.get("reference_max")
            })

        # Specific clinical flags
        if name in ("Total Cholesterol", "LDL Cholesterol") and status == "HIGH":
            findings["high_cholesterol"] = True
        elif name == "Triglycerides" and status == "HIGH":
            findings["high_triglycerides"] = True
        elif name == "HDL Cholesterol" and status == "LOW":
            findings["low_hdl"] = True
        elif name in ("Fasting Blood Sugar", "Postprandial Blood Sugar", "Random Blood Sugar") and status == "HIGH":
            findings["high_sugar"] = True
        elif name == "HbA1c" and val >= 5.7:
            findings["high_hba1c"] = True
        elif name == "Uric Acid" and status == "HIGH":
            findings["high_uric_acid"] = True
        elif name in ("Systolic Blood Pressure", "Diastolic Blood Pressure") and status == "HIGH":
            findings["high_bp"] = True
        elif name in ("SGPT (ALT)", "SGOT (AST)") and status == "HIGH":
            findings["elevated_liver"] = True
        elif name in ("Serum Creatinine", "Blood Urea Nitrogen") and status == "HIGH":
            findings["elevated_kidney"] = True
        elif name == "Hemoglobin" and status == "LOW":
            findings["low_hemoglobin"] = True
        elif name == "Vitamin D (25-OH)" and val < 30.0:
            findings["low_vit_d"] = True
        elif name == "Vitamin B12" and val < 250.0:
            findings["low_vit_b12"] = True
        elif name == "BMI" and val >= 25.0:
            findings["high_bmi"] = True

    findings["alcohol_avoidance_required"] = bool(
        findings["elevated_liver"] or 
        findings["high_triglycerides"] or 
        findings["high_uric_acid"] or 
        findings["high_sugar"] or 
        findings["high_hba1c"] or 
        findings["high_bp"] or 
        findings["high_cholesterol"]
    )

    return findings


def generate_health_goals(findings: Dict[str, Any]) -> List[str]:
    """Builds targeted primary health goals based on lab findings."""
    goals = []
    
    if findings.get("alcohol_avoidance_required"):
        goals.append("Metabolic & Hepatic Protection: Strict alcohol elimination to alleviate liver strain and arrest lipid/uric acid surges.")
    if findings["high_cholesterol"] or findings["high_triglycerides"]:
        goals.append("Cardiovascular Lipid Optimization: Reduce circulating LDL and Triglycerides to protect arterial endothelium.")
    if findings["high_sugar"] or findings["high_hba1c"]:
        goals.append("Glycemic Regulation: Smooth postprandial glucose spikes and improve insulin sensitivity.")
    if findings["high_uric_acid"]:
        goals.append("Purine Minimization & Renal Clearance: Lower serum uric acid to avoid joint crystallisation.")
    if findings["high_bp"]:
        goals.append("Endothelial & Blood Pressure Control: Support arterial dilation via sodium reduction and potassium-rich foods.")
    if findings["elevated_liver"]:
        goals.append("Hepatic De-steatosis: Reduce simple sugars and saturated fats to alleviate liver enzyme burden.")
    if findings["elevated_kidney"]:
        goals.append("Renal Workload Management: Moderate nitrogenous waste by moderating high biological value protein density.")
    if findings["low_hemoglobin"]:
        goals.append("Hematopoiesis Support: Boost bioavailable elemental iron intake paired with Vitamin C.")
    if findings["low_vit_d"]:
        goals.append("Immune & Bone Mineralization: Augment dietary Vitamin D cofactors (calcium, magnesium) and sunlight.")
    if findings["low_vit_b12"]:
        goals.append("Erythrocyte & Neurological Support: Optimize active Cobalamin (Vitamin B12) intake.")
    if findings["high_bmi"]:
        goals.append("Caloric Equilibrium & Lean Mass Preservation: Gradual caloric deficit with nutrient-dense fiber.")

    if not goals:
        goals.append("Preventive Longevity & Metabolic Vitality: Maintain pristine biomarker baseline and cellular health.")

    return goals


def generate_foods_recommendations(
    findings: Dict[str, Any],
    diet_pref: str
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Generates foods to prioritize and foods to avoid based on findings and dietary preferences."""
    pref = diet_pref.lower()
    is_veg = pref in ("vegetarian", "lacto-vegetarian")
    is_vegan = pref == "vegan"
    is_eggetarian = pref == "eggetarian"
    is_non_veg = not (is_veg or is_vegan)

    prioritize = []
    avoid = []

    # Priority 1: High-Impact Protein & Core Dietary Foundation based on preference
    if is_non_veg and not is_eggetarian:
        if findings["high_cholesterol"] or findings["high_triglycerides"] or findings["low_hemoglobin"]:
            prioritize.append({
                "food": "Wild-Caught Salmon, Sardines & Mackerel",
                "rationale": "Direct EPA & DHA Omega-3 fatty acids actively reduce hepatic VLDL synthesis and clear arterial plaque.",
                "target_markers": ["Triglycerides", "LDL Cholesterol"]
            })
            prioritize.append({
                "food": "Lean Country Chicken Breast & Egg Whites",
                "rationale": "High Biological Value (BV 100) lean protein that provides heme iron without saturated animal fats.",
                "target_markers": ["Hemoglobin", "Total Protein"]
            })
            prioritize.append({
                "food": "Pasture-Raised Whole Eggs",
                "rationale": "Provides natural dietary choline, lutein, and bioactive Vitamin D3.",
                "target_markers": ["Vitamin D (25-OH)", "HDL Cholesterol"]
            })
    elif is_eggetarian:
        prioritize.append({
            "food": "Farm Fresh Boiled Eggs & Egg White Omelettes",
            "rationale": "Superior protein quality with zero glycemic index, providing essential choline and bioavailable albumin.",
            "target_markers": ["Total Protein", "Hemoglobin"]
        })
        prioritize.append({
            "food": "Sprouted Green Moong & Organic Low-Fat Curd",
            "rationale": "Active probiotic enzymes and living plant nutrients for gut and cholesterol regulation.",
            "target_markers": ["LDL Cholesterol", "Immunity"]
        })
    elif is_vegan:
        prioritize.append({
            "food": "Organic Non-GMO Tofu, Tempeh & Edamame",
            "rationale": "Complete plant-based isoflavones and branched-chain amino acids with zero dietary cholesterol.",
            "target_markers": ["LDL Cholesterol", "Total Protein"]
        })
        prioritize.append({
            "food": "Nutritional Yeast & Fortified Plant Milk",
            "rationale": "Crucial vegan sources of fortified bioactive Vitamin B12 and cholecalciferol (Vitamin D).",
            "target_markers": ["Vitamin B12", "Vitamin D (25-OH)"]
        })
        prioritize.append({
            "food": "Chia Seeds, Hemp Hearts & Ground Flaxseeds",
            "rationale": "High ALA Omega-3 fatty acids that reduce systemic vascular inflammation without fish.",
            "target_markers": ["Triglycerides", "HDL Cholesterol"]
        })
    else:  # Vegetarian (Lacto-Vegetarian)
        prioritize.append({
            "food": "Fresh Low-Fat Paneer & Homemade Probiotic Curd",
            "rationale": "High bioavailable casein and calcium for bone health with beneficial gut microbial diversity.",
            "target_markers": ["Total Protein", "Gut Health"]
        })
        prioritize.append({
            "food": "Sprouted Green Moong & Kala Chana (Black Chickpeas)",
            "rationale": "Enzyme-activated living legumes that maximize non-heme iron and resistant prebiotic starch.",
            "target_markers": ["Hemoglobin", "HbA1c"]
        })

    # Priority 2: Lipid Management (Cholesterol / Triglycerides)
    if findings["high_cholesterol"] or findings["high_triglycerides"]:
        prioritize.append({
            "food": "Steel-Cut Oats & Pearl Barley",
            "rationale": "Rich in beta-glucan soluble fiber that binds intestinal bile acids to accelerate LDL clearance.",
            "target_markers": ["Total Cholesterol", "LDL Cholesterol"]
        })
        prioritize.append({
            "food": "Raw Walnuts & Pumpkin Seeds",
            "rationale": "Plant sterols and magnesium that relax vascular smooth muscle and raise protective HDL.",
            "target_markers": ["HDL Cholesterol", "Triglycerides"]
        })

        avoid.append({
            "food": "Commercial Bakery Items (Puff pastry, cookies, cakes)",
            "rationale": "Loaded with industrial trans-fats and palm oil that directly suppress hepatic LDL receptors.",
            "target_markers": ["LDL Cholesterol", "Total Cholesterol"]
        })
        avoid.append({
            "food": "Full-fat Butter, Vanaspati, Lard, and Processed Cheese",
            "rationale": "High saturated fat content raises circulating ApoB and atherogenic lipoprotein particles.",
            "target_markers": ["Total Cholesterol", "Apo Lipoprotein B"]
        })

    # Priority 3: Blood Sugar / HbA1c
    if findings["high_sugar"] or findings["high_hba1c"]:
        prioritize.append({
            "food": "Fenugreek (Methi) Seeds, Ceylon Cinnamon, and Bitter Gourd",
            "rationale": "Inhibits alpha-glucosidase and improves peripheral GLUT4 insulin receptor sensitivity.",
            "target_markers": ["Fasting Blood Sugar", "HbA1c"]
        })
        prioritize.append({
            "food": "Barnyard & Foxtail Millets with Sprouted Legumes",
            "rationale": "Low Glycemic Index (GI < 50) complex carbs that release steady glucose without postprandial spikes.",
            "target_markers": ["HbA1c", "Postprandial Blood Sugar"]
        })

        avoid.append({
            "food": "Refined White Rice, Maida, White Bread, and Pastas",
            "rationale": "High Glycemic Index carbs trigger rapid glucose surges followed by compensatory hyperinsulinemia.",
            "target_markers": ["Fasting Blood Sugar", "HbA1c"]
        })
        avoid.append({
            "food": "Packaged Juices, Sodas, and Sweetened Beverages",
            "rationale": "Liquid simple sugars accelerate hepatic de novo lipogenesis and exacerbate visceral fat.",
            "target_markers": ["HbA1c", "Triglycerides"]
        })

    # Priority 4: Anemia / Low Hemoglobin
    if findings["low_hemoglobin"]:
        if is_non_veg and not is_eggetarian:
            prioritize.append({
                "food": "Chicken Liver (in moderation) / Mutton Bone Broth",
                "rationale": "Natural heme iron and collagen peptides with 3x higher absorption than plant iron.",
                "target_markers": ["Hemoglobin", "Ferritin"]
            })
        else:
            prioritize.append({
                "food": "Halim (Garden Cress) Seeds soaked in Coconut Water + Lemon",
                "rationale": "100g provides 100mg iron; pairing with Vitamin C converts ferric to absorbable ferrous iron.",
                "target_markers": ["Hemoglobin", "Ferritin"]
            })
        prioritize.append({
            "food": "Beetroot, Pomegranate, and Soaked Munakka (Black Raisins)",
            "rationale": "Rich in natural erythropoietic cofactors, folates, and endothelial nitric oxide precursors.",
            "target_markers": ["Hemoglobin", "RBC Count"]
        })
        avoid.append({
            "food": "Drinking Tea or Coffee within 60 minutes of meals",
            "rationale": "Polyphenols and tannins bind non-heme iron in the stomach, slashing iron uptake by 60%.",
            "target_markers": ["Hemoglobin", "Ferritin"]
        })

    # Priority 5: Uric Acid
    if findings["high_uric_acid"]:
        prioritize.append({
            "food": "Tart Cherries, Strawberries, and Lime Water",
            "rationale": "Rich in anthocyanins that enhance renal clearance and excretion of uric acid.",
            "target_markers": ["Uric Acid"]
        })
        avoid.append({
            "food": "Red Meat, Shellfish, and Organ Meats",
            "rationale": "Purine-dense foods that directly degrade into excess serum uric acid.",
            "target_markers": ["Uric Acid"]
        })
        avoid.append({
            "food": "High-Fructose Corn Syrup & Alcoholic Drinks",
            "rationale": "Fructose and ethanol metabolism rapidly deplete ATP, boosting uric acid synthesis.",
            "target_markers": ["Uric Acid"]
        })

    # Priority 6: Blood Pressure
    if findings["high_bp"]:
        prioritize.append({
            "food": "Fresh Spinach, Coconut Water, and Bananas",
            "rationale": "High potassium-to-sodium ratio facilitates urinary sodium excretion and arterial vasodilation.",
            "target_markers": ["Systolic Blood Pressure"]
        })
        avoid.append({
            "food": "Pickles (Achaar), Papads, and Salted Packaged Chips",
            "rationale": "High sodium density expands intravascular volume and elevates blood pressure.",
            "target_markers": ["Systolic Blood Pressure"]
        })

    # Priority 7: Liver Enzymes
    if findings["elevated_liver"]:
        prioritize.append({
            "food": "Cruciferous Veggies (Broccoli, Brussels Sprouts) & Green Tea",
            "rationale": "Sulforaphane and EGCG upregulate Phase-2 hepatic detox enzymes.",
            "target_markers": ["SGPT (ALT)", "SGOT (AST)"]
        })
        avoid.append({
            "food": "Alcohol and Deep-Fried Reheated Oils",
            "rationale": "Directly triggers hepatocyte lipid peroxidation and inflammatory ballooning.",
            "target_markers": ["SGPT (ALT)", "SGOT (AST)"]
        })

    # Priority 8: Vitamin D & B12
    if findings["low_vit_d"] or findings["low_vit_b12"]:
        if is_non_veg or is_eggetarian:
            prioritize.append({
                "food": "Fortified Low-Fat Milk, Greek Yogurt & Farm Eggs",
                "rationale": "Bioavailable natural cobalamin and fortified Vitamin D3.",
                "target_markers": ["Vitamin B12", "Vitamin D (25-OH)"]
            })
        else:
            prioritize.append({
                "food": "Sun-Exposed Mushrooms, Fortified Almond Milk & Nutritional Yeast",
                "rationale": "Plant-derived ergocalciferol (D2) and bioavailable B-complex vitamins.",
                "target_markers": ["Vitamin B12", "Vitamin D (25-OH)"]
            })

    # Priority 9: Alcohol Avoidance Protocol (When clinically indicated)
    if findings.get("alcohol_avoidance_required"):
        reasons = []
        target_markers = []
        if findings.get("elevated_liver"):
            reasons.append("alleviate liver enzyme burden and hepatocyte stress")
            target_markers.extend(["SGPT (ALT)", "SGOT (AST)", "GGTP"])
        if findings.get("high_triglycerides"):
            reasons.append("prevent acute hepatic triglyceride synthesis and VLDL surges")
            target_markers.append("Triglycerides")
        if findings.get("high_uric_acid"):
            reasons.append("prevent purine breakdown and renal urate retention")
            target_markers.append("Uric Acid")
        if findings.get("high_sugar") or findings.get("high_hba1c"):
            reasons.append("avoid glycemic volatility and impaired hepatic glucose regulation")
            target_markers.extend(["Fasting Blood Sugar", "HbA1c"])
        if findings.get("high_bp"):
            reasons.append("blunt sympathetic arterial vasoconstriction and reduce blood pressure")
            target_markers.append("Systolic Blood Pressure")
        if findings.get("high_cholesterol"):
            reasons.append("curb atherogenic lipoprotein particle synthesis")
            target_markers.append("LDL Cholesterol")

        target_markers = list(dict.fromkeys(target_markers))[:4]
        summary_reasons = "; ".join(reasons[:2])

        avoid.insert(0, {
            "food": "Alcohol & Alcoholic Beverages (Beer, Spirits, Wine, Cocktails)",
            "rationale": f"Clinical requirement to {summary_reasons}. Ethanol metabolism imposes direct hepatic workload, spikes circulating triglycerides, and hinders renal clearance.",
            "target_markers": target_markers
        })

    if len(avoid) < 2:
        avoid.append({
            "food": "Ultra-Processed Packaged Snacks & Sugary Drinks",
            "rationale": "Elevated advanced glycation end-products (AGEs) that drive systemic low-grade inflammation.",
            "target_markers": ["Overall Vitality"]
        })

    return prioritize, avoid


def generate_weekly_meal_plan(
    findings: Dict[str, Any],
    diet_pref: str,
    cuisine: str
) -> List[Dict[str, Any]]:
    """
    Constructs an interactive 7-day personalized meal plan with:
    Breakfast, Mid-Morning, Lunch, Evening Snack, Dinner.
    Tailored specifically to dietary choice (Non-Veg, Veg, Eggetarian, Vegan) and cuisine style.
    """
    pref = diet_pref.lower()
    is_vegan = pref == "vegan"
    is_eggetarian = pref == "eggetarian"
    is_veg = pref in ("vegetarian", "lacto-vegetarian")
    is_non_veg = not (is_veg or is_vegan or is_eggetarian)

    is_indian = "indian" in cuisine.lower()
    is_med = "mediterranean" in cuisine.lower()
    has_diabetes = findings["high_sugar"] or findings["high_hba1c"]
    has_lipid = findings["high_cholesterol"] or findings["high_triglycerides"]
    has_uric = findings["high_uric_acid"]

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekly_plan = []

    if is_indian:
        templates = [
            # Day 1
            {
                "breakfast": (
                    "2 Farm Egg Omelette with baby spinach, tomatoes & 1 slice multigrain toast" if is_non_veg else
                    "Boiled Farm Eggs (2 whites + 1 whole) with avocado on multigrain toast" if is_eggetarian else
                    "Tofu Scramble with turmeric, baby spinach, tomatoes & 1 slice multigrain toast" if is_vegan else
                    "Steamed Ragi & Vegetable Idlis (3) with fresh sprouted moong dal sambar & mint chutney"
                ),
                "breakfast_portion": "2 eggs + 1 toast" if (is_non_veg or is_eggetarian) else "3 idlis + 1 cup sambar",
                "breakfast_focus": "High biological value protein & micronutrient density" if (is_non_veg or is_eggetarian) else "Low-glycemic calcium-rich ancient millets with living enzymes",
                
                "mid_morning": (
                    "Warm spiced chicken bone broth or 1 whole green apple + 4 soaked walnuts" if is_non_veg else
                    "Fresh tender coconut water with 1 tbsp soaked chia/sabja seeds + 4 soaked walnuts"
                ),
                "mid_morning_portion": "1 cup broth / 1 glass coconut water + nuts",
                "mid_morning_focus": "Collagen & electrolytes" if is_non_veg else "Hydration, kidney flushing & ALA Omega-3s",
                
                "lunch": (
                    "Multigrain Rotis (2) + Grilled Lemon Herb Chicken Breast (150g) + Yellow Moong Dal Tadka + Cucumber Salad" if is_non_veg else
                    "Multigrain Rotis (2) + Egg Curry (2 boiled eggs in light onion-tomato gravy) + Yellow Dal + Salad" if is_eggetarian else
                    "2 Multigrain Rotis + Palak Tofu Curry (150g organic tofu) + Yellow Moong Dal + Cucumber Salad" if is_vegan else
                    "Brown Rice / 2 Multigrain Rotis + Palak Paneer (120g low-fat paneer) + Yellow Moong Dal + Cucumber Salad"
                ),
                "lunch_portion": "2 rotis + 150g protein + 1 cup dal + salad",
                "lunch_focus": "Lean heme iron & high protein satiety" if is_non_veg else "Complete amino acids, bioavailable calcium & iron-rich greens",

                "evening_snack": (
                    "Spiced Masala Green Tea + handful of roasted pumpkin seeds" if is_non_veg else
                    "Roasted Makhana (Fox nuts) with turmeric & pinch of black pepper + cup of Green Tea"
                ),
                "evening_snack_portion": "1 mug tea + 20g seeds / makhana",
                "evening_snack_focus": "Zinc, magnesium & antioxidant polyphenol recovery",

                "dinner": (
                    "Grilled fish fillet (150g) with stir-fried bell peppers, steamed zucchini and light lemon broth" if is_non_veg else
                    "Egg Bhurji (2 whites) with sautéed vegetables and 1 warm phulka" if is_eggetarian else
                    "Light Vegetable Quinoa Khichdi with steamed French beans, carrots & roasted flaxseed powder" if is_vegan else
                    "Light Vegetable Quinoa Khichdi with steamed French beans, carrots & fresh probiotic curd"
                ),
                "dinner_portion": "150g fish + 1.5 cups veg" if is_non_veg else "1 medium bowl khichdi (250g)",
                "dinner_focus": "Cardio-protective marine EPA/DHA Omega-3s" if is_non_veg else "Easy-to-digest gut soothing meal 2.5 hours before sleep"
            },
            # Day 2
            {
                "breakfast": (
                    "Egg Bhurji with methi, onions, tomatoes and 1 warm whole wheat phulka" if is_non_veg else
                    "2 boiled egg whites on 1 slice toasted sourdough with sliced avocado" if is_eggetarian else
                    "Sprouted Moong & Pomegranate chaat with lemon dressing and chia seeds" if is_vegan else
                    "Besan & Fenugreek (Methi) Cheela with green mint chutney and probiotic curd"
                ),
                "breakfast_portion": "2 eggs + 1 phulka" if is_non_veg else "1 large bowl chaat / 2 cheelas",
                "breakfast_focus": "Blood sugar stabilizing fenugreek paired with high protein",

                "mid_morning": "1 whole green apple + handful of roasted chana",
                "mid_morning_portion": "1 fruit + 30g chana",
                "mid_morning_focus": "Pectin fiber to bind circulating cholesterol",

                "lunch": (
                    "Brown Rice (1 cup) + Steamed Rohu/Pomfret Fish in Light Mustard Curry + Steamed Green Beans + Salad" if is_non_veg else
                    "2 Jowar (Sorghum) Rotis + Methi Baingan Sabzi + Rajma (Kidney Bean) Curry + Radish Tomato Salad" if (is_veg or is_vegan) else
                    "Brown Rice + Egg Bhurji with Spinach + Rajma Curry + Kachumber"
                ),
                "lunch_portion": "1 cup rice/2 rotis + 1 cup curry + salad",
                "lunch_focus": "Gluten-free complex carbs with liver-protective glucosinolates",

                "evening_snack": "Ginger Lemon Green Tea + 6-8 soaked almonds",
                "evening_snack_portion": "1 mug + 8 nuts",
                "evening_snack_focus": "Vitamin E and anti-inflammatory gingerols",

                "dinner": (
                    "Clear Country Chicken Soup with shredded chicken, sweet corn, baby spinach & mushrooms" if is_non_veg else
                    "Lauki (Bottle Gourd) & Chana Dal soup with a bowl of sautéed mushrooms and broccoli"
                ),
                "dinner_portion": "1 large bowl soup (350ml)",
                "dinner_focus": "High water content, vascular soothing & cellular recovery"
            },
            # Day 3
            {
                "breakfast": (
                    "Poached eggs (2) on toasted sourdough with smashed avocado and lemon pepper" if (is_non_veg or is_eggetarian) else
                    "Steamed Ragi Idli (2) or Vegetable Dalia Upma with coconut-chana dal chutney"
                ),
                "breakfast_portion": "2 eggs + toast" if (is_non_veg or is_eggetarian) else "2 idlis / 1 bowl upma",
                "breakfast_focus": "Monounsaturated fats & sustained energy",

                "mid_morning": "1 medium Guava or bowl of fresh papaya pearls",
                "mid_morning_portion": "1 cup (150g)",
                "mid_morning_focus": "Vitamin C surge to optimize non-heme iron absorption",

                "lunch": (
                    "2 Jowar Rotis + Chicken Tikka (non-creamy, 150g) + Methi Palak Sabzi + Tomato Onion Kachumber" if is_non_veg else
                    "1 cup Quinoa Pulao with peas + Sprouted Kala Chana Curry + Beetroot Raita (salad for vegan)"
                ),
                "lunch_portion": "2 rotis/1 cup grain + 150g protein + salad",
                "lunch_focus": "Nitrate-rich endothelial support & complete amino acids",

                "evening_snack": "Sprouts bhel with tomato, onion, coriander, and squeeze of lime",
                "evening_snack_portion": "1 small bowl (100g)",
                "evening_snack_focus": "Prebiotic dietary fiber & digestive enzymes",

                "dinner": (
                    "Pan-seared Lemon Chicken Breast (140g) with steamed broccoli, carrots and roasted cauliflower" if is_non_veg else
                    "Warm Lentil & Spinach Soup (Dal Palak) with grilled low-fat paneer/tofu cubes (100g)"
                ),
                "dinner_portion": "140g chicken + 1.5 cups veg" if is_non_veg else "1 bowl soup + 100g protein",
                "dinner_focus": "Ultra-low glycemic load restorative recovery"
            },
            # Day 4
            {
                "breakfast": (
                    "Scrambled eggs (2) with sautéed mushrooms, bell peppers, and fresh cilantro + 1 toast" if (is_non_veg or is_eggetarian) else
                    "Besan & Fenugreek (Methi) chilla with green chutney and probiotic curd"
                ),
                "breakfast_portion": "2 eggs + 1 toast" if (is_non_veg or is_eggetarian) else "2 chillas",
                "breakfast_focus": "Insulin-sensitizing minerals & protein",

                "mid_morning": "Fresh tender coconut water with 1 tbsp soaked basil seeds (sabja)",
                "mid_morning_portion": "1 glass (250ml)",
                "mid_morning_focus": "Natural potassium & arterial tension reduction",

                "lunch": (
                    "Quinoa Pulao with peas + Grilled Fish Fillet (150g) + Mixed Vegetable Salad with Lemon" if is_non_veg else
                    "2 Multigrain rotis + Bhindi (Okra) fry in cold-pressed oil + Mixed Dal + Cucumber mint salad"
                ),
                "lunch_portion": "2 rotis/1 cup grain + protein + dal + salad",
                "lunch_focus": "Soluble mucilage for intestinal cholesterol binding",

                "evening_snack": "Roasted Makhana (Fox nuts) tossed with turmeric and black pepper",
                "evening_snack_portion": "1 bowl (30g)",
                "evening_snack_focus": "Kidney-friendly low-sodium crunch",

                "dinner": (
                    "Steamed fish tikka (150g) with a bowl of warm lentil soup and fresh green salad" if is_non_veg else
                    "Millet vegetable khichdi (Barnyard / Kodo millet) served with probiotic curd"
                ),
                "dinner_portion": "150g fish + soup" if is_non_veg else "1.5 cups khichdi",
                "dinner_focus": "Hepatic detox support with zero trans fats"
            },
            # Day 5
            {
                "breakfast": (
                    "Masala egg omelette with turmeric, onions & coriander + 1 multigrain toast" if (is_non_veg or is_eggetarian) else
                    "Poha with generous peas, carrots, peanuts, turmeric and fresh lemon squeeze"
                ),
                "breakfast_portion": "2 eggs + 1 toast" if (is_non_veg or is_eggetarian) else "1 medium bowl (200g)",
                "breakfast_focus": "Bioavailable iron enhanced with Vitamin C",

                "mid_morning": "Slice of fresh papaya or bowl of pomegranate pearls",
                "mid_morning_portion": "1 cup (150g)",
                "mid_morning_focus": "Vascular polyphenols & antioxidant protection",

                "lunch": (
                    "Multigrain Rotis (2) + Country Chicken Stew with vegetables + Yellow Dal + Green Salad" if is_non_veg else
                    "2 Missi rotis (Gram flour + wheat) + Baingan Bharta + Sambar with drumsticks + Tomato salad"
                ),
                "lunch_portion": "2 rotis + protein + sambar/dal",
                "lunch_focus": "Drumstick (Moringa) bioactive peptides for metabolic regulation",

                "evening_snack": "Roasted chickpeas (Kala Chana) with fresh mint chaat",
                "evening_snack_portion": "1 small cup (40g)",
                "evening_snack_focus": "Slow-burning complex carbohydrate & zinc",

                "dinner": (
                    "Grilled herb fish with sautéed asparagus, zucchini, and light vegetable clear broth" if is_non_veg else
                    "Clear Vegetable Soup with sautéed low-fat Paneer/Tofu and steamed broccoli"
                ),
                "dinner_portion": "1 large bowl soup + 120g protein",
                "dinner_focus": "Low sodium DASH guideline compliance"
            },
            # Day 6
            {
                "breakfast": (
                    "2 Boiled eggs (1 whole + 1 white) with sliced avocado on toasted sourdough" if (is_non_veg or is_eggetarian) else
                    "Avocado & tomato mash on toasted multigrain sourdough with pumpkin seeds"
                ),
                "breakfast_portion": "2 toasts",
                "breakfast_focus": "Heart-healthy monounsaturated fats (MUFA) for HDL support",

                "mid_morning": "1 whole sweet orange or pear with skin",
                "mid_morning_portion": "1 whole fruit",
                "mid_morning_focus": "Pectin fiber to bind circulating cholesterol",

                "lunch": (
                    "Brown Rice + Fish Curry with drumsticks + Cabbage Carrot Poriyal + Radish salad" if is_non_veg else
                    "Brown rice with Chana Masala (Chickpeas) + Cabbage Thoran + Radish salad"
                ),
                "lunch_portion": "1 cup rice + 1 cup curry + salad",
                "lunch_focus": "Cruciferous indoles and sulfur compounds for hepatic clearance",

                "evening_snack": "Herbal Chamomile or Tulsi tea + roasted pumpkin and sunflower seeds",
                "evening_snack_portion": "1 cup tea + 20g seeds",
                "evening_snack_focus": "Cortisol reduction and arterial calming",

                "dinner": (
                    "Chicken breast stir-fry with broccoli, snap peas, and minimal sesame oil" if is_non_veg else
                    "Mixed vegetable & paneer (or organic tofu) stir-fry with minimal sesame oil"
                ),
                "dinner_portion": "1 large bowl (300g)",
                "dinner_focus": "High protein, zero refined carbs, restorative sleep support"
            },
            # Day 7
            {
                "breakfast": (
                    "Sunday High-Protein Bowl: 2 Boiled eggs + smoked chicken breast strips + steamed greens" if is_non_veg else
                    "Sunday Wellness Bowl: Greek yogurt / Probiotic curd with flaxseeds, blueberries, and walnuts"
                ),
                "breakfast_portion": "1 large bowl (250g)",
                "breakfast_focus": "Microbiome diversity & cellular rejuvenation",

                "mid_morning": "Cucumber, Celery, and Green Apple cold-pressed booster juice",
                "mid_morning_portion": "1 glass (200ml)",
                "mid_morning_focus": "Cellular hydration & kidney detoxification",

                "lunch": (
                    "Sunday Grill: Herb-Crusted Roasted Chicken Breast (180g) + Sautéed Broccoli, Zucchini & Sweet Potato" if is_non_veg else
                    "Whole Wheat Pasta with Olive Oil, Garlic, Broccoli, and White Cannellini Beans (or Paneer)"
                ),
                "lunch_portion": "1 balanced plate (350g)",
                "lunch_focus": "Cardio-protective polyphenol and lean protein blend",

                "evening_snack": "Roasted makhana + warm turmeric golden almond milk",
                "evening_snack_portion": "1 cup (150ml) + 20g makhana",
                "evening_snack_focus": "Curcumin anti-inflammatory vascular recovery",

                "dinner": (
                    "Clear broth with tender chicken, mushrooms, and mixed steamed vegetables" if is_non_veg else
                    "Light Vegetable Clear Broth with steamed sweet corn, mushrooms, and zucchini"
                ),
                "dinner_portion": "1 large soup bowl (300ml)",
                "dinner_focus": "Digestive rest preparing the metabolic system for the upcoming week"
            }
        ]
    else:
        # Mediterranean / Western template
        templates = [
            # Day 1
            {
                "breakfast": (
                    "Poached eggs on sourdough toast with smoked salmon, sliced avocado & lemon" if is_non_veg else
                    "Poached eggs on sourdough toast with smashed avocado, cherry tomatoes & olive oil" if is_eggetarian else
                    "Tofu scramble with turmeric, baby spinach, cherry tomatoes & avocado sourdough" if is_vegan else
                    "Greek yogurt bowl with walnuts, chia seeds, fresh blueberries & drizzle of honey"
                ),
                "breakfast_portion": "2 eggs + 1 toast / 1 bowl (250g)",
                "breakfast_focus": "Marine Omega-3s & MUFA" if is_non_veg else "Probiotic protein & polyphenol flavonoids",

                "mid_morning": "1 crisp green apple + 6 raw almonds",
                "mid_morning_portion": "1 apple + 15g nuts",
                "mid_morning_focus": "Sustained arterial satiety",

                "lunch": (
                    "Grilled Wild Salmon fillet (150g) over Mediterranean Quinoa, Kalamata olives, cucumbers & olive oil" if is_non_veg else
                    "Mediterranean Quinoa Salad with chickpeas, Kalamata olives, cucumbers, cherry tomatoes & crumbled feta"
                ),
                "lunch_portion": "1 large bowl (350g)",
                "lunch_focus": "Heart-healthy monounsaturated fatty acids & clean plant fiber",

                "evening_snack": "Carrot and celery batons with 2 tbsp traditional garlic hummus",
                "evening_snack_portion": "1 cup veggies + 30g hummus",
                "evening_snack_focus": "Prebiotic fiber with low glycemic impact",

                "dinner": (
                    "Herb-crusted baked chicken breast (150g) with roasted Brussels sprouts, zucchini & sweet potato" if is_non_veg else
                    "Lentil and vegetable stew with steamed kale, roasted zucchini and sweet potato"
                ),
                "dinner_portion": "150g protein + 1.5 cups veg",
                "dinner_focus": "Anti-inflammatory low-glycemic evening meal"
            }
        ] * 7

    for i, day_name in enumerate(days):
        t = templates[i % len(templates)]
        weekly_plan.append({
            "day": day_name,
            "meals": [
                {
                    "meal_type": "Breakfast (8:00 AM - 9:00 AM)",
                    "menu": t["breakfast"],
                    "portion_guide": t["breakfast_portion"],
                    "nutrition_focus": t["breakfast_focus"]
                },
                {
                    "meal_type": "Mid-Morning Refresh (11:00 AM)",
                    "menu": t["mid_morning"],
                    "portion_guide": t["mid_morning_portion"],
                    "nutrition_focus": t["mid_morning_focus"]
                },
                {
                    "meal_type": "Lunch (1:00 PM - 2:00 PM)",
                    "menu": t["lunch"],
                    "portion_guide": t["lunch_portion"],
                    "nutrition_focus": t["lunch_focus"]
                },
                {
                    "meal_type": "Evening Fuel (4:30 PM - 5:30 PM)",
                    "menu": t["evening_snack"],
                    "portion_guide": t["evening_snack_portion"],
                    "nutrition_focus": t["evening_snack_focus"]
                },
                {
                    "meal_type": "Dinner (7:30 PM - 8:30 PM)",
                    "menu": t["dinner"],
                    "portion_guide": t["dinner_portion"],
                    "nutrition_focus": t["dinner_focus"]
                }
            ]
        })

    return weekly_plan


def generate_lifestyle_recommendations(findings: Dict[str, Any]) -> List[str]:
    """Generates actionable physical and lifestyle protocols based on findings."""
    tips = [
        "Hydration Target: Drink at least 2.5 to 3.0 liters of filtered water daily to facilitate renal filtration of metabolic byproducts.",
        "Sleep Hygiene: Maintain 7-8 hours of continuous nocturnal sleep to prevent elevated morning cortisol and insulin resistance."
    ]

    if findings["high_cholesterol"] or findings["high_triglycerides"]:
        tips.append("Aerobic Exercise: Engage in 150 minutes per week of Zone 2 cardio (brisk walking, cycling, light jogging) to upregulate lipoprotein lipase and boost HDL.")
    if findings["high_sugar"] or findings["high_hba1c"]:
        tips.append("Post-Meal Activity: Take a light 10-15 minute walk immediately following lunch and dinner to dramatically blunt glycemic excursions via GLUT4 muscle transporters.")
    if findings["high_bp"]:
        tips.append("Sodium Moderation: Restrict total dietary sodium to < 1,800 mg/day (less than 1 level teaspoon of salt, avoiding hidden sodium in sauces, breads, and condiments).")
    if findings["high_uric_acid"]:
        tips.append("Avoid Prolonged Fasting: Prolonged dry fasting or crash dieting can precipitate ketosis and transiently elevate serum uric acid levels; eat regular balanced meals.")
    if findings["low_vit_d"]:
        tips.append("Sun Exposure: Expose arms and face to mid-morning sunlight (10 AM - 11 AM) for 15-20 minutes without sunscreen 3-4 days a week to stimulate endogenous cutaneous Vitamin D3 synthesis.")
    if findings.get("alcohol_avoidance_required"):
        triggers = []
        if findings.get("elevated_liver"): triggers.append("elevated liver enzymes (SGPT/SGOT)")
        if findings.get("high_triglycerides"): triggers.append("elevated triglycerides")
        if findings.get("high_uric_acid"): triggers.append("high uric acid")
        if findings.get("high_sugar") or findings.get("high_hba1c"): triggers.append("prediabetic glucose/HbA1c")
        if findings.get("high_bp"): triggers.append("elevated blood pressure")
        if findings.get("high_cholesterol"): triggers.append("elevated cholesterol")
        triggers_str = ", ".join(triggers[:3])
        tips.append(f"Alcohol Elimination Protocol: Strictly abstain from alcohol. Your report flags {triggers_str}, which are directly aggravated by ethanol metabolism. Complete alcohol avoidance is essential to alleviate hepatic workload, halt triglyceride surges, and support metabolic recovery.")

    return tips


def create_diet_plan(
    report_id: int,
    patient_name: str,
    biomarkers: List[Dict[str, Any]],
    diet_pref: str = "Vegetarian",
    cuisine_pref: str = "Indian",
    calorie_target: int = 2000
) -> Dict[str, Any]:
    """
    Main orchestrator: analyzes biomarkers and produces a complete, personalized, clinical diet plan.
    """
    findings = analyze_health_findings(biomarkers)
    goals = generate_health_goals(findings)
    prioritize, avoid = generate_foods_recommendations(findings, diet_pref)
    meal_plan = generate_weekly_meal_plan(findings, diet_pref, cuisine_pref)
    lifestyle = generate_lifestyle_recommendations(findings)

    return {
        "report_id": report_id,
        "patient_name": patient_name,
        "diet_preference": diet_pref,
        "cuisine_preference": cuisine_pref,
        "calorie_target": calorie_target,
        "primary_health_goals": goals,
        "foods_to_prioritize": prioritize,
        "foods_to_avoid": avoid,
        "weekly_meal_plan": meal_plan,
        "lifestyle_recommendations": lifestyle
    }
