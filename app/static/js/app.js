// Main Application State & Controller

let currentExtractedData = null;
let currentReports = [];

document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initUploadZone();
    loadDashboard();
    loadFilterOptions();
    loadReports();
    populateDietReportSelector();
});

// -------------------------------------------------------------
// Tab Management
// -------------------------------------------------------------

function initTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.getAttribute('data-target');
            switchTab(targetTab);
        });
    });
}

function switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('border-sky-600', 'text-sky-600', 'font-semibold');
        btn.classList.add('border-transparent', 'text-slate-500');
    });

    const activeContent = document.getElementById(tabId);
    if (activeContent) activeContent.classList.remove('hidden');

    const activeBtn = document.querySelector(`[data-target="${tabId}"]`);
    if (activeBtn) {
        activeBtn.classList.remove('border-transparent', 'text-slate-500');
        activeBtn.classList.add('border-sky-600', 'text-sky-600', 'font-semibold');
    }

    if (tabId === 'dashboard-section') {
        loadDashboard();
    } else if (tabId === 'reports-section') {
        loadReports();
    } else if (tabId === 'diet-section') {
        populateDietReportSelector();
    }
}

// -------------------------------------------------------------
// Dashboard & Multi-Patient Family Analytics
// -------------------------------------------------------------

function stripPatientTitle(name) {
    if (!name) return 'Unknown Patient';
    return name.replace(/^(?:mr|mrs|ms|miss|dr|prof|shri|smt|master|baby|m\/s)\.?\s+/i, '').trim() || name.trim();
}

function getCanonicalPatientKey(name) {
    const clean = stripPatientTitle(name).toUpperCase();
    const tokens = clean.split(/[\s\.\-_]+/).filter(Boolean);
    if (tokens.length === 0) return 'UNKNOWN';
    const sig = tokens.filter(t => t.length > 2);
    return sig.length > 0 ? sig.join(' ') : tokens.join(' ');
}

let currentActivePatient = 'ALL';
let familyPatientsList = [];

async function loadDashboard() {
    try {
        // 1. Fetch multi-patient family summaries
        const patientsRes = await fetch('/api/analytics/patients');
        if (patientsRes.ok) {
            const data = await patientsRes.json();
            familyPatientsList = Array.isArray(data) ? data : [];
        } else {
            console.error('Failed to load patients:', patientsRes.statusText);
            familyPatientsList = [];
        }

        renderPatientSelectorPills();
        renderFamilyCards();

        // 2. Fetch metrics and trends for the active patient (or ALL)
        await loadMetricsAndTrendsForActivePatient();
    } catch (err) {
        console.error('Error loading dashboard summary:', err);
    }
}

function renderPatientSelectorPills() {
    const container = document.getElementById('patient-selector-pills');
    if (!container || !Array.isArray(familyPatientsList)) return;

    let html = `
        <button onclick="selectPatient('ALL')" class="px-3 py-1 rounded-full text-xs font-bold transition flex items-center gap-1.5 ${currentActivePatient === 'ALL' ? 'bg-sky-600 text-white shadow-sm' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}">
            <i data-lucide="home" class="w-3 h-3"></i> All Family (${familyPatientsList.length})
        </button>
    `;

    familyPatientsList.forEach(p => {
        const isSelected = (currentActivePatient === p.patient_name);
        const hasFlags = (p.abnormal_findings_count > 0);
        html += `
            <button onclick="selectPatient('${escapeHtml(p.patient_name)}')" class="px-3 py-1 rounded-full text-xs font-bold transition flex items-center gap-1.5 ${isSelected ? 'bg-sky-600 text-white shadow-sm' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'}">
                <span>${escapeHtml(p.patient_name)}</span>
                ${hasFlags ? `<span class="w-2 h-2 rounded-full bg-rose-500 ring-2 ring-white"></span>` : `<span class="w-2 h-2 rounded-full bg-emerald-500"></span>`}
            </button>
        `;
    });

    container.innerHTML = html;
    lucide.createIcons();
}

function renderFamilyCards() {
    const section = document.getElementById('family-overview-section');
    const grid = document.getElementById('family-cards-grid');
    const banner = document.getElementById('patient-active-banner');

    if (!section || !grid) return;

    if (currentActivePatient === 'ALL') {
        section.classList.remove('hidden');
        if (banner) banner.classList.add('hidden');

        if (familyPatientsList.length === 0) {
            grid.innerHTML = `
                <div class="col-span-full bg-white p-8 rounded-xl border border-slate-200 text-center text-slate-400">
                    <i data-lucide="user-x" class="w-10 h-10 mx-auto text-slate-300 mb-2"></i>
                    <p class="text-sm font-semibold text-slate-600">No patient reports uploaded yet</p>
                    <p class="text-xs text-slate-400 mt-1">Upload your report or your family member's report in the Upload Report tab.</p>
                </div>
            `;
            lucide.createIcons();
            return;
        }

        grid.innerHTML = familyPatientsList.map(p => {
            const initials = p.patient_name.replace(/^(Mr\.|Mrs\.|Ms\.|Dr\.)\s*/i, '').split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase() || 'P';
            const isAttention = p.abnormal_findings_count > 0;
            const badgeClass = isAttention ? 'bg-rose-50 text-rose-700 border-rose-200' : 'bg-emerald-50 text-emerald-700 border-emerald-200';
            const badgeText = isAttention ? `${p.abnormal_findings_count} Flag${p.abnormal_findings_count > 1 ? 's' : ''} Attention Needed` : 'All Key Markers Normal';

            // Top abnormal markers badges
            const markersHtml = (p.latest_abnormal_markers || []).slice(0, 4).map(m => `
                <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-200">
                    ${escapeHtml(m.test_name)}: ${m.result_value} ${escapeHtml(m.unit || '')}
                </span>
            `).join('');

            return `
                <div class="bg-white rounded-2xl border border-slate-200 hover:border-sky-300 hover:shadow-md transition p-5 flex flex-col justify-between space-y-4">
                    <div>
                        <div class="flex items-start justify-between gap-2 mb-3">
                            <div class="flex items-center gap-3">
                                <div class="w-11 h-11 rounded-xl bg-gradient-to-br from-sky-500 to-indigo-600 text-white font-black flex items-center justify-center text-sm shadow-sm">
                                    ${initials}
                                </div>
                                <div>
                                    <h4 class="text-sm font-bold text-slate-900">${escapeHtml(p.patient_name)}</h4>
                                    <p class="text-[11px] text-slate-400">Latest: ${p.latest_year} • ${escapeHtml(p.latest_lab)}</p>
                                </div>
                            </div>
                            <span class="px-2 py-0.5 rounded-full text-[10px] font-bold border ${badgeClass} shrink-0">
                                ${badgeText}
                            </span>
                        </div>

                        <div class="grid grid-cols-2 gap-2 my-3 p-2.5 bg-slate-50 rounded-xl border border-slate-100 text-center">
                            <div>
                                <div class="text-xs text-slate-400">Total Checkups</div>
                                <div class="text-sm font-bold text-slate-800">${p.total_reports} Annual Record${p.total_reports > 1 ? 's' : ''}</div>
                            </div>
                            <div>
                                <div class="text-xs text-slate-400">Timeline</div>
                                <div class="text-sm font-bold text-sky-700">${(p.years_tracked || []).join(', ')}</div>
                            </div>
                        </div>

                        ${p.latest_abnormal_markers && p.latest_abnormal_markers.length > 0 ? `
                            <div class="space-y-1.5 mt-2">
                                <div class="text-[11px] font-semibold text-slate-600 flex items-center gap-1">
                                    <i data-lucide="alert-triangle" class="w-3 h-3 text-amber-500"></i> Active Health Focus:
                                </div>
                                <div class="flex flex-wrap gap-1">
                                    ${markersHtml}
                                    ${p.latest_abnormal_markers.length > 4 ? `<span class="text-[10px] text-slate-400 self-center">+${p.latest_abnormal_markers.length - 4} more</span>` : ''}
                                </div>
                            </div>
                        ` : `
                            <div class="text-[11px] text-emerald-600 font-medium flex items-center gap-1 mt-2">
                                <i data-lucide="check-circle" class="w-3.5 h-3.5"></i> Optimal health benchmarks maintained
                            </div>
                        `}
                    </div>

                    <button onclick="selectPatient('${escapeHtml(p.patient_name)}')" class="w-full py-2 bg-slate-50 hover:bg-sky-50 hover:text-sky-700 text-slate-700 font-bold text-xs rounded-xl border border-slate-200 hover:border-sky-300 transition flex items-center justify-center gap-1.5 shadow-sm">
                        <i data-lucide="trending-up" class="w-3.5 h-3.5"></i> View Health Trajectory & Diet
                    </button>
                </div>
            `;
        }).join('');
        lucide.createIcons();
    } else {
        section.classList.add('hidden');
        if (banner) {
            banner.classList.remove('hidden');
            const p = familyPatientsList.find(x => x.patient_name === currentActivePatient) || {
                patient_name: currentActivePatient,
                latest_year: new Date().getFullYear(),
                latest_lab: 'Lab Record',
                total_reports: 1
            };
            const initials = p.patient_name.replace(/^(Mr\.|Mrs\.|Ms\.|Dr\.)\s*/i, '').split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase() || 'P';
            document.getElementById('patient-banner-avatar').textContent = initials;
            document.getElementById('patient-banner-name').textContent = p.patient_name;
            document.getElementById('patient-banner-meta').textContent = `${p.total_reports} checkup record${p.total_reports > 1 ? 's' : ''} • Latest: ${p.latest_year} (${p.latest_lab})`;
        }
    }
}

