# backend/train_model.py - Model Training Script

import pandas as pd
import numpy as np
import re
from urllib.parse import urlparse
from tld import get_tld
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from lightgbm import LGBMClassifier
import joblib
import os

# Load and clean dataset
df = pd.read_csv("malicious_phish.csv")

# Clean 'type' column: Remove null or empty types
df = df[df['type'].notnull()]
df = df[df['type'].str.strip() != '']

# Define label mapping and filter valid types
label_mapping = {'benign': 0, 'phishing': 1, 'defacement': 2}
df = df[df['type'].isin(label_mapping.keys())]
df['label'] = df['type'].map(label_mapping)

print(f"✅ Total samples after cleaning: {len(df)}")
print(df['label'].value_counts())

# Feature extraction function
def extract_features(url):
    features = []
    features.append(1 if re.search(r'\d+\.\d+\.\d+\.\d+', url) else 0)  # IP address
    features.append(1 if '-' in urlparse(url).netloc else 0)                   # dash in domain
    features.append(url.count('.'))
    features.append(url.count('www'))
    features.append(url.count('@'))
    features.append(url.count('/'))
    features.append(url.count('https'))
    features.append(url.count('http'))
    features.append(url.count('%'))
    features.append(len(url))
    features.append(len(urlparse(url).netloc))
    features.append(1 if re.search(r'paypal|bank|login|signin', url, re.I) else 0)  # Suspicious words
    try:
        tld_res = get_tld(url, fail_silently=True)
        features.append(len(tld_res) if tld_res else -1)
    except:
        features.append(-1)
    return features

# Generate features for all URLs
feature_list = df['url'].apply(extract_features).to_list()
X = pd.DataFrame(feature_list)
y = df['label']

print(f"✅ Feature matrix shape: {X.shape}")

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train Random Forest
rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
rf_model.fit(X_train, y_train)

# Train LightGBM
lgb_model = LGBMClassifier(n_estimators=100, random_state=42)
lgb_model.fit(X_train, y_train)

# Save models
os.makedirs("models", exist_ok=True)
joblib.dump(rf_model, "models/random_forest_model.pkl")
joblib.dump(lgb_model, "models/lightgbm_model.pkl")

print("✅ Models trained and saved successfully!")