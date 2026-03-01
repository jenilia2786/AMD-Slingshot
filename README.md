# 🎓 AccelerateAI
## AI-Powered Fair Internship Ecosystem — Government of Global

> **Get Paid During Evaluation • AI-Fair Assessment • Platform Verified • Blockchain Transparent**

---

## 📁 Project Structure

```
tn-internfair/
├── frontend/
│   ├── index.html                  ← Landing page (particles, counters, CTA)
│   ├── css/
│   │   ├── global.css              ← Shared design system, animations, components
│   │   └── landing.css             ← Landing page specific styles
│   ├── js/
│   │   ├── utils.js                ← Toast, modal, loader, API helpers
│   │   └── auth.js                 ← Login, JWT, mock auth
│   ├── student/
│   │   ├── login.html              ← Slingshot Talent OAuth + direct login
│   │   ├── dashboard.html          ← Stats, recommended tasks, earnings chart
│   │   ├── tasks.html              ← Browse + filter all tasks
│   │   ├── submit-task.html        ← Code editor + AI evaluation flow
│   │   ├── wallet.html             ← Balance, transactions, CSV export
│   │   └── profile.html            ← Skills, resume AI analysis, readiness index
│   ├── company/
│   │   ├── login.html              ← Company login/register
│   │   ├── dashboard.html          ← Stats, active tasks, trust score
│   │   ├── create-task.html        ← Task form + live preview + CSR calculator
│   │   ├── candidates.html         ← AI-ranked candidates, select/reject
│   │   └── csr-wallet.html         ← CSR balance, escrows, transaction log
│   └── government/
│       ├── login.html              ← Secure login with OTP
│       ├── dashboard.html          ← Live analytics, exploitation prevented ⭐
│       ├── analytics.html          ← Full reports, bias monitoring, company compliance
│       └── audit.html              ← Blockchain ledger, fraud alerts, escrow tracking
│
├── backend/
│   ├── main.py                     ← FastAPI app entry point
│   ├── routers/
│   │   ├── auth.py                 ← Login endpoints for all roles
│   │   ├── student.py              ← Student CRUD + submission + wallet
│   │   ├── company.py              ← Company CRUD + task + candidates
│   │   ├── government.py           ← Analytics + audit + oversight
│   │   └── ai_evaluation.py        ← CrewAI evaluation endpoint
│   ├── models/
│   │   └── user.py                 ← Pydantic models for all entities
│   ├── services/
│   │   ├── crew_ai_service.py      ← 4-agent CrewAI evaluation system
│   │   ├── escrow_service.py       ← CSR fund lock/release/refund
│   │   └── blockchain_service.py   ← SHA256 immutable transaction logging
│   ├── database/
│   │   ├── connection.py           ← MongoDB + in-memory fallback
│   │   └── mock_data.py            ← 50 students, 15 companies, 30 tasks, 500 txns
│   └── utils/
│       └── jwt_handler.py          ← JWT create/decode/verify
│
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🚀 Quick Start (Frontend Only — No Backend Needed)

The frontend works completely standalone using mock data. No installation required.

```bash
# Option 1: Python HTTP server
cd tn-internfair/frontend
python -m http.server 3000
# Open http://localhost:3000

# Option 2: Just open directly
open frontend/index.html
```

### 🔑 Login Credentials

| Role | Email | Password | Notes |
|------|-------|----------|-------|
| Student | student1@nm.tn.gov.in | student123 | Wallet: ₹12,400 |
| Student | student2@nm.tn.gov.in | student123 | Wallet: ₹8,750 |
| Student | student3@nm.tn.gov.in | student123 | Wallet: ₹5,200 |
| Company | techcorp@company.com | company123 | Corporate, CSR: ₹2.45L |
| Company | startup@company.com | company123 | Startup, CSR: ₹78K |
| Company | bigcorp@company.com | company123 | Corporate, CSR: ₹5.2L |
| Government | admin@tn.gov.in | admin123 | OTP: 123456 |

---

## 🛠️ Full Stack Setup (With Backend)

### Prerequisites
- Python 3.9+
- MongoDB (optional — works with in-memory mock)
- Node.js (optional — only for live reload)

### Step 1: Clone & Setup

```bash
git clone <repo>
cd tn-internfair

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Linux/Mac
# OR: venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment

