import sqlite3
from datetime import datetime, date, timezone

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, UniqueConstraint, event
from sqlalchemy.engine import Engine
from werkzeug.security import generate_password_hash, check_password_hash

from services import SUBJECT_NAMES

db = SQLAlchemy()


def utc_now():
    return datetime.now(timezone.utc)

SUBJECT_LIST_SQL = ", ".join(f"'{subject}'" for subject in SUBJECT_NAMES)


@event.listens_for(Engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    """SQLite ignores foreign keys unless you switch them on for every connection."""
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


class Student(db.Model):
    __tablename__ = "students"
    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="ck_students_name_not_blank"),
        CheckConstraint("length(trim(email)) > 0", name="ck_students_email_not_blank"),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    exams = db.relationship("Exam", backref="student", cascade="all, delete-orphan")
    predictions = db.relationship("Prediction", backref="student", cascade="all, delete-orphan")

    def set_password(self, raw_password: str):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str):
        return check_password_hash(self.password_hash, raw_password)

    def __repr__(self):
        return f"<Student {self.id} {self.name}>"


class Exam(db.Model):
    __tablename__ = "exams"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer,
        db.ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    exam_name = db.Column(db.String(100), nullable=False)
    exam_date = db.Column(db.Date, default=date.today, nullable=False)

    marks = db.relationship("Marks", backref="exam", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Exam {self.id} {self.exam_name}>"


class Marks(db.Model):
    __tablename__ = "marks"
    __table_args__ = (
        UniqueConstraint("exam_id", "subject", name="uq_marks_exam_subject"),
        CheckConstraint("score >= 0 AND score <= 100", name="ck_marks_score_range"),
        CheckConstraint(f"subject IN ({SUBJECT_LIST_SQL})", name="ck_marks_subject_valid"),
    )

    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(
        db.Integer,
        db.ForeignKey("exams.id", ondelete="CASCADE"),
        nullable=False,
    )
    subject = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<Marks {self.subject}={self.score}>"


class Prediction(db.Model):
    __tablename__ = "predictions"
    __table_args__ = (
        UniqueConstraint("student_id", "subject", name="uq_predictions_student_subject"),
        CheckConstraint("predicted_score >= 0 AND predicted_score <= 100", name="ck_predictions_score_range"),
        CheckConstraint(f"subject IN ({SUBJECT_LIST_SQL})", name="ck_predictions_subject_valid"),
    )

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer,
        db.ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
    )
    subject = db.Column(db.String(50), nullable=False)
    predicted_score = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Prediction {self.subject}={self.predicted_score}>"