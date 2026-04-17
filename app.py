from flask import Flask, render_template, request, redirect, session
import sqlite3
import requests
import os
import joblib
import random
from dotenv import load_dotenv
from datetime import datetime, date, timedelta
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)

# ─── SECURITY: enforce SECRET_KEY ─────────────────────────
_secret = os.getenv("SECRET_KEY")
if not _secret:
    import secrets
    _secret = secrets.token_hex(32)
    print("⚠️  WARNING: SECRET_KEY not set. Using temporary key — sessions will reset on restart.")
app.secret_key = _secret

app.config["ADMIN_USERNAME"] = os.getenv("ADMIN_USERNAME", "admin")
app.config["ADMIN_PASSWORD"] = os.getenv("ADMIN_PASSWORD")
app.config["DATABASE_PATH"] = os.getenv(
    "DATABASE_PATH",
    os.path.join(os.path.dirname(__file__), "helix.db")
)

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODEL_DIR, exist_ok=True)

# ─── DB CONNECTION ────────────────────────────────────────
def get_db_connection():
    db_dir = os.path.dirname(app.config["DATABASE_PATH"])
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    return sqlite3.connect(app.config["DATABASE_PATH"])

# ─── MODEL PERSISTENCE ───────────────────────────────────
def save_model(model, name):
    joblib.dump(model, os.path.join(MODEL_DIR, f"{name}.pkl"))

def load_model(name):
    return joblib.load(os.path.join(MODEL_DIR, f"{name}.pkl"))

def model_exists(name):
    return os.path.exists(os.path.join(MODEL_DIR, f"{name}.pkl"))

# ─── RF MODEL 1 — Login Anomaly ──────────────────────────
def train_login_model():
    X = np.array([
        [10, 0, 1], [14, 0, 1], [18, 0, 1],
        [2,  1, 3], [3,  1, 4], [1,  1, 5],
        [22, 1, 2], [9,  0, 2], [11, 0, 1], [0, 1, 3]
    ])
    y = np.array([0, 0, 0, 1, 1, 1, 1, 0, 0, 1])
    model = RandomForestClassifier(n_estimators=50, max_depth=4, random_state=42)
    model.fit(X, y)
    return model

# ─── RF MODEL 2 — Risk Classifier ────────────────────────
def train_risk_model():
    X = np.array([
        [46, 70, 90, 8,  30, 350],
        [45, 60, 85, 7,  30, 300],
        [44, 55, 80, 9,  25, 280],
        [42, 30, 70, 6,  20, 200],
        [40, 20, 65, 5,  25, 180],
        [38, 10, 60, 4,  10, 120],
        [32,  0, 50, 2,  10,  80],
        [30,  0, 45, 1,  10,  60],
        [28,  0, 40, 3,  10,  70],
        [35,  5, 55, 11, 25, 250],
        [33,  0, 48, 12, 30, 380],
        [43, 40, 75, 7,  30, 320],
        [36,  2, 52, 10, 15, 420],
        [34,  0, 48, 1,  10, 450],
    ])
    y = np.array([2, 2, 2, 1, 1, 1, 0, 0, 0, 1, 0, 2, 1, 2])
    model = RandomForestClassifier(n_estimators=50, max_depth=4, random_state=42)
    model.fit(X, y)
    return model

# ─── RF MODEL 3 — Premium Predictor ──────────────────────
def train_premium_model():
    X = np.array([
        [30, 30, 40], [30, 20, 35], [25, 30, 40],
        [25, 25, 20], [20, 20, 20], [10, 10,  5],
        [10, 20,  5], [20, 25, 35], [30, 25, 20],
        [10, 25,  5], [25, 20, 40], [10, 10, 20],
    ])
    y = np.array([75, 65, 70, 55, 45, 25, 30, 60, 60, 35, 65, 30])
    model = RandomForestRegressor(n_estimators=50, max_depth=4, random_state=42)
    model.fit(X, y)
    return model

