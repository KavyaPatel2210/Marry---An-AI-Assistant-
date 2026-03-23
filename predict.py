import pickle
import json
import os
import random

current_dir = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(current_dir, 'model.pkl')
VEC_PATH = os.path.join(current_dir, 'vectorizer.pkl')
INTENTS_PATH = os.path.join(current_dir, 'intents.json')

# Load the model and vectorizer
try:
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)

    with open(VEC_PATH, 'rb') as f:
        vectorizer = pickle.load(f)

    with open(INTENTS_PATH, 'r', encoding='utf-8') as f:
        intents_data = json.load(f)
except Exception as e:
    print(f"Warning: Model or vectorizer not found. Please run train_model.py first. Error: {e}")
    model, vectorizer, intents_data = None, None, {"intents": []}

def predict_intent(text):
    if not model or not vectorizer:
        return 'unknown', 0.0

    text_vec = vectorizer.transform([text.lower()])
    
    # Get probabilities
    probs = model.predict_proba(text_vec)[0]
    max_idx = probs.argmax()
    confidence = probs[max_idx]
    
    tag = model.classes_[max_idx]
    
    # Fallback if confidence is low
    if confidence < 0.15:
        return 'unknown', confidence
    
    return tag, confidence

def get_response(tag):
    for intent in intents_data.get('intents', []):
        if intent['tag'] == tag:
            return random.choice(intent['responses'])
    return "Sorry, I didn't understand that."

# Reload trigger
