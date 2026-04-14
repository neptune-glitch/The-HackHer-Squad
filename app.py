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
        "Noida": "Delhi",
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

# premium calculator
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
    
    from datetime import date
    today = str(date.today())
    
    # Check 1 - Total claims ever
    cursor.execute(
        'SELECT COUNT(*) FROM claims WHERE worker_id=?',
        (worker_id,)
    )
    total_claims = cursor.fetchone()[0]
    
    # Check 2 - Claims today
    cursor.execute('''
        SELECT COUNT(*) FROM claims 
        WHERE worker_id=? AND date=?
    ''', (worker_id, today))
    today_claims = cursor.fetchone()[0]
    
    # Check 3 - Claims this week
    cursor.execute('''
        SELECT COUNT(*) FROM claims 
        WHERE worker_id=? 
        AND date >= date('now', '-7 days')
    ''', (worker_id,))
    week_claims = cursor.fetchone()[0]
    
    conn.close()
    
    fraud_score = 0
    reasons = []
    
    # Frequency analysis
    if total_claims > 4:
        fraud_score += 40
        reasons.append("High claim frequency ⚠️")
    elif total_claims > 2:
        fraud_score += 20
        reasons.append("Moderate claim frequency 🔍")
    else:
        reasons.append("Normal claim frequency ✅")
    
    # Same day check
    if today_claims > 1:
        fraud_score += 40
        reasons.append("Multiple claims today ⚠️")
    else:
        reasons.append("No duplicate claims today ✅")
    
    # Weekly pattern
    if week_claims > 3:
        fraud_score += 20
        reasons.append("Suspicious weekly pattern ⚠️")
    else:
        reasons.append("Normal weekly pattern ✅")
    
    # Location check (mock)
    reasons.append("Location verified ✅")
    
    if fraud_score >= 60:
        return "REJECTED ❌", fraud_score, reasons
    elif fraud_score >= 30:
        return "UNDER REVIEW 🔍", fraud_score, reasons
    return "APPROVED ✅", fraud_score, reasons

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
    fraud_status, fraud_score, fraud_reasons = fraud_detection(session['worker_id'])
    return render_template('dashboard.html',
        worker=worker,
        weather=weather,
        risk_score=risk_score,
        risk_level=risk_level,
        premium=premium,
        fraud_status=fraud_status,
        fraud_score=fraud_score,
        fraud_reasons=fraud_reasons,
        prediction_confidence=prediction_confidence,
        prediction_message=prediction_message,
        best_time=best_time,
        avoid_time=avoid_time,
        income_loss=income_loss,
        smart_alert=smart_alert,
        claim_triggered=claim_triggered,
        disruption_type=disruption_type
    )
@app.route('/claims')
def claims():
    if 'worker_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect('helix.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM claims WHERE worker_id=?', (session['worker_id'],))
    claim_history = cursor.fetchall()

    cursor.execute('SELECT * FROM workers WHERE id=?', (session['worker_id'],))
    worker = cursor.fetchone()

    conn.close()

    weather = get_delhi_weather(worker[3])
    fraud_status, fraud_score, fraud_reasons = fraud_detection(session['worker_id'])

    claim_triggered = False
    disruption_type = ""

    if weather['rainfall'] > 50:
        claim_triggered = True
        disruption_type = "Heavy Rain"
    elif weather['temp'] > 44:
        claim_triggered = True
        disruption_type = "Extreme Heat"

    return render_template('claims.html',
        claim_history=claim_history,
        worker=worker,
        weather=weather,
        fraud_status=fraud_status,
        fraud_score=fraud_score,
        fraud_reasons=fraud_reasons,
        claim_triggered=claim_triggered,
        disruption_type=disruption_type
    )

@app.route('/policy')
def policy():
    if 'worker_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect('helix.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM workers WHERE id=?', (session['worker_id'],))
    worker = cursor.fetchone()

    conn.close()

    return render_template('policy.html', worker=worker)

@app.route('/financial')
def financial():
    if 'worker_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect('helix.db')
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

# PAYOUT
@app.route('/payout')
def payout():
    if 'worker_id' not in session:
        return redirect('/login')
    
    conn = sqlite3.connect('helix.db')
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM workers WHERE id=?',
        (session['worker_id'],)
    )
    worker = cursor.fetchone()
    conn.close()
    
    weather = get_delhi_weather(worker[3])
    
    disruption_type = ""
    if weather['rainfall'] > 50:
        disruption_type = "Heavy Rain/Flood 🌧️"
    elif weather['temp'] > 44:
        disruption_type = "Extreme Heat 🌡️"
    else:
        disruption_type = "Manual Request"
    
    return render_template('payout.html',
        worker=worker,
        disruption_type=disruption_type
    )

# ADMIN DASHBOARD
@app.route('/admin')
def admin():
    conn = sqlite3.connect('helix.db')
    cursor = conn.cursor()
    
    # Stats
    cursor.execute('SELECT COUNT(*) FROM workers')
    total_workers = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM claims')
    total_claims = cursor.fetchone()[0]
    
    cursor.execute(
        "SELECT COUNT(*) FROM claims WHERE status LIKE '%APPROVED%'"
    )
    approved_claims = cursor.fetchone()[0]
    
    # All data
    cursor.execute('SELECT * FROM workers')
    all_workers = cursor.fetchall()
    
    cursor.execute('SELECT * FROM claims ORDER BY id DESC')
    all_claims = cursor.fetchall()
    
    conn.close()
    
    # Financial
    weekly_premium = total_workers * 40
    total_payouts = approved_claims * 500
    profit = weekly_premium - total_payouts
    
    if weekly_premium > 0:
        loss_ratio = round(total_payouts / weekly_premium * 100, 1)
    else:
        loss_ratio = 0
    
    # Next week prediction
    weather = get_delhi_weather()
    if weather['temp'] > 42:
        next_week_risk = "HIGH 🔴 — Heat wave likely"
    elif weather['rainfall'] > 20:
        next_week_risk = "MEDIUM 🟡 — Rain expected"
    else:
        next_week_risk = "LOW 🟢 — Normal conditions"
    
    return render_template('admin.html',
        total_workers=total_workers,
        total_claims=total_claims,
        approved_claims=approved_claims,
        all_workers=all_workers,
        all_claims=all_claims,
        weekly_premium=weekly_premium,
        total_payouts=total_payouts,
        profit=profit,
        loss_ratio=loss_ratio,
        next_week_risk=next_week_risk,
        weather=weather
    )

# RUN
if __name__ == '__main__':
    create_database()
    app.run(debug=True)
