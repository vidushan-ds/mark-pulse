import argparse
import csv
from collections import defaultdict
 
from services.evaluation import (
    DEFAULT_MIN_HISTORY,
    METHODS,
    MIN_RELIABLE_CASES,
    build_histories,
    evaluate_methods,
    range_coverage,
    sensitivity_grid,
)
 
 
def load_from_database():
    from app import app
    from models import Student
    from services.exams import get_exam_records
 
    with app.app_context():
        return [get_exam_records(student.id) for student in Student.query.all()]
 
 
def load_from_csv(path):
    students = defaultdict(lambda: defaultdict(dict))
 
    with open(path, newline="") as file:
        for row in csv.DictReader(file):
            students[row["student"]][int(row["exam_order"])][row["subject"]] = float(row["score"])
 
    records_by_student = []
    for exams in students.values():
        # every exam number between the first and last gets a record, so a missed exam stays a gap
        records = [
            {"exam_name": str(order), "exam_date": None, "marks": exams.get(order, {})}
            for order in range(min(exams), max(exams) + 1)
        ]
        records_by_student.append(records)
    return records_by_student
 
 
def main():
    parser = argparse.ArgumentParser(description="Evaluate the prediction method on past exams.")
    parser.add_argument("--csv", help="read marks from this CSV instead of the database")
    parser.add_argument("--min-history", type=int, default=DEFAULT_MIN_HISTORY,
                        help="earlier marks needed before a prediction is tested (default 2)")
    args = parser.parse_args()
 
    records_by_student = load_from_csv(args.csv) if args.csv else load_from_database()
    histories = build_histories(records_by_student)
 
    results = evaluate_methods(histories, METHODS, args.min_history)
    cases = next(iter(results.values()))["cases"]
 
    print(f"\nStudents: {len(records_by_student)}   "
          f"Test cases: {cases}   (a case = one real mark predicted from the marks before it)")
 
    if cases == 0:
        print("\nNot enough history yet. A student needs more than "
              f"{args.min_history} marks in a subject before anything can be tested.")
        return
 
    if cases < MIN_RELIABLE_CASES:
        print(f"\n!! Only {cases} test cases (rule of thumb: at least {MIN_RELIABLE_CASES}).")
        print("!! Treat everything below as anecdotes, not evidence.")
 
    baseline = results["last score (baseline)"]["mae"]
 
    print("\n1. Average miss (MAE, in marks). Lower is better.")
    print(f"   {'method':<38}{'MAE':>7}{'vs last score':>16}")
    for name, result in sorted(results.items(), key=lambda item: item[1]["mae"]):
        change = (baseline - result["mae"]) / baseline * 100 if baseline else 0.0
        print(f"   {name:<38}{result['mae']:>7.2f}{change:>+15.1f}%")
    print("   (+ means closer to the real marks than just repeating the last score)")
 
    print("\n2. Does the 60/40 choice matter? MAE for other settings.")
    shares = (0.0, 0.2, 0.4, 0.6, 1.0)
    grid = sensitivity_grid(histories, trend_shares=shares, min_history=args.min_history)
    print("   newest-exam weight \\ trend share " + "".join(f"{share:>7.0%}" for share in shares))
    for ratio in (1.0, 2.0, 4.0):
        print(f"   {ratio:>5.0f}x" + " " * 28 + "".join(f"{grid[(ratio, share)]:>7.2f}" for share in shares))
    print("   If every number is about the same, the exact weights don't matter.")
 
    coverage = range_coverage(histories, args.min_history)
    print("\n3. The 'typical range' shown next to each estimate.")
    if coverage["cases"]:
        print(f"   Real mark landed inside it {coverage['coverage']:.0%} of the time "
              f"({coverage['cases']} cases).")
        print("   It is a rough guide, not a 95% interval.")
    else:
        print("   Not enough history to test it (needs 3+ earlier marks).")
 
 
if __name__ == "__main__":
    main()