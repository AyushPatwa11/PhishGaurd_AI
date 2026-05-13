import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from utils.features import FEATURE_COLS, FEATURE_LABELS


def _generate_training_data(n: int = 1000) -> pd.DataFrame:
    np.random.seed(42)
    rows = []

    # Phishing samples
    for _ in range(n // 2):
        url_phish = np.random.random() > 0.3
        rows.append({
            "url_length":        np.random.uniform(0.3, 1.0) if url_phish else np.random.uniform(0.0, 0.4),
            "has_ip":            np.random.choice([0, 1], p=[0.5, 0.5]) if url_phish else 0,
            "num_dots":          np.random.uniform(0.3, 1.0) if url_phish else np.random.uniform(0.0, 0.3),
            "num_hyphens":       np.random.uniform(0.3, 1.0) if url_phish else np.random.uniform(0.0, 0.2),
            "num_subdomains":    np.random.uniform(0.4, 1.0) if url_phish else np.random.uniform(0.0, 0.3),
            "has_https":         np.random.choice([0, 1], p=[0.7, 0.3]),
            "suspicious_tld":    np.random.choice([0, 1], p=[0.2, 0.8]) if url_phish else 0,
            "has_at_sign":       np.random.choice([0, 1], p=[0.4, 0.6]) if url_phish else 0,
            "has_double_slash":  np.random.choice([0, 1], p=[0.5, 0.5]) if url_phish else 0,
            "num_special_chars": np.random.uniform(0.2, 1.0) if url_phish else np.random.uniform(0.0, 0.2),
            "urgency_score":     np.random.uniform(0.5, 1.0),
            "authority_score":   np.random.uniform(0.3, 1.0),
            "fear_score":        np.random.uniform(0.3, 1.0),
            "text_length":       np.random.uniform(0.1, 0.8),
            "exclamation_count": np.random.uniform(0.2, 1.0),
            "question_count":    np.random.uniform(0.0, 0.6),
            "all_caps_ratio":    np.random.uniform(0.1, 0.8),
            "link_count":        np.random.uniform(0.2, 1.0),
            "money_mention":     np.random.choice([0, 1], p=[0.3, 0.7]),
            "label": 1
        })

    # Legitimate samples
    for _ in range(n // 2):
        rows.append({
            "url_length":        np.random.uniform(0.0, 0.4),
            "has_ip":            0,
            "num_dots":          np.random.uniform(0.1, 0.4),
            "num_hyphens":       np.random.uniform(0.0, 0.2),
            "num_subdomains":    np.random.uniform(0.0, 0.3),
            "has_https":         np.random.choice([0, 1], p=[0.1, 0.9]),
            "suspicious_tld":    0,
            "has_at_sign":       0,
            "has_double_slash":  0,
            "num_special_chars": np.random.uniform(0.0, 0.2),
            "urgency_score":     np.random.uniform(0.0, 0.3),
            "authority_score":   np.random.uniform(0.0, 0.2),
            "fear_score":        np.random.uniform(0.0, 0.1),
            "text_length":       np.random.uniform(0.2, 0.8),
            "exclamation_count": np.random.uniform(0.0, 0.2),
            "question_count":    np.random.uniform(0.0, 0.3),
            "all_caps_ratio":    np.random.uniform(0.0, 0.1),
            "link_count":        np.random.uniform(0.0, 0.3),
            "money_mention":     np.random.choice([0, 1], p=[0.85, 0.15]),
            "label": 0
        })

    return pd.DataFrame(rows)


def train_model() -> RandomForestClassifier:
    print("[PhishGuard] Training Random Forest model...")
    df    = _generate_training_data(1000)
    X     = df[FEATURE_COLS].values
    y     = df["label"].values
    clf   = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=8)
    clf.fit(X, y)
    print(f"[PhishGuard] Model ready — {len(FEATURE_COLS)} features, {len(X)} samples")
    return clf


def blend_score(ml_prob: float, feats: dict) -> float:
    """Blend ML probability with rule-based score so text-only attacks aren't missed."""
    rule = (
        feats["urgency_score"]   * 0.35 +
        feats["authority_score"] * 0.25 +
        feats["fear_score"]      * 0.20 +
        feats["money_mention"]   * 0.15 +
        feats["all_caps_ratio"]  * 0.05
    )
    return max(ml_prob, rule * 0.9)


def explain(model: RandomForestClassifier, feats: dict, prediction: int) -> tuple:
    importances = model.feature_importances_
    contributions = []
    for i, col in enumerate(FEATURE_COLS):
        val = feats[col]
        imp = importances[i]
        weight = imp * val if prediction == 1 else imp * (1 - val)
        if val > 0.1 or col in ["has_ip", "has_at_sign", "suspicious_tld", "has_https"]:
            contributions.append({
                "feature":   FEATURE_LABELS[col],
                "value":     round(val, 3),
                "weight":    round(float(weight), 4),
                "direction": "phishing" if (prediction == 1 and val > 0.3) else "safe"
            })

    contributions.sort(key=lambda x: x["weight"], reverse=True)
    top = contributions[:5]

    reasons = []
    for c in top:
        if c["value"] > 0.5 and prediction == 1:
            reasons.append(f"High {c['feature'].lower()} detected")
        elif c["feature"] == "HTTPS present" and c["value"] == 0 and prediction == 1:
            reasons.append("Missing HTTPS — unencrypted connection")
        elif c["value"] > 0 and prediction == 1:
            reasons.append(f"{c['feature']} flagged")

    return top, reasons[:3]
