from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def home():
    result = None
    
    if request.method == 'POST':
        exam_name = request.form.get('exam_name', '')
        science = request.form.get('science', type=float)
        mathematics = request.form.get('math', type=float)
        english = request.form.get('english', type=float)
        ict = request.form.get('ict', type=float)
        sinhala = request.form.get('sinhala', type=float)
        
        result = {
            "exam_name" : exam_name,
            "science" : science,
            "mathematics" : mathematics,
            "english" : english,
            "ict" : ict,
            "sinhala" : sinhala
        }
    
    return render_template("index.html", result=result)

if __name__ == "__main__":
    app.run(debug=True)
