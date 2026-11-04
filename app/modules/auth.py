import hashlib
import time

import jwt

from app import config

ALGO = "HS256"
TOKEN_TTL = 3600  # 1 ghanta


def _h(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# Demo users (real project me database/IdP hota)
USERS = {
    "admin": {"password": _h("admin123"), "role": "admin"},
    "akash": {"password": _h("employee123"), "role": "employee"},
    "guest1": {"password": _h("guest123"), "role": "guest"},
}


def login(username: str, password: str):
    """Sahi credentials par token deta hai, warna None."""
    user = USERS.get(username)
    if not user or user["password"] != _h(password):
        return None
    payload = {
        "sub": username,
        "role": user["role"],
        "exp": int(time.time()) + TOKEN_TTL,
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm=ALGO)


def verify(token: str):
    """Valid token par {'user', 'role'} deta hai, warna None."""
    try:
        data = jwt.decode(token, config.JWT_SECRET, algorithms=[ALGO])
        return {"user": data["sub"], "role": data["role"]}
    except jwt.PyJWTError:
        return None