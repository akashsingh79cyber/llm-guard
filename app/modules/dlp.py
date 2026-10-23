import re

# Order matters: pehle API key/email, phir numbers
PATTERNS = [
    ("API_KEY", re.compile(r"\b(?:sk-[A-Za-z0-9_-]{16,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})\b")),
    ("EMAIL", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    ("CREDIT_CARD", re.compile(r"\b(?:\d[ -]?){13,19}\b")),
    ("SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("AADHAAR", re.compile(r"\b\d{4}\s\d{4}\s\d{4}\b")),
    ("PHONE", re.compile(r"(?:\+91[\s-]?)?\b[6-9]\d{9}\b")),
    ("PAN", re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")),
]


def luhn_ok(number: str) -> bool:
    """Credit card valid hai ya nahi (Luhn algorithm)."""
    digits = [int(c) for c in number if c.isdigit()]
    if not 13 <= len(digits) <= 19:
        return False
    total = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def mask_text(text: str, mapping: dict) -> str:
    """Sensitive data ko [EMAIL_1] jaise placeholder se badalta hai.
    mapping me placeholder -> asli value save hoti hai."""
    for label, pattern in PATTERNS:

        def repl(m):
            value = m.group(0)
            if label == "CREDIT_CARD" and not luhn_ok(value):
                return value
            n = sum(1 for k in mapping if k.startswith(f"[{label}_")) + 1
            placeholder = f"[{label}_{n}]"
            mapping[placeholder] = value
            return placeholder

        text = pattern.sub(repl, text)
    return text


def mask_messages(messages: list):
    """Saare messages ko mask karo. (masked messages, mapping) wapas deta hai."""
    mapping = {}
    for msg in messages:
        if isinstance(msg.get("content"), str):
            msg["content"] = mask_text(msg["content"], mapping)
    return messages, mapping


def unmask_text(text: str, mapping: dict) -> str:
    """Placeholder ko wapas asli value se badalta hai (return trip)."""
    for placeholder, value in mapping.items():
        text = text.replace(placeholder, value)
    return text