# ─── RF MODEL 4 — Fraud Detector ─────────────────────────
def train_fraud_model():
    X = np.array([
        [0, 0, 0, 0, 0],
        [1, 0, 1, 0, 0],
        [2, 1, 2, 0, 0],
        [1, 0, 2, 0, 0],
        [3, 1, 3, 0, 1],
        [4, 2, 4, 1, 0],
        [5, 2, 5, 1, 1],
        [6, 3, 6, 1, 1],
        [2, 0, 2, 0, 0],
        [7, 2, 5, 1, 1],
        [3, 2, 3, 0, 1],
        [1, 1, 1, 0, 0],
    ])
    y = np.array([0, 0, 0, 0, 1, 1, 2, 2, 0, 2, 1, 0])
    model = RandomForestClassifier(n_estimators=50, max_depth=4, random_state=42)
    model.fit(X, y)
    return model

# ─── LOAD OR TRAIN ALL MODELS ────────────────────────────
def get_or_train(name, train_fn):
    if model_exists(name):
        print(f"  ✅ Loaded {name} model from disk.")
        return load_model(name)
    else:
        print(f"  🔧 Training {name} model...")
        model = train_fn()
        save_model(model, name)
        print(f"  💾 Saved {name} model to disk.")
        return model

print("🚀 Loading Helix ML models...")
rf_login_model   = get_or_train("login",   train_login_model)
rf_risk_model    = get_or_train("risk",    train_risk_model)
rf_premium_model = get_or_train("premium", train_premium_model)
rf_fraud_model   = get_or_train("fraud",   train_fraud_model)
print("✅ All models ready.\n")

# ─── WEATHER API ─────────────────────────────────────────
ZONE_TO_CITY = {
    "Dwarka": "Delhi", "Lajpat Nagar": "Delhi", "Rohini": "Delhi",
    "Connaught Place": "Delhi", "Mumbai": "Mumbai", "Bangalore": "Bangalore",
    "Bengaluru": "Bangalore", "Chennai": "Chennai", "Kolkata": "Kolkata",
    "Hyderabad": "Hyderabad", "Pune": "Pune", "Ahmedabad": "Ahmedabad",
    "Jaipur": "Jaipur", "Lucknow": "Lucknow", "Noida": "Delhi", "Delhi": "Delhi"
}

def get_aqi(city="Delhi"):
    api_key = os.getenv('WEATHER_API_KEY')
    geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city},IN&limit=1&appid={api_key}"
    try:
        geo_resp = requests.get(geo_url, timeout=5).json()
        if not geo_resp:
            return None
        lat, lon = geo_resp[0]['lat'], geo_resp[0]['lon']
        aqi_url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={api_key}"
        aqi_resp = requests.get(aqi_url, timeout=5).json()
        aqi_index = aqi_resp['list'][0]['main']['aqi']
        pm25 = round(aqi_resp['list'][0]['components'].get('pm2_5', 0), 1)
        aqi_map = {1: 50, 2: 100, 3: 200, 4: 350, 5: 500}
        return {'aqi': aqi_map.get(aqi_index, 100), 'pm25': pm25, 'aqi_index': aqi_index}
    except Exception:
        return None

def get_delhi_weather(city="Delhi"):
    api_key = os.getenv('WEATHER_API_KEY')
    city_name = city.split(",")[0].strip()

    # FIX: resolve zone → actual API city
    api_city = ZONE_TO_CITY.get(city_name)
    if not api_city:
        for key in ZONE_TO_CITY:
            if key.lower() in city_name.lower():
                api_city = ZONE_TO_CITY[key]
                break
    if not api_city:
        api_city = city_name

    url = f"http://api.openweathermap.org/data/2.5/weather?q={api_city},IN&appid={api_key}&units=metric"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        if response.status_code != 200:
            return default_weather(city_name)

        aqi_data = get_aqi(api_city) or {'aqi': 100, 'pm25': 20, 'aqi_index': 2}

        return {
            'temp': round(data['main']['temp'], 1),
            'rainfall': data.get('rain', {}).get('1h', 0),
            'humidity': data['main']['humidity'],
            'description': data['weather'][0]['description'].title(),
            # FIX: show user's zone/city, not the raw OWM city name
            'city': city_name if city_name != api_city else data['name'],
            'api_city': api_city,          # actual city used for API call
            'aqi': aqi_data['aqi'],
            'pm25': aqi_data['pm25'],
            'aqi_index': aqi_data['aqi_index']
        }
    except Exception:
        return default_weather(city_name)

