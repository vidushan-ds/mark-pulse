from flask import Flask, render_template, request, redirect, url_for, session
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from models import db, Student, Exam, Marks, Prediction
from sqlalchemy import func

class SignupForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password", message="Passwords must match")])
    submit = SubmitField("Sign Up")
    
    
class LoginForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

app = Flask(__name__)

app.config["SECRET_KEY"] = "vidushan-ds"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///ol_predictor.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()

def grade_calculator(marks: list):
    
    A_count = 0
    B_count = 0
    C_count = 0
    S_count = 0
    W_count = 0
    
    for mark in marks:
        if mark >= 75:
            A_count += 1
        elif mark >= 65:
            B_count += 1
        elif mark >= 55:
            C_count += 1
        elif mark >= 35:
            S_count += 1
        else:
            W_count += 1
    
    return [A_count, B_count, C_count, S_count, W_count]

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

@app.route("/home", methods=['GET', 'POST'])
def home():
    result = None
    card_data = None
    
    student_id = session.get("student_id")
    name = session.get("name")
    
    subject_names = ["science", 
                    "mathematics",
                    "sinhala",
                    "english",
                    "history", 
                    "religion", 
                    "category_1", 
                    "category_2", 
                    "category_3"]
    
    if request.method == 'POST':
        
        exam_name = request.form.get('exam_name', '')
        
        science = request.form.get('science', type=float)
        mathematics = request.form.get('math', type=float)
        sinhala = request.form.get('sinhala', type=float)
        english = request.form.get('english', type=float)
        history = request.form.get('history', type=float)
        religion = request.form.get('religion', type=float)
        category_1 = request.form.get('category_1', type=float)
        category_2 = request.form.get('category_2', type=float)
        category_3 = request.form.get('category_3', type=float)
        
        marks = [science,
                mathematics,
                sinhala,
                english, 
                history, 
                religion, 
                category_1, 
                category_2, 
                category_3]
        
        grades = grade_calculator(marks)
        
        exam = Exam(student_id=student_id, 
                    exam_name=exam_name)
        
        db.session.add(exam)
        db.session.commit()
        
        for subject, score in zip(subject_names, marks):
            if score is not None:
                db.session.add(Marks(exam_id=exam.id, 
                                     subject=subject, 
                                     score=score))
                
        db.session.commit()
        
        result = {
            "exam_name" : exam_name,
            "science" : science,
            "mathematics" : mathematics,
            "sinhala" : sinhala,
            "english" : english,
            "history" : history,
            "religion" : religion,
            "category_1" : category_1,
            "category_2" : category_2,
            "category_3" : category_3,
            "grades" : grades
        }
        
    recent_exams = (
        Exam.query
        .filter_by(student_id=student_id)
        .order_by(Exam.id.desc())
        .limit(5)
        .all()
    )
    
    recent_exams.reverse()
    
    line_labels = [exam.exam_name for exam in recent_exams]
    line_data = {subject: [] for subject in subject_names}
    
    for exam in recent_exams:
        marks_by_subject = {m.subject: m.score for m in exam.marks}
        for subject in subject_names:
            line_data[subject].append(marks_by_subject.get(subject))
            
    radar_data = []
    
    for subject in subject_names:
        avg_score = (
            db.session.query(func.avg(Marks.score))
            .join(Exam)
            .filter(Exam.student_id == student_id,
                       Marks.subject == subject
                       )
            .scalar()
        )
        radar_data.append(round(avg_score, 1) if avg_score is not None else 0)
        
    if any(score > 0 for score in radar_data):
        best_index = radar_data.index(max(radar_data))
        weakest_index = radar_data.index(min(radar_data))
        
        card_data = {
            "best_subject" : subject_names[best_index],
            "best_score" : radar_data[best_index],
            "weakest_subject" : subject_names[weakest_index],
            "weakest_score" : radar_data[weakest_index]
        }
        
    chart_data = {
        "line_labels" : line_labels,
        "line_data" : line_data,
        "radar_labels" : subject_names,
        "radar_data" : radar_data
    }
    
    return render_template("index.html", result=result, card_data=card_data, name=name, chart_data=chart_data)

if __name__ == "__main__":
    app.run(debug=True)
