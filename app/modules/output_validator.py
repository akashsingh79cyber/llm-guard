import re

from app.modules import dlp

TOXIC_PATTERNS = [
    r"\bidiot\b", r"\bstupid\b", r"\bmoron\b", r"\bdumb\b", r"\bscum\b",
    r"\bi hate you\b", r"\bshut up\b", r"\bkill yourself\b", r"\bgo die\b",
    r"\byou are worthless\b", r"\bpiece of trash\b",
    r"how to make a bomb", r"how to build a weapon",
]
TOXIC_RE = re.compile("|".join(TOXIC_PATTERNS), re.IGNORECASE)


def redact_text(text):
    """LLM ke jawab me bacha hua raw sensitive data [REDACTED_...] se badalta hai."""
    findings = []
    for label, pattern in dlp.PATTERNS:

        def repl(m, label=label):
            value = m.group(0)
            if label == "CREDIT_CARD" and not dlp.luhn_ok(value):
                return value
            findings.append(label)
            return f"[REDACTED_{label}]"

        text = pattern.sub(repl, text)
    return text, findings


def is_toxic(text):
    return bool(TOXIC_RE.search(text))


def validate_response(data, system_instruction=""):
    """Response check karo. (clean_data, findings) wapas deta hai."""
    findings = []
    marker = system_instruction[:40].lower()
    for choice in data.get("choices", []):
        msg = choice.get("message") or {}
        content = msg.get("content")
        if not isinstance(content, str):
            continue
        # 1. System prompt leak
        if marker and marker in content.lower():
            msg["content"] = "[BLOCKED: response contained confidential instructions]"
            findings.append("SYSTEM_PROMPT_LEAK")
            continue
        # 2. Toxic / unsafe content
        if is_toxic(content):
            msg["content"] = "[BLOCKED: response contained unsafe or toxic content]"
            findings.append("TOXIC_CONTENT")
            continue
        # 3. PII / secrets leak
        clean, found = redact_text(content)
        msg["content"] = clean
        findings.extend(found)
    return data, findings