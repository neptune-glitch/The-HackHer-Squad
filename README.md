# 🛡️ GigShield — AI-Powered Parametric Insurance for E-Commerce Delivery Partners

> **Team: HackHer Squad | Guidewire DEVTrails 2026**

---

## 📌 Problem Statement

E-commerce delivery partners working for platforms like **Amazon and Flipkart** in cities like **Delhi** are the backbone of India's digital economy. However, external disruptions such as **severe pollution/smog, extreme heat, and heavy rain/floods** can completely halt their work — causing them to lose **20–30% of their monthly income**.

Currently, these gig workers have **no financial safety net** against such uncontrollable events. When disruptions occur, they bear the full loss alone.

---

## 👤 Who Is Our User REALLY?

**Name:** Ramesh Kumar
**Age:** 24 years old
**City:** Delhi
**Delivery Zone:** Dwarka, Lajpat Nagar, Connaught Place — Delhi
**Platform:** Amazon & Flipkart Delivery Partner
**Device:** Budget Android smartphone (Redmi/Realme, 4G)
**Education:** 12th pass
**Work Hours:** 9–11 hours/day, 6 days a week
**Daily Earnings:** ₹600–₹900/day
**Weekly Earnings:** ₹3,600–₹5,400/week
**How He Gets Paid:** Weekly UPI transfer from Amazon/Flipkart

### Ramesh's Real Life Story in Delhi:

Ramesh lives in a rented room in Delhi and sends money home every week to his family in a village. Every morning he wakes up not knowing if he will earn today.

**Delhi specific problems Ramesh faces:**

- 🌫️ **Winter Smog (Nov–Jan):** AQI crosses 400+ in Delhi sectors. Ramesh cannot breathe properly while riding. He stays home. **Zero income.**
- 🌡️ **Summer Heat (April–June):** Temperature crosses 45°C in Delhi. Riding for 10 hours is dangerous. He cannot work. **Zero income.**
- 🌧️ **Monsoon Floods (July–Sept):** Heavy rain floods roads in Dwarka, Lajpat Nagar areas. Packages cannot be delivered. **Zero income.**
- 🚫 **He has no savings, no insurance, no safety net.**
- At end of week he is short on rent, food, and phone recharge.

### Why Existing Insurance Does NOT Work for Ramesh:
- Traditional insurance is **monthly** — Ramesh thinks and earns **weekly**
- Claims require **paperwork** — Ramesh has no time for that
- Most insurance covers **health or vehicle** — not his **lost daily wages**
- Premium is too **expensive** for his income level

---

## 💡 Our Solution — GigShield

**GigShield** is a simple web platform where Ramesh pays a small weekly premium (₹25–₹60) and gets automatic income protection when external disruptions in **Delhi** stop him from working.

**No paperwork. No phone calls. Money directly in his UPI wallet within minutes.**

---

## 🔄 How The App Works — Step by Step

### Step 1 — Ramesh Registers (2 minutes)
- Opens GigShield on his phone browser (no app download needed)
- Enters: Name, Phone Number, Delivery Zone (Alpha/Beta/Gamma), UPI ID
- Selects his platform: Amazon or Flipkart
- AI creates his risk profile based on his Delhi zone

### Step 2 — He Picks a Weekly Plan
- Sees 3 plan options (Basic / Standard / Premium)
- AI shows personalized price based on his specific zone risk
- He pays weekly premium via UPI (₹25–₹60/week)
- Coverage starts immediately

### Step 3 — System Monitors Delhi 24/7
- GigShield checks weather, AQI, flood alerts every 30 minutes
- Monitors Ramesh's specific delivery zone
- No action needed from Ramesh at all

### Step 4 — Disruption Happens in Delhi
- Example: AQI crosses 400 in Alpha sector at 7am
- System automatically detects this in Ramesh's zone

### Step 5 — Claim Auto-Triggered
- System checks: Is Ramesh's policy active? ✅
- System checks: Is disruption in his registered zone? ✅
- System checks: Is this a genuine claim? ✅ (AI fraud check)
- Claim approved in under 2 minutes

### Step 6 — Money Reaches Ramesh
- ₹500 credited to his UPI instantly
- He gets SMS + app notification
- **He didn't fill any form. He didn't call anyone.**

---

## 💰 Weekly Premium Model

| Plan | Weekly Premium | Coverage Per Disruption Day | Max Days Covered/Week |
|------|---------------|----------------------------|-----------------------|
| Basic | ₹25/week | ₹300/day | 2 days |
| Standard | ₹40/week | ₹500/day | 2 days |
| Premium | ₹60/week | ₹700/day | 2 days |

### Why Weekly Pricing?
- Ramesh gets paid **weekly** by Amazon/Flipkart
- He cannot commit to monthly payments
- Weekly model matches his income cycle perfectly
- He can pause or renew every week

---

## ⚡ Parametric Triggers — Delhi Specific

These are our 5 automated triggers built specifically for Delhi:

| Trigger | Exact Condition | Data Source |
|---------|----------------|-------------|
| Severe Pollution / Smog | AQI > 400 in worker's Delhi zone | CPCB Mock API |
| Extreme Heat | Temperature > 44°C for 4+ hours | OpenWeatherMap API (free tier) |
| Heavy Rain / Flood | Rainfall > 50mm in 6 hours in delivery zone | OpenWeatherMap API (free tier) |
| Flash Flood Alert | Flood warning issued for Delhi sectors | Mock Government Alert API |
| Local Curfew / Bandh | Curfew declared in worker's zone | Mock News API |

