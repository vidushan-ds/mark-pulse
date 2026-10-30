from models import db, Exam, Marks

def save_exam(student_id, exam_name, marks):
    
    exam = Exam(student_id=student_id, exam_name=exam_name)
    db.session.add(exam)
    db.session.flush()
    
    for subject, score in marks.items():
        if score is not None:
            db.session.add(Marks(exam_id=exam.id, 
                                 subject=subject,
                                 score=score))
    
    db.session.commit()
    return exam

def get_exam_records(student_id):
    exams = (
        Exam.query
        .filter_by(student_id=student_id)
        .order_by(Exam.id.asc())
        .all()
    )
    
    return [
        {
            "exam_name": exam.exam_name,
            "exam_date": exam.exam_date,
            "marks": {m.subject: m.score for m in exam.marks},
        }
        for exam in exams
    ]