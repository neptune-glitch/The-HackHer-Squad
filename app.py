from flask import Flask, render_template, request, redirect, session
import sqlite3
import requests
from datetime import datetime

app = Flask(__name__)
app.secret_key = "gigshield2026"

# ─── DATABASE SETUP ───────────────────────
def create_database():
    conn = sqlite3.connect('gigshield.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS workers (
            id INTEGER PRIMARY KEY,
            name TEXT,
            phone TEXT,
            zone TEXT,
            upi_id TEXT,
            platform TEXT,
            plan TEXT,
            password TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS claims (
            id INTEGER PRIMARY KEY,
            worker_id INTEGER,
            disruption_type TEXT,
            amount TEXT,
            status TEXT,
            date TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

# ─── HOME PAGE ────────────────────────────
@app.route('/')
def home():
    return render_template('home.html')

# ─── REGISTER ROUTE ───────────────────────
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        zone = request.form['zone']
        upi = request.form['upi']
        platform = request.form['platform']
        plan = request.form['plan']
        password = request.form['password']
        
        conn = sqlite3.connect('gigshield.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO workers 
            (name, phone, zone, upi_id, 
            platform, plan, password)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, phone, zone, upi, 
              platform, plan, password))
        conn.commit()
        conn.close()
        return redirect('/login')
    
    return render_template('register.html')

# ─── LOGIN ROUTE ──────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form['phone']
        password = request.form['password']
        
        conn = sqlite3.connect('gigshield.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM workers 
            WHERE phone=? AND password=?
        ''', (phone, password))
        worker = cursor.fetchone()
        conn.close()
        
        if worker:
            session['worker_id'] = worker[0]
            session['worker_name'] = worker[1]
            session['worker_zone'] = worker[3]
            return redirect('/dashboard')
        else:
            return "Invalid login! Try again!"
    
    return render_template('login.html')

# ─── LOGOUT ───────────────────────────────
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ─── DASHBOARD ────────────────────────────
@app.route('/dashboard')
def dashboard():
    if 'worker_id' not in session:
        return redirect('/login')
    
    conn = sqlite3.connect('gigshield.db')
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM workers WHERE id=?',
        (session['worker_id'],)
    )
    worker = cursor.fetchone()
    conn.close()
    
    return render_template('dashboard.html',
        worker=worker
    )

# ─── RUN APP ──────────────────────────────
if __name__ == '__main__':
    create_database()
    app.run(debug=True)
