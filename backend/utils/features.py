import re
import urllib.parse

URGENCY_WORDS = [
    "urgent", "immediately", "action required", "verify now", "account suspended",
    "limited time", "expires", "click here", "confirm your", "update your",
    "unusual activity", "security alert", "final notice", "respond now",
    "act now", "warning", "alert", "important notice", "your account will"
]

AUTHORITY_WORDS = [
    "ceo", "manager", "director", "hr department", "it support", "helpdesk",
    "bank", "paypal", "amazon", "google", "microsoft", "apple", "irs", "fbi",
    "government", "official", "administration", "executive", "president", "chairman"
]

FEAR_WORDS = [
    "suspended", "locked", "compromised", "breach", "unauthorized",
    "illegal", "fraud", "criminal", "penalty", "fine", "lawsuit",
    "confidential", "do not discuss", "do not tell", "keep secret"
]

SUSPICIOUS_TLD = [".xyz", ".top", ".club", ".work", ".gq", ".tk", ".ml", ".cf", ".ga"]

FEATURE_COLS = [
    "url_length", "has_ip", "num_dots", "num_hyphens", "num_subdomains",
    "has_https", "suspicious_tld", "has_at_sign", "has_double_slash",
    "num_special_chars", "urgency_score", "authority_score", "fear_score",
    "text_length", "exclamation_count", "question_count", "all_caps_ratio",
    "link_count", "money_mention"
]

FEATURE_LABELS = {
    "url_length":       "URL length",
    "has_ip":           "IP-based URL",
    "num_dots":         "Dot count in domain",
    "num_hyphens":      "Hyphens in URL",
    "num_subdomains":   "Subdomain depth",
    "has_https":        "HTTPS present",
    "suspicious_tld":   "Suspicious TLD",
    "has_at_sign":      "@ in URL",
    "has_double_slash": "Double slash in path",
    "num_special_chars":"Special characters",
    "urgency_score":    "Urgency language",
    "authority_score":  "Authority impersonation",
    "fear_score":       "Fear-inducing language",
    "text_length":      "Message length",
    "exclamation_count":"Exclamation marks",
    "question_count":   "Question marks",
    "all_caps_ratio":   "ALL CAPS usage",
    "link_count":       "Number of links",
    "money_mention":    "Money/payment mention",
}


def extract_url_features(url: str) -> dict:
    empty = {k: 0 for k in [
        "url_length", "has_ip", "num_dots", "num_hyphens",
        "num_subdomains", "has_https", "suspicious_tld",
        "has_at_sign", "has_double_slash", "num_special_chars"
    ]}
    if not url:
        return empty
    try:
        parsed = urllib.parse.urlparse(url if url.startswith("http") else "http://" + url)
        hostname = parsed.hostname or ""
        path     = parsed.path or ""
        return {
            "url_length":        min(len(url) / 200, 1.0),
            "has_ip":            1 if re.match(r"\d{1,3}(\.\d{1,3}){3}", hostname) else 0,
            "num_dots":          min(hostname.count(".") / 5, 1.0),
            "num_hyphens":       min(url.count("-") / 5, 1.0),
            "num_subdomains":    min(max(len(hostname.split(".")) - 2, 0), 3) / 3,
            "has_https":         1 if parsed.scheme == "https" else 0,
            "suspicious_tld":    1 if any(hostname.endswith(t) for t in SUSPICIOUS_TLD) else 0,
            "has_at_sign":       1 if "@" in url else 0,
            "has_double_slash":  1 if "//" in path else 0,
            "num_special_chars": min(len(re.findall(r"[%@!$]", url)) / 5, 1.0),
        }
    except Exception:
        return empty


def extract_text_features(text: str) -> dict:
    empty = {k: 0 for k in [
        "urgency_score", "authority_score", "fear_score", "text_length",
        "exclamation_count", "question_count", "all_caps_ratio", "link_count", "money_mention"
    ]}
    if not text:
        return empty

    tl    = text.lower()
    words = tl.split()
    total = max(len(words), 1)

    return {
        "urgency_score":    min(sum(1 for w in URGENCY_WORDS   if w in tl) / 3, 1.0),
        "authority_score":  min(sum(1 for w in AUTHORITY_WORDS if w in tl) / 3, 1.0),
        "fear_score":       min(sum(1 for w in FEAR_WORDS       if w in tl) / 3, 1.0),
        "text_length":      min(len(text) / 1000, 1.0),
        "exclamation_count":min(text.count("!") / 5, 1.0),
        "question_count":   min(text.count("?") / 5, 1.0),
        "all_caps_ratio":   min(sum(1 for w in text.split() if w.isupper() and len(w) > 2) / total, 1.0),
        "link_count":       min(len(re.findall(r"https?://", text)) / 3, 1.0),
        "money_mention":    1 if re.search(
            r"\$[\d,]+|money|payment|wire|transfer|bitcoin|crypto|gift card|send funds", tl
        ) else 0,
    }


def get_all_features(text: str, url: str) -> dict:
    return {**extract_url_features(url), **extract_text_features(text)}


def get_triggered_tactics(text: str, url: str) -> list:
    tl  = (text or "").lower()
    tactics = []
    if any(w in tl for w in URGENCY_WORDS[:8]):
        tactics.append({"name": "Urgency",       "color": "#E85D24", "desc": "Creates time pressure to prevent careful thinking"})
    if any(w in tl for w in AUTHORITY_WORDS):
        tactics.append({"name": "Authority",     "color": "#7F77DD", "desc": "Impersonates a trusted person or organization"})
    if any(w in tl for w in FEAR_WORDS):
        tactics.append({"name": "Fear",          "color": "#D4537E", "desc": "Triggers anxiety to override rational judgment"})
    if re.search(r"\$[\d,]+|limited offer|only \d+ left", tl):
        tactics.append({"name": "Scarcity",      "color": "#BA7517", "desc": "Implies loss if action is not taken immediately"})
    if url:
        try:
            parsed = urllib.parse.urlparse(url if url.startswith("http") else "http://" + url)
            if parsed.hostname and len(parsed.hostname.split(".")) > 3:
                tactics.append({"name": "Disguised URL", "color": "#185FA5", "desc": "Uses subdomain tricks to mimic legitimate domains"})
        except Exception:
            pass
    return tactics
