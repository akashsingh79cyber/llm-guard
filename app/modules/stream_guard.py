import json

from app.modules import dlp, output_validator


def process_sse_line(line, mapping):
    """Ek SSE 'data: {...}' line ko clean karta hai.
    (new_line, findings) wapas deta hai."""
    if not line.startswith("data:"):
        return line, []
    payload = line[5:].strip()
    if payload == "[DONE]" or not payload:
        return line, []
    try:
        obj = json.loads(payload)
    except Exception:
        return line, []

    findings = []
    for ch in obj.get("choices", []):
        delta = ch.get("delta") or {}
        text = delta.get("content")
        if not isinstance(text, str):
            continue
        if output_validator.is_toxic(text):
            delta["content"] = "[BLOCKED] "
            findings.append("TOXIC_CONTENT")
            continue
        clean, found = output_validator.redact_text(text)
        findings.extend(found)
        if mapping:
            clean = dlp.unmask_text(clean, mapping)
        delta["content"] = clean
    return "data: " + json.dumps(obj), findings