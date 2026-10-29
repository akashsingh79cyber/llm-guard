import pickle
from pathlib import Path

MODELS_DIR = Path(__file__).resolve().parent.parent.parent / "models"
_model = None


def load_model():
    global _model
    if _model is None:
        path = MODELS_DIR / "better.pkl"
        if not path.exists():
            path = MODELS_DIR / "baseline.pkl"
        with open(path, "rb") as f:
            _model = pickle.load(f)
    return _model


def scan(text: str, threshold: float = 0.5):
    """(is_attack, attack_probability) wapas deta hai."""
    model = load_model()
    prob = float(model.predict_proba([text])[0][1])
    return prob >= threshold, prob