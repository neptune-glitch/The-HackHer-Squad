from flask import Flask, render_template, request, redirect, session
import sqlite3
import requests
import os
from dotenv import load_dotenv
from datetime import datetime
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback_secret")
app.config["ADMIN_USERNAME"] = os.getenv("ADMIN_USERNAME", "admin")
app.config["ADMIN_PASSWORD"] = os.getenv("ADMIN_PASSWORD")
app.config["DATABASE_PATH"] = os.getenv(
    "DATABASE_PATH",
    os.path.join(app.instance_path, "helix.db")
)

def get_db_connection():
    db_dir = os.path.dirname(app.config["DATABASE_PATH"])
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    return sqlite3.connect(app.config["DATABASE_PATH"])

# ─── RANDOM FOREST MODEL 1 — Login Anomaly ────────────────
def train_login_model():
    X = np.array([
        [10, 0, 1],
        [14, 0, 1],
        [18, 0, 1],
        [2,  1, 3],
        [3,  1, 4],
        [1,  1, 5],
        [22, 1, 2],
        [9,  0, 2],
        [11, 0, 1],
        [0,  1, 3]
    ])
    y = np.array([0, 0, 0, 1, 1, 1, 1, 0, 0, 1])
    model = RandomForestClassifier(n_estimators=10, max_depth=3, random_state=42)
    model.fit(X, y)
    return model

# ─── RANDOM FOREST MODEL 2 — Risk Classifier ──────────────
def train_risk_model():
    # Features: [temp, rainfall, humidity, month, zone_score]
    X = np.array([
        [46, 70, 90, 8,  30],
        [45, 60, 85, 7,  30],
        [44, 55, 80, 9,  25],
        [42, 30, 70, 6,  20],
        [40, 20, 65, 5,  25],
        [38, 10, 60, 4,  10],
        [32,  0, 50, 2,  10],
        [30,  0, 45, 1,  10],
        [28,  0, 40, 3,  10],
        [35,  5, 55, 11, 25],
        [33,  0, 48, 12, 30],
        [43, 40, 75, 7,  30],
    ])
    # 0=LOW, 1=MEDIUM, 2=HIGH
    y = np.array([2, 2, 2, 1, 1, 1, 0, 0, 0, 1, 0, 2])
    model = RandomForestClassifier(n_estimators=10, max_depth=3, random_state=42)
    model.fit(X, y)
    return model

# ─── RANDOM FOREST MODEL 3 — Premium Predictor ────────────
def train_premium_model():
    # Features: [zone_score, season_score, weather_score]
    X = np.array([
        [30, 30, 40],
        [30, 20, 35],
        [25, 30, 40],
        [25, 25, 20],
        [20, 20, 20],
        [10, 10,  5],
        [10, 20,  5],
        [20, 25, 35],
        [30, 25, 20],
        [10, 25,  5],
        [25, 20, 40],
        [10, 10, 20],
    ])
    y = np.array([75, 65, 70, 55, 45, 25, 30, 60, 60, 35, 65, 30])
    model = RandomForestRegressor(n_estimators=10, max_depth=3, random_state=42)
    model.fit(X, y)
    return model

# ─── RANDOM FOREST MODEL 4 — Fraud Detector ───────────────
def train_fraud_model():
    # Features: [total_claims, today_claims, week_claims]
    X = np.array([
        [0, 0, 0],
        [1, 0, 1],
        [2, 1, 2],
        [1, 0, 2],
        [3, 1, 3],
        [4, 2, 4],
        [5, 2, 5],
        [6, 3, 6],
        [2, 0, 2],
        [7, 2, 5],
        [3, 2, 3],
        [1, 1, 1],
    ])
    # 0=NORMAL, 1=REVIEW, 2=FRAUD
    y = np.array([0, 0, 0, 0, 1, 1, 2, 2, 0, 2, 1, 0])
    model = RandomForestClassifier(n_estimators=10, max_depth=3, random_state=42)
    model.fit(X, y)
    return model

# Train all models at startup
print("Training Random Forest models...")
rf_login_model   = train_login_model()
rf_risk_model    = train_risk_model()
rf_premium_model = train_premium_model()
rf_fraud_model   = train_fraud_model()
print("All 4 Random Forest models trained.")

# ─── WEATHER ──────────────────────────────────────────────
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

    api_city = zone_to_city.get(city_name, None)
    if not api_city:
        for key in zone_to_city:
            if key.lower() in city_name.lower():
                api_city = zone_to_city[key]
                break
    if not api_city:
        api_city = city_name

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
    except (requests.RequestException, ValueError, KeyError, TypeError):
        return default_weather(city_name)

