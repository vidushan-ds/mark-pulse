from flask import Flask, render_template, request, redirect, url_for, session
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from models import db, Student
from services.grades import grade_calculator
from services.exams import save_exam, get_exam_records
from services.analytics import (
    build_marks_table,
    build_chart_data,
    calculate_subject_averages,
    calculate_improvement,
    find_best_and_weakest,
)
from services.predictions import generate_predictions, save_predictions
import os

# checking sign up data
class SignupForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password", message="Passwords must match")])
    submit = SubmitField("Sign Up")
    
# check login data   
class LoginForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-fallback-key")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///ol_predictor.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

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


# root route
@app.route("/")
def index():
    if session.get("student_id"):
        return redirect(url_for("home"))
    return redirect(url_for("login"))

# login page
@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    
    if form.validate_on_submit():
        student = Student.query.filter_by(email=form.email.data).first()
        
        if student and student.check_password(form.password.data):
            session["student_id"] = student.id
            session["name"] = student.name
            return redirect(url_for("home"))
        else:
            form.email.errors.append("Invalid email or password")
    
    return render_template("login.html", form=form)

# sign-up page
@app.route("/signup", methods=["GET", "POST"])
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
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=False)
