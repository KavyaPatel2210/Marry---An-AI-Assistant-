"""
========================================================
  train_model.py  —  Marry AI Assistant  (AIML Project)
========================================================
Machine Learning Pipeline
  1. Load intents from intents.json
  2. Preprocess text  (lowercase, stopword removal, lemmatization)
  3. Vectorise with TF-IDF (unigrams + bigrams)
  4. Train a Logistic Regression classifier
  5. Evaluate with 5-fold cross-validation
  6. Save model.pkl  and  vectorizer.pkl  for prediction

Run this script once before starting the assistant:
    python train_model.py
"""

import json
import pickle
import os
import warnings
warnings.filterwarnings("ignore")

# ── NLP ──────────────────────────────────────────────────────────────
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# ── ML ───────────────────────────────────────────────────────────────
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sklearn.pipeline import Pipeline

# ─────────────────────────────────────────────────────────────────────
# 1.  Download required NLTK resources (runs once; cached after that)
# ─────────────────────────────────────────────────────────────────────
def _download_nltk_resources():
    resources = [
        ("corpora/stopwords",    "stopwords"),
        ("corpora/wordnet",      "wordnet"),
        ("tokenizers/punkt",     "punkt"),
        ("taggers/averaged_perceptron_tagger", "averaged_perceptron_tagger"),
    ]
    for path, package in resources:
        try:
            nltk.data.find(path)
        except LookupError:
            print(f"  Downloading NLTK resource: {package} ...")
            nltk.download(package, quiet=True)

_download_nltk_resources()

# ─────────────────────────────────────────────────────────────────────
# 2.  Text Preprocessing
# ─────────────────────────────────────────────────────────────────────
_lemmatizer = WordNetLemmatizer()
_stop_words  = set(stopwords.words("english"))

# Words to KEEP even if they appear in the stopword list
# (because they are meaningful in assistant commands)
_KEEP_WORDS = {"what", "who", "how", "when", "where", "why", "open", "play",
               "search", "find", "show", "tell", "give", "check", "start",
               "stop", "exit", "bye", "hello", "hi", "hey", "good", "help",
               "me", "my", "you", "i", "am", "are", "is", "do", "not", "no"}

STOP_WORDS_FILTERED = _stop_words - _KEEP_WORDS


def preprocess(text: str) -> str:
    """
    Lowercase → tokenise → remove punctuation tokens →
    remove unimportant stopwords → lemmatise → rejoin.

    Example:
        "Tell me a Joke please!"  →  "tell joke please"
    """
    tokens = nltk.word_tokenize(text.lower())
    cleaned = [
        _lemmatizer.lemmatize(tok)
        for tok in tokens
        if tok.isalpha() and tok not in STOP_WORDS_FILTERED
    ]
    return " ".join(cleaned) if cleaned else text.lower()


# ─────────────────────────────────────────────────────────────────────
# 3.  Main training function
# ─────────────────────────────────────────────────────────────────────
def train():
    print("=" * 56)
    print("  Marry — ML Intent Classifier  |  Training Started")
    print("=" * 56)

    # ── Paths ──────────────────────────────────────────────────
    base = os.path.dirname(os.path.abspath(__file__))
    intents_path    = os.path.join(base, "intents.json")
    model_path      = os.path.join(base, "model.pkl")
    vectorizer_path = os.path.join(base, "vectorizer.pkl")

    # ── Load intents.json ──────────────────────────────────────
    print("\n[1/5]  Loading intents.json ...")
    with open(intents_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # ── Build corpus ───────────────────────────────────────────
    print("[2/5]  Building training corpus ...")
    X_raw, y = [], []
    intent_counts = {}

    for intent in data["intents"]:
        tag = intent["tag"]
        intent_counts[tag] = len(intent["patterns"])
        for pattern in intent["patterns"]:
            X_raw.append(pattern)
            y.append(tag)

    print(f"        Total samples  : {len(X_raw)}")
    print(f"        Total intents  : {len(set(y))}")
    for tag, count in sorted(intent_counts.items()):
        print(f"          • {tag:<25} {count} patterns")

    # ── Preprocess ─────────────────────────────────────────────
    print("\n[3/5]  Preprocessing text (lowercasing, stopwords, lemmatisation) ...")
    X_processed = [preprocess(text) for text in X_raw]

    # ── TF-IDF Vectoriser ──────────────────────────────────────
    # ngram_range=(1,2) captures both single words and 2-word phrases
    # min_df=1  keeps even rare terms (small dataset)
    # sublinear_tf=True  applies log normalisation to term frequencies
    print("[4/5]  Fitting TF-IDF Vectoriser (unigrams + bigrams) ...")
    vectorizer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        min_df=1,
        sublinear_tf=True,
        analyzer="word",
    )
    X_vec = vectorizer.fit_transform(X_processed)
    print(f"        Vocabulary size : {len(vectorizer.vocabulary_)} terms")

    # ── Logistic Regression ────────────────────────────────────
    # C=10     → less regularisation (favours fitting on small data)
    # max_iter → enough iterations for convergence
    # class_weight='balanced' → handles any imbalance between intents
    print("[5/5]  Training Logistic Regression classifier ...")
    model = LogisticRegression(
        C=10.0,
        max_iter=1000,
        class_weight="balanced",
        solver="lbfgs",
    )
    model.fit(X_vec, y)

    # ── Evaluation ─────────────────────────────────────────────
    print("\n" + "-" * 56)
    print("  EVALUATION RESULTS")
    print("-" * 56)

    # Training accuracy (how well the model fits its own data)
    train_acc = model.score(X_vec, y)
    print(f"  Training Accuracy  : {train_acc * 100:.2f}%")

    # 5-fold cross-validation — a more realistic generalisation estimate
    try:
        cv_scores = cross_val_score(model, X_vec, y, cv=5, scoring="accuracy")
        print(f"  5-Fold CV Accuracy : {cv_scores.mean() * 100:.2f}%  "
              f"(±{cv_scores.std() * 100:.2f}%)")
    except Exception:
        print("  (Cross-validation skipped — too few samples per class)")

    # Per-class report if there's enough label diversity
    try:
        if len(set(y)) > 1:
            X_train, X_test, y_train, y_test = train_test_split(
                X_vec, y, test_size=0.25, random_state=42, stratify=y
            )
            model_tmp = LogisticRegression(
                C=10.0, max_iter=1000, class_weight="balanced",
                solver="lbfgs"
            )
            model_tmp.fit(X_train, y_train)
            y_pred = model_tmp.predict(X_test)
            print(f"  Test-set Accuracy  : {accuracy_score(y_test, y_pred) * 100:.2f}%")
            print("\n  Per-class Classification Report (test split):")
            print(classification_report(y_test, y_pred, zero_division=0))
    except Exception as ex:
        print(f"  (Holdout evaluation unavailable: {ex})")

    print("-" * 56)

    # ── Save artefacts ─────────────────────────────────────────
    with open(vectorizer_path, "wb") as f:
        pickle.dump(vectorizer, f)
    print(f"\n  Vectorizer saved → {vectorizer_path}")

    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    print(f"  Model saved       → {model_path}")

    print("\n  Training complete! You can now start the assistant.\n")


# ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    train()