let currentTrendPatient = '';

function populateTrendPatientDropdown() {
    const select = document.getElementById('trend-patient-select');
    if (!select) return;

    if (familyPatientsList.length === 0) {
        select.innerHTML = '<option value="">No patients</option>';
        return;
    }

    if (!currentTrendPatient || !familyPatientsList.some(p => p.patient_name === currentTrendPatient)) {
        currentTrendPatient = (currentActivePatient && currentActivePatient !== 'ALL')
            ? currentActivePatient
            : familyPatientsList[0].patient_name;
    }

    select.innerHTML = familyPatientsList.map(p => `
        <option value="${escapeHtml(p.patient_name)}" ${p.patient_name === currentTrendPatient ? 'selected' : ''}>
            ${escapeHtml(p.patient_name)} (${p.total_reports} checkup${p.total_reports > 1 ? 's' : ''})
        </option>
    `).join('');
}

async function onTrendPatientChange(selectedPatient) {
    currentTrendPatient = selectedPatient;
    await loadTrendsForPatient(selectedPatient);
}

async function loadTrendsForPatient(patientName) {
    if (!patientName) {
        initTrendChart([], '');
        return;
    }
    try {
        const trendsRes = await fetch(`/api/analytics/trends?patient_name=${encodeURIComponent(patientName)}`);
        const trends = await trendsRes.json();
        initTrendChart(trends, patientName);
    } catch (err) {
        console.error('Error loading trends for patient:', err);
    }
}

async function selectPatient(patientName) {
    currentActivePatient = patientName;
    if (patientName !== 'ALL') {
        currentTrendPatient = patientName;
    }
    renderPatientSelectorPills();
    renderFamilyCards();
    await loadMetricsAndTrendsForActivePatient();
}

async function loadMetricsAndTrendsForActivePatient() {
    const isAll = (!currentActivePatient || currentActivePatient === 'ALL');
    const url = !isAll
        ? `/api/analytics/summary?patient_name=${encodeURIComponent(currentActivePatient)}`
        : '/api/analytics/summary';
    
    const res = await fetch(url);
    const summary = await res.json();
    const activeName = isAll ? 'All Family Members' : stripPatientTitle(currentActivePatient);

    // Update KPI Section Header Badge
    const badge = document.getElementById('kpi-patient-scope-badge');
    if (badge) {
        badge.innerHTML = isAll 
            ? `<i data-lucide="users" class="w-3.5 h-3.5 text-sky-600 inline mr-1"></i> Scope: All Family Members (${summary.total_reports || 0} checkups)`
            : `<i data-lucide="user-check" class="w-3.5 h-3.5 text-sky-600 inline mr-1"></i> Patient: ${escapeHtml(activeName)}`;
    }

    // Top Numbers
    document.getElementById('stat-total-reports').textContent = summary.total_reports || 0;
    document.getElementById('stat-years-tracked').textContent = summary.distinct_years || 0;
    document.getElementById('stat-total-biomarkers').textContent = summary.total_biomarkers || 0;
    document.getElementById('stat-abnormal-findings').textContent = summary.abnormal_findings_count || 0;

    // Subtexts with explicit Patient Attribution
    const dateEl = document.getElementById('stat-latest-date');
    const yearsEl = document.getElementById('stat-years-meta');
    const bioEl = document.getElementById('stat-biomarkers-meta');
    const abEl = document.getElementById('stat-abnormal-meta');

    if (isAll) {
        const breakdown = summary.breakdown || [];
        const reportsBreakdown = breakdown.map(b => `${b.patient_name}: ${b.reports_count}`).join(' • ');
        const flagsBreakdown = breakdown.map(b => `${b.patient_name}: ${b.abnormal_count}`).join(' • ');

        if (dateEl) dateEl.innerHTML = reportsBreakdown ? `<span class="text-slate-500 font-bold">Family:</span> ${escapeHtml(reportsBreakdown)}` : 'No reports yet';
        if (yearsEl) yearsEl.innerHTML = `<span class="text-indigo-600 font-bold">Timeline:</span> ${(summary.years_list || []).join(', ') || 'None'}`;
        if (bioEl) bioEl.innerHTML = `<span class="text-teal-600 font-bold">Monitored:</span> Across all ${breakdown.length} members`;
        if (abEl) abEl.innerHTML = flagsBreakdown ? `<span class="text-rose-600 font-bold">Flags:</span> ${escapeHtml(flagsBreakdown)}` : 'All normal';
    } else {
        if (dateEl) dateEl.innerHTML = `<span class="font-bold text-sky-800">${escapeHtml(activeName)}:</span> Latest ${summary.latest_report_date || 'N/A'}`;
        if (yearsEl) yearsEl.innerHTML = `<span class="font-bold text-indigo-800">${escapeHtml(activeName)}:</span> ${(summary.years_list || []).join(', ')}`;
        if (bioEl) bioEl.innerHTML = `<span class="font-bold text-teal-800">${escapeHtml(activeName)}:</span> ${summary.total_biomarkers} tests monitored`;
        if (abEl) abEl.innerHTML = `<span class="font-bold text-rose-700">${escapeHtml(activeName)}:</span> ${summary.abnormal_findings_count} attention needed`;
    }
    lucide.createIcons();

    // Populate chart patient dropdown & load trends strictly for the target patient
    populateTrendPatientDropdown();

    const trendTarget = (currentActivePatient && currentActivePatient !== 'ALL')
        ? currentActivePatient
        : currentTrendPatient || (familyPatientsList[0] ? familyPatientsList[0].patient_name : '');
    
    currentTrendPatient = trendTarget;
    const trendSelect = document.getElementById('trend-patient-select');
    if (trendSelect && trendTarget) {
        trendSelect.value = trendTarget;
    }

    await loadTrendsForPatient(trendTarget);
}

// -------------------------------------------------------------
// Filters & Reports Archive
// -------------------------------------------------------------

async function loadFilterOptions() {
    try {
        // Load distinct years
        const yearsRes = await fetch('/api/reports/filter/years');
        const years = await yearsRes.json();
        const yearSelect = document.getElementById('filter-year');
        if (yearSelect) {
            yearSelect.innerHTML = '<option value="">All Years</option>';
            years.forEach(y => {
                const opt = document.createElement('option');
                opt.value = y;
                opt.textContent = y;
                yearSelect.appendChild(opt);
            });
        }

        // Load distinct patients
        const patientRes = await fetch('/api/reports/filter/patients');
        const patients = await patientRes.json();
        const patientSelect = document.getElementById('filter-patient');
        if (patientSelect) {
            patientSelect.innerHTML = '<option value="">All Patients</option>';
            patients.forEach(p => {
                const opt = document.createElement('option');
                opt.value = p;
                opt.textContent = p;
                patientSelect.appendChild(opt);
            });
        }
    } catch (err) {
        console.error('Error loading filter options:', err);
    }
}

