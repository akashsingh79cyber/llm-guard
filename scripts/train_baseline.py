import pickle
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

df = pd.read_csv("data/dataset.csv")
X_train, X_test, y_train, y_test = train_test_split(
    df["text"], df["label"], test_size=0.2, random_state=42, stratify=df["label"]
)

model = Pipeline([
    ("tfidf", TfidfVectorizer(ngram_range=(1, 2), lowercase=True, sublinear_tf=True)),
    ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
])
model.fit(X_train, y_train)

pred = model.predict(X_test)
print("=== BASELINE REPORT (TF-IDF + Logistic Regression) ===")
print("Train rows:", len(X_train), "| Test rows:", len(X_test))
print(classification_report(y_test, pred, target_names=["safe", "attack"], digits=3))
print("Confusion matrix [rows=actual, cols=predicted]:")
print(confusion_matrix(y_test, pred))

Path("models").mkdir(exist_ok=True)
with open("models/baseline.pkl", "wb") as f:
    pickle.dump(model, f)
print("\nModel saved: models/baseline.pkl")