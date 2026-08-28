const ctx = document.getElementById("marksChart");

new Chart(ctx,{
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
            label : "Marks",

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
}
)