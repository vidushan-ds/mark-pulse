import pytest

from app import app
from models import db, Student, Prediction
from services.predictions import (
    estimate_range,
    generate_predictions,
    linear_trend,
    predict_subject,
    save_predictions,
    subject_points,
)
from tests.test_csrf import EXAM_DATA, log_in_directly


def record(name, **marks):
    
    return {"exam_name": name, "exam_date": None, "marks": marks}


# ---------- the estimate ----------

def test_single_mark_is_returned_as_it_is():
    
    assert predict_subject([(0, 72.0)]) == 72.0


def test_no_marks_gives_none():
    
    assert predict_subject([]) is None


def test_evenly_spaced_marks_give_the_same_answer_as_before():
    
    assert predict_subject([(0, 50), (1, 60), (2, 70)], 3) == 69.3


def test_estimate_is_kept_between_0_and_100():
    
    assert predict_subject([(0, 60), (1, 80), (2, 100)], 3) <= 100
    assert predict_subject([(0, 40), (1, 20), (2, 0)], 3) >= 0


# ---------- missing exams (the gap problem) ----------

def test_trend_uses_real_exam_positions_not_list_order():

    points = [(0, 50), (1, 55), (4, 70)]
    assert linear_trend(points, 5) == pytest.approx(75.0)


def test_subject_points_leave_a_gap_for_a_missing_mark():
    
    records = [
        record("T1", science=50),
        record("T2", science=55),
        record("T3", mathematics=60),      # no science this time
        record("T4", mathematics=65),
        record("T5", science=70),
    ]
    assert subject_points(records, "science") == [(0, 50), (1, 55), (4, 70)]


def test_next_exam_position_counts_every_exam_not_just_marks_present():
    
    records = [
        record("T1", science=50),
        record("T2", science=55),
        record("T3", mathematics=60),
        record("T4", mathematics=65),
        record("T5", science=70),
    ]
    details = generate_predictions(records)["science"]
    assert details["score"] == predict_subject([(0, 50), (1, 55), (4, 70)], 5)
    assert details["n_scores"] == 3


# ---------- typical range ----------

def test_no_range_with_fewer_than_three_marks():
    
    assert estimate_range([(0, 50), (1, 60)], 70) is None


def test_range_is_estimate_plus_or_minus_typical_change():
    
    assert estimate_range([(0, 50), (1, 60), (2, 50)], 55) == (45.0, 65.0)


def test_range_stays_between_0_and_100():
    
    low, high = estimate_range([(0, 50), (1, 60), (2, 50)], 95)
    assert high == 100.0
    low, high = estimate_range([(0, 50), (1, 60), (2, 50)], 4)
    assert low == 0.0


# ---------- generate_predictions ----------

def test_predictions_need_two_exams():
    
    assert generate_predictions([record("T1", science=50)]) == {}


def test_prediction_details_have_the_expected_shape():
    
    records = [record("T1", science=50), record("T2", science=60)]
    details = generate_predictions(records)["science"]

    assert set(details) == {"score", "low", "high", "n_scores"}
    assert details["low"] is None and details["high"] is None   
    assert details["n_scores"] == 2


# ---------- saving ----------

def test_save_predictions_stores_the_score_and_updates_instead_of_duplicating():
    
    with app.app_context():
        student = Student(name="Ann", email="ann@example.com")
        student.set_password("Str0ng!Pass")
        db.session.add(student)
        db.session.commit()

        save_predictions(student.id, {"science": {"score": 70.0, "low": None, "high": None, "n_scores": 2}})
        save_predictions(student.id, {"science": {"score": 75.0, "low": None, "high": None, "n_scores": 3}})

        rows = Prediction.query.all()
        assert len(rows) == 1
        assert rows[0].predicted_score == 75.0


# ---------- the dashboard ----------

def test_dashboard_shows_estimates_with_a_range_after_three_exams(client):
    
    log_in_directly(client)

    for name, science in [("T1", "50"), ("T2", "60"), ("T3", "55")]:
        client.post("/home", data={**EXAM_DATA, "exam_name": name, "science": science})

    page = client.get("/home").get_data(as_text=True)

    assert "Estimated O/L Performance" in page
    assert "Typical range" in page
    assert "based on 3 exams" in page