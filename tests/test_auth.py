from app.modules import auth

t = auth.login("akash", "employee123")
assert t and auth.verify(t) == {"user": "akash", "role": "employee"}
assert auth.login("akash", "wrong") is None
assert auth.verify("fake.token.value") is None
assert auth.verify(t + "x") is None  # tampered token

print("AUTH TESTS PASSED")