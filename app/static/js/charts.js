// Chart.js helper for multi-year biomarker trends

let trendChartInstance = null;
let allTrendsData = [];
let currentTrendPatientName = '';

function initTrendChart(trends, activePatientName) {
    allTrendsData = trends || [];
    currentTrendPatientName = activePatientName || currentTrendPatientName || '';
    const metricSelect = document.getElementById('trend-metric-select');
    
    if (!metricSelect) return;

    // Populate metric dropdown
    metricSelect.innerHTML = '';
    
    if (allTrendsData.length === 0) {
        metricSelect.innerHTML = '<option value="">No biomarker trend data yet</option>';
        const trendNote = document.getElementById('trend-metric-note');
        if (trendNote) trendNote.innerHTML = '<span class="text-slate-400">Upload your checkup reports in the "Upload Report" tab to track biomarker trends here.</span>';
        if (trendChartInstance) {
            trendChartInstance.destroy();
            trendChartInstance = null;
        }
        return;
    }

    // Sort by common metrics first
    const preferredOrder = ["Total Cholesterol", "LDL Cholesterol", "HbA1c", "Fasting Blood Sugar", "Triglycerides", "Serum Creatinine", "Hemoglobin", "Systolic Blood Pressure"];
    allTrendsData.sort((a, b) => {
        const idxA = preferredOrder.indexOf(a.test_name);
        const idxB = preferredOrder.indexOf(b.test_name);
        if (idxA !== -1 && idxB !== -1) return idxA - idxB;
        if (idxA !== -1) return -1;
        if (idxB !== -1) return 1;
        return a.test_name.localeCompare(b.test_name);
    });

    allTrendsData.forEach((series, idx) => {
        const opt = document.createElement('option');
        opt.value = series.test_name;
        opt.textContent = `${series.test_name} (${series.category}) [${series.points.length} record${series.points.length > 1 ? 's' : ''}]`;
        if (idx === 0) opt.selected = true;
        metricSelect.appendChild(opt);
    });

    metricSelect.onchange = () => {
        renderSelectedMetric(metricSelect.value);
    };

    if (allTrendsData.length > 0) {
        renderSelectedMetric(allTrendsData[0].test_name);
    }
}

function renderSelectedMetric(testName) {
    const series = allTrendsData.find(s => s.test_name === testName);
    const canvas = document.getElementById('trendChart');
    if (!canvas || !series) return;

    const ctx = canvas.getContext('2d');

    // Sort points chronologically
    const points = [...series.points].sort((a, b) => new Date(a.date) - new Date(b.date));

    const labels = points.map(p => `${p.year} (${p.date.split('-').slice(1).join('/')})`);
    const values = points.map(p => p.value);
    const pointBackgroundColors = points.map(p => {
        if (p.status === 'HIGH') return '#ef4444';
        if (p.status === 'LOW') return '#3b82f6';
        return '#10b981';
    });

    // Destroy prior chart
    if (trendChartInstance) {
        trendChartInstance.destroy();
    }

    // Reference annotations
    const datasets = [
        {
            label: `${series.test_name} (${series.unit})`,
            data: values,
            borderColor: '#0284c7',
            backgroundColor: 'rgba(2, 132, 199, 0.08)',
            borderWidth: 2.5,
            fill: true,
            tension: 0.25,
            pointBackgroundColor: pointBackgroundColors,
            pointBorderColor: '#ffffff',
            pointBorderWidth: 2,
            pointRadius: 6,
            pointHoverRadius: 8
        }
    ];

    // Add reference threshold guide lines if present
    if (series.reference_max !== null && series.reference_max !== undefined) {
        datasets.push({
            label: `Max Normal Limit (${series.reference_max} ${series.unit})`,
            data: Array(labels.length).fill(series.reference_max),
            borderColor: '#f87171',
            borderWidth: 1.5,
            borderDash: [6, 4],
            pointRadius: 0,
            fill: false
        });
    }

    if (series.reference_min !== null && series.reference_min !== undefined) {
        datasets.push({
            label: `Min Normal Limit (${series.reference_min} ${series.unit})`,
            data: Array(labels.length).fill(series.reference_min),
            borderColor: '#93c5fd',
            borderWidth: 1.5,
            borderDash: [6, 4],
            pointRadius: 0,
            fill: false
        });
    }

    trendChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        boxWidth: 14,
                        font: { family: 'Inter', size: 12 }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            if (context.datasetIndex === 0) {
                                const pt = points[context.dataIndex];
                                const testLabel = (pt.test_name && pt.test_name !== series.test_name) ? ` (${pt.test_name})` : '';
                                return `${context.dataset.label}: ${context.parsed.y} ${series.unit}${testLabel}`;
                            }
                            return context.dataset.label;
                        },
                        afterLabel: function(context) {
                            if (context.datasetIndex === 0) {
                                const pt = points[context.dataIndex];
                                return `Status: ${pt.status} | Normal Ref: ${series.reference_min ?? 'N/A'} - ${series.reference_max ?? 'N/A'} ${series.unit}`;
                            }
                            return null;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    grid: { color: '#f1f5f9' },
                    title: {
                        display: true,
                        text: `${series.test_name} (${series.unit})`,
                        font: { family: 'Inter', size: 12, weight: 'bold' }
                    }
                },
                x: {
                    grid: { color: '#f8fafc' },
                    title: {
                        display: true,
                        text: 'Year of Checkup',
                        font: { family: 'Inter', size: 12 }
                    }
                }
            }
        }
    });

    // Update status note in UI
    const latestPoint = points[points.length - 1];
    const trendNote = document.getElementById('trend-metric-note');
    if (trendNote && latestPoint) {
        let badgeClass = latestPoint.status === 'HIGH' ? 'text-red-600 bg-red-50 border-red-200' : 
                         latestPoint.status === 'LOW' ? 'text-blue-600 bg-blue-50 border-blue-200' : 'text-emerald-700 bg-emerald-50 border-emerald-200';
        let patientBadge = currentTrendPatientName ? `<span class="px-2 py-0.5 rounded text-xs font-bold bg-sky-100 text-sky-800 border border-sky-200 mr-2">Patient: ${escapeHtml(currentTrendPatientName)}</span>` : '';
        let testSub = (latestPoint.test_name && latestPoint.test_name !== series.test_name) ? ` <span class="text-xs font-normal text-slate-500">(${escapeHtml(latestPoint.test_name)})</span>` : '';
        trendNote.innerHTML = `
            ${patientBadge}
            Latest reading: <strong>${latestPoint.value} ${series.unit}</strong> in ${latestPoint.year}${testSub} 
            <span class="px-2 py-0.5 rounded text-xs font-semibold ml-2 border ${badgeClass}">${latestPoint.status}</span>
            <span class="text-slate-400 ml-2">(Normal Ref: ${series.reference_min ?? '—'} - ${series.reference_max ?? '—'} ${series.unit})</span>
        `;
    }
}
