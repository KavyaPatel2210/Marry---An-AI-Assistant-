import json
import pickle
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

def train():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, 'intents.json')
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    X_train = []
    y_train = []

    for intent in data['intents']:
        tag = intent['tag']
        for pattern in intent['patterns']:
            X_train.append(pattern)
            y_train.append(tag)

    # Use TF-IDF Vectorizer with n-grams
    vectorizer = TfidfVectorizer(lowercase=True, ngram_range=(1, 2))
    X_vec = vectorizer.fit_transform(X_train)
 
    # Use Logistic Regression with balanced weights and less regularization (C=10)
    model = LogisticRegression(max_iter=500, class_weight='balanced', C=10.0)
    model.fit(X_vec, y_train)

    # Show accuracy on training data
    accuracy = model.score(X_vec, y_train)
    print(f"Model trained successfully. Training Accuracy: {accuracy * 100:.2f}%")

    with open(os.path.join(current_dir, 'vectorizer.pkl'), 'wb') as f:
        pickle.dump(vectorizer, f)
    
    with open(os.path.join(current_dir, 'model.pkl'), 'wb') as f:
        pickle.dump(model, f)

if __name__ == "__main__":
    train()
