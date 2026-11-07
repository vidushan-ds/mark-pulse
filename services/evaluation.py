from services import SUBJECT_NAMES
from services.predictions import (
    clamp_mark,
    estimate_range,
    linear_trend,
    make_predictor,
    predict_subject,
    subject_points,
    weighted_average,
)
 
DEFAULT_MIN_HISTORY = 2
MIN_RELIABLE_CASES = 30  
 
 
# --- simple baselines the real method has to beat ---
def last_score(points, next_position):
    return points[-1][1]
 
 
def historical_mean(points, next_position):
    return sum(score for _, score in points) / len(points)
 
 
def recency_weighted_mean(points, next_position):
    return clamp_mark(weighted_average(points))
 
 
def trend_only(points, next_position):
    return clamp_mark(linear_trend(points, next_position))
 
 
METHODS = {
    "last score (baseline)": last_score,
    "average of all exams (baseline)": historical_mean,
    "recency-weighted average": recency_weighted_mean,
    "trend line only": trend_only,
    "current blend (what the site uses)": predict_subject,
}
 
#One [(position, mark), ...] list per student and subject.
def build_histories(records_by_student):

    histories = []
    for records in records_by_student:
        for subject in SUBJECT_NAMES:
            points = subject_points(records, subject)
            if points:
                histories.append(points)
    return histories
 
#Yield (earlier_points, position, actual_mark) for each mark with enough history before it.
def backtest_cases(history, min_history=DEFAULT_MIN_HISTORY):
    
    ordered = sorted(history)
    for i in range(max(min_history, 2), len(ordered)):
        position, actual = ordered[i]
        yield ordered[:i], position, actual
 
#Mean absolute error (MAE) of each method over every backtest case 
def evaluate_methods(histories, methods, min_history=DEFAULT_MIN_HISTORY):

    errors = {name: [] for name in methods}
 
    for history in histories:
        for earlier, position, actual in backtest_cases(history, min_history):
            for name, method in methods.items():
                errors[name].append(abs(method(earlier, position) - actual))
 
    return {
        name: {
            "mae": sum(errs) / len(errs) if errs else None,
            "cases": len(errs),
        }
        for name, errs in errors.items()
    }
 
#MAE for other weight/blend choices
def sensitivity_grid(
    histories,
    ratios=(1.0, 2.0, 4.0),
    trend_shares=(0.0, 0.2, 0.4, 0.6, 1.0),
    min_history=DEFAULT_MIN_HISTORY,
):
    grid = {}
    for ratio in ratios:
        for share in trend_shares:
            result = evaluate_methods(
                histories, {"x": make_predictor(ratio, share)}, min_history
            )
            grid[(ratio, share)] = result["x"]["mae"]
    return grid
 
 #How often did the real mark land inside the range the site would have shown?
def range_coverage(histories, min_history=DEFAULT_MIN_HISTORY):

    inside = total = 0
 
    for history in histories:
        for earlier, position, actual in backtest_cases(history, min_history):
            estimate = predict_subject(earlier, position)
            value_range = estimate_range(earlier, estimate)
            if value_range is None:
                continue
            total += 1
            if value_range[0] <= actual <= value_range[1]:
                inside += 1
 
    return {"cases": total, "coverage": inside / total if total else None}