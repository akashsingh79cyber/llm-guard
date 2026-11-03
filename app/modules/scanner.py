import json
import pickle
import re
from pathlib import Path

MODELS_DIR = Path(__file__).resolve().parent.parent.parent / "models"
_model = None
_threshold = None

LEET = str.maketrans(
    {"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a", "$": "s"}
)


def normalize(text: str) -> str:
    """Obfuscation hatata hai: 'i g n o r e' -> 'ignore', '1gn0re' -> 'ignore'."""
    t = text.lower()
    t = re.sub(r"\b(?:[a-z] ){2,}[a-z]\b", lambda m: m.group(0).replace(" ", ""), t)

    def fix(m):
        w = m.group(0)
        if re.search(r"[a-z]", w) and re.search(r"[0-9@$]", w):
            return w.translate(LEET)
        return w

    t = re.sub(r"\S+", fix, t)
    return re.sub(r"\s+", " ", t).strip()


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
    """(is_attack, attack_probability). Original aur normalized, dono score hote hain, max liya jata hai."""
    if threshold is None:
        threshold = load_threshold()
    model = load_model()
    probs = model.predict_proba([text, normalize(text)])[:, 1]
    prob = float(max(probs))
    return prob >= threshold, prob