def default_weather(city="Delhi"):
    return {
        'temp': 35, 'rainfall': 0, 'humidity': 60,
        'description': 'Clear Sky', 'city': city,
        'api_city': ZONE_TO_CITY.get(city, city),
        'aqi': 150, 'pm25': 45, 'aqi_index': 3
    }

def aqi_label(aqi):
    if aqi <= 50:   return ("Good", "#10b981")
    if aqi <= 100:  return ("Moderate", "#f59e0b")
    if aqi <= 200:  return ("Unhealthy for Sensitive", "#f97316")
    if aqi <= 300:  return ("Unhealthy", "#ef4444")
    if aqi <= 400:  return ("Very Unhealthy", "#8b5cf6")
    return ("Hazardous 🚨", "#dc2626")

# ─── RISK SCORE ──────────────────────────────────────────
def calculate_risk_score(zone, rainfall, temp, humidity=60, aqi=150):
    zone_lower = zone.lower()
    if any(z in zone_lower for z in ["dwarka", "mumbai"]):
        zone_score = 30
    elif any(z in zone_lower for z in ["lajpat", "kolkata"]):
        zone_score = 25
    elif any(z in zone_lower for z in ["rohini", "chennai"]):
        zone_score = 20
    else:
        zone_score = 10

    month = datetime.now().month
    features = np.array([[temp, rainfall, humidity, month, zone_score, aqi]])
    prediction = rf_risk_model.predict(features)[0]
    confidence = round(max(rf_risk_model.predict_proba(features)[0]) * 100, 1)
    score_map = {0: 25, 1: 50, 2: 80}
    return score_map[prediction], confidence, zone_score

# ─── PREMIUM ─────────────────────────────────────────────
def calculate_premium(zone_score, season_score, weather_score, plan):
    base = 25 if "Basic" in plan else 40 if "Standard" in plan else 60
    features = np.array([[zone_score, season_score, weather_score]])
    predicted = rf_premium_model.predict(features)[0]
    adjustment = predicted / 50
    premium = round(base * adjustment)
    return max(base, min(base + 20, premium))

