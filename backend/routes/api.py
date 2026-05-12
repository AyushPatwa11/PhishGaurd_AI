import numpy as np
from flask import Blueprint, request, jsonify
from utils.features import FEATURE_COLS, FEATURE_LABELS, get_all_features, get_triggered_tactics
from models.classifier import train_model, blend_score, explain

api_bp = Blueprint("api", __name__)

# Train once at import time
_model = train_model()


@api_bp.route("/predict", methods=["POST"])
def predict():
    body  = request.get_json(silent=True) or {}
    text  = body.get("text", "").strip()
    url   = body.get("url",  "").strip()

    feats       = get_all_features(text, url)
    X           = np.array([[feats[f] for f in FEATURE_COLS]])
    prediction  = int(_model.predict(X)[0])
    ml_prob     = float(_model.predict_proba(X)[0][1])
    probability = blend_score(ml_prob, feats)
    risk_score  = round(probability * 100)

    if risk_score >= 75:
        verdict, level = "Phishing",     "high"
    elif risk_score >= 45:
        verdict, level = "Suspicious",   "medium"
    else:
        verdict, level = "Likely Safe",  "low"

    top_features, reasons = explain(_model, feats, prediction)
    tactics               = get_triggered_tactics(text, url)

    return jsonify({
        "verdict":       verdict,
        "level":         level,
        "risk_score":    risk_score,
        "probability":   round(probability, 4),
        "top_features":  top_features,
        "reasons":       reasons,
        "tactics":       tactics,
        "raw_features":  {FEATURE_LABELS[k]: round(v, 3) for k, v in feats.items()},
    })


@api_bp.route("/examples", methods=["GET"])
def examples():
    return jsonify([
        {
            "label": "Phishing email",
            "text":  "URGENT: Your PayPal account has been suspended due to unauthorized activity! Click here immediately to verify your account and avoid permanent closure. Act now before it expires!",
            "url":   "http://paypal-verify-account.xyz/login?token=abc123"
        },
        {
            "label": "Legitimate email",
            "text":  "Hi, just wanted to follow up on the project proposal we discussed last week. Let me know if you have any questions or need more details before our meeting on Friday.",
            "url":   "https://docs.google.com/document/d/1a2b3c"
        },
        {
            "label": "CEO fraud",
            "text":  "This is the CEO. I need you to wire $15,000 immediately to this account for a confidential acquisition. Do not discuss with anyone. Respond now, this is time-sensitive.",
            "url":   ""
        },
        {
            "label": "Borderline marketing",
            "text":  "Limited time offer! Get 50% off your subscription today only. Click to claim your discount before it expires. Only 10 spots left!",
            "url":   "https://shop.example.com/deal"
        }
    ])


@api_bp.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status":   "ok",
        "model":    "RandomForest",
        "features": len(FEATURE_COLS),
    })
