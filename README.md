# 📊 GradePulse

GradePulse is a Flask web app built for students preparing for the O/L exam in Sri Lanka. Students log their term/model exam marks over time, and the app tracks trends, highlights strengths and weaknesses, and gives a statistically estimated O/L performance based on their own exam history.

---

## ✨ Features

- 🔐 **Authentication** — signup/login with hashed passwords (Werkzeug), session-based auth
- 📝 **Marks entry** — log marks for Science, Mathematics, Sinhala, English, History, Religion, and 3 elective categories per exam
- 🎯 **Grade calculator** — automatic A/B/C/S/W grade breakdown per submission
- 📈 **Marks trend chart** — line chart of the last 5 exams, per subject, with checkbox filters to isolate individual subjects
- 🕸️ **Performance radar chart** — average marks per subject across all exams
- 🏆 **Best/weakest subject insight cards**
- 📊 **Recent performance comparison** — improvement/decline between the last two exams, per subject
- 📋 **Full marks history table** — every exam and subject score in one place
- 🔮 **O/L prediction** — recency-weighted average + linear trend extrapolation per subject (a statistical estimate, not a trained ML model — built without a labeled O/L-outcome dataset)
- 📱 **Responsive design** — shared `responsive.css` across all pages for mobile layouts

---

## 🛠️ Tech Stack

- **Backend:** Flask, Flask-SQLAlchemy, Flask-WTF
- **Database:** SQLite
- **Frontend:** Jinja2 templates, vanilla CSS, Chart.js
- **Prediction logic:** NumPy (weighted average + linear regression trend), isolated in `predict.py`
- **Deployment:** PythonAnywhere

---

## 📁 Project Structure

```
mark-pulse/
├── app.py                 # Flask routes, grade calculator
├── predict.py               # O/L prediction logic (weighted average + trend)
├── models.py               # SQLAlchemy models: Student, Exam, Marks, Prediction
├── requirements.txt
├── templates/
│   ├── index.html          # Dashboard: form, charts, insights, predictions, table
│   ├── login.html
│   └── signup.html
└── static/
    ├── style.css            # Dashboard styling
    ├── login.css            # Auth pages styling
    ├── responsive.css       # Shared mobile layout rules
    └── js/
        └── chart.js         # Chart.js configs for bar/line/radar charts
```

---

## 🚀 Running Locally

1. Clone the repository
   ```
   git clone https://github.com/vidushan-ds/mark-pulse.git
   cd mark-pulse
   ```

2. Create and activate a virtual environment
   ```
   python -m venv venv
   venv\Scripts\activate      # Windows
   source venv/bin/activate   # Mac/Linux
   ```

3. Install dependencies
   ```
   pip install -r requirements.txt
   ```

4. Run the app
   ```
   python app.py
   ```

5. Open `http://127.0.0.1:5000` in your browser

---

## 🔮 On the Prediction Approach

GradePulse deliberately does **not** use a trained machine learning model for O/L prediction. A real ML model would need many students' historical marks paired with their actual O/L results to learn from — data that isn't available here. Instead, each subject's prediction is computed per student, from that student's own marks only, using a recency-weighted average blended with a linear trend fit. This keeps the estimate honest about what it actually knows, rather than presenting a black-box "AI prediction" built on data it doesn't have.

---

## 👤 Author

**Vidushan Pathirana**
