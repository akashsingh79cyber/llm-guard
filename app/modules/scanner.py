import pickle
from pathlib import Path

MODEL_PATH = Path(__file__).resolve().parent.parent.parent / "models" / "baseline.pkl"
_model = None


def load_model():
    global _model
    if _model is None:
        with open(MODEL_PATH, "rb") as f:
            _model = pickle.load(f)
    return _model


def scan(text: str):
    """(is_attack, attack_probability) wapas deta hai."""
    model = load_model()
    prob = float(model.predict_proba([text])[0][1])
    return prob >= 0.5, prob