import os
import sys
from typing import Optional

# Ensure project root is on path so existing modules import correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import numpy as np

from utils.features import FEATURE_COLS, FEATURE_LABELS, get_all_features, get_triggered_tactics
from importlib import import_module

# Lazy-loaded model placeholder
_model = None
_model_module = None

app = FastAPI(title="PhishGuard AI - Inference API", version="0.1.0")


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
