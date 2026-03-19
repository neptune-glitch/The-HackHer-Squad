# 🛡️ GigShield — AI-Powered Parametric Insurance for E-Commerce Delivery Partners

> **Team: HackHer Squad | Guidewire DEVTrails 2026**

---

## 👤 Who Is Our User REALLY?

**Name:** Ramesh Kumar
**Age:** 26 years old
**City:** Lucknow, Uttar Pradesh
**Platform:** Amazon & Flipkart Delivery Partner
**Device:** Android smartphone (budget phone, 3G/4G)
**Education:** 12th pass
**Work Hours:** 8–10 hours/day, 6 days a week
**Daily Earnings:** ₹600–₹900/day (depends on number of deliveries)
**Weekly Earnings:** ₹3,600–₹5,400/week
**How He Gets Paid:** Weekly UPI transfer from Amazon/Flipkart

### Ramesh's Real Life Problem:
Ramesh wakes up every morning not knowing if he will earn today.
- If it rains heavily → roads are flooded → he cannot deliver → **zero income**
- If there is a local strike or bandh → he cannot reach pickup point → **zero income**
- If extreme heat (45°C+) → unsafe to ride → he stays home → **zero income**
- He has **no savings**, **no insurance**, **no safety net**
- At end of month he is short on rent, food, and EMI payments

### Why Existing Insurance Doesn't Work for Ramesh:
- Traditional insurance is **monthly** — Ramesh thinks and earns **weekly**
- Claims require **paperwork and documents** — Ramesh has no time for that
- Most insurance covers **health or vehicle** — not his **lost daily wages**
- Premium is too **expensive** for his income level

---

## 💡 Our Solution — GigShield

**GigShield** is a simple web platform where Ramesh pays a small weekly premium (₹25–₹60) and gets automatic income protection when external disruptions stop him from working.

**No paperwork. No phone calls. Money directly in his UPI wallet.**

---

## 🔄 How The App Works — Step by Step

### Step 1 — Ramesh Registers (2 minutes)
- Opens GigShield on his phone browser
- Enters: Name, Phone Number, City, Delivery Zone, UPI ID
- Selects his platform: Amazon or Flipkart
- AI creates his risk profile automatically

### Step 2 — He Picks a Weekly Plan
- Sees 3 plan options (Basic / Standard / Premium)
- AI shows him a personalized price based on his zone
- He pays weekly premium via UPI (₹25–₹60/week)
- Coverage starts immediately

### Step 3 — System Monitors 24/7
- GigShield checks weather, AQI, news every 30 minutes
- Monitors Ramesh's delivery zone specifically
- No action needed from Ramesh

### Step 4 — Disruption Happens
- Example: Heavy rain hits Lucknow at 8am
- Rainfall crosses 50mm threshold
- System automatically detects this

### Step 5 — Claim Auto-Triggered
- System checks: Is Ramesh's policy active? ✅
- System checks: Is disruption in his zone? ✅
- System checks: Is this a genuine claim? ✅ (AI fraud check)
- Claim is approved in under 2 minutes

### Step 6 — Money Reaches Ramesh
- ₹500 credited to his UPI instantly
- He gets SMS + app notification
- He didn't fill any form. He didn't call anyone.

---

## 💰 Weekly Premium Model

| Plan | Weekly Premium | Coverage Per Disruption Day | Max Days Covered/Week |
|------|---------------|----------------------------|-----------------------|
| Basic | ₹25/week | ₹300/day | 2 days |
| Standard | ₹40/week | ₹500/day | 2 days |
| Premium | ₹60/week | ₹700/day | 2 days |

### Why Weekly Pricing?
- Ramesh gets paid weekly by Amazon/Flipkart
- He cannot commit to monthly payments
- Weekly model matches his income cycle perfectly
- He can pause or renew every week based on his situation

---

## ⚡ Parametric Triggers — Exactly How Claims Fire

These are the 5 automated triggers we will build:

| Trigger | Exact Condition | API Used |
|---------|----------------|----------|
| Heavy Rain | Rainfall > 50mm in 6 hours in worker's zone | OpenWeatherMap API (free tier) |
| Extreme Heat | Temperature > 44°C for 4+ continuous hours | OpenWeatherMap API (free tier) |
| Severe Flood | Flood alert issued for worker's district | Mock Government Alert API |
| Local Curfew / Bandh | Curfew declared in worker's city zone | Mock News API |
| Hazardous Pollution | AQI > 400 in worker's area | CPCB Mock API |

**Important:** Claim fires ONLY when the disruption is in the worker's registered delivery zone. Not citywide. Zone-specific.

---

## 🤖 How Our AI REALLY Works

### AI Feature 1 — Dynamic Premium Calculation

**What goes IN:**
- Worker's delivery zone (example: Hazratganj, Lucknow)
- Historical disruption frequency of that zone (last 12 months)
- Season / month (monsoon = higher risk)
- Worker's claim history (honest workers get discount)
- Weather forecast for next 7 days

