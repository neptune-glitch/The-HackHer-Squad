from flask import Flask, render_template, request, redirect, session
import sqlite3
import requests
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback_secret")

# ---------------- WEATHER ----------------
def get_delhi_weather(city="Delhi"):
    api_key = os.getenv('WEATHER_API_KEY')

    city_name = city.split(",")[0].strip()

    zone_to_city = {
        "Dwarka": "Delhi",
        "Lajpat Nagar": "Delhi",
        "Rohini": "Delhi",
        "Connaught Place": "Delhi",
        "Mumbai": "Mumbai",
        "Bangalore": "Bangalore",
        "Bengaluru": "Bangalore",
        "Chennai": "Chennai",
        "Kolkata": "Kolkata",
        "Hyderabad": "Hyderabad",
        "Pune": "Pune",
        "Ahmedabad": "Ahmedabad",
        "Jaipur": "Jaipur",
        "Lucknow": "Lucknow",
        "Noida": "Noida",
        "Delhi": "Delhi"
    }

    api_city = zone_to_city.get(city_name, city_name)

    url = f"http://api.openweathermap.org/data/2.5/weather?q={api_city},IN&appid={api_key}&units=metric"

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
            'city': data['name']
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

# ---------------- RISK ----------------
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

# ---------------- PREMIUM ----------------
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

# ---------------- FRAUD ----------------
def fraud_detection(worker_id):
    conn = sqlite3.connect('helix.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM claims WHERE worker_id=?', (worker_id,))
    count = cursor.fetchone()[0]
    conn.close()

    if count > 4:
        return "REJECTED ❌", 50
    elif count > 2:
        return "UNDER REVIEW 🔍", 25
    return "APPROVED ✅", 0

# ---------------- DB ----------------
def create_database():
    conn = sqlite3.connect('helix.db')
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

# ---------------- ROUTES ----------------
@app.route('/')
def home():
    return render_template('home.html')

# REGISTER
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        conn = sqlite3.connect('helix.db')
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

# LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        conn = sqlite3.connect('helix.db')
        cursor = conn.cursor()

        cursor.execute(
            'SELECT * FROM workers WHERE phone=? AND password=?',
            (request.form['phone'], request.form['password'])
        )

        worker = cursor.fetchone()
        conn.close()

        if worker:
            session['worker_id'] = worker[0]
            return redirect('/dashboard')

        return "Invalid login"

    return render_template('login.html')

# LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# UPDATE ZONE
@app.route('/update_zone', methods=['POST'])
def update_zone():
    if 'worker_id' not in session:
        return redirect('/login')

    new_zone = request.form['zone']

    conn = sqlite3.connect('helix.db')
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE workers SET zone=? WHERE id=?',
        (new_zone, session['worker_id'])
    )
    conn.commit()
    conn.close()

    return redirect('/dashboard')

# DASHBOARD
@app.route('/dashboard')
def dashboard():
    if 'worker_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect('helix.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM workers WHERE id=?', (session['worker_id'],))
    worker = cursor.fetchone()
    conn.close()

    weather = get_delhi_weather(worker[3])

    # RISK
    risk_score = calculate_risk_score(worker[3], weather['rainfall'], weather['temp'])
    risk_level = "HIGH 🔴" if risk_score >= 70 else "MEDIUM 🟡" if risk_score >= 40 else "LOW 🟢"
    premium = calculate_premium(risk_score, worker[6])

    # AI PREDICTION
    prediction_confidence = min(95, risk_score + 10)

    if risk_score >= 70:
        prediction_message = "⚠️ High disruption likely!"
        best_time = "5:00 AM – 9:00 AM"
        avoid_time = "12:00 PM – 4:00 PM"
        income_loss = round(weather['temp'] * 15) if weather['temp'] > 35 else 0
        smart_alert = f"🌡️ Temperature {weather['temp']}°C detected"
    elif risk_score >= 40:
        prediction_message = "🟡 Moderate disruption possible"
        best_time = "6:00 AM – 11:00 AM"
        avoid_time = "2:00 PM – 5:00 PM"
        income_loss = round(weather['temp'] * 5) if weather['temp'] > 38 else 0
        smart_alert = f"☁️ Weather uncertain in {weather['city']}"
    else:
        prediction_message = "✅ Low disruption chance"
        best_time = "All day safe"
        avoid_time = "None"
        income_loss = 0
        smart_alert = f"✅ Great weather in {weather['city']}"

    # CLAIM
    claim_triggered = False
    disruption_type = ""

    if weather['rainfall'] > 50:
        claim_triggered = True
        disruption_type = "Heavy Rain"
    elif weather['temp'] > 44:
        claim_triggered = True
        disruption_type = "Extreme Heat"

    # FRAUD
    fraud_status, fraud_score = fraud_detection(session['worker_id'])

    return render_template('dashboard.html',
        worker=worker,
        weather=weather,
        risk_score=risk_score,
        risk_level=risk_level,
        premium=premium,
        fraud_status=fraud_status,
        fraud_score=fraud_score,
        prediction_confidence=prediction_confidence,
        prediction_message=prediction_message,
        best_time=best_time,
        avoid_time=avoid_time,
        income_loss=income_loss,
        smart_alert=smart_alert,
        claim_triggered=claim_triggered,
        disruption_type=disruption_type
    )

# RUN
if __name__ == '__main__':
    create_database()
    app.run(debug=True)