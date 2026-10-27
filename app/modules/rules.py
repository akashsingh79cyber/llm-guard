import json
import re
from pathlib import Path

RULES_FILE = Path(__file__).resolve().parent.parent / "rules.json"


def load_rules():
    with open(RULES_FILE, encoding="utf-8") as f:
        return json.load(f)


def user_text(messages):
    """Saare user messages ka text jodta hai."""
    parts = []
    for m in messages:
        if m.get("role") == "user" and isinstance(m.get("content"), str):
            parts.append(m["content"])
    return " ".join(parts)


def check_prompt(messages, rules=None):
    """Rule todne par dict deta hai, sab theek ho to None."""
    rules = rules or load_rules()
    text = user_text(messages)

    if len(text) > rules["max_prompt_length"]:
        return {
            "rule": "MAX_LENGTH",
            "reason": f"Prompt too long ({len(text)} > {rules['max_prompt_length']} chars)",
        }

    normalized = re.sub(r"\s+", " ", text.lower())
    for keyword in rules["blocked_keywords"]:
        if keyword.lower() in normalized:
            return {
                "rule": "BLOCKED_KEYWORD",
                "reason": f"Blocked phrase detected: '{keyword}'",
            }

    return None


def enforce_system_prompt(messages, rules=None):
    """User ke bheje system messages hatao, aur hamara safe system message sabse upar lagao."""
    rules = rules or load_rules()
    cleaned = [m for m in messages if m.get("role") != "system"]
    return [{"role": "system", "content": rules["system_instruction"]}] + cleaned