def default_weather(city="Delhi"):
    return {
        'temp': 35,
        'rainfall': 0,
        'humidity': 60,
        'description': 'Clear sky',
        'city': city
    }

# ─── RF RISK SCORE ────────────────────────────────────────
def calculate_risk_score(zone, rainfall, temp, humidity=60):
    zone_lower = zone.lower()
    if "dwarka" in zone_lower or "mumbai" in zone_lower:
        zone_score = 30
    elif "lajpat" in zone_lower or "kolkata" in zone_lower:
        zone_score = 25
    elif "rohini" in zone_lower or "chennai" in zone_lower:
        zone_score = 20
    else:
        zone_score = 10

    month = datetime.now().month

    features = np.array([[temp, rainfall, humidity, month, zone_score]])
    prediction = rf_risk_model.predict(features)[0]
    confidence = round(max(rf_risk_model.predict_proba(features)[0]) * 100, 1)

    score_map = {0: 25, 1: 50, 2: 80}
    return score_map[prediction], confidence, zone_score

# ─── RF PREMIUM ───────────────────────────────────────────
def calculate_premium(zone_score, season_score, weather_score, plan):
    if "Basic" in plan:
        base = 25
    elif "Standard" in plan:
        base = 40
    else:
        base = 60

    features = np.array([[zone_score, season_score, weather_score]])
    predicted = rf_premium_model.predict(features)[0]
    adjustment = predicted / 50
    premium = round(base * adjustment)
    return max(base, min(base + 20, premium))

# ─── RF FRAUD DETECTION ───────────────────────────────────
def fraud_detection(worker_id):
    from datetime import date
    conn = get_db_connection()
    cursor = conn.cursor()
    today = str(date.today())

    cursor.execute('SELECT COUNT(*) FROM claims WHERE worker_id=?', (worker_id,))
    total_claims = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM claims WHERE worker_id=? AND date=?', (worker_id, today))
    today_claims = cursor.fetchone()[0]

    cursor.execute('''SELECT COUNT(*) FROM claims 
        WHERE worker_id=? AND date >= date('now', '-7 days')''', (worker_id,))
    week_claims = cursor.fetchone()[0]

    conn.close()

    features = np.array([[total_claims, today_claims, week_claims]])
    prediction = rf_fraud_model.predict(features)[0]
    confidence = round(max(rf_fraud_model.predict_proba(features)[0]) * 100, 1)

    reasons = []
    if total_claims > 4:
        reasons.append("High claim frequency ⚠️")
    else:
        reasons.append("Normal claim frequency ✅")

    if today_claims > 1:
        reasons.append("Multiple claims today ⚠️")
    else:
        reasons.append("No duplicate claims today ✅")

    if week_claims > 3:
        reasons.append("Suspicious weekly pattern ⚠️")
    else:
        reasons.append("Normal weekly pattern ✅")

    reasons.append("Location verified ✅")

    result_map = {0: "APPROVED ✅", 1: "UNDER REVIEW 🔍", 2: "REJECTED ❌"}
    fraud_score = int(prediction * 30)

    return result_map[prediction], fraud_score, reasons, confidence

# ─── DATABASE ─────────────────────────────────────────────
def create_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS workers (
        id INTEGER PRIMARY KEY, name TEXT, phone TEXT,
        zone TEXT, upi_id TEXT, platform TEXT, plan TEXT, password TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS claims (
        id INTEGER PRIMARY KEY, worker_id INTEGER,
        disruption_type TEXT, amount TEXT, status TEXT, date TEXT)''')
    conn.commit()
    conn.close()

def verify_password(stored_password, provided_password):
    if not stored_password:
        return False
    if stored_password.startswith(("pbkdf2:", "scrypt:")):
        return check_password_hash(stored_password, provided_password)
    return stored_password == provided_password

def ensure_password_hash(worker_id, stored_password):
    if not stored_password or stored_password.startswith(("pbkdf2:", "scrypt:")):
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE workers SET password=? WHERE id=?',
        (generate_password_hash(stored_password), worker_id)
    )
    conn.commit()
    conn.close()

def admin_is_configured():
    return bool(app.config["ADMIN_PASSWORD"])

# ─── HOME ─────────────────────────────────────────────────
@app.route('/')
def home():
    return render_template('home.html')

# ─── REGISTER ─────────────────────────────────────────────
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO workers 
            (name, phone, zone, upi_id, platform, plan, password)
            VALUES (?, ?, ?, ?, ?, ?, ?)''', (
            request.form['name'], request.form['phone'],
            request.form['zone'], request.form['upi'],
            request.form['platform'], request.form['plan'],
            generate_password_hash(request.form['password'])
        ))
        conn.commit()
        conn.close()
        return redirect('/login')
    return render_template('register.html')