```bash
cp .env.example .env
# Edit .env — minimum required:
# MONGODB_URL=mongodb://localhost:27017   (or leave blank for mock)
# JWT_SECRET=your_secret_key
# JWT_SECRET=your_secret_key
# Ollama runs locally; no API key needed for evaluation.
```

### Step 3: Generate Mock Data

```bash
python -m backend.database.mock_data
# Output: 50 students, 15 companies, 30 tasks, 200 submissions, 500 transactions
```

### Step 4: Start Backend

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
# API docs: http://localhost:8000/docs
```

### Step 5: Start Frontend

```bash
cd frontend
python -m http.server 3000
# Open: http://localhost:3000
```

---

## 🤖 AI Evaluation System (CrewAI)

The system uses 4 specialized AI agents:

| Agent | Role | Evaluates |
|-------|------|-----------|
| 🔧 Technical Evaluator | Senior Software Engineer | Code quality, correctness, best practices |
| 🔍 Plagiarism Detector | Code Authenticity Specialist | Originality via embedding similarity |
| 📄 Resume Analyzer | Talent Assessment Expert | Skill-to-task match alignment |
| 🛡️ Fraud Synthesizer | Risk Management Expert | Fraud patterns + final score synthesis |

**Scoring Formula:**
```
Combined Score = Technical(50%) + Originality(30%) + Skills Match(20%)
```

**To enable local AI evaluation:**
```bash
# Ensure Ollama is installed and running
ollama run llama3
pip install langchain-community
```

The system uses Ollama with the 'llama3' model for local agent orchestration.

---

## 💰 CSR Escrow System

```
Company Deposits CSR
       ↓
Task Created → Funds Locked in Escrow (reward × max_participants)
       ↓
Student Submits → AI Evaluates
       ↓
Score ≥ 60? → ✅ Release reward to student wallet
Score < 60? → ❌ Keep in escrow, notify student
       ↓
Task Expired? → ↩️ Refund unused escrow to company
```

**Anti-Exploitation Rule:** Maximum 2 task submissions per student per company.

---

## 🔗 Blockchain Audit Trail

Every transaction is logged with:
- SHA256 hash linking to previous transaction
- Immutable timestamp
- From/To entities
- Amount and task reference
- Government-verifiable audit trail

```python
Hash = SHA256(timestamp + from_id + to_id + amount + prev_hash)
```

---

## 📊 Key Impact Metrics

| Metric | Value | Formula |
|--------|-------|---------|
| CSR Funds Utilized | ₹25,00,000 | Sum of all escrow releases |
| Students Compensated | 1,247 | Unique students receiving rewards |
| Exploitation Prevented | ₹18,49,914 ⭐ | Non-hired × Avg tasks × Avg reward |
| Active Companies | 156 | Companies with active tasks |

---

## 🔌 API Documentation

Once backend is running, visit: **http://localhost:8000/docs**

Key endpoints:
```
POST /api/auth/login              — Login for all roles
GET  /api/student/dashboard       — Student home
GET  /api/student/tasks           — Browse available tasks
POST /api/student/submit-task     — Submit code for evaluation
GET  /api/student/wallet          — Wallet balance + history
POST /api/company/create-task     — Create evaluation task
GET  /api/company/candidates/{id} — AI-ranked candidate list
GET  /api/government/analytics    — Live platform analytics
GET  /api/government/audit-logs   — Blockchain transaction viewer
POST /api/ai/evaluate             — Run CrewAI evaluation
```

---

## 🎨 Design System

- **Primary Blue:** #1E40AF — Buttons, headers
- **Success Green:** #059669 — Government, payments
- **CSR Gold:** #F59E0B — Rewards, escrow
- **Alert Red:** #DC2626 — Fraud, rejections
- **Font:** Plus Jakarta Sans + Syne (headings)

---

## 🏛️ Integration

- **Slingshot Talent:** Student identity verification (OAuth mock)
- **slingshot.amd.com:** Job portal integration
- **Government of Global:** Policy compliance framework

---

*Built for AccelerateAI Hackathon — Transforming Internship Culture in Global*