async function loadReports() {
    const patient = document.getElementById('filter-patient')?.value || '';
    const year = document.getElementById('filter-year')?.value || '';
    const abnormalOnly = document.getElementById('filter-abnormal')?.checked || false;
    const search = document.getElementById('filter-search')?.value || '';

    const params = new URLSearchParams();
    if (patient) params.append('patient_name', patient);
    if (year) params.append('year', year);
    if (abnormalOnly) params.append('abnormal_only', 'true');
    if (search) params.append('search', search);

    const listContainer = document.getElementById('reports-list');
    if (!listContainer) return;
    listContainer.innerHTML = '<div class="p-8 text-center text-slate-400">Loading reports...</div>';

    try {
        const res = await fetch(`/api/reports?${params.toString()}`);
        currentReports = await res.json();

        if (currentReports.length === 0) {
            listContainer.innerHTML = `
                <div class="bg-white rounded-xl border border-dashed border-slate-300 p-12 text-center">
                    <i data-lucide="file-text" class="w-12 h-12 text-slate-400 mx-auto mb-3"></i>
                    <h3 class="text-base font-semibold text-slate-700">No medical reports found</h3>
                    <p class="text-sm text-slate-500 mt-1">Try clearing filters or upload your yearly checkup report.</p>
                    <button onclick="switchTab('upload-section')" class="mt-4 px-4 py-2 bg-sky-600 text-white text-sm font-medium rounded-lg hover:bg-sky-700 transition">
                        Upload Medical Report
                    </button>
                </div>
            `;
            lucide.createIcons();
            return;
        }

        // Group reports by canonical patient name (ignoring titles like Mr./Mrs./Ms./Dr.)
        const byPatient = {};
        const patientDisplayNames = {};

        currentReports.forEach(r => {
            const rawName = r.patient_name || 'Self / Patient';
            const key = getCanonicalPatientKey(rawName);
            const titleFree = stripPatientTitle(rawName);

            if (!byPatient[key]) {
                byPatient[key] = [];
                patientDisplayNames[key] = titleFree;
            } else {
                if (titleFree.length > patientDisplayNames[key].length) {
                    patientDisplayNames[key] = titleFree;
                }
            }
            byPatient[key].push(r);
        });

        let html = '<div class="space-y-8">';
        for (const [key, pReports] of Object.entries(byPatient)) {
            const displayName = patientDisplayNames[key] || key;
            const initials = displayName.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase() || 'P';
            const years = [...new Set(pReports.map(r => r.report_year).filter(Boolean))].sort((a, b) => b - a);

            html += `
                <div class="space-y-3.5">
                    <!-- Patient Group Header (Title-Free) -->
                    <div class="flex items-center justify-between border-b border-slate-200 pb-2.5">
                        <div class="flex items-center gap-3">
                            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-sky-600 to-indigo-700 text-white font-black flex items-center justify-center text-xs shadow-sm">
                                ${initials}
                            </div>
                            <div>
                                <h3 class="text-base font-bold text-slate-900 flex items-center gap-2">
                                    ${escapeHtml(displayName)}
                                    <span class="px-2 py-0.5 rounded-full text-[11px] font-bold bg-sky-50 text-sky-700 border border-sky-200">
                                        ${pReports.length} Report${pReports.length > 1 ? 's' : ''}
                                    </span>
                                </h3>
                                <p class="text-xs text-slate-400">Timeline: ${years.join(', ')}</p>
                            </div>
                        </div>
                    </div>

                    <!-- Patient's Reports Grid (Ordered by Year Descending) -->
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            `;

            pReports.forEach(report => {
                const hasAbnormal = report.abnormal_biomarkers > 0;
                html += `
                    <div class="bg-white rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition p-5 flex flex-col justify-between">
                        <div>
                            <div class="flex items-start justify-between">
                                <div>
                                    <span class="text-xs font-bold uppercase tracking-wider text-sky-600 bg-sky-50 px-2 py-0.5 rounded">
                                        Year ${report.report_year}
                                    </span>
                                    <h3 class="text-base font-bold text-slate-800 mt-1">${escapeHtml(report.patient_name)}</h3>
                                </div>
                                <span class="text-xs text-slate-400">${report.report_date}</span>
                            </div>

                            <p class="text-xs text-slate-500 mt-1 flex items-center gap-1">
                                <i data-lucide="building-2" class="w-3.5 h-3.5"></i>
                                ${escapeHtml(report.hospital_lab_name || 'Diagnostic Center')}
                            </p>

                            <div class="mt-4 pt-4 border-t border-slate-100 flex items-center justify-between text-xs">
                                <span class="text-slate-600 font-medium">
                                    <strong>${report.total_biomarkers}</strong> Tests Monitored
                                </span>
                                ${hasAbnormal ? `
                                    <span class="px-2 py-0.5 rounded-full text-xs font-semibold bg-red-50 text-red-700 border border-red-200">
                                        ${report.abnormal_biomarkers} Attention Needed
                                    </span>
                                ` : `
                                    <span class="px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                                        All Normal
                                    </span>
                                `}
                            </div>
                            <div class="mt-3.5 pt-3 border-t border-slate-100 flex items-center gap-2">
                                <a href="/api/reports/${report.id}/file" target="_blank" class="flex-1 py-2 px-3 bg-sky-600 hover:bg-sky-700 text-white rounded-lg text-xs font-bold flex items-center justify-center gap-2 transition shadow-sm">
                                    <i data-lucide="file-text" class="w-4 h-4"></i> Open Original Document
                                </a>
                                <button onclick="openDocModal(${report.id}, '${escapeHtml(report.patient_name)} - Year ${report.report_year}', '${escapeHtml(report.original_filename || 'Medical_Report.pdf')}')" class="p-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg transition" title="Preview Document Inside App">
                                    <i data-lucide="maximize-2" class="w-4 h-4"></i>
                                </button>
                            </div>
                        </div>

                        <div class="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between gap-2">
                            <button onclick="openDietForReport(${report.id})" class="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition shadow-sm">
                                <i data-lucide="salad" class="w-3.5 h-3.5"></i> Plan Diet
                            </button>
                            <button onclick="deleteReport(${report.id})" class="text-slate-400 hover:text-red-600 p-1.5 rounded-lg transition" title="Delete Report">
                                <i data-lucide="trash-2" class="w-4 h-4"></i>
                            </button>
                        </div>
                    </div>
                `;
            });

            html += `
                    </div>
                </div>
            `;
        }
        html += '</div>';

        listContainer.innerHTML = html;
        lucide.createIcons();
    } catch (err) {
        listContainer.innerHTML = `<div class="p-4 bg-red-50 text-red-700 rounded-lg text-sm">Failed to load reports: ${err.message}</div>`;
    }
}

// -------------------------------------------------------------
// Report Details Modal
// -------------------------------------------------------------

