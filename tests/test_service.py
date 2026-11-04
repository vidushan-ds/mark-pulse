from services.grades import grade_calculator
from services.analytics import (
    calculate_improvement,
    calculate_subject_averages,
    find_best_and_weakest,
)
from services.predictions import predict_subject, generate_predictions


def record(name, **marks):
    return {"exam_name": name, "exam_date": None, "marks": marks}


def test_grade_calculator_counts_each_band():
    assert grade_calculator([80, 70, 60, 40, 10]) == [1, 1, 1, 1, 1]


def test_grade_calculator_skips_blank_marks():
    assert grade_calculator([80, None]) == [1, 0, 0, 0, 0]


def test_improvement_needs_two_exams():
    assert calculate_improvement([record("T1", science=50)]) == {}


def test_improvement_is_latest_minus_previous():
    records = [record("T1", science=50), record("T2", science=65)]
    assert calculate_improvement(records)["science"]["improvement"] == 15


def test_averages_ignore_missing_subjects():
    records = [record("T1", science=50), record("T2", science=70)]
    averages = calculate_subject_averages(records)
    assert averages[0] == 60.0   # science
    assert averages[1] == 0      # mathematics: no data


def test_best_and_weakest_returns_none_without_data():
    assert find_best_and_weakest([0] * 9) is None


def test_predict_single_score_returns_it():
    assert predict_subject([72.0]) == 72.0


def test_predict_rising_trend_is_above_the_average():
    assert predict_subject([50, 60, 70]) == 69.3


def test_predictions_need_two_exams():
    assert generate_predictions([record("T1", science=50)]) == {}