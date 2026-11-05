import json
import re
from pathlib import Path

RULES_FILE = Path(__file__).resolve().parent.parent / "rules.json"


def load_rules():
    with open(RULES_FILE, encoding="utf-8") as f:
        return json.load(f)


def user_text(messages):
    parts = []
    for m in messages:
        if m.get("role") == "user" and isinstance(m.get("content"), str):
            parts.append(m["content"])
    return " ".join(parts)


def check_prompt(messages, rules=None, role="employee"):
    """Rule todne par dict deta hai, sab theek ho to None."""
    rules = rules or load_rules()
    text = user_text(messages)

    limit = rules.get("role_limits", {}).get(role, rules["max_prompt_length"])
    if len(text) > limit:
        return {
            "rule": "MAX_LENGTH",
            "reason": f"Prompt too long for role '{role}' ({len(text)} > {limit} chars)",
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
    rules = rules or load_rules()
    cleaned = [m for m in messages if m.get("role") != "system"]
    return [{"role": "system", "content": rules["system_instruction"]}] + cleaned