from flask import Flask, render_template, request, redirect, session
import sqlite3
import requests
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback_secret")

# ─── WEATHER API ──────────────────────────
def get_delhi_weather(city="Delhi"):
    api_key = os.getenv('WEATHER_API_KEY')
    city_name = city.split(",")[0].strip()
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name},IN&appid={api_key}&units=metric"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        if response.status_code != 200:
            return default_weather(city_name)
        return {
            'temp': round(data['main']['temp'], 1),
            'rainfall': data.get('rain', {}).get('1h', 0),
            'humidity': data['main']['humidity'],
            'description': data['weather'][0]['description'],
            'city': city_name
        }
    except:
        return default_weather(city_name)

def default_weather(city="Delhi"):
    return {
        'temp': 35,
        'rainfall': 0,
        'humidity': 60,
        'description': 'Clear sky',
        'city': city
    }

# ─── RISK SCORE ───────────────────────────
def calculate_risk_score(zone, rainfall, temp):
    score = 0
    zone_lower = zone.lower()
    if "dwarka" in zone_lower or "mumbai" in zone_lower:
        score += 30
    elif "lajpat" in zone_lower or "kolkata" in zone_lower:
        score += 25
    elif "rohini" in zone_lower or "chennai" in zone_lower:
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
        return base + 15
    elif risk_score >= 60:
        return base + 10
    elif risk_score >= 40:
        return base + 5
    return base

# ─── FRAUD DETECTION ──────────────────────
def fraud_detection(worker_id):
    conn = sqlite3.connect('gigshield.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM claims WHERE worker_id=?', (worker_id,))
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

# ─── HOME ─────────────────────────────────
@app.route('/')
def home():
    return render_template('home.html')

# ─── REGISTER ─────────────────────────────
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        conn = sqlite3.connect('gigshield.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO workers 
            (name, phone, zone, upi_id, platform, plan, password)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            request.form['name'],
            request.form['phone'],
            request.form['zone'],
            request.form['upi'],
            request.form['platform'],
            request.form['plan'],
            request.form['password']
        ))
        conn.commit()
        conn.close()
        return redirect('/login')
    return render_template('register.html')

# ─── LOGIN ────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form['phone']
        password = request.form['password']
        conn = sqlite3.connect('gigshield.db')
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM workers WHERE phone=? AND password=?',
            (phone, password)
        )
        worker = cursor.fetchone()
        conn.close()
        if worker:
            session['worker_id'] = worker[0]
            session['worker_name'] = worker[1]
            session['worker_zone'] = worker[3]
            return redirect('/dashboard')
        return "Invalid login!"
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
    cursor.execute('SELECT * FROM workers WHERE id=?', (session['worker_id'],))
    worker = cursor.fetchone()
    conn.close()
    weather = get_delhi_weather(worker[3])
    risk_score = calculate_risk_score(worker[3], weather['rainfall'], weather['temp'])
    risk_level = "HIGH 🔴" if risk_score >= 70 else "MEDIUM 🟡" if risk_score >= 40 else "LOW 🟢"
    premium = calculate_premium(risk_score, worker[6])
    claim_triggered = False
    disruption_type = ""
    if weather['rainfall'] > 50:
        claim_triggered = True
        disruption_type = "Heavy Rain/Flood 🌧️"
    elif weather['temp'] > 44:
        claim_triggered = True
        disruption_type = "Extreme Heat 🌡️"
    fraud_status, fraud_score = fraud_detection(session['worker_id'])
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

# ─── CLAIMS ───────────────────────────────
@app.route('/claims')
def claims():
    if 'worker_id' not in session:
        return redirect('/login')
    conn = sqlite3.connect('gigshield.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM claims WHERE worker_id=?', (session['worker_id'],))
    claim_history = cursor.fetchall()
    cursor.execute('SELECT * FROM workers WHERE id=?', (session['worker_id'],))
    worker = cursor.fetchone()
    conn.close()
    weather = get_delhi_weather(worker[3])
    claim_triggered = False
    disruption_type = ""
    if weather['rainfall'] > 50:
        claim_triggered = True
        disruption_type = "Heavy Rain/Flood 🌧️"
    elif weather['temp'] > 44:
        claim_triggered = True
        disruption_type = "Extreme Heat 🌡️"
    fraud_status, fraud_score = fraud_detection(session['worker_id'])
    return render_template('claims.html',
        claim_history=claim_history,
        worker=worker,
        claim_triggered=claim_triggered,
        disruption_type=disruption_type,
        fraud_status=fraud_status,
        fraud_score=fraud_score,
        weather=weather
    )

# ─── POLICY ───────────────────────────────
@app.route('/policy')
def policy():
    if 'worker_id' not in session:
        return redirect('/login')
    conn = sqlite3.connect('gigshield.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM workers WHERE id=?', (session['worker_id'],))
    worker = cursor.fetchone()
    conn.close()
    return render_template('policy.html', worker=worker)

# ─── FINANCIAL ────────────────────────────
@app.route('/financial')
def financial():
    if 'worker_id' not in session:
        return redirect('/login')
    conn = sqlite3.connect('gigshield.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM workers')
    total_workers = cursor.fetchone()[0]
    conn.close()
    weekly_premium = total_workers * 40
    expected_claims = total_workers // 10
    total_payouts = expected_claims * 500
    profit = weekly_premium - total_payouts
    return render_template('financial.html',
        total_workers=total_workers,
        weekly_premium=weekly_premium,
        expected_claims=expected_claims,
        total_payouts=total_payouts,
        profit=profit
    )

# ─── TEST WEATHER ─────────────────────────
@app.route('/test-weather')
def test_weather():
    return str(get_delhi_weather())

# ─── RUN ──────────────────────────────────
if __name__ == '__main__':
    create_database()
    app.run(debug=True)