**What comes OUT:**
- A personalized weekly premium price for that worker

**Simple Example:**
- Ramesh works in Hazratganj zone — historically floods every monsoon
- It is July (peak monsoon month)
- AI calculates: Base ₹40 + Zone risk ₹10 + Season risk ₹5 = **₹55/week**
- Another worker in a safer zone gets: Base ₹40 - Safe zone ₹10 = **₹30/week**

**Algorithm We Will Use:**
- Rule-based scoring model (Phase 1 & 2)
- Upgrade to Linear Regression model (Phase 3)
- Training data: Mock historical weather + disruption dataset

---

### AI Feature 2 — Fraud Detection

**Problem:** Some workers might try to fake claims.

**How We Detect Fraud — 4 Checks:**

**Check 1 — GPS Location Check**
- When disruption is detected, system checks if worker's last known location is inside the affected zone
- If worker is in a different city → claim rejected

**Check 2 — Platform Activity Check**
- System checks if worker actually had deliveries scheduled that day
- If worker had no active orders → suspicious → flagged for review

**Check 3 — Duplicate Claim Check**
- One claim allowed per disruption event per worker
- If same worker tries to claim twice for same rain event → auto rejected

**Check 4 — Pattern Analysis**
- If a worker claims every single week for 8 weeks straight → flagged as suspicious
- Normal workers don't face disruptions every single week

**Result:** Each claim gets a Fraud Risk Score (0–100)
- 0–30 = Low risk → Auto approved ✅
- 31–60 = Medium risk → Manual review 🔍
- 61–100 = High risk → Rejected ❌

---

### AI Feature 3 — Risk Profiling

Every worker gets a Risk Score when they register:

| Factor | Low Risk | High Risk |
|--------|----------|-----------|
| Delivery Zone | Rarely floods | Flood-prone area |
| Season | Winter/Summer | Monsoon |
| Claim History | No past fraud | Suspicious patterns |
| Work Hours | Daytime only | Night shifts in bad weather |

Risk score determines:
- Their weekly premium amount
- Their maximum coverage limit

---

## 🖥️ Platform — Web App

**Why Web and not Mobile App?**
- Ramesh uses a budget Android phone with low storage
- He cannot install another app
- Web app opens directly in his Chrome browser
- Works on 3G/4G connection
- No download needed → more workers will use it

---

## 🛠️ Tech Stack — How We Will Build It

| Layer | Technology | Why We Chose It |
|-------|-----------|-----------------|
| Frontend | React.js + Tailwind CSS | Fast UI, mobile-friendly |
| Backend | Node.js + Express.js | Lightweight, fast API |
| Database | MongoDB | Flexible data storage |
| AI/ML | Python + scikit-learn | Easy ML model building |
| Weather API | OpenWeatherMap (free tier) | Free, accurate, real-time |
| Payment | Razorpay Test Mode | UPI simulation for demo |
| Hosting | Vercel + Render | Free hosting for hackathon |
| Authentication | JWT Tokens | Secure login system |

---

## 📅 Development Plan — Who Builds What

### Phase 1 (March 4–20) — Ideation ✅
- Research and persona definition ✅
- Weekly premium model design ✅
- README documentation ✅

### Phase 2 (March 21–April 4) — Core Building
- Worker registration and login system
- AI risk profiling module
- Weekly insurance policy creation
- Dynamic premium calculation engine
- Claims management system
- Weather API integration
- Basic fraud detection (GPS + duplicate check)

### Phase 3 (April 5–17) — Scale and Polish
- Advanced fraud detection (pattern analysis)
- Razorpay test mode payment integration
- Worker dashboard (active coverage, earnings protected)
- Admin dashboard (loss ratios, weekly analytics)
- Final 5-minute demo video
- Final pitch deck (PDF)

---

## ⚠️ Coverage Exclusions — What We DO NOT Cover

We strictly follow the hackathon rules:

| NOT Covered ❌ | Covered ✅ |
|---------------|-----------|
| Health / Medical bills | Lost income due to heavy rain |
| Life insurance | Lost income due to extreme heat |
| Vehicle repair | Lost income due to floods |
| Accident claims | Lost income due to curfew/strike |
| Personal injury | Lost income due to hazardous AQI |

**We ONLY insure LOST INCOME. Nothing else.**

---

## 👥 Team — HackHer Squad

- **Team Name:** HackHer Squad
- **Hackathon:** Guidewire DEVTrails 2026
- **University:** AKTU (Dr. A.P.J. Abdul Kalam Technical University)
- **Platform:** Web Application

### Team Members:
1. Bharti Pathak — Research
2. Supriya Verma — README File
3. Sanjoli Singh — Video
4. Nandini Verma — Project Management
---

*Built with ❤️ for India's gig economy workers by HackHer Squad*
