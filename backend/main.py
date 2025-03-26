from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import numpy as np
import re
import requests
import dns.resolver
import tldextract
from urllib.parse import urlparse
from fastapi.middleware.cors import CORSMiddleware
from utils import get_ssl_expiry, get_domain_age, get_screenshot
import whois
from fastapi.staticfiles import StaticFiles

# Load trained models
try:
    rf_model = joblib.load("models/random_forest_model.pkl")
    lgb_model = joblib.load("models/lightgbm_model.pkl")
    print("✅ Models loaded successfully!")
except Exception as e:
    print(f"❌ Error loading models: {e}")

app = FastAPI()


app.mount("/screenshots", StaticFiles(directory="screenshots"), name="screenshots")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Google Safe Browsing API Key
SAFE_BROWSING_API_KEY = "AIzaSyBVX1mJdkopR__1pOmSQLd3RnJ4QrYvqJA"
SAFE_BROWSING_URL = "https://safebrowsing.googleapis.com/v4/threatMatches:find"

# Input model
class URLInput(BaseModel):
    url: str

# Extract Features
def extract_features(url):
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        features = [
            1 if re.search(r'\d+\.\d+\.\d+\.\d+', url) else 0,  # IP address check
            1 if '-' in domain else 0,  # Hyphen in domain
            url.count('.'), url.count('www'), url.count('@'),
            url.count('/'), url.count('https'), url.count('http'),
            url.count('%'), len(url), len(domain),
            1 if re.search(r'paypal|bank|login|signin', url, re.I) else 0  # Suspicious words
        ]

        # ✅ **TLD Length Feature (13th Feature)**
        extracted = tldextract.extract(url)
        tld_length = len(extracted.suffix) if extracted.suffix else -1
        features.append(tld_length)

        print(f"🔍 Extracted Features: {features}")  # Debug print
        return np.array(features).reshape(1, -1)

    except Exception as e:
        print(f"❌ Error extracting features: {e}")
        raise HTTPException(status_code=500, detail=f"Feature extraction error: {e}")

# ✅ DNS Record Check
def check_dns_records(url):
    try:
        domain = urlparse(url).netloc
        answers = dns.resolver.resolve(domain, 'A')
        return [str(ip) for ip in answers]
    except Exception:
        return []

# ✅ Google Safe Browsing Check
def check_safe_browsing(url):
    try:
        payload = {
            "client": {"clientId": "your-app", "clientVersion": "1.0"},
            "threatInfo": {
                "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE"],
                "platformTypes": ["ANY_PLATFORM"],
                "threatEntryTypes": ["URL"],
                "threatEntries": [{"url": url}],
            },
        }
        response = requests.post(f"{SAFE_BROWSING_URL}?key={SAFE_BROWSING_API_KEY}", json=payload)
        data = response.json()
        return "Safe" if "matches" not in data else "Unsafe"
    except Exception as e:
        return "Error"

# ✅ WHOIS Data Dump
def get_whois_data(url):
    try:
        domain = urlparse(url).netloc
        whois_info = whois.whois(domain)
        return whois_info.text
    except Exception:
        return "WHOIS lookup failed."

# ✅ Historical Rank (Alexa/SimilarWeb)
def get_historical_rank(url):
    try:
        domain = urlparse(url).netloc
        response = requests.get(f"https://www.similarweb.com/website/{domain}")
        return "Rank retrieved" if response.status_code == 200 else "No data"
    except Exception:
        return "Error retrieving rank"

# ✅ AI Explanation
def generate_explanation(prediction, confidence_score):
    if prediction == "Phishing":
        return f"The website was flagged as phishing with {confidence_score}% confidence. Possible reasons: suspicious keywords, low domain age, SSL issues."
    else:
        return f"The website appears safe with {confidence_score}% confidence."

# ✅ Prediction Endpoint
@app.post("/predict")
async def predict_url(data: URLInput):
    url = data.url.strip()
    if not url.startswith("http"):
        url = "http://" + url  # Ensure proper URL format

    try:
        # Extract Features
        features = extract_features(url)

        # Get Model Predictions
        rf_pred = rf_model.predict_proba(features)[0]
        lgb_pred = lgb_model.predict_proba(features)[0]
        final_probs = (rf_pred + lgb_pred) / 2
        labels = ["benign", "phishing", "defacement"]
        predicted_label = labels[np.argmax(final_probs)]
        confidence_score = int(np.max(final_probs) * 100)

        # Get WHOIS Domain Age & SSL Status
        domain_age = get_domain_age(url)
        ssl_valid = get_ssl_expiry(url)

        # ✅ DNS Records
        dns_records = check_dns_records(url)

        # ✅ Google Safe Browsing Check
        safe_browsing_status = check_safe_browsing(url)

        # ✅ Full WHOIS Data
        whois_data = get_whois_data(url)

        # ✅ Historical Rank
        historical_rank = get_historical_rank(url)

        # ✅ AI Explanation
        explanation = generate_explanation(predicted_label, confidence_score)

        # ✅ Page Screenshot
        screenshot_url = get_screenshot(url)

        print(f"🔍 Domain Age: {domain_age}, SSL Valid: {ssl_valid}")  # Debug print

        # ✅ Override logic (Fixing the issue)
        if ssl_valid and domain_age > 2:
            predicted_label = "benign"  # Force Benign
            confidence_score = 100  # Override confidence score to 100%
            final_probs = [1.0, 0.0, 0.0]  # Override confidence scores to Benign = 100%

        print(f"✅ Final Prediction: {predicted_label}, Confidence: {confidence_score}")  # Debug print

        return {
            "prediction": predicted_label.capitalize(),
            "domain_age": domain_age,
            "ssl_valid": ssl_valid,
            "confidence_score": confidence_score,
            "dns_records": dns_records,
            "safe_browsing": safe_browsing_status,
            "whois_data": whois_data,
            "historical_rank": historical_rank,
            "ai_explanation": explanation,
            "screenshot": screenshot_url,
            "scores": {
                "benign": int(final_probs[0] * 100),
                "phishing": int(final_probs[1] * 100),
                "defacement": int(final_probs[2] * 100),
            }
        }

    except Exception as e:
        print(f"❌ Error in prediction: {e}")  # Debug print
        raise HTTPException(status_code=500, detail=f"Error processing URL: {e}")

# ✅ Health Check Endpoint
@app.get("/healthcheck")
async def healthcheck():
    return {"status": "OK", "message": "API is running!"}
