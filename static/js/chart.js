// Bar chart - marks from the exam just submitted
if (result) {
    new Chart(document.getElementById("marksChart"), {
        type: 'bar',
        data: {
            labels: [
                "Science", 
                "Mathematics", 
                "Sinhala", 
                "English",
                "History", 
                "Religion", 
                "Category 1", 
                "Category 2", 
                "Category 3"
            ],
            datasets: [{
                label: "Marks",
                data: [
                    result.science, 
                    result.mathematics, 
                    result.sinhala,
                    result.english, 
                    result.history,
                    result.religion,
                    result.category_1, 
                    result.category_2, 
                    result.category_3
                ]
            }]
        }
    });
}

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

if (chartData && chartData.line_labels && chartData.line_labels.length > 0) {

    // Line chart - last 5 exams, one line per subject
    const colors = [
        "#4f6ef7", 
        "#2e7d32", 
        "#fb8c00", 
        "#e53935", 
        "#8e24aa",
        "#00897b", 
        "#f9a825", 
        "#5d4037", 
        "#3949ab"
    ];

    const lineDatasets = Object.keys(chartData.line_data).map((subject, i) => ({
        label: subjectLabels[subject],
        data: chartData.line_data[subject],
        borderColor: colors[i % colors.length],
        backgroundColor: colors[i % colors.length],
        fill: false,
        tension: 0.3,
        spanGaps: true
    }));

    new Chart(document.getElementById("lineChart"), {
        type: 'line',
        data: {
            labels: chartData.line_labels,
            datasets: lineDatasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { title: { display: true, text: "Marks Trend — Last 5 Exams" } },
            scales: { y: { min: 0, max: 100 } }
        }
    });

    // Radar chart - average performance per subject, across all exams
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