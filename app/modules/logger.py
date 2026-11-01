import json
from datetime import datetime, timezone
from pathlib import Path

from app.modules import dlp

LOG_FILE = Path(__file__).resolve().parent.parent.parent / "logs" / "guard.jsonl"


def log_event(event, user_id="anonymous", rule=None, reason=None, score=None, prompt=""):
    """Ek event ko JSON line ki tarah file me likhta hai (SIEM format).
    Prompt me PII ho sakta hai, isliye pehle mask karke, 200 chars tak save karte hain."""
    LOG_FILE.parent.mkdir(exist_ok=True)
    safe_prompt = dlp.mask_text(prompt or "", {})[:200]
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "user_id": user_id,
        "rule": rule,
        "reason": reason,
        "score": round(score, 3) if score is not None else None,
        "prompt": safe_prompt,
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return record