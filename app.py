from flask import Flask, render_template, request, redirect, url_for, session
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Email
from models import db, Student, Exam, Marks, Prediction


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

@app.route("/home", methods=['GET', 'POST'])
def home():
    result = None
    
    student_id = session.get("student_id")
    name = session.get("name")
    
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
        
        marks = [science, mathematics, sinhala, english, history, religion, category_1, category_2, category_3]
        grades = grade_calculator(marks)
        
        exam = Exam(student_id=student_id, exam_name=exam_name)
        db.session.add(exam)
        db.session.commit()
        
        subject_names = ["science", 
                        "mathematics",
                        "sinhala",
                        "english",
                        "history", 
                        "religion", 
                        "category_1", 
                        "category_2", 
                        "category_3"]
        
        for subject, score in zip(subject_names, marks):
            if score is not None:
                db.session.add(Marks(exam_id=exam.id, subject=subject, score=score))
                
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
    
    return render_template("index.html", result=result, name=name)

if __name__ == "__main__":
    app.run(debug=True)
