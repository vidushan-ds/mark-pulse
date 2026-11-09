from flask import Flask, render_template, request, redirect, url_for, session
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect, CSRFError
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Email, EqualTo
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from models import db, Student

from services.grades import grade_calculator
from services.passwords import strong_password
from services.exams import save_exam, get_exam_records
from services.analytics import (
    build_marks_table,
    build_chart_data,
    calculate_subject_averages,
    calculate_improvement,
    find_best_and_weakest,
)
from services.predictions import generate_predictions, save_predictions
from services.password_reset import generate_reset_token, verify_reset_token, send_reset_email
import os

# checking sign up data
class SignupForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), strong_password])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password", message="Passwords must match")])
    submit = SubmitField("Sign Up")
    
# check login data   
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")
    
# forgot password form
class ForgotPasswordForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Send reset link")
    
# reset password form
class ResetPasswordForm(FlaskForm):
    password = PasswordField("New Password", validators=[DataRequired(), strong_password])
    confirm_password = PasswordField("Confirm New Password", validators=[DataRequired(), EqualTo("password", message="Passwords must match")])
    submit = SubmitField("Reset Password")

app = Flask(__name__)

app.wsgi_app = ProxyFix(
    app.wsgi_app,
    x_for=1
)

# --------- SECRET_KEY ------------

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")

if not app.config["SECRET_KEY"]:
    raise RuntimeError("SECRET_KEY must be configured")

# --------------------------------

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///ol_predictor.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

db.init_app(app)

with app.app_context():
    db.create_all()

#--------------------------------
FORM_FIELDS = {
   "science": "science",
    "mathematics": "math",
    "sinhala": "sinhala",
    "english": "english",
    "history": "history",
    "religion": "religion",
    "category_1": "category_1",
    "category_2": "category_2",
    "category_3": "category_3" 
}
#--------------------------------

def parse_exam_form(form):
    exam_name = form.get("exam_name", "")
    marks = {
        subject: form.get(field, type=float)
        for subject, field in FORM_FIELDS.items()
    }
    return exam_name, marks

#---------------------------------

limiter = Limiter(get_remote_address,
                  app=app,
                  default_limits=[],
                  storage_uri=os.environ.get("RATELIMIT_STORAGE_URI", "memory://"))

# checks the CSRF token on every POST/PUT/PATCH/DELETE before the view runs
csrf = CSRFProtect(app)

@app.errorhandler(429)
def too_many_request(error):
    return "Too many attempts. Please wait a minute and try again", 429

@app.errorhandler(CSRFError)
def csrf_failed(error):
    return "Your form expired or was invalid. Please go back, refresh the page and try again.", 400

#----------------------------------

# root route
@app.route("/")
def index():
    if session.get("student_id"):
        return redirect(url_for("home"))
    return redirect(url_for("login"))

# login page
@app.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def login():
    form = LoginForm()
    
    if form.validate_on_submit():
        student = Student.query.filter_by(email=form.email.data).first()
        
        if student and student.check_password(form.password.data):
            session.clear()
            session["student_id"] = student.id
            session["name"] = student.name
            return redirect(url_for("home"))
        else:
            form.email.errors.append("Invalid email or password")
    
    return render_template("login.html", form=form)

# sign-up page
@app.route("/signup", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def signup():
    form = SignupForm()
    
    if form.validate_on_submit():
        existing = Student.query.filter_by(email=form.email.data).first()
        if existing:
            form.email.errors.append("An account with this email already exists")
        else:
            student = Student(name=form.name.data, email=form.email.data)
            student.set_password(form.password.data)
            db.session.add(student)
            db.session.commit()
            
            session["student_id"] = student.id
            session["name"] = student.name
            return redirect(url_for("home"))
    
    return render_template("signup.html", form=form)

# forgot password page
@app.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("5 per hour", methods=["POST"])
def forgot_password():
    form = ForgotPasswordForm()
    message = None

    if form.validate_on_submit():
        student = Student.query.filter_by(email=form.email.data).first()

        if student:
            token = generate_reset_token(student)
            link = url_for("reset_password", token=token, _external=True)
            send_reset_email(student.email, link)

        message = "If that email is registered, a reset link has been sent."

    return render_template("forgot_password.html", form=form, message=message)

# reset password page
@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    student = verify_reset_token(token)

    if student is None:
        return render_template(
            "forgot_password.html",
            form=ForgotPasswordForm(),
            message="That reset link is invalid or has expired. Please request a new one.",
        ), 400

    form = ResetPasswordForm()

    if form.validate_on_submit():
        student.set_password(form.password.data)
        db.session.commit()
        return redirect(url_for("login"))

    return render_template("reset_password.html", form=form)

# home page
@app.route("/home", methods=["GET", "POST"])
def home():
    student_id = session.get("student_id")
    if student_id is None:
        return redirect(url_for("login"))

    result = None
    if request.method == "POST":
        exam_name, marks = parse_exam_form(request.form)
        save_exam(student_id, exam_name, marks)
        result = {
            "exam_name": exam_name,
            **marks,
            "grades": grade_calculator(list(marks.values())),
        }

    records = get_exam_records(student_id)
    averages = calculate_subject_averages(records)
    prediction_data = generate_predictions(records)
    save_predictions(student_id, prediction_data)

    return render_template(
        "index.html",
        name=session.get("name"),
        result=result,
        card_data=find_best_and_weakest(averages),
        chart_data=build_chart_data(records, averages),
        improvement_data=calculate_improvement(records),
        prediction_data=prediction_data,
        marks_table=build_marks_table(records),
    )

# log out route   
@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=False)
