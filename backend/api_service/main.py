import os
import sys
from typing import Optional

# Ensure project root is on path so existing modules import correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from db import SessionLocal
from models.db_models import Scan, Explanation
from pydantic import BaseModel
import numpy as np

from utils.features import FEATURE_COLS, FEATURE_LABELS, get_all_features, get_triggered_tactics
from importlib import import_module

# Lazy-loaded model placeholder
_model = None
_model_module = None

app = FastAPI(title="PhishGuard AI - Inference API", version="0.1.0")

# Allow browser-based dev from the frontend origin(s)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5000", "http://localhost:5000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PredictRequest(BaseModel):
    text: Optional[str] = ""
    url: Optional[str] = ""


class PredictResponse(BaseModel):
    verdict: str
    level: str
    risk_score: int
    probability: float
    top_features: list
    reasons: list
    tactics: list
    raw_features: dict


@app.on_event("startup")
def startup_event():
    # Do not eagerly train the model on startup to keep startup fast.
    # The model will be loaded/trained lazily on first request.
    global _model, _model_module
    _model = None
    _model_module = None


@app.post("/api/v1/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    try:
        text = (req.text or "").strip()
        url = (req.url or "").strip()

        # Lazy import and model training/loading
        global _model, _model_module
        if _model is None:
            _model_module = import_module("models.classifier")
            _model = _model_module.train_model()

        feats = get_all_features(text, url)
        X = np.array([[feats[f] for f in FEATURE_COLS]])
        prediction = int(_model.predict(X)[0])
        ml_prob = float(_model.predict_proba(X)[0][1])
        probability = _model_module.blend_score(ml_prob, feats)
        risk_score = round(probability * 100)

        if risk_score >= 75:
            verdict, level = "Phishing", "high"
        elif risk_score >= 45:
            verdict, level = "Suspicious", "medium"
        else:
            verdict, level = "Likely Safe", "low"

        top_features, reasons = _model_module.explain(_model, feats, prediction)
        tactics = get_triggered_tactics(text, url)

        # Persist scan + explanations
        db = SessionLocal()
        try:
            scan = Scan(
                text=text or None,
                url=url or None,
                verdict=verdict,
                level=level,
                risk_score=risk_score,
                probability=float(probability),
                raw_features={FEATURE_LABELS[k]: round(v, 3) for k, v in feats.items()},
                reasons=reasons,
            )
            db.add(scan)
            db.flush()
            for f in top_features:
                ex = Explanation(
                    scan_id=scan.id,
                    feature=f.get("feature"),
                    weight=float(f.get("weight", 0)),
                    direction=f.get("direction"),
                    value=float(f.get("value", 0)),
                )
                db.add(ex)
            db.commit()
        except SQLAlchemyError:
            db.rollback()
        finally:
            db.close()

        return {
            "verdict": verdict,
            "level": level,
            "risk_score": risk_score,
            "probability": round(probability, 4),
            "top_features": top_features,
            "reasons": reasons,
            "tactics": tactics,
            "raw_features": {FEATURE_LABELS[k]: round(v, 3) for k, v in feats.items()},
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "model": "RandomForest", "features": len(FEATURE_COLS)}


@app.get("/api/v1/examples")
def examples():
    return [
        {
            "label": "Phishing email",
            "text": "URGENT: Your PayPal account has been suspended due to unauthorized activity! Click here immediately to verify your account and avoid permanent closure. Act now before it expires!",
            "url": "http://paypal-verify-account.xyz/login?token=abc123"
        },
        {
            "label": "Legitimate email",
            "text": "Hi, just wanted to follow up on the project proposal we discussed last week. Let me know if you have any questions or need more details before our meeting on Friday.",
            "url": "https://docs.google.com/document/d/1a2b3c"
        },
        {
            "label": "CEO fraud",
            "text": "This is the CEO. I need you to wire $15,000 immediately to this account for a confidential acquisition. Do not discuss with anyone. Respond now, this is time-sensitive.",
            "url": ""
        },
        {
            "label": "Borderline marketing",
            "text": "Limited time offer! Get 50% off your subscription today only. Click to claim your discount before it expires. Only 10 spots left!",
            "url": "https://shop.example.com/deal"
        }
    ]


@app.get("/api/v1/scans")
def get_scans():
    db = SessionLocal()
    try:
        items = db.query(Scan).order_by(Scan.created_at.desc()).limit(10).all()
        out = []
        for s in items:
            preview_text = (s.text or s.url or "")
            preview = preview_text[:48] + ("…" if len(preview_text) > 48 else "")
            out.append({
                "time": s.created_at.isoformat() if s.created_at else None,
                "preview": preview,
                "score": s.risk_score,
                "level": s.level,
                "verdict": s.verdict,
            })
        return out
    finally:
        db.close()
