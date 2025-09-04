#!/usr/bin/env python3
"""
Lightweight Emotion Detection Server using BERT-Emotion
Model: https://huggingface.co/boltuix/bert-emotion
"""
import logging
import traceback
from flask import Flask, request, jsonify
from transformers import pipeline
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

emotion_analyzer = None

EMOTION_EMOJI_MAP = {
    "Sadness": "😢",
    "Anger": "😠",
    "Love": "❤️",
    "Surprise": "😲",
    "Fear": "😱",
    "Happiness": "😄",
    "Neutral": "😐",
    "Disgust": "🤢",
    "Shame": "🙈",
    "Guilt": "😔",
    "Confusion": "😕",
    "Desire": "🔥",
    "Sarcasm": "😏",
}

def load_emotion_model() -> bool:
    global emotion_analyzer
    try:
        logger.info("Loading BERT-Emotion model...")
        emotion_analyzer = pipeline(
            "text-classification",
            model="boltuix/bert-emotion",
            return_all_scores=False,
        )
        logger.info("Model loaded ✅")
        return True
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        traceback.print_exc()
        return False

@app.get("/health")
def health():
    return jsonify({
        "status": "healthy" if emotion_analyzer is not None else "uninitialized",
        "model_loaded": emotion_analyzer is not None,
        "model": "boltuix/bert-emotion",
    })

@app.post("/predict")
def predict():
    if emotion_analyzer is None:
        return jsonify({"error": "Model not loaded"}), 503
    data = request.get_json(silent=True) or {}
    text = data.get("text")
    if not isinstance(text, str) or not text.strip():
        return jsonify({"error": "Missing 'text'"}), 400
    try:
        res = emotion_analyzer(text)[0]
        label = res.get("label", "")
        score = float(res.get("score", 0.0))
        # Normalize label capitalization to match map keys
        label_cap = label.capitalize()
        emoji = EMOTION_EMOJI_MAP.get(label_cap, "❓")
        return jsonify({
            "prediction": label_cap,
            "emoji": emoji,
            "confidence": score,
        })
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        traceback.print_exc()
        return jsonify({"error": "Internal error"}), 500

if __name__ == "__main__":
    if not load_emotion_model():
        raise SystemExit(1)
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "5001"))
    logger.info(f"Starting on http://{host}:{port}")
    app.run(host=host, port=port, debug=False, threaded=True)
