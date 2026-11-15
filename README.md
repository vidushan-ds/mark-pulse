# 📊 GradePulse

GradePulse is a Flask web app built for students preparing for the O/L exam in Sri Lanka. Students log their term/model exam marks over time, and the app tracks trends, highlights strengths and weaknesses, and gives a statistically estimated O/L performance based on their own exam history.

🌐 **Live demo:** https://vidushan.pythonanywhere.com

---

## ✨ Features

### 📚 For students

- 📝 **Marks entry** — log marks for Science, Mathematics, Sinhala, English, History, Religion, and 3 elective categories per exam
- 🎯 **Grade calculator** — automatic A/B/C/S/W grade breakdown per submission
- 📈 **Marks trend chart** — line chart of the last 5 exams, per subject, with checkbox filters to isolate individual subjects
- 🕸️ **Performance radar chart** — average marks per subject across all exams
- 🏆 **Best/weakest subject insight cards**
- 📊 **Recent performance comparison** — improvement/decline between the last two exams, per subject
- 📋 **Full marks history table** — every exam and subject score in one place
- 🔮 **O/L estimate** — a recency-weighted average blended with a linear trend, calculated per subject from each exam's real position (a missed exam leaves a gap instead of distorting the trend). Shown with a "typical range" and the number of exams it is based on. It is a statistical estimate, not a trained ML model and not a guarantee
- 📱 **Responsive design** — shared `responsive.css` across all pages for mobile layouts

### 🔐 Accounts and security
 
- **Authentication** — signup/login with hashed passwords (Werkzeug) and session-based auth
- **Password rules** — at least 8 characters with upper and lower case letters, a number and a symbol
- **Password reset** — signed, single-use link that expires after one hour; the page gives the same answer whether or not an email is registered
- **Rate limiting** — Flask-Limiter on login, signup and reset requests
- **CSRF protection** — every form carries a token that the server validates (Flask-WTF `CSRFProtect`)

### 🧱 Data integrity and code quality
 
- **Database constraints** — marks and predictions must be 0–100, subjects must be one of the nine allowed, one mark per subject per exam, one prediction per student and subject, foreign keys enforced with cascade delete
- **One-time migration script** — `migrate_constraints.py` upgrades an existing database to the constraints without losing data (checks first, backs up, rolls back on failure)
- **Services layer** — routes only coordinate; the logic lives in `services/` so it can be tested on its own
- **Prediction evaluation** — `evaluate_predictions.py` measures the method against simple baselines on past exams (MAE)
- **Automated tests** — pytest suite covering authentication, CSRF, database constraints, predictions and evaluation

---

## 🛠️ Tech Stack

- **Backend:** Flask, Flask-SQLAlchemy, Flask-WTF
- **Database:** SQLite
- **Frontend:** Jinja2 templates, vanilla CSS, Chart.js
- **Prediction logic:** NumPy (weighted average + linear trend), in `services/predictions.py`
-**Testing:** pytest
- **Deployment:** PythonAnywhere

---

## 📁 Project Structure

```
mark-pulse/
├── app.py                  # Flask routes, forms, rate limiting, CSRF
├── models.py               # SQLAlchemy models and database constraints
├── evaluate_predictions.py # measures prediction accuracy on past exams
├── migrate_constraints.py  # one-time upgrade of an existing database
├── requirements.txt
├── requirements-dev.txt    # test tools (pytest)
├── pytest.ini
├── README.md
├── services/
│   ├── __init__.py               # SUBJECT_NAMES
│   ├── grades.py                 # grade calculator
│   ├── exams.py                  # saving and loading exams (database)
│   ├── analytics.py              # averages, chart data, improvement
│   ├── predictions.py            # O/L estimates and typical range
│   ├── evaluation.py             # walk-forward evaluation of predictions
│   ├── passwords.py              # password strength rules
│   └── password_reset.py         # reset tokens and email sending
├── templates/
│   ├── index.html                # dashboard: form, charts, insights, predictions, table
│   ├── login.html
│   ├── signup.html
│   ├── forgot_password.html
│   └── reset_password.html
├── static/
│   ├── style.css                 # dashboard styling
│   ├── login.css                 # auth pages styling
│   ├── responsive.css            # shared mobile layout rules
│   ├── favicon.png
│   └── js/
│       └── chart.js              # Chart.js configs for line/radar charts
└── tests/
    ├── conftest.py               # fresh in-memory database for every test
    ├── test_auth.py
    ├── test_csrf.py
    ├── test_models.py
    ├── test_predictions.py
    ├── test_evaluation.py
    └── test_services.py
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

## ⚙️ Configuration
 
All settings are optional for local use.
 
| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Signs sessions, CSRF tokens and password-reset links. **Set it in production**; without it a development fallback key is used |
| `DATABASE_URL` | Database to use. Defaults to a SQLite file in `instance/` |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` | Send real password-reset emails. Without `SMTP_HOST`, the reset link is written to the server log instead |
 
---
 
## 🧪 Tests and Evaluation
 
```
pip install -r requirements-dev.txt
pytest                                   # run the test suite
python evaluate_predictions.py           # measure prediction accuracy on your database
python evaluate_predictions.py --csv marks.csv   # or on a CSV (student, exam_order, subject, score)
```
 
---
 
## ☁️ Deploying an Update (PythonAnywhere)
 
1. Back up `instance/ol_predictor.db`
2. `git pull`
3. `pip install -r requirements.txt`
4. If the database was created before the constraints were added, run `python migrate_constraints.py` once
5. Click **Reload** on the Web tab
Set `SECRET_KEY` (and optionally the `SMTP_*` variables) in the WSGI file.
 
---
 
## 🔮 On the Prediction Approach
 
GradePulse deliberately does **not** use a trained machine learning model for O/L prediction. A real ML model would need many students' historical marks paired with their actual O/L results to learn from — data that isn't available here. Instead, each subject's estimate is computed per student, from that student's own marks only:
 
- a **recency-weighted average**, where the newest exam counts up to twice as much as the oldest
- a **linear trend** fitted through the marks and read at the next exam
- the two blended 60/40, kept between 0 and 100, and shown with a "typical range" (the estimate ± how much that student's marks usually change between exams)
Marks keep their real exam position, so a missed exam is a gap in the timeline rather than squeezing the remaining marks together.
 
**How it is checked.** `evaluate_predictions.py` replays past exams: for every mark that has at least two earlier marks, it predicts that mark using only the earlier ones and compares it with what really happened. It reports the average miss (MAE) against simple baselines (the last score, the average of all exams, the weighted average alone, the trend alone), a grid of other weight and blend settings, and how often real marks landed inside the typical range.
 
**Known limitations**
 
- The weights and the 60/40 blend are design choices that have **not yet been validated on real student data**. The evaluation script exists to test them once enough marks are collected
- The evaluation measures predicting the *next exam*, not the actual O/L result, because O/L outcomes are not in the data
- The typical range is a rough guide, not a statistical confidence interval
- Exam position means the order marks were entered; the real exam date is not collected
This keeps the estimate honest about what it actually knows, rather than presenting a black-box "AI prediction" built on data it doesn't have.
 
---
 
## 👤 Author
 
**Vidushan Pathirana**