**Zone Specific:** Claim fires ONLY when disruption is in worker's registered delivery zone (Dwarka/Lajpat Nagar/CP sectors) — not citywide.

---

## 🤖 How Our AI REALLY Works

### AI Feature 1 — Dynamic Premium Calculation

**What goes IN:**
- Worker's delivery zone in Delhi (Alpha 1 / Beta 2 / Gamma)
- Historical disruption data of that zone (smog, heat, floods)
- Current season (Winter = smog risk, Summer = heat risk, Monsoon = flood risk)
- Worker's honest claim history
- Weather and AQI forecast for next 7 days

**What comes OUT:**
- Personalized weekly premium for that specific worker

**Real Delhi Example:**
- Ramesh works in **Dwarka sector** — historically gets flooded every monsoon
- It is **July** (peak monsoon)
- AI calculates: Base ₹40 + Flood zone risk ₹10 + Monsoon season ₹5 = **₹55/week**
- Another worker in safer **Connaught Place sector** gets: Base ₹40 - Safe zone ₹8 = **₹32/week**

**Algorithm:**
- Phase 1 and 2: Rule-based scoring model
- Phase 3: Linear Regression model trained on mock historical data

---

### AI Feature 2 — Fraud Detection (4 Checks)

**Check 1 — GPS Zone Check**
- Worker's last known location must be inside the disruption affected zone
- If worker is outside Delhi → claim rejected ❌

**Check 2 — Platform Activity Check**
- System checks if worker had active deliveries scheduled that day
- No active orders + claiming disruption → flagged 🔍

**Check 3 — Duplicate Claim Check**
- One claim per disruption event per worker
- Claiming twice for same smog event → auto rejected ❌

**Check 4 — Pattern Analysis**
- Worker claiming every single week → suspicious → flagged 🔍
- Normal workers don't face disruptions every week

**Fraud Risk Score:**

| Score | Risk Level | Action |
|-------|-----------|--------|
| 0–30 | Low | Auto approved ✅ |
| 31–60 | Medium | Manual review 🔍 |
| 61–100 | High | Rejected ❌ |

---

### AI Feature 3 — Risk Profiling

Every worker gets a Risk Score when they register:

| Factor | Low Risk | High Risk |
|--------|----------|-----------|
| Delivery Zone | Gamma (less flood prone) | Alpha/Beta (flood prone) |
| Season | Winter (less rain) | Monsoon (heavy rain) |
| Claim History | No suspicious claims | Repeated claims |
| AQI History | Zone rarely hits 400+ | Zone regularly hits 400+ |

---

## 🖥️ Platform — Web App

**Why Web App and not Mobile App?**
- Ramesh uses a budget Android phone with low storage
- Cannot install another app
- Web app opens directly in Chrome browser
- Works on 4G connection
- No download needed → more Delhi workers will use it

---

## 🛠️ Tech Stack

| Layer | Technology | Why We Chose It |
|-------|-----------|-----------------|
| Frontend | React.js + Tailwind CSS | Fast UI, mobile friendly |
| Backend | Node.js + Express.js | Lightweight, fast API |
| Database | MongoDB | Flexible data storage |
| AI/ML | Python + scikit-learn | Easy ML model building |
| Weather API | OpenWeatherMap (free tier) | Free, real-time data |
| AQI API | CPCB Mock API | Delhi pollution data |
| Payment | Razorpay Test Mode | UPI simulation for demo |
| Hosting | Vercel + Render | Free hosting |
| Auth | JWT Tokens | Secure login |

---

## 📅 Development Plan

### Phase 1 (March 4–20) — Ideation ✅
- Research and Delhi persona definition ✅
- Weekly premium model design ✅
- Parametric trigger identification ✅
- Tech stack finalization ✅
- README documentation ✅

### Phase 2 (March 21–April 4) — Core Building
- Worker registration and login
- AI risk profiling for Delhi zones
- Weekly insurance policy creation
- Dynamic premium calculation
- Claims management system
- Weather + AQI API integration

### Phase 3 (April 5–17) — Scale and Polish
- Advanced fraud detection
- Razorpay test mode payment
- Worker dashboard
- Admin/Insurer dashboard
- Final demo video + pitch deck

---

## ⚠️ Coverage — What We Cover and What We Don't

| NOT Covered ❌ | Covered ✅ |
|---------------|-----------|
| Health / Medical | Lost income due to smog/pollution |
| Life insurance | Lost income due to extreme heat |
| Vehicle repair | Lost income due to heavy rain/floods |
| Accident claims | Lost income due to curfew/strike |

**We ONLY insure LOST INCOME. Nothing else.**

---

## 👥 Team — HackHer Squad

- **Team Name:** HackHer Squad
- **Hackathon:** Guidewire DEVTrails 2026
- **University:** AKTU (Dr. A.P.J. Abdul Kalam Technical University)
- **City:** Delhi
- **Platform:** Web Application

### Team Members:
1. Bharti Pathak — Research
2. Supriya Verma — Documentation
3. Sanjoli Singh — Video Production
4. Nandini Verma — Project Management

---

*Built with ❤️ for Delhi's gig economy workers by HackHer Squad*