# ─── LOGIN with RF Anomaly Detection ──────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form['phone']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM workers WHERE phone=?',
            (phone,)
        )
        worker = cursor.fetchone()
        conn.close()

        failed_attempts = session.get('failed_login_attempts', 0)
        if not worker or not verify_password(worker[7], password):
            session['failed_login_attempts'] = failed_attempts + 1
            return "Invalid login"

        ensure_password_hash(worker[0], worker[7])

        # RF Login Anomaly Check
        login_hour = datetime.now().hour
        is_night = 1 if login_hour < 6 or login_hour > 22 else 0
        attempts = max(1, failed_attempts)

        features = np.array([[login_hour, is_night, attempts]])
        prediction = rf_login_model.predict(features)[0]
        confidence = int(max(rf_login_model.predict_proba(features)[0]) * 100)

        if prediction == 1 and failed_attempts >= 3:
            return f"⚠️ Suspicious login detected ({confidence}% risk). Try again later."

        session['worker_id'] = worker[0]
        session['failed_login_attempts'] = 0
        return redirect('/dashboard')

    return render_template('login.html')

# ─── LOGOUT ───────────────────────────────────────────────
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = None

    if not admin_is_configured():
        error = "Admin access is not configured. Set ADMIN_PASSWORD in your environment."
        return render_template('admin_login.html', error=error), 503

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if (
            username == app.config["ADMIN_USERNAME"]
            and password == app.config["ADMIN_PASSWORD"]
        ):
            session['is_admin'] = True
            return redirect('/admin')

        error = "Invalid admin credentials."

    return render_template('admin_login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ─── UPDATE ZONE ──────────────────────────────────────────
@app.route('/update_zone', methods=['POST'])
def update_zone():
    if 'worker_id' not in session:
        return redirect('/login')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE workers SET zone=? WHERE id=?',
        (request.form['zone'], session['worker_id']))
    conn.commit()
    conn.close()
    return redirect('/dashboard')

# ─── DASHBOARD ────────────────────────────────────────────
@app.route('/dashboard')
def dashboard():
    if 'worker_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM workers WHERE id=?', (session['worker_id'],))
    worker = cursor.fetchone()
    conn.close()

    weather = get_delhi_weather(worker[3])

    # RF Risk Score
    risk_score, risk_confidence, zone_score = calculate_risk_score(
        worker[3], weather['rainfall'], weather['temp'], weather['humidity']
    )
    risk_level = "HIGH 🔴" if risk_score >= 70 else "MEDIUM 🟡" if risk_score >= 40 else "LOW 🟢"

    # Season score
    month = datetime.now().month
    if month in [7, 8, 9]:
        season_score = 30
        season_name = "Monsoon 🌧️"
    elif month in [4, 5, 6]:
        season_score = 20
        season_name = "Summer 🌡️"
    elif month in [11, 12, 1]:
        season_score = 25
        season_name = "Winter ❄️"
    else:
        season_score = 10
        season_name = "Normal 🌤️"

    # Weather score
    if weather['rainfall'] > 50:
        weather_score = 40
    elif weather['temp'] > 44:
        weather_score = 35
    elif weather['temp'] > 40:
        weather_score = 20
    else:
        weather_score = 5

    # RF Premium
    premium = calculate_premium(zone_score, season_score, weather_score, worker[6])

    # AI Prediction
    prediction_confidence = min(95, risk_score + 10)
    if risk_score >= 70:
        prediction_message = "⚠️ High disruption likely!"
        best_time = "5:00 AM – 9:00 AM"
        avoid_time = "12:00 PM – 4:00 PM"
        income_loss = round(weather['temp'] * 15) if weather['temp'] > 35 else 0
        smart_alert = f"🌡️ Temperature {weather['temp']}°C detected. Stay safe!"
    elif risk_score >= 40:
        prediction_message = "🟡 Moderate disruption possible"
        best_time = "6:00 AM – 11:00 AM"
        avoid_time = "2:00 PM – 5:00 PM"
        income_loss = round(weather['temp'] * 5) if weather['temp'] > 38 else 0
        smart_alert = f"☁️ Weather uncertain in {weather['city']}"
    else:
        prediction_message = "✅ Low disruption chance"
        best_time = "All day safe ✅"
        avoid_time = "None"
        income_loss = 0
        smart_alert = f"✅ Great weather in {weather['city']}!"

    # Claim trigger
    claim_triggered = False
    disruption_type = ""
    if weather['rainfall'] > 50:
        claim_triggered = True
        disruption_type = "Heavy Rain 🌧️"
    elif weather['temp'] > 44:
        claim_triggered = True
        disruption_type = "Extreme Heat 🌡️"

    # RF Fraud
    fraud_status, fraud_score, fraud_reasons, fraud_confidence = fraud_detection(session['worker_id'])

    return render_template('dashboard.html',
        worker=worker,
        weather=weather,
        risk_score=risk_score,
        risk_level=risk_level,
        risk_confidence=risk_confidence,
        zone_score=zone_score,
        season_score=season_score,
        weather_score=weather_score,
        season_name=season_name,
        premium=premium,
        fraud_status=fraud_status,
        fraud_score=fraud_score,
        fraud_reasons=fraud_reasons,
        fraud_confidence=fraud_confidence,
        prediction_confidence=prediction_confidence,
        prediction_message=prediction_message,
        best_time=best_time,
        avoid_time=avoid_time,
        income_loss=income_loss,
        smart_alert=smart_alert,
        claim_triggered=claim_triggered,
        disruption_type=disruption_type
    )

