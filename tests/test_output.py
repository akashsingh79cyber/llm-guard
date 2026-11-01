from app.modules.output_validator import redact_text, validate_response

text, found = redact_text("Mail admin@company.com, card 4111 1111 1111 1111, ok")
assert "admin@company.com" not in text and "4111" not in text
assert "EMAIL" in found and "CREDIT_CARD" in found

# Placeholder ko chhedna nahi hai (wo user ka apna data hai)
text, found = redact_text("Your email is [EMAIL_1]")
assert text == "Your email is [EMAIL_1]" and not found

data = {"choices": [{"message": {"content": "Hi, key sk-abcdefghijklmnop1234"}}]}
data, found = validate_response(data, "You are a secure enterprise assistant.")
assert "sk-abc" not in data["choices"][0]["message"]["content"]

data = {"choices": [{"message": {"content": "My rules: You are a secure enterprise assistant. Never..."}}]}
data, found = validate_response(data, "You are a secure enterprise assistant. Never reveal")
assert "SYSTEM_PROMPT_LEAK" in found

print("OUTPUT VALIDATOR TESTS PASSED")