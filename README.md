# HealthTrack & DietRx 🩺🥗
### Personal Medical Health Report Manager & AI Diet Planner

A private, self-contained personal health management application to upload annual medical checkup reports, store structured biomarkers and files in a local SQL database, filter and search historical reports by year and patient name, track multi-year health trajectories, and generate clinical diet plans tailored to specific health findings.

---

## 🌟 Key Features

1. **📄 Upload & Smart Report Ingestion**:
   - Drag & drop PDF or text medical checkup reports (Apollo, Metropolis, Dr Lal PathLabs, Quest, LabCorp, etc.).
   - Automatically extracts parameters across **Lipid Profile**, **Blood Sugar / Diabetes**, **Kidney Function (KFT)**, **Liver Function (LFT)**, **Complete Blood Count (CBC)**, **Thyroid & Vitamins**, and **Vitals**.
   - **Interactive Review & Edit Table**: Verify and adjust test values, reference ranges, and abnormal flags before committing to SQL.

2. **🗄️ SQL Database Storage**:
   - Zero-configuration local **SQLite** database (`data/health_reports.db`).
   - Secure and 100% private to your local computer.
   - Relational schema linking reports, biomarkers, and generated diet plans with cascade integrity.

3. **🔍 Multi-Year Retrieval & Apt Filters**:
   - Filter by **Checkup Year** (e.g., 2023, 2024, 2025, 2026).
   - Filter by **Patient Name** (e.g. your name, family members).
   - Filter by **Attention Needed / Out-of-Range Only**.
   - Instant search across lab names and clinical notes.

4. **📈 Multi-Year Health Trajectory & Trends**:
   - Interactive line graphs powered by Chart.js.
   - Select any test (e.g., *Total Cholesterol*, *LDL*, *HbA1c*, *Fasting Blood Sugar*, *Creatinine*, *Blood Pressure*) to compare values across annual checkups against normal reference thresholds.

5. **🥗 Biomarker-Driven Clinical Diet Planner**:
   - Formulates targeted nutrition plans based on abnormal lab results:
     - **Elevated Lipids / LDL / Triglycerides**: Soluble fiber protocols, omega-3 ALA/EPA, phytosterols, eliminates trans-fats and palm oil.
     - **Elevated Fasting Glucose / HbA1c**: Low-glycemic index carbohydrates, fiber, methi/cinnamon, avoids refined sugars and juices.
     - **Elevated Uric Acid**: Low-purine framework, hydration, cherries/citrus, eliminates organ meats and high-fructose corn syrup.
     - **Elevated Blood Pressure**: DASH sodium moderation (<1800mg/day) and potassium/nitrate-rich foods.
     - **Elevated Liver Enzymes**: Cruciferous indoles, antioxidant greens, zero-alcohol protocols.
     - **Low Hemoglobin / Vitamins**: Targeted bioavailable nutrient pairings.
   - Supports **Vegetarian**, **Non-Vegetarian**, **Eggetarian**, and **Vegan** preferences.
   - Offers **Indian (Rotis, Dals, Millets)**, **Mediterranean**, and **Western** cuisine templates.
   - Complete 7-Day structured 5-meal schedule (Breakfast, Mid-Morning, Lunch, Evening Snack, Dinner) with portion guidelines.
   - **Print Diet Sheet** button formatted for easy printing.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.9+ installed on your system.

### 2. Install Dependencies
Open your terminal or PowerShell in this project directory:
```bash
cd "C:\Users\Pavithran\.gemini\antigravity\scratch\health-report-diet-planner"
pip install -r requirements.txt
```

### 3. Run the App

#### Option A: Run Streamlit Web App (Recommended for Streamlit Cloud deployment)
```bash
streamlit run streamlit_app.py
```
👉 Opens immediately in your browser at **http://localhost:8501**!

#### Option B: Run FastAPI Web App
```bash
python run.py
```
The server will start at:
👉 **[http://localhost:8000](http://localhost:8000)**

*Note: On the very first run, the SQLite database is initialized and loaded with your checkup reports so you can immediately explore multi-year trends, archives, and diet plans!*

---

## 🌐 Deploy to Streamlit Community Cloud (streamlit.io)

You can deploy this application for free to **Streamlit Community Cloud** in 3 easy steps so your family or colleagues can view it on the web:

1. **Push your code to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Deploy HealthTrack to Streamlit"
   git remote add origin https://github.com/<your-username>/<your-repo-name>.git
   git branch -M main
   git push -u origin main
   ```

2. **Sign in to Streamlit**:
   - Go to [share.streamlit.io](https://share.streamlit.io) and log in with your GitHub account.

3. **Deploy the App**:
   - Click **"New app"**.
   - Select your repository and branch (`main`).
   - Set **Main file path** to: `streamlit_app.py`.
   - Click **Deploy!**

In ~1-2 minutes, Streamlit will provide a live public HTTPS URL (e.g. `https://your-app-name.streamlit.app`) that anyone can open on mobile or desktop!

---

### 4. Running Automated Tests
```bash
python -m pytest tests/
```

---

## 📁 Project Structure

```
health-report-diet-planner/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application & REST endpoints
│   ├── database.py              # SQLite engine & SQLAlchemy setup
│   ├── models.py                # SQL models (Report, Biomarker, DietPlan)
│   ├── schemas.py               # Pydantic request/response validation schemas
│   ├── extractor.py             # Medical report parser & clinical range evaluator
│   ├── diet_engine.py           # Clinical nutrition matrix & 7-day meal planner
│   └── static/
│       ├── index.html           # Modern responsive dashboard
│       ├── css/styles.css       # Custom styles & print layout
│       └── js/
│           ├── app.js           # UI logic, uploads, filters, and modal handling
│           └── charts.js        # Chart.js multi-year trend line visualization
├── data/
│   ├── sample_reports/          # Sample checkup report for testing
│   ├── uploads/                 # Uploaded checkup documents
│   └── health_reports.db        # SQLite database (auto-created)
├── tests/
│   ├── test_db.py               # Database CRUD & filter tests
│   ├── test_diet.py             # Diet engine clinical logic tests
│   └── test_extractor.py        # Biomarker text & date extraction tests
├── seed_data.py                 # Seeds sample multi-year checkups
├── run.py                       # One-click launch script
└── requirements.txt             # Project dependencies
```
