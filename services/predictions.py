"""O/L prediction: the maths (pure) and saving the results (database)."""
from datetime import datetime

import numpy as np

from models import db, Prediction
from services import SUBJECT_NAMES


#Predict the next mark from a subject's past marks (oldest first).
def predict_subject(scores):

    if not scores:
        return None
    if len(scores) == 1:
        return round(scores[0], 1)

    x = np.arange(len(scores))
    weights = np.linspace(1, 2, len(scores))

    weighted_avg = np.average(scores, weights=weights)

    slope, intercept = np.polyfit(x, scores, 1)
    trend_prediction = slope * len(scores) + intercept

    predicted = 0.6 * weighted_avg + 0.4 * trend_prediction

    return round(max(0, min(100, float(predicted))), 1)

#Predict every subject that has at least 2 recorded marks.
def generate_predictions(records):
    
    if len(records) < 2:
        return {}

    predictions = {}
    for subject in SUBJECT_NAMES:
        scores = [
            r["marks"][subject]
            for r in records
            if r["marks"].get(subject) is not None
        ]
        if len(scores) >= 2:
            predictions[subject] = predict_subject(scores)
    return predictions

#Insert or update one Prediction row per subject.
def save_predictions(student_id, prediction_data):

    if not prediction_data:
        return

    for subject, score in prediction_data.items():
        existing = Prediction.query.filter_by(
            student_id=student_id, subject=subject
        ).first()

        if existing:
            existing.predicted_score = score
            existing.created_at = datetime.utcnow()
        else:
            db.session.add(
                Prediction(student_id=student_id, subject=subject, predicted_score=score)
            )

    db.session.commit()