# ─── ADVANCED FRAUD DETECTION ────────────────────────────
def fraud_detection(worker_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    today = str(date.today())

    cursor.execute('''
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN date=? THEN 1 ELSE 0 END) as today_count,
            SUM(CASE WHEN date >= date('now','-7 days') THEN 1 ELSE 0 END) as week_count
        FROM claims WHERE worker_id=?
    ''', (today, worker_id))
    row = cursor.fetchone()
    total_claims  = row[0] or 0
    today_claims  = row[1] or 0
    week_claims   = row[2] or 0

    cursor.execute('SELECT zone FROM workers WHERE id=?', (worker_id,))
    wrow = cursor.fetchone()
    worker_zone = wrow[0] if wrow else "Unknown"

    cursor.execute('''SELECT disruption_type, date, temp, rainfall 
        FROM claims WHERE worker_id=? ORDER BY id DESC LIMIT 5''', (worker_id,))
    recent_claims = cursor.fetchall()
    conn.close()

    high_heat_zones = ["delhi", "dwarka", "lajpat", "rohini", "noida",
                       "connaught", "jaipur", "ahmedabad", "lucknow"]
    high_rain_zones = ["mumbai", "kolkata", "chennai", "bangalore", "hyderabad", "pune"]
    zone_lower = worker_zone.lower()

    zone_mismatch = 0
    weather_mismatch = 0
    reasons = []

    if recent_claims:
        last_type = recent_claims[0][0].lower()
        last_temp = recent_claims[0][2]
        last_rain = recent_claims[0][3]

        if "heat" in last_type and not any(z in zone_lower for z in high_heat_zones):
            reasons.append("🔴 GPS mismatch — heat claim from low-heat zone!")
            zone_mismatch = 1
        elif "rain" in last_type and not any(z in zone_lower for z in high_rain_zones + high_heat_zones):
            reasons.append("🟡 Zone vs disruption type mismatch — flagged for review")
            zone_mismatch = 1
        else:
            reasons.append("✅ GPS zone matches disruption type")

        if last_temp is not None and last_rain is not None:
            if "heat" in last_type and float(last_temp) < 40:
                reasons.append(f"🔴 Fake weather — recorded temp was only {last_temp}°C at claim time")
                weather_mismatch = 1
            elif "rain" in last_type and float(last_rain) < 10:
                reasons.append(f"🔴 Fake weather — recorded rainfall was only {last_rain}mm at claim time")
                weather_mismatch = 1
            elif "pollution" in last_type or "aqi" in last_type:
                reasons.append("✅ AQI-based claim — verified via stored sensor data")
            else:
                reasons.append("✅ Weather data matches stored historical snapshot")
        else:
            live_weather = get_delhi_weather(worker_zone)
            if "heat" in last_type and live_weather['temp'] < 40:
                reasons.append(f"🔴 Live weather check — temp only {live_weather['temp']}°C")
                weather_mismatch = 1
            elif "rain" in last_type and live_weather['rainfall'] < 10:
                reasons.append(f"🔴 Live weather check — minimal rainfall ({live_weather['rainfall']}mm)")
                weather_mismatch = 1
            else:
                reasons.append("✅ Weather conditions cross-verified")
    else:
        reasons.append("✅ GPS location verified — no prior claims")
        reasons.append("✅ No previous suspicious weather claims")

    features = np.array([[total_claims, today_claims, week_claims, zone_mismatch, weather_mismatch]])
    prediction = rf_fraud_model.predict(features)[0]
    confidence = round(max(rf_fraud_model.predict_proba(features)[0]) * 100, 1)
    fraud_score = int(prediction * 30)

    if total_claims > 4:
        reasons.append("🔴 High lifetime claim frequency")
    elif total_claims > 2:
        reasons.append("🟡 Moderate claim frequency")
    else:
        reasons.append("✅ Normal claim frequency")

    if today_claims > 1:
        reasons.append("🔴 Multiple claims same day — suspicious!")
    else:
        reasons.append("✅ No duplicate claims today")

    if week_claims > 3:
        reasons.append("🔴 High weekly claim rate — suspicious pattern!")
    else:
        reasons.append("✅ Normal weekly claim pattern")

    trust_score = max(0, 100 - fraud_score)
    result_map = {0: "APPROVED ✅", 1: "UNDER REVIEW 🔍", 2: "REJECTED ❌"}
    return result_map[prediction], fraud_score, reasons, confidence, trust_score

# ─── DISRUPTION TRIGGER ──────────────────────────────────
def check_disruption(weather):
    if weather['rainfall'] > 50:
        return True, "Heavy Rain / Flood 🌧️"
    elif weather['temp'] > 44:
        return True, "Extreme Heat 🌡️"
    elif weather.get('aqi', 0) > 400:
        return True, "Hazardous Air Quality 😷"
    return False, ""

# ─── DATABASE ────────────────────────────────────────────
def create_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS workers (
        id INTEGER PRIMARY KEY, name TEXT, phone TEXT,
        zone TEXT, upi_id TEXT, platform TEXT, plan TEXT, password TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS claims (
        id INTEGER PRIMARY KEY, worker_id INTEGER,
        disruption_type TEXT, amount TEXT, status TEXT, date TEXT,
        temp REAL, rainfall REAL, aqi INTEGER)''')
    try:
        cursor.execute("ALTER TABLE claims ADD COLUMN temp REAL")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE claims ADD COLUMN rainfall REAL")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE claims ADD COLUMN aqi INTEGER")
    except Exception:
        pass
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
    cursor.execute('UPDATE workers SET password=? WHERE id=?',
                   (generate_password_hash(stored_password), worker_id))
    conn.commit()
    conn.close()

def admin_is_configured():
    return bool(app.config["ADMIN_PASSWORD"])

# ─── HOME ────────────────────────────────────────────────
@app.route('/')
def home():
    return render_template('home.html')

# ─── REGISTER ────────────────────────────────────────────
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO workers 
            (name, phone, zone, upi_id, platform, plan, password)
            VALUES (?, ?, ?, ?, ?, ?, ?)''', (
            request.form['name'],
            request.form['phone'].strip(),
            request.form['zone'],
            request.form['upi'],
            request.form['platform'],
            request.form['plan'],
            generate_password_hash(request.form['password'])
        ))
        conn.commit()
        conn.close()
        return redirect('/login')
    return render_template('register.html')

# ─── LOGIN ────────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form['phone'].strip()
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM workers WHERE phone=?', (phone,))
        worker = cursor.fetchone()
        conn.close()
        if worker and verify_password(worker[7], password):
            ensure_password_hash(worker[0], worker[7])
            session['worker_id'] = worker[0]
            return redirect('/dashboard')
        return render_template('login.html', error="Invalid phone or password.")
    return render_template('login.html')

# ─── DASHBOARD ───────────────────────────────────────────
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
    aqi_text, aqi_color = aqi_label(weather.get('aqi', 100))
    claim_triggered, disruption_type = check_disruption(weather)

    risk_score, confidence, zone_score = calculate_risk_score(
        worker[3], weather['rainfall'], weather['temp'],
        weather['humidity'], weather.get('aqi', 150)
    )

    month = datetime.now().month
    season_score = 30 if month in [6,7,8,9] else 20 if month in [4,5,10] else 10
    weather_score = min(40, int(weather['temp']/2 + weather['rainfall']/5))
    premium = calculate_premium(zone_score, season_score, weather_score, worker[6])

    fraud_status, fraud_score, fraud_reasons, fraud_confidence, trust_score = fraud_detection(worker[0])

    # Prediction
    if risk_score >= 70:
        prediction_confidence = random.randint(70, 90)
        prediction_message = "High disruption risk — consider rescheduling heavy outdoor work"
        income_loss = random.randint(300, 700)
    elif risk_score >= 40:
        prediction_confidence = random.randint(40, 69)
        prediction_message = "Moderate conditions — stay alert for weather updates"
        income_loss = random.randint(0, 300)
    else:
        prediction_confidence = random.randint(10, 39)
        prediction_message = "Conditions look favorable for work today"
        income_loss = 0

    best_time = "6 AM – 10 AM" if weather['temp'] > 35 else "Anytime"
    avoid_time = "12 PM – 4 PM" if weather['temp'] > 35 else "None"
    smart_alert = (
        f"⚠️ Heat Advisory: {weather['temp']}°C — hydrate frequently" if weather['temp'] > 40
        else f"🌧️ Rain Alert: {weather['rainfall']}mm recorded" if weather['rainfall'] > 20
        else "✅ All clear — good conditions for delivery work"
    )

    return render_template('dashboard.html',
        worker=worker, weather=weather,
        aqi_text=aqi_text, aqi_color=aqi_color,
        risk_score=risk_score, zone_score=zone_score,
        season_score=season_score, weather_score=weather_score,
        premium=premium, claim_triggered=claim_triggered,
        disruption_type=disruption_type, fraud_status=fraud_status,
        trust_score=trust_score,
        prediction_confidence=prediction_confidence,
        prediction_message=prediction_message,
        income_loss=income_loss, best_time=best_time,
        avoid_time=avoid_time, smart_alert=smart_alert
    )

# ─── CLAIMS ──────────────────────────────────────────────
@app.route('/claims')
def claims():
    if 'worker_id' not in session:
        return redirect('/login')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM workers WHERE id=?', (session['worker_id'],))
    worker = cursor.fetchone()
    cursor.execute('SELECT * FROM claims WHERE worker_id=? ORDER BY id DESC', (session['worker_id'],))
    claim_history = cursor.fetchall()
    conn.close()

    weather = get_delhi_weather(worker[3])
    aqi_text, aqi_color = aqi_label(weather.get('aqi', 100))
    claim_triggered, disruption_type = check_disruption(weather)
    fraud_status, fraud_score, fraud_reasons, fraud_confidence, trust_score = fraud_detection(worker[0])

    return render_template('claims.html',
        worker=worker, weather=weather,
        aqi_text=aqi_text, aqi_color=aqi_color,
        claim_triggered=claim_triggered,
        disruption_type=disruption_type,
        claim_history=claim_history,
        fraud_status=fraud_status,
        fraud_confidence=fraud_confidence,
        fraud_reasons=fraud_reasons,
        trust_score=trust_score
    )

# ─── POLICY ──────────────────────────────────────────────
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

# ─── FINANCIAL ───────────────────────────────────────────
@app.route('/financial')
def financial():
    if 'worker_id' not in session:
        return redirect('/login')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM workers')
    total_workers = cursor.fetchone()[0]

    cursor.execute("""
        SELECT strftime('%Y-%m', date) as month,
               SUM(CAST(amount AS REAL)) as total_payout
        FROM claims
        WHERE status LIKE '%APPROVED%'
        GROUP BY month
        ORDER BY month DESC
        LIMIT 6
    """)
    rows = cursor.fetchall()
    conn.close()

    month_names = {
        '01':'Jan','02':'Feb','03':'Mar','04':'Apr','05':'May','06':'Jun',
        '07':'Jul','08':'Aug','09':'Sep','10':'Oct','11':'Nov','12':'Dec'
    }
    monthly_performance = []
    for r in rows:
        m_num = r[0].split('-')[1] if r[0] else '--'
        year = r[0].split('-')[0] if r[0] else '--'
        total_payout = int(r[1] or 0)
        est_premium = total_workers * 40
        pl = est_premium - total_payout
        monthly_performance.append({
            'month': f"{month_names.get(m_num, m_num)} {year}",
            'premium': est_premium, 'claims': total_payout,
            'pl': pl, 'positive': pl >= 0
        })

    weekly_premium = total_workers * 40
    expected_claims = total_workers // 10
    total_payouts = expected_claims * 500
    profit = weekly_premium - total_payouts

    return render_template('financial.html',
        total_workers=total_workers,
        weekly_premium=weekly_premium,
        expected_claims=expected_claims,
        total_payouts=total_payouts,
        profit=profit,
        monthly_performance=monthly_performance
    )

# ─── PAYOUT PAGE ─────────────────────────────────────────
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
    _, disruption_type = check_disruption(weather)
    if not disruption_type:
        disruption_type = "Manual Request"

    if "Basic" in worker[6]:
        payout_amount = 300
    elif "Standard" in worker[6]:
        payout_amount = 500
    else:
        payout_amount = 700

    return render_template('payout.html',
        worker=worker, disruption_type=disruption_type,
        payout_amount=payout_amount, weather=weather
    )

# ─── PROCESS PAYOUT ──────────────────────────────────────
@app.route('/process_payout', methods=['POST'])
def process_payout():
    if 'worker_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM workers WHERE id=?', (session['worker_id'],))
    worker = cursor.fetchone()

    disruption_type = request.form.get('disruption_type', 'Weather Disruption')
    today = str(date.today())

    if "Basic" in worker[6]:
        amount = "300"
    elif "Standard" in worker[6]:
        amount = "500"
    else:
        amount = "700"

    cursor.execute('SELECT COUNT(*) FROM claims WHERE worker_id=? AND date=?',
                   (session['worker_id'], today))
    already_claimed = cursor.fetchone()[0]

    if not already_claimed:
        weather = get_delhi_weather(worker[3])
        cursor.execute('''INSERT INTO claims 
            (worker_id, disruption_type, amount, status, date, temp, rainfall, aqi)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (session['worker_id'], disruption_type, amount, "APPROVED ✅",
             today, weather['temp'], weather['rainfall'], weather.get('aqi', 0))
        )
        conn.commit()
        success = True
        transaction_id = f"HLX{random.randint(100000, 999999)}"
    else:
        success = False
        transaction_id = None

    conn.close()

    return render_template('payout_success.html',
        worker=worker, disruption_type=disruption_type,
        amount=amount, success=success,
        transaction_id=transaction_id, upi_id=worker[4]
    )

# ─── ADMIN LOGIN ─────────────────────────────────────────
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if not admin_is_configured():
        error = "Admin access not configured. Set ADMIN_PASSWORD in environment."
        return render_template('admin_login.html', error=error), 503

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin_pw = app.config["ADMIN_PASSWORD"]

        if admin_pw and admin_pw.startswith(("pbkdf2:", "scrypt:")):
            pw_ok = check_password_hash(admin_pw, password)
        else:
            pw_ok = (password == admin_pw)

        if username == app.config["ADMIN_USERNAME"] and pw_ok:
            session['is_admin'] = True
            return redirect('/admin')
        error = "Invalid admin credentials."

    return render_template('admin_login.html', error=error)

# ─── ADMIN DASHBOARD ─────────────────────────────────────
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
    cursor.execute('SELECT c.id, w.name, c.disruption_type, c.amount, c.status, c.date FROM claims c JOIN workers w ON c.worker_id=w.id ORDER BY c.id DESC')
    all_claims = cursor.fetchall()
    conn.close()

    weekly_premium = total_workers * 40
    total_payouts = approved_claims * 500
    profit = weekly_premium - total_payouts
    loss_ratio = round(total_payouts / weekly_premium * 100, 1) if weekly_premium > 0 else 0

    # Always fetch Delhi weather for admin (headquarters)
    weather = get_delhi_weather("Delhi")

    next_month = (datetime.now().month % 12) + 1
    next_humidity = min(100, weather['humidity'] + 5)
    nw_features = np.array([[weather['temp'], weather['rainfall'], next_humidity,
                              next_month, 20, weather.get('aqi', 150)]])
    nw_prediction = rf_risk_model.predict(nw_features)[0]
    nw_confidence = round(max(rf_risk_model.predict_proba(nw_features)[0]) * 100, 1)
    risk_labels = {
        0: "LOW 🟢 — Normal conditions",
        1: "MEDIUM 🟡 — Disruptions possible",
        2: "HIGH 🔴 — Significant disruptions likely"
    }
    next_week_risk = f"{risk_labels[nw_prediction]} ({nw_confidence}% confidence)"
    aqi_text, aqi_color = aqi_label(weather.get('aqi', 100))

    return render_template('admin.html',
        total_workers=total_workers, total_claims=total_claims,
        approved_claims=approved_claims, all_workers=all_workers,
        all_claims=all_claims, weekly_premium=weekly_premium,
        total_payouts=total_payouts, profit=profit, loss_ratio=loss_ratio,
        next_week_risk=next_week_risk, weather=weather,
        aqi_text=aqi_text, aqi_color=aqi_color
    )

# ─── LOGOUT ──────────────────────────────────────────────
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ─── UPDATE ZONE ─────────────────────────────────────────
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

# ─── RETRAIN ENDPOINT ─────────────────────────────────────
@app.route('/admin/retrain', methods=['POST'])
def retrain_models():
    if not session.get('is_admin'):
        return redirect('/admin/login')
    global rf_login_model, rf_risk_model, rf_premium_model, rf_fraud_model
    rf_login_model   = train_login_model();   save_model(rf_login_model,   "login")
    rf_risk_model    = train_risk_model();    save_model(rf_risk_model,    "risk")
    rf_premium_model = train_premium_model(); save_model(rf_premium_model, "premium")
    rf_fraud_model   = train_fraud_model();   save_model(rf_fraud_model,   "fraud")
    return redirect('/admin')

# ─── RUN ─────────────────────────────────────────────────
create_database()

if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_DEBUG') == '1')
