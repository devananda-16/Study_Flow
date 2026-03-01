import os
import sqlite3
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
# A secret key is required by Flask to securely sign the session cookie
# In a real production app, you would use os.environ.get('SECRET_KEY') here
app.secret_key = 'your_secure_random_secret_key' 

# ==========================================
# DATABASE SETUP (UPDATED FOR SERVER DEPLOYMENT)
# ==========================================
# Get the absolute path of the directory where app.py lives
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'studyflow.db')

def get_db_connection():
    # Use the absolute path instead of just the file name
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row 
    return conn

def init_db():
    conn = get_db_connection()
    # Create Users table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fullname TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    # Create Exams table linked to a specific user
    conn.execute('''
        CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    # Create Tasks table linked to a specific user
    conn.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            portions TEXT NOT NULL,
            deadline TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

# Initialize the database when the app starts
init_db()

# ==========================================
# AUTHENTICATION DECORATOR
# ==========================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ==========================================
# MAIN DASHBOARD ROUTES
# ==========================================

@app.route('/')
@login_required
def index():
    conn = get_db_connection()
    user_id = session['user_id']
    
    # Fetch the logged-in user's details
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    
    # Fetch only the logged-in user's data
    exams = conn.execute('SELECT * FROM exams WHERE user_id = ? ORDER BY date ASC', (user_id,)).fetchall()
    tasks = conn.execute('SELECT * FROM tasks WHERE user_id = ? ORDER BY deadline ASC', (user_id,)).fetchall()
    
    conn.close()
    
    # Pass the 'user' variable to the template
    return render_template('index.html', user=user, exams=exams, tasks=tasks)

@app.route('/add_exam', methods=['POST'])
@login_required
def add_exam():
    subject = request.form.get('subject')
    date = request.form.get('date')
    time = request.form.get('time')
    
    if subject and date:
        conn = get_db_connection()
        conn.execute('INSERT INTO exams (user_id, subject, date, time) VALUES (?, ?, ?, ?)',
                     (session['user_id'], subject, date, time or "TBD"))
        conn.commit()
        conn.close()
        
    return redirect(url_for('index'))

@app.route('/add_study_plan', methods=['POST'])
@login_required
def add_study_plan():
    subject = request.form.get('subject')
    portions = request.form.get('portions')
    deadline = request.form.get('deadline')
    
    if subject and portions:
        conn = get_db_connection()
        conn.execute('INSERT INTO tasks (user_id, subject, portions, deadline) VALUES (?, ?, ?, ?)',
                     (session['user_id'], subject, portions, deadline or "No Date"))
        conn.commit()
        conn.close()
        
    return redirect(url_for('index'))

# ==========================================
# DELETE ROUTES
# ==========================================

@app.route('/delete_exam/<int:exam_id>')
@login_required
def delete_exam(exam_id):
    conn = get_db_connection()
    # Ensure the user can only delete their own exams
    conn.execute('DELETE FROM exams WHERE id = ? AND user_id = ?', (exam_id, session['user_id']))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete_task/<int:task_id>')
@login_required
def delete_task(task_id):
    conn = get_db_connection()
    # Ensure the user can only delete their own tasks
    conn.execute('DELETE FROM tasks WHERE id = ? AND user_id = ?', (task_id, session['user_id']))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# ==========================================
# AUTHENTICATION ROUTES
# ==========================================

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fullname = request.form.get('fullname')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Hash the password for security
        hashed_password = generate_password_hash(password)
        
        conn = get_db_connection()
        try:
            # Insert new user into the database
            cursor = conn.execute('INSERT INTO users (fullname, email, password) VALUES (?, ?, ?)',
                                  (fullname, email, hashed_password))
            conn.commit()
            
            # Automatically log the user in after registration
            session['user_id'] = cursor.lastrowid
            return redirect(url_for('index'))
            
        except sqlite3.IntegrityError:
            # This triggers if the email is already in the database
            flash("Email already exists. Please log in.")
            return redirect(url_for('register'))
        finally:
            conn.close()
            
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # The login HTML form uses 'username' for the input name, mapping it to our 'email' column
        email = request.form.get('username') 
        password = request.form.get('password')
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            # Credentials are correct, create a session
            session['user_id'] = user['id']
            return redirect(url_for('index'))
        else:
            flash("Invalid email or password.")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    # Clear the session to log the user out
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)