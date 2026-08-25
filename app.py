from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def home():
    result = None
    
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
            "category_3" : category_3
        }
    
    return render_template("index.html", result=result)

if __name__ == "__main__":
    app.run(debug=True)