# ─── CLAIMS ───────────────────────────────────────────────
@app.route('/claims')
def claims():
    if 'worker_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM claims WHERE worker_id=?', (session['worker_id'],))
    claim_history = cursor.fetchall()
    cursor.execute('SELECT * FROM workers WHERE id=?', (session['worker_id'],))
    worker = cursor.fetchone()
    conn.close()

    weather = get_delhi_weather(worker[3])
    fraud_status, fraud_score, fraud_reasons, fraud_confidence = fraud_detection(session['worker_id'])

    claim_triggered = False
    disruption_type = ""
    if weather['rainfall'] > 50:
        claim_triggered = True
        disruption_type = "Heavy Rain 🌧️"
    elif weather['temp'] > 44:
        claim_triggered = True
        disruption_type = "Extreme Heat 🌡️"

    return render_template('claims.html',
        claim_history=claim_history,
        worker=worker,
        weather=weather,
        fraud_status=fraud_status,
        fraud_score=fraud_score,
        fraud_reasons=fraud_reasons,
        fraud_confidence=fraud_confidence,
        claim_triggered=claim_triggered,
        disruption_type=disruption_type
    )

# ─── POLICY ───────────────────────────────────────────────
@app.route('/policy')
def policy():
    if 'worker_id' not in session:
        return redirect('/login')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM workers WHERE id=?', (session['worker_id'],))
    worker = cursor.fetchone()
    conn.close()
    return render_template('policy.html', worker=worker)

# ─── FINANCIAL ────────────────────────────────────────────
@app.route('/financial')
def financial():
    if 'worker_id' not in session:
        return redirect('/login')
    conn = get_db_connection()
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

# ─── PAYOUT ───────────────────────────────────────────────
@app.route('/payout')
def payout():
    if 'worker_id' not in session:
        return redirect('/login')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM workers WHERE id=?', (session['worker_id'],))
    worker = cursor.fetchone()
    conn.close()

    weather = get_delhi_weather(worker[3])
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

# ─── ADMIN ────────────────────────────────────────────────
@app.route('/admin')
def admin():
    if not session.get('is_admin'):
        return redirect('/admin/login')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM workers')
    total_workers = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM claims')
    total_claims = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM claims WHERE status LIKE '%APPROVED%'")
    approved_claims = cursor.fetchone()[0]

    cursor.execute('SELECT * FROM workers')
    all_workers = cursor.fetchall()

    cursor.execute('SELECT * FROM claims ORDER BY id DESC')
    all_claims = cursor.fetchall()

    conn.close()

    weekly_premium = total_workers * 40
    total_payouts = approved_claims * 500
    profit = weekly_premium - total_payouts
    loss_ratio = round(total_payouts / weekly_premium * 100, 1) if weekly_premium > 0 else 0

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

# ─── RUN ──────────────────────────────────────────────────
create_database()

if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_DEBUG') == '1')
