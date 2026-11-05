from app import app, limiter
from models import db, Student
from services.passwords import password_problems
from services.password_reset import generate_reset_token, verify_reset_token

GOOD_PASSWORD = "Str0ng!Pass"
EMAIL = "ann@example.com"


# ---------- helpers ----------

def signup(client, email=EMAIL, password=GOOD_PASSWORD, name="Ann"):
    return client.post("/signup", data={
        "name": name,
        "email": email,
        "password": password,
        "confirm_password": password,
    })


def login(client, email=EMAIL, password=GOOD_PASSWORD, name="Ann", **kwargs):
    return client.post("/login", data={
        "name": name,
        "email": email,
        "password": password,
    }, **kwargs)


def is_logged_in(client):
    with client.session_transaction() as sess:
        return "student_id" in sess


def student_count():
    with app.app_context():
        return Student.query.count()


# ---------- signup ----------

def test_signup_creates_account_and_logs_in(client):
    response = signup(client)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/home")
    assert is_logged_in(client)
    assert student_count() == 1


def test_password_is_stored_hashed(client):
    signup(client)

    with app.app_context():
        student = Student.query.filter_by(email=EMAIL).first()
        assert student.password_hash != GOOD_PASSWORD
        assert student.check_password(GOOD_PASSWORD)


def test_signup_rejects_duplicate_email(client):
    signup(client)
    response = signup(client)

    assert response.status_code == 200
    assert b"already exists" in response.data
    assert student_count() == 1


def test_signup_rejects_short_password(client):
    response = signup(client, password="Ab1!xyz")  

    assert b"at least 8 characters" in response.data
    assert student_count() == 0


def test_signup_rejects_password_missing_character_types(client):
    response = signup(client, password="alllowercase")

    assert b"an uppercase letter" in response.data
    assert b"a number" in response.data
    assert b"a symbol" in response.data
    assert student_count() == 0


# login 

def test_login_succeeds_with_correct_password(client):
    signup(client)
    client.get("/logout")

    response = login(client)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/home")
    assert is_logged_in(client)


def test_login_fails_with_wrong_password(client):
    signup(client)
    client.get("/logout")

    response = login(client, password="Wr0ng!Password")

    assert response.status_code == 200
    assert b"Invalid email or password" in response.data
    assert not is_logged_in(client)


def test_login_fails_for_unknown_email(client):
    response = login(client, email="nobody@example.com")

    assert b"Invalid email or password" in response.data
    assert not is_logged_in(client)


# logout and protected pages 

def test_logout_clears_session(client):
    signup(client)
    assert is_logged_in(client)

    response = client.get("/logout")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")
    assert not is_logged_in(client)


def test_home_redirects_to_login_when_logged_out(client):
    response = client.get("/home")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


# rate limiting 

def test_login_is_rate_limited(client):
    limiter.enabled = True
    limiter.reset()
    try:
        for _ in range(10):
            response = login(client, password="Wr0ng!Password")
            assert response.status_code == 200

        response = login(client, password="Wr0ng!Password")
        assert response.status_code == 429
    finally:
        limiter.enabled = False


def test_rate_limit_is_per_visitor_ip(client):
    limiter.enabled = True
    limiter.reset()
    try:
        for _ in range(10):
            login(client, password="Wr0ng!Password", headers={"X-Real-IP": "1.1.1.1"})

        blocked = login(client, password="Wr0ng!Password", headers={"X-Real-IP": "1.1.1.1"})
        other_visitor = login(client, password="Wr0ng!Password", headers={"X-Real-IP": "2.2.2.2"})

        assert blocked.status_code == 429
        assert other_visitor.status_code == 200
    finally:
        limiter.enabled = False


# password strength rules

def test_strong_password_has_no_problems():
    assert password_problems(GOOD_PASSWORD) == []


def test_password_problems_lists_every_missing_rule():
    assert password_problems("abc") == [
        "at least 8 characters",
        "an uppercase letter",
        "a number",
        "a symbol",
    ]


# password reset 

def make_student():
    with app.app_context():
        student = Student(name="Ann", email=EMAIL)
        student.set_password(GOOD_PASSWORD)
        db.session.add(student)
        db.session.commit()
        return student.id


def test_forgot_password_gives_same_message_for_unknown_email(client):
    make_student()

    known = client.post("/forgot-password", data={"email": EMAIL})
    unknown = client.post("/forgot-password", data={"email": "nobody@example.com"})

    assert b"If that email is registered" in known.data
    assert b"If that email is registered" in unknown.data


def test_reset_token_round_trip():
    student_id = make_student()

    with app.app_context():
        student = db.session.get(Student, student_id)
        token = generate_reset_token(student)
        assert verify_reset_token(token).id == student_id


def test_garbage_token_is_rejected():
    make_student()

    with app.app_context():
        assert verify_reset_token("not-a-real-token") is None


def test_expired_token_is_rejected():
    student_id = make_student()

    with app.app_context():
        token = generate_reset_token(db.session.get(Student, student_id))
        assert verify_reset_token(token, max_age=-1) is None


def test_reset_changes_password_and_link_works_only_once(client):
    student_id = make_student()
    new_password = "N3w!Password"

    with app.app_context():
        token = generate_reset_token(db.session.get(Student, student_id))

    response = client.post(f"/reset-password/{token}", data={
        "password": new_password,
        "confirm_password": new_password,
    })
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")

    assert login(client, password=new_password).status_code == 302
    client.get("/logout")
    assert b"Invalid email or password" in login(client).data

    reused = client.get(f"/reset-password/{token}")
    assert reused.status_code == 400


def test_reset_rejects_weak_password(client):
    student_id = make_student()

    with app.app_context():
        token = generate_reset_token(db.session.get(Student, student_id))

    response = client.post(f"/reset-password/{token}", data={
        "password": "weak",
        "confirm_password": "weak",
    })

    assert response.status_code == 200
    assert b"Password needs" in response.data