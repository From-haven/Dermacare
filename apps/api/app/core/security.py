"""
security.py — Authentication, password hashing, and JWT tokens.
Supports:
- Password hashing (bcrypt with fallback)
- User session JWT
- Short-lived 60-second Image Access Tokens
"""
import time
import jwt
import hashlib
import hmac
import os
import bcrypt
from app.config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_MINUTES
from app.errors import UnauthenticatedException

def hash_password(password: str) -> str:
    """Hash password using bcrypt with salt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def create_access_token(user_id: str, role: str, email: str, expires_in_seconds: int = None) -> str:
    """Create JWT access token for user."""
    if expires_in_seconds is None:
        expires_in_seconds = JWT_EXPIRE_MINUTES * 60
    now = int(time.time())
    payload = {
        "sub": user_id,
        "role": role,
        "email": email,
        "iat": now,
        "exp": now + expires_in_seconds
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_access_token(token: str) -> dict:
    """Decode and verify JWT access token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise UnauthenticatedException("Token đã hết hạn")
    except Exception:
        raise UnauthenticatedException("Token không hợp lệ")

def create_image_token(image_id: str, user_id: str, lifetime_seconds: int = 60) -> str:
    """Create short-lived 60-second token for viewing encrypted image."""
    now = int(time.time())
    payload = {
        "kind": "image_access",
        "image_id": image_id,
        "sub": user_id,
        "iat": now,
        "exp": now + lifetime_seconds
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_image_token(token: str, expected_image_id: str) -> str:
    """Verify short-lived image token; returns user_id if valid."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("kind") != "image_access":
            raise UnauthenticatedException("Token không phải token xem ảnh")
        if payload.get("image_id") != expected_image_id:
            raise UnauthenticatedException("Token không khớp với ảnh yêu cầu")
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise UnauthenticatedException("Token xem ảnh đã hết hạn (60s)")
    except Exception:
        raise UnauthenticatedException("Token xem ảnh không hợp lệ")
