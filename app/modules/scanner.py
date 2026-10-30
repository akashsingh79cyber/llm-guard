import json
import pickle
from pathlib import Path

MODELS_DIR = Path(__file__).resolve().parent.parent.parent / "models"
_model = None
_threshold = None


def load_model():
    global _model
    if _model is None:
        path = MODELS_DIR / "better.pkl"
        if not path.exists():
            path = MODELS_DIR / "baseline.pkl"
        with open(path, "rb") as f:
            _model = pickle.load(f)
    return _model


def load_threshold():
    global _threshold
    if _threshold is None:
        path = MODELS_DIR / "threshold.json"
        if path.exists():
            _threshold = float(json.loads(path.read_text())["threshold"])
        else:
            _threshold = 0.5
    return _threshold


def scan(text: str, threshold: float = None):
    """(is_attack, attack_probability) wapas deta hai."""
    if threshold is None:
        threshold = load_threshold()
    model = load_model()
    prob = float(model.predict_proba([text])[0][1])
    return prob >= threshold, prob