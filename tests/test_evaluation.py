import pytest

from services.evaluation import (
    backtest_cases,
    build_histories,
    evaluate_methods,
    historical_mean,
    last_score,
    range_coverage,
    sensitivity_grid,
    trend_only,
)

STEADY_CLIMB = [(0, 10), (1, 20), (2, 30), (3, 40)]


def test_each_case_only_sees_exams_before_it():
    
    cases = list(backtest_cases(STEADY_CLIMB, min_history=2))

    assert [(len(earlier), position, actual) for earlier, position, actual in cases] == [
        (2, 2, 30),
        (3, 3, 40),
    ]


def test_methods_are_never_given_the_exam_they_are_predicting():
    
    def spy(points, next_position):
        assert all(position < next_position for position, _ in points)
        return 0

    evaluate_methods([STEADY_CLIMB], {"spy": spy})  


def test_a_perfect_straight_line_is_predicted_perfectly_by_the_trend():
    
    results = evaluate_methods(
        [STEADY_CLIMB],
        {"trend": trend_only, "last": last_score, "mean": historical_mean},
    )

    assert results["trend"]["mae"] == pytest.approx(0.0)
    assert results["last"]["mae"] == pytest.approx(10.0)      
    assert results["mean"]["mae"] > results["last"]["mae"]    


def test_too_little_history_means_no_cases_and_no_mae():
    
    results = evaluate_methods([[(0, 50), (1, 60)]], {"last": last_score}, min_history=2)

    assert results["last"] == {"mae": None, "cases": 0}


def test_histories_keep_the_gaps_left_by_missing_marks():
    
    records = [
        {"marks": {"science": 50}},
        {"marks": {"science": 55}},
        {"marks": {"mathematics": 60}},
        {"marks": {"science": 70}},
    ]
    histories = build_histories([records])

    assert [(0, 50), (1, 55), (3, 70)] in histories


def test_sensitivity_grid_has_one_value_per_setting():
    
    grid = sensitivity_grid([STEADY_CLIMB], ratios=(1.0, 2.0), trend_shares=(0.0, 1.0))

    assert set(grid) == {(1.0, 0.0), (1.0, 1.0), (2.0, 0.0), (2.0, 1.0)}


def test_range_coverage_counts_only_cases_that_have_a_range():
    
    flat = [(0, 60), (1, 60), (2, 60), (3, 60)]   

    result = range_coverage([flat], min_history=3)

    assert result["cases"] == 1
    assert result["coverage"] == 1.0 