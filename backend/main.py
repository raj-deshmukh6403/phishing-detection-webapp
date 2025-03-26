from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import numpy as np
import re
from urllib.parse import urlparse
from utils import get_ssl_expiry, get_domain_age
from fastapi.middleware.cors import CORSMiddleware
import tldextract

# Load trained models
try:
    rf_model = joblib.load("models/random_forest_model.pkl")
    lgb_model = joblib.load("models/lightgbm_model.pkl")
    print("✅ Models loaded successfully!")
except Exception as e:
    print(f"❌ Error loading models: {e}")

app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

        # ✅ **Add back the 13th Feature: TLD Length**
        extracted = tldextract.extract(url)
        tld_length = len(extracted.suffix) if extracted.suffix else -1
        features.append(tld_length)

        print(f"🔍 Extracted Features: {features}")  # Debug print
        return np.array(features).reshape(1, -1)

    except Exception as e:
        print(f"❌ Error extracting features: {e}")
        raise HTTPException(status_code=500, detail=f"Feature extraction error: {e}")

# Prediction Endpoint
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

        # Get WHOIS Domain Age & SSL Status
        domain_age = get_domain_age(url)
        ssl_valid = get_ssl_expiry(url)

        print(f"🔍 Domain Age: {domain_age}, SSL Valid: {ssl_valid}")  # Debug print

        # ✅ Override logic (Fixing the issue)
        if ssl_valid and domain_age > 2:
            predicted_label = "benign"  # Force Benign
            confidence_score = 100  # Override confidence score to 100%
            final_probs = [1.0, 0.0, 0.0]  # Override confidence scores to Benign = 100%

        print(f"✅ Final Prediction: {predicted_label}, Confidence: {final_probs}")  # Debug print

        return {
            "prediction": predicted_label.capitalize(),
            "domain_age": domain_age,
            "confidence_score": confidence_score,
            "ssl_valid": ssl_valid,
            "scores": {
                "benign": int(final_probs[0] * 100),
                "phishing": int(final_probs[1] * 100),
                "defacement": int(final_probs[2] * 100),
            }
        }

    except Exception as e:
        print(f"❌ Error in prediction: {e}")  # Debug print
        raise HTTPException(status_code=500, detail=f"Error processing URL: {e}")

# Health Check
@app.get("/healthcheck")
async def healthcheck():
    return {"status": "OK", "message": "API is running!"}
