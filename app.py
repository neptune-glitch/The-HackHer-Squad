from flask import Flask, render_template, request, redirect, session
import sqlite3
import requests
from datetime import datetime

app = Flask(__name__)
app.secret_key = "gigshield2026"

# ─── WEATHER API ──────────────────────────
def get_delhi_weather():
    api_key = "153b4130cd47b17c07d7462e65251ae9"
    url = f"http://api.openweathermap.org/data/2.5/weather?q=Delhi,IN&appid={api_key}&units=metric"
    
    try:
        response = requests.get(url)
        data = response.json()
        temp = data['main']['temp']
        rainfall = data.get('rain', {}).get('1h', 0)
        humidity = data['main']['humidity']
        description = data['weather'][0]['description']
        return {
            'temp': round(temp, 1),
            'rainfall': rainfall,
            'humidity': humidity,
            'description': description
        }
    except:
        return {
            'temp': 35,
            'rainfall': 0,
            'humidity': 60,
            'description': 'Clear sky'
        }

# ─── RISK SCORE ───────────────────────────
def calculate_risk_score(zone, rainfall, temp):
    score = 0
    if zone == "Dwarka":
        score += 30
    elif zone == "Lajpat Nagar":
        score += 25
    elif zone == "Rohini":
        score += 20
    else:
        score += 10
    
    month = datetime.now().month
    if month in [7, 8, 9]:
        score += 30
    elif month in [4, 5, 6]:
        score += 20
    elif month in [11, 12, 1]:
        score += 25
    else:
        score += 10
    
    if rainfall > 50:
        score += 40
    elif temp > 44:
        score += 35
    elif temp > 40:
        score += 20
    else:
        score += 5
    return score

# ─── PREMIUM CALCULATOR ───────────────────
def calculate_premium(risk_score, plan):
    if "Basic" in plan:
        base = 25
    elif "Standard" in plan:
        base = 40
    else:
        base = 60
    if risk_score >= 80:
        premium = base + 15
    elif risk_score >= 60:
        premium = base + 10
    elif risk_score >= 40:
        premium = base + 5
    else:
        premium = base
    return premium

# ─── FRAUD DETECTION ──────────────────────
def fraud_detection(worker_id):
    conn = sqlite3.connect('gigshield.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*) FROM claims 
        WHERE worker_id=?
    ''', (worker_id,))
    claim_count = cursor.fetchone()[0]
    conn.close()
    fraud_score = 0
    if claim_count > 4:
        fraud_score += 50
    elif claim_count > 2:
        fraud_score += 25
    if fraud_score >= 60:
        return "REJECTED ❌", fraud_score
    elif fraud_score >= 30:
        return "UNDER REVIEW 🔍", fraud_score
    else:
        return "APPROVED ✅", fraud_score

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

# ─── HOME PAGE 
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
    weather = get_delhi_weather()
    risk_score = calculate_risk_score(
        worker[3],
        weather['rainfall'],
        weather['temp']
    )
    if risk_score >= 70:
        risk_level = "HIGH 🔴"
    elif risk_score >= 40:
        risk_level = "MEDIUM 🟡"
    else:
        risk_level = "LOW 🟢"
    premium = calculate_premium(risk_score, worker[6])
    claim_triggered = False
    disruption_type = ""
    if weather['rainfall'] > 50:
        claim_triggered = True
        disruption_type = "Heavy Rain/Flood 🌧️"
    elif weather['temp'] > 44:
        claim_triggered = True
        disruption_type = "Extreme Heat 🌡️"
    fraud_status, fraud_score = fraud_detection(
        session['worker_id']
    )
    return render_template('dashboard.html',
        worker=worker,
        weather=weather,
        risk_score=risk_score,
        risk_level=risk_level,
        premium=premium,
        claim_triggered=claim_triggered,
        disruption_type=disruption_type,
        fraud_status=fraud_status
    )

# ─── TEST WEATHER ─────────────────────────
@app.route('/test-weather')
def test_weather():
    weather = get_delhi_weather()
    return str(weather)

# ─── RUN APP 
if __name__ == '__main__':
    create_database()
    app.run(debug=True)
