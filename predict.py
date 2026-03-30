"""
========================================================
  predict.py  —  Marry AI Assistant  (AIML Project)
========================================================
Intent Prediction Module

Responsibilities
  • Load the trained model.pkl and vectorizer.pkl from disk
  • Apply the SAME preprocessing used during training
  • Return a (tag, confidence) tuple for any input text
  • Fetch a random response from intents.json for a given tag
  • Support hot-reloading the model without restarting the app

Usage (standalone test):
    python predict.py
Then type sentences to see predictions interactively.
"""

import pickle
import json
import os
import random
import warnings
warnings.filterwarnings("ignore")

# ── NLP (must match train_model.py exactly) ───────────────────────────
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Silently ensure required NLTK data is present
for _resource, _path in [
    ("stopwords",    "corpora/stopwords"),
    ("wordnet",      "corpora/wordnet"),
    ("punkt",        "tokenizers/punkt"),
]:
    try:
        nltk.data.find(_path)
    except LookupError:
        nltk.download(_resource, quiet=True)

# ─────────────────────────────────────────────────────────────────────
# 1.  Preprocessing  (identical to train_model.py)
# ─────────────────────────────────────────────────────────────────────
_lemmatizer  = WordNetLemmatizer()
_stop_words  = set(stopwords.words("english"))

# Words kept intentionally (meaningful assistant keywords)
_KEEP_WORDS = {"what", "who", "how", "when", "where", "why", "open", "play",
               "search", "find", "show", "tell", "give", "check", "start",
               "stop", "exit", "bye", "hello", "hi", "hey", "good", "help",
               "me", "my", "you", "i", "am", "are", "is", "do", "not", "no"}

_STOP_FILTERED = _stop_words - _KEEP_WORDS


def _preprocess(text: str) -> str:
    """
    Lowercase → tokenise → remove punctuation tokens →
    remove unimportant stopwords → lemmatise → rejoin.
    Mirrors the preprocessing used during model training.
    """
    tokens = nltk.word_tokenize(text.lower())
    cleaned = [
        _lemmatizer.lemmatize(tok)
        for tok in tokens
        if tok.isalpha() and tok not in _STOP_FILTERED
    ]
    return " ".join(cleaned) if cleaned else text.lower()


# ─────────────────────────────────────────────────────────────────────
# 2.  File paths
# ─────────────────────────────────────────────────────────────────────
_BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
_MODEL_PATH     = os.path.join(_BASE_DIR, "model.pkl")
_VEC_PATH       = os.path.join(_BASE_DIR, "vectorizer.pkl")
_INTENTS_PATH   = os.path.join(_BASE_DIR, "intents.json")

# ─────────────────────────────────────────────────────────────────────
# 3.  Load model artefacts (called at import time and by reload_model)
# ─────────────────────────────────────────────────────────────────────
_model        = None
_vectorizer   = None
_intents_data = {"intents": []}


def _load_artefacts():
    """
    (Re)load model.pkl, vectorizer.pkl, and intents.json from disk.
    Prints a warning if any file is missing (run train_model.py first).
    """
    global _model, _vectorizer, _intents_data

    try:
        with open(_MODEL_PATH, "rb") as f:
            _model = pickle.load(f)
        print("[predict] Model loaded successfully.")
    except FileNotFoundError:
        print("[predict] WARNING: model.pkl not found. Run train_model.py first.")
        _model = None

    try:
        with open(_VEC_PATH, "rb") as f:
            _vectorizer = pickle.load(f)
        print("[predict] Vectorizer loaded successfully.")
    except FileNotFoundError:
        print("[predict] WARNING: vectorizer.pkl not found. Run train_model.py first.")
        _vectorizer = None

    try:
        with open(_INTENTS_PATH, "r", encoding="utf-8") as f:
            _intents_data = json.load(f)
    except FileNotFoundError:
        print("[predict] WARNING: intents.json not found.")
        _intents_data = {"intents": []}


# Load on import
_load_artefacts()


# ─────────────────────────────────────────────────────────────────────
# 4.  Public API
# ─────────────────────────────────────────────────────────────────────

def reload_model():
    """
    Hot-reload the model and intents from disk without restarting.
    Call this after re-training to pick up the new artefacts.
    """
    print("[predict] Reloading model artefacts ...")
    _load_artefacts()
    print("[predict] Reload complete.")


def predict_intent(text: str) -> tuple:
    """
    Predict the intent tag for a given text string.

    Parameters
    ----------
    text : str
        Raw user input (voice-to-text or typed).

    Returns
    -------
    (tag, confidence) : tuple[str, float]
        tag        — matched intent tag, or 'unknown' if confidence is low
        confidence — probability score in range [0.0, 1.0]

    Pipeline
    --------
    raw text  →  preprocess()  →  TF-IDF transform  →  LR.predict_proba()
    """
    if _model is None or _vectorizer is None:
        print("[predict] Model not loaded. Returning 'unknown'.")
        return "unknown", 0.0

    # Apply the same preprocessing as training
    processed = _preprocess(text)

    # Vectorise and predict
    X_vec      = _vectorizer.transform([processed])
    probs      = _model.predict_proba(X_vec)[0]
    max_idx    = probs.argmax()
    confidence = float(probs[max_idx])
    tag        = _model.classes_[max_idx]

    # ── Confidence threshold ──────────────────────────────────
    # If the model is not confident enough, return 'unknown'
    # so the assistant can fall back to a web search.
    CONFIDENCE_THRESHOLD = 0.20   # 20 % — adjust as needed
    if confidence < CONFIDENCE_THRESHOLD:
        return "unknown", confidence

    return tag, confidence


def get_response(tag: str) -> str:
    """
    Fetch a random response string from intents.json for the given tag.
    Returns a default message if the tag is not found.

    Parameters
    ----------
    tag : str
        Intent tag (e.g. 'greeting', 'music', 'weather').

    Returns
    -------
    str : A randomly chosen response from the matching intent's responses list.
    """
    for intent in _intents_data.get("intents", []):
        if intent["tag"] == tag:
            return random.choice(intent["responses"])
    return "Sorry, I didn't understand that. Could you please rephrase?"


def get_all_tags() -> list:
    """Return a list of all intent tags defined in intents.json."""
    return [intent["tag"] for intent in _intents_data.get("intents", [])]


# ─────────────────────────────────────────────────────────────────────
# 5.  Standalone demo / quick test
# ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "=" * 56)
    print("  Marry — Intent Predictor  |  Interactive Test Mode")
    print("=" * 56)
    print("  Type a sentence and press Enter to see predictions.")
    print("  Type 'quit' or 'exit' to stop.\n")

    while True:
        try:
            user_input = input("  You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n  Exiting test mode.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit"):
            print("  Goodbye!")
            break

        tag, conf = predict_intent(user_input)
        response  = get_response(tag)

        print(f"  Preprocessed : {_preprocess(user_input)!r}")
        print(f"  Intent tag   : {tag}")
        print(f"  Confidence   : {conf * 100:.1f}%")
        print(f"  Response     : {response}")
        print()
