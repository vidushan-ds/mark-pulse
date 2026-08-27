from flask import Flask, render_template, request, redirect, url_for, session
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Email

class LoginForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

app = Flask(__name__)

app.config["SECRET_KEY"] = "vidushan-ds"

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
        session["name"] = form.name.data
        return redirect(url_for("home"))
    
    return render_template("login.html", form=form)

@app.route("/home", methods=['GET', 'POST'])
def home():
    result = None
    
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
