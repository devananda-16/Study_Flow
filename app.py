from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime

app = Flask(__name__)

# Dummy Data for testing the UI
exams = [
    {"id": 1, "subject": "Mathematics", "date": "2026-03-15", "time": "09:00 AM"},
    {"id": 2, "subject": "History", "date": "2026-03-18", "time": "01:00 PM"},
    {"id": 3, "subject": "Physics", "date": "2026-03-22", "time": "10:30 AM"}
]

study_tasks = [
    {"id": 1, "subject": "Mathematics", "portions": "Calculus & Integrals", "deadline": "2026-03-10"},
    {"id": 2, "subject": "History", "portions": "The French Revolution", "deadline": "2026-03-12"}
]

@app.route('/')
def index():
    # Sort exams by date so the closest one is first
    sorted_exams = sorted(exams, key=lambda x: x['date'])
    return render_template('index.html', exams=sorted_exams, tasks=study_tasks)

@app.route('/add_exam', methods=['POST'])
def add_exam():
    subject = request.form.get('subject')
    date = request.form.get('date')
    time = request.form.get('time')
    if subject and date:
        exams.append({"id": len(exams)+1, "subject": subject, "date": date, "time": time or "TBD"})
    return redirect(url_for('index'))

@app.route('/add_study_plan', methods=['POST'])
def add_study_plan():
    subject = request.form.get('subject')
    portions = request.form.get('portions')
    deadline = request.form.get('deadline')
    if subject and portions:
        study_tasks.append({
            "id": len(study_tasks)+1, 
            "subject": subject, 
            "portions": portions, 
            "deadline": deadline or "No Date"
        })
    return redirect(url_for('index'))

@app.route('/delete_task/<int:task_id>')
def delete_task(task_id):
    global study_tasks
    study_tasks = [t for t in study_tasks if t['id'] != task_id]
    return redirect(url_for('index'))

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)