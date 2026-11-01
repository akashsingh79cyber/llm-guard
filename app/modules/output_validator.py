from app.modules import dlp


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
        # 2. PII / secrets leak
        clean, found = redact_text(content)
        msg["content"] = clean
        findings.extend(found)
    return data, findings