async function viewReportDetail(reportId) {
    try {
        const res = await fetch(`/api/reports/${reportId}`);
        const report = await res.json();

        document.getElementById('modal-patient-name').textContent = report.patient_name;
        document.getElementById('modal-report-meta').textContent = `${report.report_date} (Year ${report.report_year}) • ${report.hospital_lab_name || 'Diagnostic Center'}`;

        const container = document.getElementById('modal-biomarkers-container');
        container.innerHTML = '';

        // Group by category
        const byCategory = {};
        report.biomarkers.forEach(b => {
            if (!byCategory[b.category]) byCategory[b.category] = [];
            byCategory[b.category].push(b);
        });

        for (const [category, markers] of Object.entries(byCategory)) {
            let catHtml = `
                <div class="mb-5">
                    <h4 class="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2 border-b pb-1">${escapeHtml(category)}</h4>
                    <div class="overflow-x-auto">
                        <table class="w-full text-left text-xs border-collapse">
                            <thead>
                                <tr class="text-slate-400 border-b">
                                    <th class="py-2">Test Name</th>
                                    <th class="py-2">Result</th>
                                    <th class="py-2">Ref Range</th>
                                    <th class="py-2">Status</th>
                                </tr>
                            </thead>
                            <tbody>
            `;

            markers.forEach(m => {
                let badgeClass = 'badge-normal';
                if (m.status === 'HIGH') badgeClass = 'badge-high';
                if (m.status === 'LOW') badgeClass = 'badge-low';

                catHtml += `
                    <tr class="border-b border-slate-100 hover:bg-slate-50">
                        <td class="py-2 font-medium text-slate-800">${escapeHtml(m.test_name)}</td>
                        <td class="py-2 font-bold ${m.status !== 'NORMAL' ? 'text-red-600' : 'text-slate-800'}">
                            ${m.result_value} <span class="text-slate-400 font-normal">${escapeHtml(m.unit)}</span>
                        </td>
                        <td class="py-2 text-slate-500">
                            ${m.reference_min !== null ? m.reference_min : '—'} - ${m.reference_max !== null ? m.reference_max : '—'} ${escapeHtml(m.unit)}
                        </td>
                        <td class="py-2">
                            <span class="px-2 py-0.5 rounded text-[10px] font-bold ${badgeClass}">
                                ${m.status}
                            </span>
                        </td>
                    </tr>
                `;
            });

            catHtml += `
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
            container.innerHTML += catHtml;
        }

        document.getElementById('modal-diet-btn').onclick = () => {
            closeReportModal();
            openDietForReport(report.id);
        };

        document.getElementById('report-detail-modal').classList.remove('hidden');
    } catch (err) {
        alert('Could not load report details: ' + err.message);
    }
}

function closeReportModal() {
    document.getElementById('report-detail-modal').classList.add('hidden');
}

async function deleteReport(reportId) {
    if (!confirm('Are you sure you want to delete this medical report from your SQL database?')) return;

    try {
        const res = await fetch(`/api/reports/${reportId}`, { method: 'DELETE' });
        if (res.ok) {
            loadReports();
            loadDashboard();
            loadFilterOptions();
        } else {
            alert('Failed to delete report.');
        }
    } catch (err) {
        alert('Error: ' + err.message);
    }
}

async function resetDatabase() {
    if (!confirm('Are you sure you want to clear ALL data from the database? This will remove all checkup reports and start with a completely empty database.')) return;

    try {
        let res = await fetch('/api/reports/reset-database', { method: 'POST' });
        
        // If the running server doesn't have reset-database yet, delete each report via the DELETE endpoint
        if (!res.ok) {
            const listRes = await fetch('/api/reports');
            const reports = await listRes.json();
            for (const r of reports) {
                await fetch(`/api/reports/${r.id}`, { method: 'DELETE' });
            }
        }

        alert('All records cleared! Your database is now completely empty.');
        loadReports();
        loadDashboard();
        loadFilterOptions();
    } catch (err) {
        alert('Error: ' + err.message);
    }
}

// -------------------------------------------------------------
// Direct Document Upload & In-App Viewer
// -------------------------------------------------------------

let currentExtractedBiomarkers = [];

function updateSelectedFileName(input) {
    if (input.files && input.files.length > 0) {
        const file = input.files[0];
        const sizeMb = (file.size / (1024 * 1024)).toFixed(2);
        
        // 1. Update dropzone label with analyzing spinner
        document.getElementById('selected-file-label').innerHTML = `
            <span class="text-sky-700 font-bold flex items-center justify-center gap-1.5">
                <i data-lucide="file-check" class="w-4 h-4 text-emerald-600"></i>
                ${escapeHtml(file.name)} (${sizeMb} MB)
                <span class="text-[11px] font-normal text-sky-600 animate-pulse ml-2">[Analyzing document...]</span>
            </span>
        `;
        lucide.createIcons();

        // 2. Open PDF directly in the live container using blob URL
        const blobUrl = URL.createObjectURL(file);
        const iframe = document.getElementById('upload-pdf-preview');
        const placeholder = document.getElementById('pdf-preview-placeholder');
        const statusDot = document.getElementById('pdf-status-dot');
        const title = document.getElementById('pdf-container-title');
        const extBtn = document.getElementById('upload-pdf-external-btn');

        if (iframe && placeholder) {
            iframe.src = blobUrl;
            iframe.classList.remove('hidden');
            placeholder.classList.add('hidden');
            
            if (statusDot) {
                statusDot.classList.remove('bg-slate-300');
                statusDot.classList.add('bg-emerald-500');
            }
            if (title) {
                title.textContent = `Viewing: ${file.name}`;
            }
            if (extBtn) {
                extBtn.href = blobUrl;
                extBtn.classList.remove('hidden');
            }
        }

        // 3. Auto-extract biomarkers and generate improvement areas & diet plan
        const formData = new FormData();
        formData.append('file', file);

        fetch('/api/reports/upload', {
            method: 'POST',
            body: formData
        })
        .then(res => {
            if (!res.ok) throw new Error('Extraction failed');
            return res.json();
        })
        .then(data => {
            // Fill metadata
            const nameInput = document.getElementById('direct-patient-name');
            if (nameInput) {
                nameInput.value = data.patient_name || 'Self / Patient';
            }
            const dateInput = document.getElementById('direct-report-date');
            if (dateInput && data.report_date) {
                dateInput.value = data.report_date;
            }
            const yearInput = document.getElementById('direct-report-year');
            if (yearInput && data.report_year) {
                yearInput.value = data.report_year;
            }
            const labInput = document.getElementById('direct-lab-name');
            if (labInput && data.hospital_lab_name) {
                labInput.value = data.hospital_lab_name;
            }

            // Physician Notes / Executive Summary: Update if found, or else clear!
            const notesInput = document.getElementById('direct-notes');
            if (notesInput) {
                notesInput.value = data.physician_notes || '';
            }

            // Store and render extracted biomarkers
            currentExtractedBiomarkers = data.biomarkers || [];
            renderExtractedBiomarkers(currentExtractedBiomarkers);

            // Generate improvement areas and targeted diet
            fetchQuickDietAndImprovements(currentExtractedBiomarkers);

            // Update label
            document.getElementById('selected-file-label').innerHTML = `
                <span class="text-sky-700 font-bold flex items-center justify-center gap-1.5">
                    <i data-lucide="check-circle" class="w-4 h-4 text-emerald-600"></i>
                    ${escapeHtml(file.name)} (${sizeMb} MB)
                    <span class="text-[11px] font-semibold text-emerald-600 ml-2">✓ Extracted ${currentExtractedBiomarkers.length} Tests</span>
                </span>
            `;
            lucide.createIcons();
        })
        .catch(err => {
            console.warn('Extraction fallback:', err);
            document.getElementById('selected-file-label').innerHTML = `
                <span class="text-sky-700 font-bold flex items-center justify-center gap-1.5">
                    <i data-lucide="file-check" class="w-4 h-4 text-emerald-600"></i>
                    ${escapeHtml(file.name)} (${sizeMb} MB)
                </span>
            `;
            lucide.createIcons();
        });
    }
}

function renderExtractedBiomarkers(biomarkers) {
    const container = document.getElementById('extracted-data-container');
    const tbody = document.getElementById('extracted-biomarkers-tbody');
    const countBadge = document.getElementById('extracted-count-badge');
    const abnormalBadge = document.getElementById('extracted-abnormal-badge');

    if (!container || !tbody) return;

    let abnormalCount = 0;
    tbody.innerHTML = '';

    biomarkers.forEach((b, idx) => {
        const isAbnormal = b.status === 'HIGH' || b.status === 'LOW';
        if (isAbnormal) abnormalCount++;

        let statusClass = 'bg-slate-100 text-slate-700 border-slate-200';
        if (b.status === 'HIGH') statusClass = 'bg-rose-50 text-rose-700 border-rose-200';
        if (b.status === 'LOW') statusClass = 'bg-amber-50 text-amber-700 border-amber-200';
        if (b.status === 'NORMAL') statusClass = 'bg-emerald-50 text-emerald-700 border-emerald-200';

        const row = document.createElement('tr');
        row.className = `biomarker-row hover:bg-slate-50 transition ${isAbnormal ? 'bg-amber-50/20' : ''}`;
        row.setAttribute('data-category', b.category || 'General Lab');
        row.innerHTML = `
            <td class="py-2.5 px-3 font-medium text-slate-500">${escapeHtml(b.category)}</td>
            <td class="py-2.5 px-3 font-bold text-slate-800">${escapeHtml(b.test_name)}</td>
            <td class="py-2.5 px-3">
                <input type="number" step="any" value="${b.result_value}" onchange="updateBiomarkerValue(${idx}, this.value)" class="w-20 p-1 border border-slate-200 rounded font-bold text-slate-800 bg-white focus:ring-1 focus:ring-sky-500">
            </td>
            <td class="py-2.5 px-3 text-slate-500">${escapeHtml(b.unit || '')}</td>
            <td class="py-2.5 px-3 text-slate-500">
                ${b.reference_min !== null && b.reference_max !== null 
                    ? `${b.reference_min} - ${b.reference_max}` 
                    : (b.reference_min !== null ? `≥ ${b.reference_min}` : (b.reference_max !== null ? `< ${b.reference_max}` : '—'))}
            </td>
            <td class="py-2.5 px-3">
                <span class="px-2 py-0.5 rounded text-[11px] font-bold border ${statusClass}">
                    ${b.status}
                </span>
            </td>
            <td class="py-2.5 px-3 text-right">
                <button type="button" onclick="removeBiomarkerRow(${idx})" class="text-slate-300 hover:text-red-500 p-1 rounded" title="Remove Test">
                    <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });

    if (countBadge) countBadge.textContent = `${biomarkers.length} Tests`;
    if (abnormalBadge) abnormalBadge.textContent = `${abnormalCount} Attention Needed`;

    container.classList.remove('hidden');
    lucide.createIcons();
}

