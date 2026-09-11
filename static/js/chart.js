const subjectLabels = {
    science: "Science",
    mathematics: "Mathematics",
    sinhala: "Sinhala",
    english: "English",
    history: "History",
    religion: "Religion",
    category_1: "Category 1",
    category_2: "Category 2",
    category_3: "Category 3"
};

let lineChart = null;

if (chartData && chartData.line_labels && chartData.line_labels.length > 0) {

    const colors = [
        "#4f6ef7", "#2e7d32", "#fb8c00", "#e53935", "#8e24aa",
        "#00897b", "#f9a825", "#5d4037", "#3949ab"
    ];

    const lineDatasets = Object.keys(chartData.line_data).map((subject, i) => ({
        label: subjectLabels[subject],
        subjectKey: subject,
        data: chartData.line_data[subject],
        borderColor: colors[i % colors.length],
        backgroundColor: colors[i % colors.length],
        fill: false,
        tension: 0.3,
        spanGaps: true
    }));

    lineChart = new Chart(document.getElementById("lineChart"), {
        type: 'line',
        data: {
            labels: chartData.line_labels,
            datasets: lineDatasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: { display: true, text: "Marks Trend — Last 5 Exams" },
                legend: { display: false }
            },
            scales: { y: { min: 0, max: 100 } }
        }
    });

    // Radar chart stays exactly as before
    new Chart(document.getElementById("radarChart"), {
        type: 'radar',
        data: {
            labels: chartData.radar_labels.map(s => subjectLabels[s]),
            datasets: [{
                label: "Average Marks",
                data: chartData.radar_data,
                backgroundColor: "rgba(79, 110, 247, 0.2)",
                borderColor: "#4f6ef7",
                pointBackgroundColor: "#4f6ef7"
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { title: { display: true, text: "Overall Performance by Subject" } },
            scales: { r: { min: 0, max: 100 } }
        }
    });
}

// --- Subject filter checkbox logic ---
const subjectCheckboxes = document.querySelectorAll(".subject-checkbox");
const showAllCheckbox = document.getElementById("showAllSubjects");

function updateLineChartVisibility() {
    if (!lineChart) return;

    const checkedSubjects = Array.from(subjectCheckboxes)
        .filter(cb => cb.checked)
        .map(cb => cb.value);

    lineChart.data.datasets.forEach(dataset => {
        dataset.hidden = !checkedSubjects.includes(dataset.subjectKey);
    });

    lineChart.update();
}

subjectCheckboxes.forEach(checkbox => {
    checkbox.addEventListener("change", () => {
        const allChecked = Array.from(subjectCheckboxes).every(cb => cb.checked);
        showAllCheckbox.checked = allChecked;
        updateLineChartVisibility();
    });
});

if (showAllCheckbox) {
    showAllCheckbox.addEventListener("change", () => {
        subjectCheckboxes.forEach(cb => {
            cb.checked = showAllCheckbox.checked;
        });
        updateLineChartVisibility();
    });
}