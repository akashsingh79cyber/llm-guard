from app.modules.dlp import mask_text, unmask_text

text = (
    "Mera email ramesh@gmail.com hai, card 4111 1111 1111 1111, "
    "SSN 123-45-6789, key sk-abcdefghijklmnop1234, phone 9876543210"
)
mapping = {}
masked = mask_text(text, mapping)

print("BEFORE:", text)
print("AFTER :", masked)
print("MAP   :", mapping)

assert "ramesh@gmail.com" not in masked
assert "4111" not in masked
assert "123-45-6789" not in masked
assert "sk-abcdefghijklmnop1234" not in masked
assert unmask_text(masked, mapping) == text
print("\nALL TESTS PASSED")