function filterBiomarkerTable(category) {
    const tabs = document.querySelectorAll('.cat-filter-btn');
    tabs.forEach(tab => {
        if (tab.getAttribute('data-category') === category) {
            tab.className = 'cat-filter-btn px-3 py-1.5 rounded-lg font-semibold bg-sky-600 text-white';
        } else {
            tab.className = 'cat-filter-btn px-3 py-1.5 rounded-lg font-semibold bg-slate-100 text-slate-600 hover:bg-slate-200';
        }
    });

    const rows = document.querySelectorAll('.biomarker-row');
    rows.forEach(row => {
        if (category === 'ALL' || row.getAttribute('data-category') === category) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

function updateBiomarkerValue(idx, val) {
    if (currentExtractedBiomarkers[idx]) {
        currentExtractedBiomarkers[idx].result_value = parseFloat(val) || 0;
        // Re-evaluate status
        const min = currentExtractedBiomarkers[idx].reference_min;
        const max = currentExtractedBiomarkers[idx].reference_max;
        const v = currentExtractedBiomarkers[idx].result_value;
        if (min !== null && v < min) currentExtractedBiomarkers[idx].status = 'LOW';
        else if (max !== null && v > max) currentExtractedBiomarkers[idx].status = 'HIGH';
        else currentExtractedBiomarkers[idx].status = 'NORMAL';

        renderExtractedBiomarkers(currentExtractedBiomarkers);
        fetchQuickDietAndImprovements(currentExtractedBiomarkers);
    }
}

function removeBiomarkerRow(idx) {
    currentExtractedBiomarkers.splice(idx, 1);
    renderExtractedBiomarkers(currentExtractedBiomarkers);
    fetchQuickDietAndImprovements(currentExtractedBiomarkers);
}

function addCustomBiomarkerRow() {
    const newTest = {
        category: 'Custom Lab',
        test_name: prompt('Enter Test Name (e.g. Ferritin, Vitamin B12, LDL):') || 'New Test',
        result_value: parseFloat(prompt('Enter Test Value:') || '0'),
        unit: prompt('Enter Unit (e.g. mg/dL, g/dL, %):') || '',
        reference_min: 0,
        reference_max: 100,
        status: 'NORMAL',
        clinical_summary: ''
    };
    currentExtractedBiomarkers.unshift(newTest);
    renderExtractedBiomarkers(currentExtractedBiomarkers);
    fetchQuickDietAndImprovements(currentExtractedBiomarkers);
}

async function fetchQuickDietAndImprovements(biomarkers) {
    const dietPref = document.getElementById('quick-diet-pref')?.value || 'Non-Vegetarian';
    const cuisinePref = document.getElementById('quick-cuisine-pref')?.value || 'Indian';

    let markersToSend = biomarkers;
    if (!markersToSend || markersToSend.length === 0) {
        markersToSend = [];
        document.querySelectorAll('input[name="condition"]:checked').forEach(cb => {
            const val = cb.value;
            if (val === 'low_hemoglobin') markersToSend.push({ category: 'Complete Blood Count', test_name: 'Hemoglobin', result_value: 9.6, unit: 'g/dL', reference_min: 12.0, reference_max: 15.5, status: 'LOW', clinical_summary: 'Anemia / Low Hemoglobin' });
            if (val === 'high_cholesterol') markersToSend.push({ category: 'Lipid Profile', test_name: 'LDL Cholesterol', result_value: 172.0, unit: 'mg/dL', reference_min: 0.0, reference_max: 130.0, status: 'HIGH', clinical_summary: 'Hyperlipidemia / Elevated LDL' });
            if (val === 'high_sugar') markersToSend.push({ category: 'Blood Sugar / Diabetes', test_name: 'HbA1c', result_value: 5.9, unit: '%', reference_min: 0.0, reference_max: 5.7, status: 'HIGH', clinical_summary: 'Prediabetic Glycated Hemoglobin' });
            if (val === 'low_vit_d') markersToSend.push({ category: 'Thyroid & Vitamins', test_name: 'Vitamin D (25-OH)', result_value: 19.8, unit: 'ng/mL', reference_min: 30.0, reference_max: 80.0, status: 'LOW', clinical_summary: 'Hypovitaminosis D' });
            if (val === 'high_bp') markersToSend.push({ category: 'Vitals', test_name: 'Systolic Blood Pressure', result_value: 135.0, unit: 'mmHg', reference_min: 90.0, reference_max: 120.0, status: 'HIGH', clinical_summary: 'Elevated Blood Pressure' });
            if (val === 'high_uric_acid') markersToSend.push({ category: 'Kidney Function', test_name: 'Uric Acid', result_value: 7.6, unit: 'mg/dL', reference_min: 2.5, reference_max: 6.0, status: 'HIGH', clinical_summary: 'Elevated Uric Acid' });
            if (val === 'elevated_liver') markersToSend.push({ category: 'Liver Function', test_name: 'SGPT (ALT)', result_value: 55.0, unit: 'U/L', reference_min: 10.0, reference_max: 50.0, status: 'HIGH', clinical_summary: 'Elevated Liver Enzymes' });
        });
    }

    try {
        const res = await fetch('/api/diet/preview', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                biomarkers: markersToSend,
                diet_preference: dietPref,
                cuisine_preference: cuisinePref,
                calorie_target: 2000
            })
        });

        if (!res.ok) throw new Error('Diet preview failed');
        const data = await res.json();
        renderQuickDietAndImprovements(data);
    } catch (err) {
        console.error('Quick diet error:', err);
    }
}

function refreshQuickDietPlan() {
    const sched = document.getElementById('quick-daily-schedule');
    if (sched) {
        const dPref = document.getElementById('quick-diet-pref')?.value || 'Diet';
        const cPref = document.getElementById('quick-cuisine-pref')?.value || '';
        sched.innerHTML = `<div class="p-4 text-emerald-700 text-xs font-semibold col-span-2 flex items-center justify-center gap-2 bg-emerald-50/70 rounded-xl border border-emerald-200"><i data-lucide="loader-2" class="w-4 h-4 animate-spin text-emerald-600"></i> Updating meal plan for ${escapeHtml(dPref)} (${escapeHtml(cPref)})...</div>`;
        if (window.lucide) lucide.createIcons();
    }
    fetchQuickDietAndImprovements(currentExtractedBiomarkers);
}

function renderQuickDietAndImprovements(data) {
    const container = document.getElementById('improvement-and-diet-section');
    if (!container) return;

    const findings = data.findings || {};
    const diet = data.diet_plan || {};
    const abnormalList = findings.abnormal_list || [];

    // 1. Improvement Areas List
    const areasList = document.getElementById('improvement-areas-list');
    if (areasList) {
        if (abnormalList.length === 0) {
            areasList.innerHTML = `
                <div class="p-3 bg-white/80 rounded-xl border border-emerald-200 flex items-center gap-2 text-emerald-800 text-xs">
                    <i data-lucide="check-circle" class="w-4 h-4 text-emerald-600"></i>
                    <span>All monitored parameters are within optimal clinical ranges! Focus on general vitality and balanced whole foods.</span>
                </div>
            `;
        } else {
            let html = '';
            abnormalList.forEach(item => {
                let icon = 'alert-circle';
                let flagColor = 'text-rose-700 bg-rose-50 border-rose-200';
                let explanation = 'Requires dietary attention';

                if (item.test_name.includes('Hemoglobin') || item.test_name.includes('MCH') || item.test_name.includes('MCV') || item.test_name.includes('PCV')) {
                    icon = 'droplet';
                    explanation = 'Microcytic anemia indicator. Needs iron-rich foods, Vitamin C pairings, and reduced tannins during meals.';
                } else if (item.test_name.includes('Cholesterol') || item.test_name.includes('LDL') || item.test_name.includes('Triglycerides')) {
                    icon = 'heart-pulse';
                    explanation = 'Lipid particle elevation. Requires high soluble fiber, Omega-3s, plant sterols, and reduced saturated/trans fats.';
                } else if (item.test_name.includes('HbA1c') || item.test_name.includes('Sugar')) {
                    icon = 'activity';
                    explanation = 'Prediabetic glycemic range. Requires complex low-GI millets, sprouted legumes, and reduced simple sugars.';
                } else if (item.test_name.includes('Vitamin D')) {
                    icon = 'sun';
                    explanation = 'Hypovitaminosis D. Essential for bone mineralization, calcium uptake, and immune modulation.';
                } else if (item.test_name.includes('Uric Acid')) {
                    icon = 'shield-alert';
                    explanation = 'Hyperuricemia. Requires generous hydration, low-purine proteins, and alkaline lemon water.';
                }

                html += `
                    <div class="p-3 bg-white/90 rounded-xl border border-amber-200/80 shadow-sm flex items-start gap-2.5">
                        <span class="p-1.5 rounded-lg ${flagColor} shrink-0 mt-0.5">
                            <i data-lucide="${icon}" class="w-3.5 h-3.5"></i>
                        </span>
                        <div class="flex-1 min-w-0">
                            <div class="flex items-center justify-between">
                                <strong class="text-xs font-bold text-slate-800">${escapeHtml(item.test_name)}</strong>
                                <span class="text-[11px] font-bold ${item.status === 'HIGH' ? 'text-rose-600' : 'text-amber-600'}">
                                    ${item.value} ${escapeHtml(item.unit || '')} (${item.status})
                                </span>
                            </div>
                            <p class="text-[11px] text-slate-600 mt-0.5">${explanation}</p>
                        </div>
                    </div>
                `;
            });
            areasList.innerHTML = html;
        }
    }

    // 2. Primary Goals
    const goalsList = document.getElementById('improvement-goals-list');
    if (goalsList) {
        const goals = diet.primary_health_goals || [];
        goalsList.innerHTML = goals.length > 0 
            ? goals.map(g => `<li class="font-medium">${escapeHtml(g)}</li>`).join('')
            : '<li>Maintain metabolic balance and antioxidant defenses</li>';
    }

    // 3. Superfoods to Include
    const includeList = document.getElementById('quick-diet-include');
    if (includeList) {
        const foods = diet.foods_to_prioritize || diet.foods_to_include || [];
        if (foods.length > 0) {
            includeList.innerHTML = foods.slice(0, 5).map(f => {
                const name = f.food || f.item_name || 'Recommended Food';
                const reason = f.rationale || f.reason || '';
                return `
                    <li class="flex items-start gap-1.5">
                        <span class="text-emerald-600 font-bold mt-0.5">✓</span>
                        <div>
                            <strong class="text-slate-800">${escapeHtml(name)}:</strong>
                            <span class="text-slate-500">${escapeHtml(reason)}</span>
                        </div>
                    </li>
                `;
            }).join('');
        } else {
            includeList.innerHTML = '<li class="text-slate-400">Balanced colorful vegetables, complex fiber, and lean protein.</li>';
        }
    }

    // 4. Foods to Avoid
    const avoidList = document.getElementById('quick-diet-avoid');
    if (avoidList) {
        const avoid = diet.foods_to_avoid || [];
        if (avoid.length > 0) {
            avoidList.innerHTML = avoid.slice(0, 5).map(f => {
                const name = f.food || f.item_name || 'Item to Limit';
                const reason = f.rationale || f.reason || '';
                return `
                    <li class="flex items-start gap-1.5">
                        <span class="text-rose-600 font-bold mt-0.5">✕</span>
                        <div>
                            <strong class="text-slate-800">${escapeHtml(name)}:</strong>
                            <span class="text-slate-500">${escapeHtml(reason)}</span>
                        </div>
                    </li>
                `;
            }).join('');
        } else {
            avoidList.innerHTML = '<li class="text-slate-400">Deep-fried foods, refined palm oil, and sugary snacks.</li>';
        }
    }

    // 5. Daily Meal Schedule
    const sched = document.getElementById('quick-daily-schedule');
    if (sched) {
        let dayMeals = [];
        if (diet.weekly_meal_plan && diet.weekly_meal_plan.length > 0 && diet.weekly_meal_plan[0].meals) {
            dayMeals = diet.weekly_meal_plan[0].meals;
        }

        if (dayMeals.length > 0) {
            sched.innerHTML = dayMeals.map(m => {
                const title = m.meal_type ? m.meal_type.split('(')[0].trim() : 'Meal';
                let tagColor = 'bg-sky-50 text-sky-700';
                if (title.toLowerCase().includes('breakfast')) tagColor = 'bg-sky-50 text-sky-700';
                else if (title.toLowerCase().includes('mid-morning')) tagColor = 'bg-amber-50 text-amber-700';
                else if (title.toLowerCase().includes('lunch')) tagColor = 'bg-emerald-50 text-emerald-700';
                else if (title.toLowerCase().includes('snack')) tagColor = 'bg-purple-50 text-purple-700';
                else if (title.toLowerCase().includes('dinner')) tagColor = 'bg-indigo-50 text-indigo-700';

                return `
                    <div class="p-3 bg-slate-50 border border-slate-200 rounded-xl flex flex-col justify-between">
                        <div>
                            <div class="flex items-center justify-between">
                                <span class="text-[10px] font-bold uppercase tracking-wider ${tagColor} px-2 py-0.5 rounded">${escapeHtml(title)}</span>
                                <span class="text-[10px] text-slate-400">${escapeHtml(m.portion_guide || '')}</span>
                            </div>
                            <p class="font-bold text-slate-800 text-xs mt-2">${escapeHtml(m.menu)}</p>
                        </div>
                        ${m.nutrition_focus ? `
                            <p class="text-[10px] text-emerald-700 mt-2 pt-2 border-t border-slate-200/60 flex items-center gap-1 font-medium">
                                <i data-lucide="sparkles" class="w-3 h-3 text-emerald-500"></i> ${escapeHtml(m.nutrition_focus)}
                            </p>
                        ` : ''}
                    </div>
                `;
            }).join('');
        } else {
            sched.innerHTML = '<div class="p-3 text-slate-400 text-xs col-span-2">Select your report or conditions to generate the daily schedule.</div>';
        }
    }

    container.classList.remove('hidden');
    lucide.createIcons();
}

