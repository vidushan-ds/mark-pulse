import re

import pytest

from app import app
from models import db, Student, Exam

EXAM_DATA = {
    "exam_name": "Term 1",
    "science": "70", "math": "65", "sinhala": "80", "english": "75",
    "history": "60", "religion": "90", "category_1": "55",
    "category_2": "45", "category_3": "85",
}


@pytest.fixture
def csrf_on():
    
    app.config["WTF_CSRF_ENABLED"] = True
    yield
    app.config["WTF_CSRF_ENABLED"] = False

#Create a student and put them in the session, skipping the login form.
def log_in_directly(client, email="ann@example.com"):
    
    with app.app_context():
        student = Student(name="Ann", email=email)
        student.set_password("Str0ng!Pass")
        db.session.add(student)
        db.session.commit()
        student_id = student.id

    with client.session_transaction() as sess:
        sess["student_id"] = student_id
        sess["name"] = "Ann"

#Load the dashboard and read the token out of the form, like a browser would.
def get_token(client):

    page = client.get("/home")
    match = re.search(r'name="csrf_token" value="([^"]+)"', page.get_data(as_text=True))
    assert match, "dashboard form has no csrf_token field"
    return match.group(1)


def exam_count():
    with app.app_context():
        return Exam.query.count()


def test_dashboard_form_contains_a_csrf_token(client, csrf_on):
    log_in_directly(client)
    assert get_token(client)


def test_dashboard_post_without_token_is_rejected(client, csrf_on):
    log_in_directly(client)

    response = client.post("/home", data=EXAM_DATA)

    assert response.status_code == 400
    assert exam_count() == 0


def test_dashboard_post_with_forged_token_is_rejected(client, csrf_on):
    log_in_directly(client)
    get_token(client)  

    response = client.post("/home", data={**EXAM_DATA, "csrf_token": "forged-token"})

    assert response.status_code == 400
    assert exam_count() == 0


def test_dashboard_post_with_valid_token_saves_the_exam(client, csrf_on):
    log_in_directly(client)
    token = get_token(client)

    response = client.post("/home", data={**EXAM_DATA, "csrf_token": token})

    assert response.status_code == 200
    assert exam_count() == 1

# The attacker has a perfectly valid token, but for THEIR session, not the victim's.
def test_token_from_another_session_is_rejected(client, csrf_on):
    
    log_in_directly(client, email="victim@example.com")
    get_token(client)

    attacker = app.test_client()
    log_in_directly(attacker, email="attacker@example.com")
    attackers_token = get_token(attacker)

    response = client.post("/home", data={**EXAM_DATA, "csrf_token": attackers_token})

    assert response.status_code == 400
    assert exam_count() == 0


def test_login_post_without_token_is_rejected(client, csrf_on):
    response = client.post("/login", data={
        "name": "Ann", "email": "ann@example.com", "password": "Str0ng!Pass",
    })

    assert response.status_code == 400

# login/signup use Flask-WTF form classes, which render their own hidden token.
def test_login_form_still_works_with_its_own_token(client, csrf_on):

    with app.app_context():
        student = Student(name="Ann", email="ann@example.com")
        student.set_password("Str0ng!Pass")
        db.session.add(student)
        db.session.commit()

    page = client.get("/login")
    match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', page.get_data(as_text=True))
    assert match, "login form has no csrf_token field"

    response = client.post("/login", data={
        "name": "Ann",
        "email": "ann@example.com",
        "password": "Str0ng!Pass",
        "csrf_token": match.group(1),
    })

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/home")