import sqlite3
import sys
from datetime import datetime

from sqlalchemy.dialects import sqlite as sqlite_dialect
from sqlalchemy.schema import CreateIndex, CreateTable

from app import app, db
from services import SUBJECT_NAMES

TABLES = ["students", "exams", "marks", "predictions"] 

COLUMNS = {
    "students": "id, name, email, password_hash, created_at",
    "exams": "id, student_id, exam_name, exam_date",
    "marks": "id, exam_id, subject, score",
    "predictions": "id, student_id, subject, predicted_score, created_at",
}

SUBJECTS = ", ".join(f"'{subject}'" for subject in SUBJECT_NAMES)


PREFLIGHT = {
    "students with a blank name or email":
        "SELECT id, name, email FROM students WHERE length(trim(name)) = 0 OR length(trim(email)) = 0",
    "students with no created_at":
        "SELECT id, name FROM students WHERE created_at IS NULL",
    "exams with no date":
        "SELECT id, exam_name FROM exams WHERE exam_date IS NULL",
    "marks outside 0-100":
        "SELECT id, exam_id, subject, score FROM marks WHERE score < 0 OR score > 100",
    "marks with an unknown subject":
        f"SELECT id, exam_id, subject FROM marks WHERE subject NOT IN ({SUBJECTS})",
    "duplicate marks (same exam and subject)":
        "SELECT exam_id, subject, COUNT(*) AS copies FROM marks GROUP BY exam_id, subject HAVING COUNT(*) > 1",
    "predictions outside 0-100":
        "SELECT id, student_id, subject, predicted_score FROM predictions WHERE predicted_score < 0 OR predicted_score > 100",
    "predictions with an unknown subject":
        f"SELECT id, student_id, subject FROM predictions WHERE subject NOT IN ({SUBJECTS})",
    "duplicate predictions (same student and subject)":
        "SELECT student_id, subject, COUNT(*) AS copies FROM predictions GROUP BY student_id, subject HAVING COUNT(*) > 1",
    "predictions with no created_at":
        "SELECT id, student_id, subject FROM predictions WHERE created_at IS NULL",
}


def find_problems(conn):
    problems = {}

    for label, sql in PREFLIGHT.items():
        rows = conn.execute(sql).fetchall()
        if rows:
            problems[label] = rows

    orphans = conn.execute("PRAGMA foreign_key_check").fetchall()
    if orphans:
        problems["rows pointing at a parent that no longer exists"] = orphans

    return problems


def already_upgraded(conn):
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'marks'"
    ).fetchone()
    return bool(row) and "ck_marks_score_range" in row[0]


def main():
    with app.app_context():
        db_path = db.engine.url.database
        new_tables = list(db.metadata.sorted_tables)

    if not db_path or db_path == ":memory:":
        sys.exit("This script needs a database file, but the app is using an in-memory database.")

    conn = sqlite3.connect(db_path, isolation_level=None)

    if already_upgraded(conn):
        conn.close()
        print("Already upgraded. Nothing to do.")
        return

    problems = find_problems(conn)
    if problems:
        print("Stopped. These existing rows would break the new rules.")
        print("Nothing was changed. Fix or delete them, then run this again.\n")
        for label, rows in problems.items():
            print(f"- {label}:")
            for row in rows:
                print("    ", tuple(row))
        conn.close()
        sys.exit(1)

    backup_path = f"{db_path}.backup-{datetime.now():%Y%m%d-%H%M%S}"
    backup_conn = sqlite3.connect(backup_path)
    conn.backup(backup_conn)
    backup_conn.close()
    print(f"Backup saved: {backup_path}")

    dialect = sqlite_dialect.dialect()

    conn.execute("PRAGMA foreign_keys=OFF")  
    conn.execute("BEGIN")
    try:
        
        for name in TABLES:
            conn.execute(f"ALTER TABLE {name} RENAME TO {name}_old")

        for table in new_tables:
            conn.execute(str(CreateTable(table).compile(dialect=dialect)))
            for index in table.indexes:
                conn.execute(str(CreateIndex(index).compile(dialect=dialect)))

        for name in TABLES:
            columns = COLUMNS[name]
            conn.execute(f"INSERT INTO {name} ({columns}) SELECT {columns} FROM {name}_old")

        for name in reversed(TABLES):
            conn.execute(f"DROP TABLE {name}_old")

        leftovers = conn.execute("PRAGMA foreign_key_check").fetchall()
        if leftovers:
            raise RuntimeError(f"foreign key problems after copying: {leftovers}")

        conn.execute("COMMIT")
    except Exception as error:
        conn.execute("ROLLBACK")
        conn.close()
        print(f"\nUpgrade failed and was rolled back. Your data is unchanged.\n{error}")
        sys.exit(1)

    print("Upgrade complete. Rows now in each table:")
    for name in TABLES:
        count = conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        print(f"  {name}: {count}")
    conn.close()


if __name__ == "__main__":
    main()