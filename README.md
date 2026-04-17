# Helix — AI-Powered Predictive Insurance for Gig Workers

> **Team: HackHer Squad | Guidewire DEVTrails 2026**

---

## Problem Statement

E-commerce delivery partners working for platforms like **Amazon and Flipkart** in cities like **Delhi** are the backbone of India's digital economy. External disruptions — severe pollution (smog), extreme heat, and heavy rain/floods — can completely halt their work, causing them to lose **20–30% of their monthly income**.

Currently, gig workers have **no financial safety net** against such uncontrollable events. When disruptions occur, they bear the full loss alone.

---

## Who Is Our User?

**Name:** Ramesh Kumar  
**Age:** 24  
**City:** Delhi  
**Delivery Zones:** Dwarka, Lajpat Nagar, Connaught Place  
**Platform:** Amazon & Flipkart Delivery Partner  
**Device:** Budget Android smartphone (4G)  
**Work Hours:** 9–11 hours/day

Ramesh lives in a rented room and sends money home every week. His income is uncertain and highly dependent on external conditions.

### Real Problems He Faces

- 🌫️ **Winter Smog** — AQI crosses 400 → cannot work → Zero income
- 🌡️ **Extreme Heat** — 45°C+ → unsafe to ride → Zero income
- 🌧️ **Floods** — roads blocked → deliveries stop → Zero income
- 🚫 No savings, no insurance, no backup plan

---

## Our Solution — Helix

**Helix** is a simple web platform where gig workers pay a small weekly premium (₹25–₹60) and receive **automatic income protection** when disruptions prevent them from working.

**No paperwork. No claims process. Fully automated payouts.**

---

## What Makes Helix Intelligent?

Helix is not just reactive — it is **predictive and assistive**.

- 🔮 Predicts disruption risk for the next 24 hours (with confidence %)
- 🧠 Suggests best working hours based on weather conditions
- 💰 Estimates potential income loss before it happens
- 🔍 Explains fraud decisions transparently — no black box

Workers can **plan ahead**, not just react after losing income.

---

## How It Works

1. Worker registers (takes ~2 minutes)
2. Chooses a weekly plan
3. System continuously monitors weather and risk
4. Disruption is detected automatically
5. Claim is triggered instantly
6. Money is credited via UPI

---

## Weekly Premium Model

| Plan | Weekly Premium | Coverage/Day |
|------|---------------|--------------|
| Basic | ₹25 | ₹300 |
| Standard | ₹40 | ₹500 |
| Premium | ₹60 | ₹700 |

Designed around **weekly earning cycles** — affordable for all gig workers.

---

## Parametric Triggers

| Trigger | Condition |
|---------|-----------|
| Smog / Pollution | AQI > 400 |
| Extreme Heat | Temp > 44°C |
| Heavy Rain / Flood | Rainfall > 50mm |
| Flood Alert | Government warning |
| Curfew / Strike | Local shutdown |

---

## AI System Design

### 1. Dynamic Premium Calculation
Premiums are personalized based on zone, season, current weather, and claim history — not a flat rate for everyone.

### 2. Fraud Detection
Multi-signal fraud analysis that goes beyond simple rules:
- Claim frequency analysis
- Same-day duplicate claim detection
- Pattern-based anomaly detection using a Random Forest model
- **Explainable output** — Helix shows *why* a claim is flagged, not just that it was

### 3. Risk Profiling
Each worker receives a dynamic risk score calculated from zone risk, seasonal patterns, and claim behavior. The score updates in real time.

### 4. AI-Powered Predictive Insights

**Disruption Prediction** — forecasts next 24-hour disruption risk with a confidence percentage.

**Smart Work Suggestions** — recommends optimal working hours. Example: *"Work early morning, avoid afternoon heat."*

**Income Loss Prediction** — estimates weekly income at risk before disruptions occur. Example: *"You may lose ₹1,200 this week."*

This transforms Helix from an insurance product into an **AI assistant for gig workers**.

---

## Coverage

| Covered ✅ | Not Covered ❌ |
|-----------|--------------|
| Lost income due to weather | Health / medical |
| Weather-triggered disruptions | Vehicle damage |
| Curfew / strikes | Accidents |

---

## Tech Stack

- **Frontend:** HTML, CSS
- **Backend:** Python, Flask
- **Database:** SQLite
- **Weather & AQI:** OpenWeatherMap API
- **ML Models:** scikit-learn (Random Forest — risk, fraud, premium, login anomaly)
- **Auth:** Flask Sessions, Werkzeug password hashing
- **Payments:** Razorpay (simulated UPI, test mode)

---

## How We Used AI (Transparency)

We used AI as a **tool, not a replacement for thinking**.

**AI-assisted:** Flask boilerplate setup, debugging, structuring documentation.

**Built entirely by our team:** Risk scoring logic, fraud detection with reasoning, weekly premium model, Delhi-specific disruption triggers, and all predictive features (risk forecasting, income loss estimation, work timing suggestions).

Our focus: **AI-assisted decision making + human problem solving.**

---

## Project Evolution

This project was initially submitted in Phase 1 under the name **GigShield**. Based on feedback and our desire to build a more distinct, original, and brandable solution, we rebranded to **Helix** in Phase 2. The name reflects our shift from a generic concept to a more unique, AI-driven, predictive platform.

---

## Team — HackHer Squad

AKTU, Noida | Guidewire DEVTrails 2026

| # | Name |
|---|------|
| 1 | Bharti Pathak |
| 2 | Supriya Verma |
| 3 | Sanjoli Singh |
| 4 | Nandini |

---

## Running Locally

```bash
# Install dependencies
pip install flask requests python-dotenv scikit-learn numpy joblib werkzeug

# Set environment variables
cp .env.example .env
# Add your WEATHER_API_KEY and ADMIN_PASSWORD to .env

# Run the app
python app.py
```

Then open `http://localhost:5000` in your browser.

---

## 🚀 Live Demo

🌐 **Helix Application** is live and deployed on Render:

👉 https://helix-vxg4.onrender.com

## Pitch Deck
https://drive.google.com/file/d/1JXNu2O6F43acMj63AenMPgG3cHupQDV6/view?usp=drive_link

*Built in India 🇮🇳 by HackHer Squad*
