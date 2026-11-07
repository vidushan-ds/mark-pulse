"""O/L prediction: the maths (pure) and saving the results (database)."""

import numpy as np

from models import db, Prediction, utc_now
from services import SUBJECT_NAMES

# the newest exam counts this many times more than the oldest
RECENCY_WEIGHT_RATIO = 2.0
# share of the blend that comes from the trend line
TREND_SHARE = 0.4
# a "typical range" needs at least two exam-to-exam changes
MIN_SCORES_FOR_RANGE = 3


#Keep a mark between 0 and 100, rounded to one decimal.
def clamp_mark(value):
    return round(max(0.0, min(100.0, float(value))), 1)

def _split(points):
    ordered = sorted(points)
    positions = np.array([position for position, _ in ordered], dtype=float)
    scores = np.array([score for _, score in ordered], dtype=float)
    return positions, scores

#[(position, mark), ...] for one subject. Exams without that mark leave a gap.
def subject_points(records, subject):
    return [
        (position, record["marks"][subject])
        for position, record in enumerate(records)
        if record["marks"].get(subject) is not None
    ]
    
#Average where later exams count more. Weight grows with the exam POSITION.
def weighted_average(points, ratio=RECENCY_WEIGHT_RATIO):
    
    positions, scores = _split(points)
    span = positions[-1] - positions[0]
    if span == 0:
        return float(scores.mean())
    weights = 1 + (ratio - 1) * (positions - positions[0]) / span
    return float(np.average(scores, weights=weights))

#Fit a straight line through (position, mark) and read it at next_position.
def linear_trend(points, next_position):
    
    positions, scores = _split(points)
    slope, intercept = np.polyfit(positions, scores, 1)
    return float(slope * next_position + intercept)

#Build a predictor with chosen settings (used to test other settings).
def make_predictor(ratio, trend_share):
    def predictor(points, next_position):
        if not points:
            return None
        if len(points) == 1:
            return clamp_mark(points[0][1])
        blended = (
            (1 - trend_share) * weighted_average(points, ratio)
            + trend_share * linear_trend(points, next_position)
        )
        return clamp_mark(blended)
    return predictor

_production_predictor = make_predictor(RECENCY_WEIGHT_RATIO, TREND_SHARE)


#The estimate the website shows. points = [(position, mark), ...].
def predict_subject(points, next_position=None):

    if not points:
        return None
    if next_position is None:
        next_position = max(position for position, _ in points) + 1
    return _production_predictor(points, next_position)

def estimate_range(points, estimate):   
    if len(points) < MIN_SCORES_FOR_RANGE:
        return None
    _, scores = _split(points)
    swing = float(np.mean(np.abs(np.diff(scores))))
    return clamp_mark(estimate - swing), clamp_mark(estimate + swing)

#Predict every subject that has at least 2 recorded marks.
def generate_predictions(records):
    
    if len(records) < 2:
        return {}


    next_position = len(records)  # the exam that hasn't happened yet
    predictions = {}
 
    for subject in SUBJECT_NAMES:
        points = subject_points(records, subject)
        if len(points) < 2:
            continue
 
        estimate = predict_subject(points, next_position)
        value_range = estimate_range(points, estimate)
 
        predictions[subject] = {
            "score": estimate,
            "low": value_range[0] if value_range else None,
            "high": value_range[1] if value_range else None,
            "n_scores": len(points),
        }

    return predictions


#Insert or update one Prediction row per subject.
def save_predictions(student_id, prediction_data):

    if not prediction_data:
        return
 
    for subject, details in prediction_data.items():
        score = details["score"]
        existing = Prediction.query.filter_by(
            student_id=student_id, subject=subject
        ).first()
 
        if existing:
            existing.predicted_score = score
            existing.created_at = utc_now()
        else:
            db.session.add(
                Prediction(student_id=student_id, subject=subject, predicted_score=score)
            )
 
    db.session.commit()