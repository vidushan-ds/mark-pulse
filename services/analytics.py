from services import SUBJECT_NAMES

#Exam record table
def build_marks_table(records):
    
    table = []
    for record in records:
        row = {"exam_name": record["exam_name"], "exam_date": record["exam_date"]}
        for subject in SUBJECT_NAMES:
            row[subject] = record["marks"].get(subject)
        table.append(row)
    return table


# Give data do create a line chart
def build_line_chart_data(records, limit=5):
   
    recent = records[-limit:]
    return {
        "line_labels": [r["exam_name"] for r in recent],
        "line_data": {
            subject: [r["marks"].get(subject) for r in recent]
            for subject in SUBJECT_NAMES
        },
    }


#Average mark per subject across all exams
def calculate_subject_averages(records):

    averages = []
    for subject in SUBJECT_NAMES:
        scores = [
            r["marks"][subject]
            for r in records
            if r["marks"].get(subject) is not None
        ]
        averages.append(round(sum(scores) / len(scores), 1) if scores else 0)
    return averages


#Change in each subject between the last two exams.
def calculate_improvement(records):

    if len(records) < 2:
        return {}

    previous = records[-2]["marks"]
    latest = records[-1]["marks"]

    improvement_data = {}
    for subject in SUBJECT_NAMES:
        previous_score = previous.get(subject)
        latest_score = latest.get(subject)

        if previous_score is not None and latest_score is not None:
            improvement_data[subject] = {
                "previous": previous_score,
                "latest": latest_score,
                "improvement": latest_score - previous_score,
            }
    return improvement_data

#Best and weakest subject from the averages list
def find_best_and_weakest(averages):
    
    if not any(score > 0 for score in averages):
        return None

    best_index = averages.index(max(averages))
    weakest_index = averages.index(min(averages))

    return {
        "best_subject": SUBJECT_NAMES[best_index],
        "best_score": averages[best_index],
        "weakest_subject": SUBJECT_NAMES[weakest_index],
        "weakest_score": averages[weakest_index],
    }

#Everything chart.js needs, in one dict.
def build_chart_data(records, averages):

    chart_data = build_line_chart_data(records)
    chart_data["radar_labels"] = SUBJECT_NAMES
    chart_data["radar_data"] = averages
    return chart_data