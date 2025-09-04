import unsloth
import connexion
import logging
import torch
import torch.nn.functional as F
import traceback
from flask import current_app

# Configure logging
logging.basicConfig(level=logging.INFO)

# -----------------------------
# Config / Paths
# -----------------------------
MODEL_PATH = "./gemma3_emotion_model_unsloth/full"

# Label and emoji mapping
LABELS = [
    "anger","confusion","desire","desire","disgust","fear","guilt","happiness",
    "love","neutral","sadness","sarcasm","shame","surprise",
]
EMOJI = dict(
    anger="😡", confusion="😕", desire="🧚", disgust="🤢", fear="😨", guilt="😔",
    happiness="😊", love="❤️", neutral="😐", sadness="😢", sarcasm="🤨",
    shame="😳", surprise="😲",
)

# -----------------------------
# Core Prediction Logic
# -----------------------------
def classify_emotion(model_for_gen, tokenizer, text):
    prompt = f"### Instruction:\nClassify the emotion in this text:\n{text}\n\n### Response:"
    inputs = tokenizer(prompt, return_tensors="pt").to(model_for_gen.device)

    with torch.inference_mode():
        outputs = model_for_gen(**inputs)
    
    logits = outputs.logits
    last_token_logits = logits[0, -1, :]
    probabilities = F.softmax(last_token_logits, dim=-1)
    
    predicted_token_id = torch.argmax(probabilities).item()
    confidence = probabilities[predicted_token_id].item()
    
    pred_text = tokenizer.decode([predicted_token_id]).strip().lower()

    pred = "neutral"
    for lab in LABELS:
        if pred_text.startswith(lab):
            pred = lab
            break
            
    emoji = EMOJI.get(pred, "❓")
    
    return pred, emoji, confidence

def load_model():
    """Initializes the model and returns it and the tokenizer."""
    try:
        logging.info("Loading fine-tuned model and tokenizer...")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
        model, tokenizer = unsloth.FastLanguageModel.from_pretrained(
            model_name=MODEL_PATH,
            max_seq_length=128,
            dtype=torch.bfloat16,
            load_in_4bit=False,
            attn_implementation="flash_attention_2",
        )
        model.to(device)
        model.eval()
        logging.info("Model loaded successfully.")
        return model, tokenizer
    except Exception as e:
        logging.error(f"Error loading model: {e}")
        traceback.print_exc()
        raise e

def predict(input_data):
    """
    Makes a prediction based on the input text.
    """
    # **THIS IS THE FIX**
    # Use Flask's current_app proxy to access the model
    model = getattr(current_app, 'model', None)
    tokenizer = getattr(current_app, 'tokenizer', None)
    
    if model is None or tokenizer is None:
        logging.error("Model or tokenizer is not loaded. Cannot make a prediction.")
        return {"error": "Model not loaded. Server is not ready."}, 503

    try:
        text = input_data.get('text')
        if not text:
            logging.warning("Received a request with no 'text' field.")
            return {"error": "Invalid input data. 'text' field is required."}, 400

        logging.info(f"Received request for text: '{text}'")

        pred, emoji, confidence = classify_emotion(model, tokenizer, text)
        
        logging.info(f"Prediction made: {pred}, Confidence: {confidence:.4f}")
        
        return {"prediction": pred, "emoji": emoji, "confidence": confidence}
    except Exception as e:
        logging.error(f"An unexpected error occurred during prediction: {e}")
        traceback.print_exc()
        return {"error": f"An unexpected server error occurred: {e}"}, 500

if __name__ == '__main__':
    try:
        model, tokenizer = load_model()
        
        app = connexion.App(__name__, specification_dir='.')
        app.add_api('openapi.yaml', strict_validation=True)
        app.app.debug = True
        
        # Store the model and tokenizer on the Flask app instance
        app.app.model = model
        app.app.tokenizer = tokenizer

        app.run(port=5000)
    except Exception as e:
        logging.error(f"Application failed to start due to a model loading error: {e}")
        traceback.print_exc()