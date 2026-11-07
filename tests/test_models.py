import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app import app
from models import db, Student, Exam, Marks, Prediction


@pytest.fixture
def ctx():
    with app.app_context():
        yield


def add_student(email="ann@example.com", name="Ann"):
    student = Student(name=name, email=email)
    student.set_password("Str0ng!Pass")
    db.session.add(student)
    db.session.commit()
    return student.id


def add_exam(student_id, name="Term 1"):
    exam = Exam(student_id=student_id, exam_name=name)
    db.session.add(exam)
    db.session.commit()
    return exam.id


def assert_rejected(row):
    """Saving this row must make the database say no."""
    db.session.add(row)
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


# marks 

def test_mark_above_100_is_rejected(ctx):
    exam_id = add_exam(add_student())
    assert_rejected(Marks(exam_id=exam_id, subject="science", score=100.5))


def test_negative_mark_is_rejected(ctx):
    exam_id = add_exam(add_student())
    assert_rejected(Marks(exam_id=exam_id, subject="science", score=-1))


def test_marks_of_exactly_0_and_100_are_allowed(ctx):
    exam_id = add_exam(add_student())
    db.session.add_all([
        Marks(exam_id=exam_id, subject="science", score=0),
        Marks(exam_id=exam_id, subject="mathematics", score=100),
    ])
    db.session.commit()
    assert Marks.query.count() == 2


def test_unknown_subject_is_rejected(ctx):
    exam_id = add_exam(add_student())
    assert_rejected(Marks(exam_id=exam_id, subject="astrology", score=50))


def test_same_subject_twice_in_one_exam_is_rejected(ctx):
    exam_id = add_exam(add_student())
    db.session.add(Marks(exam_id=exam_id, subject="science", score=50))
    db.session.commit()
    assert_rejected(Marks(exam_id=exam_id, subject="science", score=60))


def test_same_subject_in_different_exams_is_allowed(ctx):
    student_id = add_student()
    first, second = add_exam(student_id, "Term 1"), add_exam(student_id, "Term 2")
    db.session.add_all([
        Marks(exam_id=first, subject="science", score=50),
        Marks(exam_id=second, subject="science", score=60),
    ])
    db.session.commit()
    assert Marks.query.count() == 2


# predictions 

def test_one_prediction_per_student_and_subject(ctx):
    student_id = add_student()
    db.session.add(Prediction(student_id=student_id, subject="science", predicted_score=70))
    db.session.commit()
    assert_rejected(Prediction(student_id=student_id, subject="science", predicted_score=75))


def test_prediction_outside_0_to_100_is_rejected(ctx):
    student_id = add_student()
    assert_rejected(Prediction(student_id=student_id, subject="science", predicted_score=101))


def test_prediction_for_unknown_subject_is_rejected(ctx):
    student_id = add_student()
    assert_rejected(Prediction(student_id=student_id, subject="astrology", predicted_score=50))


# students 

def test_blank_student_name_is_rejected(ctx):
    student = Student(name="   ", email="blank@example.com")
    student.set_password("Str0ng!Pass")
    assert_rejected(student)


def test_duplicate_email_is_rejected(ctx):
    add_student(email="same@example.com")
    student = Student(name="Bob", email="same@example.com")
    student.set_password("Str0ng!Pass")
    assert_rejected(student)


# foreign keys 

def test_exam_for_a_missing_student_is_rejected(ctx):
    assert_rejected(Exam(student_id=999, exam_name="Ghost exam"))


def test_mark_for_a_missing_exam_is_rejected(ctx):
    assert_rejected(Marks(exam_id=999, subject="science", score=50))


def test_exam_date_cannot_be_null(ctx):
    student_id = add_student()
    with pytest.raises(IntegrityError):
        db.session.execute(
            text("INSERT INTO exams (student_id, exam_name, exam_date) VALUES (:s, 'x', NULL)"),
            {"s": student_id},
        )
    db.session.rollback()


def test_database_deletes_a_students_data_with_them(ctx):
    student_id = add_student()
    exam_id = add_exam(student_id)
    db.session.add_all([
        Marks(exam_id=exam_id, subject="science", score=50),
        Prediction(student_id=student_id, subject="science", predicted_score=55),
    ])
    db.session.commit()

    db.session.execute(text("DELETE FROM students WHERE id = :id"), {"id": student_id})
    db.session.commit()

    assert Exam.query.count() == 0
    assert Marks.query.count() == 0
    assert Prediction.query.count() == 0