async function handleDirectUpload(e) {
    e.preventDefault();

    const fileInput = document.getElementById('direct-file-input');
    const patientName = document.getElementById('direct-patient-name').value.trim();
    const reportYear = document.getElementById('direct-report-year').value;
    const reportDate = document.getElementById('direct-report-date').value;
    const labName = document.getElementById('direct-lab-name').value.trim();
    const notes = document.getElementById('direct-notes').value.trim();

    if (!patientName || !reportDate) {
        alert('Please specify the patient name and report date.');
        return;
    }

    // Prefer confirmed extracted biomarkers from table, or fall back to checked findings
    let findings = currentExtractedBiomarkers;
    if (!findings || findings.length === 0) {
        findings = [];
        document.querySelectorAll('input[name="condition"]:checked').forEach(cb => {
            const val = cb.value;
            if (val === 'low_hemoglobin') {
                findings.push({ category: 'Complete Blood Count', test_name: 'Hemoglobin', result_value: 9.6, unit: 'g/dL', reference_min: 12.0, reference_max: 15.5, status: 'LOW', clinical_summary: 'Anemia / Low Hemoglobin' });
            } else if (val === 'high_cholesterol') {
                findings.push({ category: 'Lipid Profile', test_name: 'LDL Cholesterol', result_value: 172.0, unit: 'mg/dL', reference_min: 0.0, reference_max: 130.0, status: 'HIGH', clinical_summary: 'Hyperlipidemia / Elevated LDL' });
            } else if (val === 'high_sugar') {
                findings.push({ category: 'Blood Sugar / Diabetes', test_name: 'HbA1c', result_value: 5.9, unit: '%', reference_min: 0.0, reference_max: 5.7, status: 'HIGH', clinical_summary: 'Prediabetic Glycated Hemoglobin' });
            } else if (val === 'low_vit_d') {
                findings.push({ category: 'Thyroid & Vitamins', test_name: 'Vitamin D (25-OH)', result_value: 19.8, unit: 'ng/mL', reference_min: 30.0, reference_max: 80.0, status: 'LOW', clinical_summary: 'Hypovitaminosis D' });
            } else if (val === 'high_bp') {
                findings.push({ category: 'Vitals', test_name: 'Systolic Blood Pressure', result_value: 135.0, unit: 'mmHg', reference_min: 90.0, reference_max: 120.0, status: 'HIGH', clinical_summary: 'Elevated Blood Pressure' });
            } else if (val === 'high_uric_acid') {
                findings.push({ category: 'Kidney Function', test_name: 'Uric Acid', result_value: 7.6, unit: 'mg/dL', reference_min: 2.5, reference_max: 6.0, status: 'HIGH', clinical_summary: 'Elevated Uric Acid' });
            } else if (val === 'elevated_liver') {
                findings.push({ category: 'Liver Function', test_name: 'SGPT (ALT)', result_value: 55.0, unit: 'U/L', reference_min: 10.0, reference_max: 50.0, status: 'HIGH', clinical_summary: 'Elevated Liver Enzymes' });
            }
        });
    }

    const formData = new FormData();
    if (fileInput.files && fileInput.files.length > 0) {
        formData.append('file', fileInput.files[0]);
    }
    formData.append('patient_name', patientName);
    formData.append('report_year', reportYear);
    formData.append('report_date', reportDate);
    formData.append('hospital_lab_name', labName || 'Diagnostic Center');
    formData.append('notes', notes);
    formData.append('findings_json', JSON.stringify(findings));

    try {
        const res = await fetch('/api/reports/direct-upload', {
            method: 'POST',
            body: formData
        });

        if (!res.ok) throw new Error('Failed to upload report');
        const data = await res.json();

        alert(`Medical report successfully archived for ${patientName} (Year ${reportYear}) with ${findings.length} biomarkers!`);
        
        document.getElementById('direct-upload-form').reset();
        document.getElementById('selected-file-label').innerHTML = 'Click to choose your Medical Report (PDF, Word Doc, or Image)';

        loadFilterOptions();
        loadDashboard();
        switchTab('reports-section');
    } catch (err) {
        alert('Upload failed: ' + err.message);
    }
}

function openDocModal(reportId, title, filename) {
    const modal = document.getElementById('doc-viewer-modal');
    const iframe = document.getElementById('doc-modal-iframe');
    const titleEl = document.getElementById('doc-modal-title');
    const subEl = document.getElementById('doc-modal-subtitle');
    const extLink = document.getElementById('doc-modal-external-link');

    const fileUrl = `/api/reports/${reportId}/file`;
    if (titleEl) titleEl.textContent = title;
    if (subEl) subEl.textContent = `Original Document: ${filename || 'Medical Report'}`;
    if (extLink) extLink.href = fileUrl;
    if (iframe) iframe.src = fileUrl;

    modal.classList.remove('hidden');
    lucide.createIcons();
}

function closeDocModal() {
    const modal = document.getElementById('doc-viewer-modal');
    const iframe = document.getElementById('doc-modal-iframe');
    if (iframe) iframe.src = '';
    if (modal) modal.classList.add('hidden');
}

function initUploadZone() {
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('file-input');

    if (!dropzone || !fileInput) return;

    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
    });

    dropzone.addEventListener('dragleave', () => {
        dropzone.classList.remove('dragover');
    });

    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });
}

async function handleFileUpload(file) {
    const spinner = document.getElementById('upload-spinner');
    const reviewSection = document.getElementById('extracted-review-section');
    spinner.classList.remove('hidden');
    reviewSection.classList.add('hidden');

    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch('/api/reports/upload', {
            method: 'POST',
            body: formData
        });

        if (!res.ok) throw new Error('Upload & extraction failed');

        currentExtractedData = await res.json();
        currentExtractedData.original_filename = file.name;

        renderExtractedReview(currentExtractedData);
    } catch (err) {
        alert('Extraction failed: ' + err.message);
    } finally {
        spinner.classList.add('hidden');
    }
}

