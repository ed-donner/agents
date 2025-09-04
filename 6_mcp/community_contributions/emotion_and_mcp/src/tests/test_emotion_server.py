#!/usr/bin/env python3
import requests, sys

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5001"

print("Testing Emotion Server:", BASE)

# Health
r = requests.get(f"{BASE}/health", timeout=10)
print("/health:", r.status_code, r.text)

# Predict
for text in [
    "I am so happy today!",
    "This is terrible and frustrating!",
    "I love spending time with my family!",
]:
    r = requests.post(f"{BASE}/predict", json={"text": text}, timeout=10)
    print("/predict:", text, "->", r.status_code, r.text)
