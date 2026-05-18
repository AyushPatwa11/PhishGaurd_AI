## PhishGuard AI

AI-powered phishing detector. Flask serves both the API and the frontend — no CORS, no separate dev servers, no build step.

## Folder Structure

```
phishguard/
├── backend/
│   ├── app.py                  # Flask entry point — registers API + serves frontend
│   ├── requirements.txt
│   ├── models/
│   │   ├── __init__.py
│   │   └── classifier.py       # Random Forest training, blend_score, explain()
│   ├── routes/
│   │   ├── __init__.py
│   │   └── api.py              # /api/predict  /api/examples  /api/health
│   └── utils/
│       ├── __init__.py
│       └── features.py         # URL + text feature extraction, tactic detection
├── frontend/
│   ├── static/
│   │   ├── css/style.css       # All styles
│   │   └── js/app.js           # API calls, rendering, history table
│   └── templates/
│       └── index.html          # Clean HTML — no inline JS or CSS
├── .env.example
├── .gitignore
└── README.md
```

## Setup

```bash
cd backend
pip install -r requirements.txt
python app.py
```

Open http://localhost:5000 — frontend and API served from the same port.

## API

| Method | Endpoint        | Description              |
|--------|-----------------|--------------------------|
| POST   | /api/predict    | Analyze text + URL       |
| GET    | /api/examples   | 4 demo inputs            |
| GET    | /api/health     | Model status             |

### POST /api/predict

Request:
```json
{ "text": "URGENT: verify your account now!", "url": "http://paypal-xyz.tk/login" }
```

Response:
```json
{
  "verdict": "Phishing",
  "level": "high",
  "risk_score": 87,
  "probability": 0.87,
  "top_features": [
    { "feature": "Urgency language", "value": 1.0, "weight": 0.12, "direction": "phishing" }
  ],
  "reasons": ["High urgency language detected", "Suspicious TLD flagged"],
  "tactics": [
    { "name": "Urgency", "color": "#E85D24", "desc": "Creates time pressure..." }
  ],
  "raw_features": { "URL length": 0.24, ... }
}
```

## How it works

```
Input (text + URL)
  ↓
Feature extraction  →  19 features (10 URL + 9 text)
  ↓
Random Forest       →  ML probability
  ↓
Rule-based boost    →  catches text-only attacks (CEO fraud)
  ↓
Score blending      →  final risk score 0–100
  ↓
XAI explanation     →  top 5 weighted features + plain-language reasons
  ↓
Tactic detection    →  Urgency / Authority / Fear / Scarcity / Disguised URL
```

## Demo scores (validated)

| Input                       | Score | Level      |
|-----------------------------|-------|------------|
| Phishing email + bad URL    | 79    | 🔴 High    |
| Legitimate email            | 2     | 🟢 Safe    |
| CEO fraud (text only)       | 54    | 🟡 Medium  |
| Borderline marketing        | 21    | 🟢 Safe    |