function renderExtractedReview(data) {
    document.getElementById('edit-patient-name').value = data.patient_name || 'Self / Patient';
    document.getElementById('edit-report-date').value = data.report_date || new Date().toISOString().split('T')[0];
    document.getElementById('edit-report-year').value = data.report_year || new Date().getFullYear();
    document.getElementById('edit-lab-name').value = data.hospital_lab_name || '';

    const tbody = document.getElementById('extracted-biomarkers-table-body');
    tbody.innerHTML = '';

    if (!data.biomarkers || data.biomarkers.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center py-4 text-slate-400">
                    No biomarkers auto-detected. Click "Add Custom Test" below to record values.
                </td>
            </tr>
        `;
    } else {
        data.biomarkers.forEach((b, index) => {
            addBiomarkerRow(b, index);
        });
    }

    document.getElementById('extracted-review-section').classList.remove('hidden');
}

function addBiomarkerRow(b = null, index = null) {
    const tbody = document.getElementById('extracted-biomarkers-table-body');
    const idx = index !== null ? index : tbody.children.length;

    const row = document.createElement('tr');
    row.className = 'border-b border-slate-100 hover:bg-slate-50';
    row.dataset.index = idx;

    const category = b?.category || 'General Lab';
    const testName = b?.test_name || '';
    const val = b?.result_value !== undefined ? b.result_value : '';
    const unit = b?.unit || 'mg/dL';
    const refMin = b?.reference_min !== undefined && b?.reference_min !== null ? b.reference_min : '';
    const refMax = b?.reference_max !== undefined && b?.reference_max !== null ? b.reference_max : '';
    const status = b?.status || 'NORMAL';

    row.innerHTML = `
        <td class="py-2 pr-2">
            <input type="text" class="w-full text-xs p-1.5 border rounded" value="${escapeHtml(category)}" data-field="category">
        </td>
        <td class="py-2 pr-2">
            <input type="text" class="w-full text-xs font-semibold p-1.5 border rounded" value="${escapeHtml(testName)}" data-field="test_name" placeholder="Test Name">
        </td>
        <td class="py-2 pr-2">
            <input type="number" step="any" class="w-20 text-xs font-bold p-1.5 border rounded text-sky-700" value="${val}" data-field="result_value">
        </td>
        <td class="py-2 pr-2">
            <input type="text" class="w-16 text-xs p-1.5 border rounded" value="${escapeHtml(unit)}" data-field="unit">
        </td>
        <td class="py-2 pr-2 flex items-center gap-1">
            <input type="number" step="any" class="w-14 text-xs p-1.5 border rounded text-slate-500" value="${refMin}" data-field="reference_min" placeholder="Min">
            <span class="text-slate-400">-</span>
            <input type="number" step="any" class="w-14 text-xs p-1.5 border rounded text-slate-500" value="${refMax}" data-field="reference_max" placeholder="Max">
        </td>
        <td class="py-2 pr-2">
            <select class="text-xs p-1.5 border rounded font-semibold" data-field="status">
                <option value="NORMAL" ${status === 'NORMAL' ? 'selected' : ''}>NORMAL</option>
                <option value="HIGH" ${status === 'HIGH' ? 'selected' : ''}>HIGH</option>
                <option value="LOW" ${status === 'LOW' ? 'selected' : ''}>LOW</option>
            </select>
        </td>
        <td class="py-2 text-right">
            <button onclick="this.closest('tr').remove()" class="text-slate-400 hover:text-red-600 p-1">
                <i data-lucide="x" class="w-4 h-4"></i>
            </button>
        </td>
    `;
    tbody.appendChild(row);
    lucide.createIcons();
}

async function saveConfirmedReport() {
    const patientName = document.getElementById('edit-patient-name').value.trim();
    const reportDate = document.getElementById('edit-report-date').value;
    const reportYear = parseInt(document.getElementById('edit-report-year').value, 10);
    const labName = document.getElementById('edit-lab-name').value.trim();
    const notes = document.getElementById('edit-notes').value.trim();

    if (!patientName || !reportDate) {
        alert('Please specify patient name and report date');
        return;
    }

    const biomarkerRows = document.querySelectorAll('#extracted-biomarkers-table-body tr');
    const biomarkers = [];

    biomarkerRows.forEach(tr => {
        const testName = tr.querySelector('[data-field="test_name"]')?.value.trim();
        const valStr = tr.querySelector('[data-field="result_value"]')?.value;

        if (testName && valStr !== '') {
            const val = parseFloat(valStr);
            const category = tr.querySelector('[data-field="category"]')?.value.trim() || 'General';
            const unit = tr.querySelector('[data-field="unit"]')?.value.trim() || '';
            const minStr = tr.querySelector('[data-field="reference_min"]')?.value;
            const maxStr = tr.querySelector('[data-field="reference_max"]')?.value;
            const status = tr.querySelector('[data-field="status"]')?.value || 'NORMAL';

            biomarkers.push({
                category: category,
                test_name: testName,
                result_value: val,
                unit: unit,
                reference_min: minStr !== '' ? parseFloat(minStr) : null,
                reference_max: maxStr !== '' ? parseFloat(maxStr) : null,
                status: status,
                clinical_summary: `${testName}: ${val} ${unit} (${status})`
            });
        }
    });

    const payload = {
        patient_name: patientName,
        report_date: reportDate,
        report_year: reportYear,
        hospital_lab_name: labName,
        original_filename: currentExtractedData?.original_filename || 'manual_entry.txt',
        notes: notes,
        biomarkers: biomarkers
    };

    try {
        const res = await fetch('/api/reports', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!res.ok) throw new Error('Failed to save to database');

        const createdReport = await res.json();
        alert(`Report successfully saved into SQL Database (ID: ${createdReport.id})!`);

        // Reset and switch
        document.getElementById('extracted-review-section').classList.add('hidden');
        document.getElementById('file-input').value = '';
        loadFilterOptions();
        loadDashboard();
        switchTab('reports-section');
    } catch (err) {
        alert('Save error: ' + err.message);
    }
}

// -------------------------------------------------------------
// Diet Planner Logic
// -------------------------------------------------------------

async function openFullDietFromQuick() {
    const qDiet = document.getElementById('quick-diet-pref')?.value || 'Non-Vegetarian';
    const qCuisine = document.getElementById('quick-cuisine-pref')?.value || 'Indian';

    switchTab('diet-section');

    const dietSel = document.getElementById('diet-pref-select');
    if (dietSel) dietSel.value = qDiet;

    const cuisineSel = document.getElementById('cuisine-pref-select');
    if (cuisineSel) cuisineSel.value = qCuisine;

    await populateDietReportSelector();
    triggerDietGeneration();
}

function openDietForReport(reportId) {
    switchTab('diet-section');
    populateDietReportSelector(reportId);
    triggerDietGeneration(reportId);
}

async function populateDietReportSelector(selectedId = null) {
    const sel = document.getElementById('diet-report-select');
    if (!sel) return;

    try {
        const res = await fetch('/api/reports');
        currentReports = await res.json();
    } catch (e) {
        currentReports = [];
    }

    sel.innerHTML = '';
    if (currentReports.length === 0) {
        const opt = document.createElement('option');
        opt.value = '';
        opt.textContent = 'Active Report Findings (Interactive Preview)';
        sel.appendChild(opt);
    } else {
        currentReports.forEach(r => {
            const opt = document.createElement('option');
            opt.value = r.id;
            opt.textContent = `${r.patient_name} - Year ${r.report_year} (${r.report_date}) [${r.abnormal_biomarkers} alerts]`;
            if (selectedId && r.id === selectedId) opt.selected = true;
            sel.appendChild(opt);
        });
        if (!selectedId && sel.options.length > 0) {
            sel.selectedIndex = 0;
        }
    }
}

async function triggerDietGeneration(reportId = null) {
    const sel = document.getElementById('diet-report-select');
    if (!reportId && sel && sel.value) {
        reportId = parseInt(sel.value, 10);
    }

    const dietPref = document.getElementById('diet-pref-select')?.value || 'Non-Vegetarian';
    const cuisinePref = document.getElementById('cuisine-pref-select')?.value || 'Indian';

    const resultsContainer = document.getElementById('diet-results');
    resultsContainer.innerHTML = `<div class="p-8 text-center text-slate-500 flex flex-col items-center justify-center gap-2">
        <i data-lucide="loader-2" class="w-7 h-7 animate-spin text-emerald-600"></i>
        <p class="font-semibold text-sm text-slate-700">Synthesizing clinical findings & generating 7-day meal plan...</p>
        <p class="text-xs text-slate-400">Diet: <span class="font-bold text-emerald-700">${escapeHtml(dietPref)}</span> • Cuisine: <span class="font-bold text-emerald-700">${escapeHtml(cuisinePref)}</span></p>
    </div>`;
    if (window.lucide) lucide.createIcons();

    try {
        if (reportId) {
            const res = await fetch('/api/diet/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    report_id: reportId,
                    diet_preference: dietPref,
                    cuisine_preference: cuisinePref
                })
            });

            if (!res.ok) throw new Error('Diet generation failed');
            const plan = await res.json();
            renderDietPlan(plan);
        } else {
            // Live interactive preview using current extracted biomarkers
            let markersToSend = currentExtractedBiomarkers || [];
            if (markersToSend.length === 0) {
                document.querySelectorAll('input[name="condition"]:checked').forEach(cb => {
                    const val = cb.value;
                    if (val === 'low_hemoglobin') markersToSend.push({ category: 'Complete Blood Count', test_name: 'Hemoglobin', result_value: 9.6, unit: 'g/dL', reference_min: 12.0, reference_max: 15.5, status: 'LOW', clinical_summary: 'Anemia / Low Hemoglobin' });
                    if (val === 'high_cholesterol') markersToSend.push({ category: 'Lipid Profile', test_name: 'LDL Cholesterol', result_value: 172.0, unit: 'mg/dL', reference_min: 0.0, reference_max: 130.0, status: 'HIGH', clinical_summary: 'Hyperlipidemia / Elevated LDL' });
                    if (val === 'high_sugar') markersToSend.push({ category: 'Blood Sugar / Diabetes', test_name: 'HbA1c', result_value: 5.9, unit: '%', reference_min: 0.0, reference_max: 5.7, status: 'HIGH', clinical_summary: 'Prediabetic Glycated Hemoglobin' });
                    if (val === 'low_vit_d') markersToSend.push({ category: 'Thyroid & Vitamins', test_name: 'Vitamin D (25-OH)', result_value: 19.8, unit: 'ng/mL', reference_min: 30.0, reference_max: 80.0, status: 'LOW', clinical_summary: 'Hypovitaminosis D' });
                    if (val === 'high_bp') markersToSend.push({ category: 'Vitals', test_name: 'Systolic Blood Pressure', result_value: 135.0, unit: 'mmHg', reference_min: 90.0, reference_max: 120.0, status: 'HIGH', clinical_summary: 'Elevated Blood Pressure' });
                    if (val === 'high_uric_acid') markersToSend.push({ category: 'Kidney Function', test_name: 'Uric Acid', result_value: 7.6, unit: 'mg/dL', reference_min: 2.5, reference_max: 6.0, status: 'HIGH', clinical_summary: 'Elevated Uric Acid' });
                    if (val === 'elevated_liver') markersToSend.push({ category: 'Liver Function', test_name: 'SGPT (ALT)', result_value: 55.0, unit: 'U/L', reference_min: 10.0, reference_max: 50.0, status: 'HIGH', clinical_summary: 'Elevated Liver Enzymes' });
                });
            }

            const res = await fetch('/api/diet/preview', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    biomarkers: markersToSend,
                    diet_preference: dietPref,
                    cuisine_preference: cuisinePref,
                    calorie_target: 2000
                })
            });

            if (!res.ok) throw new Error('Diet preview failed');
            const data = await res.json();
            if (data.diet_plan) {
                renderDietPlan(data.diet_plan);
            } else {
                throw new Error('No diet plan generated');
            }
        }
    } catch (err) {
        resultsContainer.innerHTML = `<div class="p-4 bg-red-50 text-red-700 rounded-lg text-sm">${escapeHtml(err.message)}</div>`;
    }
}

function renderDietPlan(plan) {
    const container = document.getElementById('diet-results');
    if (!container) return;

    let html = `
        <div class="print-card space-y-6">
            <!-- Header Card -->
            <div class="bg-gradient-to-r from-emerald-600 to-teal-700 rounded-xl p-6 text-white shadow">
                <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <span class="text-xs font-bold uppercase tracking-wider bg-white/20 px-2.5 py-1 rounded">
                            ${escapeHtml(plan.diet_preference)} • ${escapeHtml(plan.cuisine_preference)} Cuisine
                        </span>
                        <h2 class="text-2xl font-bold mt-2">Biomarker-Driven Nutrition Protocol</h2>
                        <p class="text-emerald-100 text-sm mt-1">Formulated specifically for <strong>${escapeHtml(plan.patient_name)}</strong></p>
                    </div>
                    <button onclick="window.print()" class="no-print self-start md:self-auto px-4 py-2 bg-white text-emerald-800 rounded-lg font-semibold text-sm hover:bg-emerald-50 transition shadow flex items-center gap-2">
                        <i data-lucide="printer" class="w-4 h-4"></i> Print Diet Sheet
                    </button>
                </div>

                <!-- Primary Health Goals -->
                <div class="mt-5 pt-4 border-t border-white/20">
                    <h4 class="text-xs font-bold uppercase tracking-wider text-emerald-200">Clinical Targeted Objectives</h4>
                    <ul class="mt-2 grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
                        ${plan.primary_health_goals.map(g => `
                            <li class="flex items-start gap-2">
                                <i data-lucide="check-circle-2" class="w-4 h-4 text-emerald-300 mt-0.5 shrink-0"></i>
                                <span>${escapeHtml(g)}</span>
                            </li>
                        `).join('')}
                    </ul>
                </div>
            </div>

            <!-- Foods Matrix: Prioritize vs Avoid -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <!-- Prioritize -->
                <div class="bg-white rounded-xl border border-emerald-200 p-5 shadow-sm">
                    <div class="flex items-center gap-2 text-emerald-700 font-bold text-base mb-3 border-b border-emerald-100 pb-2">
                        <i data-lucide="thumbs-up" class="w-5 h-5"></i>
                        <h3>Foods to Prioritize & Clinical Rationale</h3>
                    </div>
                    <div class="space-y-3">
                        ${plan.foods_to_prioritize.map(item => `
                            <div class="p-3 bg-emerald-50/60 rounded-lg border border-emerald-100">
                                <div class="font-bold text-sm text-emerald-950">${escapeHtml(item.food)}</div>
                                <div class="text-xs text-emerald-800 mt-1">${escapeHtml(item.rationale)}</div>
                                <div class="mt-2 flex flex-wrap gap-1">
                                    ${item.target_markers.map(m => `
                                        <span class="text-[10px] bg-white text-emerald-700 border border-emerald-300 px-1.5 py-0.5 rounded font-medium">
                                            Targets: ${escapeHtml(m)}
                                        </span>
                                    `).join('')}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>

                <!-- Avoid -->
                <div class="bg-white rounded-xl border border-red-200 p-5 shadow-sm">
                    <div class="flex items-center gap-2 text-red-700 font-bold text-base mb-3 border-b border-red-100 pb-2">
                        <i data-lucide="alert-triangle" class="w-5 h-5"></i>
                        <h3>Foods to Limit / Avoid</h3>
                    </div>
                    <div class="space-y-3">
                        ${plan.foods_to_avoid.map(item => `
                            <div class="p-3 bg-red-50/60 rounded-lg border border-red-100">
                                <div class="font-bold text-sm text-red-950">${escapeHtml(item.food)}</div>
                                <div class="text-xs text-red-800 mt-1">${escapeHtml(item.rationale)}</div>
                                <div class="mt-2 flex flex-wrap gap-1">
                                    ${item.target_markers.map(m => `
                                        <span class="text-[10px] bg-white text-red-700 border border-red-300 px-1.5 py-0.5 rounded font-medium">
                                            Avoid due to: ${escapeHtml(m)}
                                        </span>
                                    `).join('')}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>

            <!-- 7-Day Meal Schedule -->
            <div class="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
                <div class="flex items-center justify-between border-b pb-4 mb-4">
                    <div class="flex items-center gap-2">
                        <i data-lucide="calendar" class="w-5 h-5 text-sky-600"></i>
                        <h3 class="text-lg font-bold text-slate-800">7-Day Structured Meal Schedule</h3>
                    </div>
                    <span class="text-xs text-slate-500">Target ~${plan.calorie_target} kcal/day</span>
                </div>

                <div class="space-y-4">
                    ${plan.weekly_meal_plan.map(day => `
                        <div class="border border-slate-200 rounded-lg p-4 bg-slate-50/50">
                            <h4 class="font-bold text-sm text-slate-800 border-b border-slate-200 pb-2 mb-3 flex items-center justify-between">
                                <span>${escapeHtml(day.day)}</span>
                                <span class="text-xs font-normal text-slate-500">5 Meal Structure</span>
                            </h4>
                            <div class="grid grid-cols-1 md:grid-cols-5 gap-3 text-xs">
                                ${day.meals.map(m => `
                                    <div class="bg-white p-3 rounded-lg border border-slate-200 flex flex-col justify-between">
                                        <div>
                                            <div class="font-bold text-sky-700 text-[11px] mb-1">${escapeHtml(m.meal_type)}</div>
                                            <div class="text-slate-800 font-medium">${escapeHtml(m.menu)}</div>
                                        </div>
                                        <div class="mt-2 pt-2 border-t border-slate-100 text-[10px] text-slate-400">
                                            <div><strong>Portion:</strong> ${escapeHtml(m.portion_guide)}</div>
                                            <div class="text-emerald-600 mt-0.5">${escapeHtml(m.nutrition_focus)}</div>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>

            <!-- Lifestyle & Hydration Guidelines -->
            <div class="bg-amber-50 rounded-xl border border-amber-200 p-5 shadow-sm">
                <div class="flex items-center gap-2 text-amber-800 font-bold text-base mb-2">
                    <i data-lucide="activity" class="w-5 h-5"></i>
                    <h3>Physiological & Lifestyle Protocols</h3>
                </div>
                <ul class="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs text-amber-900 mt-3">
                    ${plan.lifestyle_recommendations.map(tip => `
                        <li class="flex items-start gap-2 bg-white/70 p-2.5 rounded border border-amber-200">
                            <i data-lucide="arrow-right-circle" class="w-4 h-4 text-amber-600 mt-0.5 shrink-0"></i>
                            <span>${escapeHtml(tip)}</span>
                        </li>
                    `).join('')}
                </ul>
            </div>
        </div>
    `;

    container.innerHTML = html;
    lucide.createIcons();
}

// -------------------------------------------------------------
// Utilities
// -------------------------------------------------------------

function escapeHtml(text) {
    if (!text) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return String(text).replace(/[&<>"']/g, m => map[m]);
}
