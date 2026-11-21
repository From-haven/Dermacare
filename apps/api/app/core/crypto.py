"""
crypto.py — Cryptographic primitives for DermaCare Agent.
- Envelope encryption with AES-256-GCM
- Unique DEK per image wrapped by APP_MASTER_KEY
- Secure CSPRNG nonce generation
"""
import os
import secrets
import base64
from typing import Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.config import APP_MASTER_KEY

def generate_random_bytes(length: int = 32) -> bytes:
    """Generate cryptographically secure random bytes (CSPRNG)."""
    return secrets.token_bytes(length)

def wrap_dek(dek: bytes, master_key: bytes = APP_MASTER_KEY) -> str:
    """Wrap (encrypt) per-image DEK with master key using AES-256-GCM."""
    aesgcm = AESGCM(master_key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, dek, None)
    wrapped = nonce + ciphertext
    return base64.b64encode(wrapped).decode('utf-8')

def unwrap_dek(wrapped_dek_b64: str, master_key: bytes = APP_MASTER_KEY) -> bytes:
    """Unwrap (decrypt) per-image DEK with master key."""
    wrapped = base64.b64decode(wrapped_dek_b64)
    nonce = wrapped[:12]
    ciphertext = wrapped[12:]
    aesgcm = AESGCM(master_key)
    return aesgcm.decrypt(nonce, ciphertext, None)

def encrypt_image_bytes(image_data: bytes, dek: bytes = None) -> Tuple[bytes, str]:
    """
    Encrypt image bytes with a unique DEK using AES-256-GCM.
    Returns: (encrypted_bytes, wrapped_dek_base64)
    """
    if dek is None:
        dek = generate_random_bytes(32)
    aesgcm = AESGCM(dek)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, image_data, None)
    encrypted_payload = nonce + ciphertext
    wrapped_dek_b64 = wrap_dek(dek)
    return encrypted_payload, wrapped_dek_b64

def decrypt_image_bytes(encrypted_payload: bytes, wrapped_dek_b64: str) -> bytes:
    """Decrypt image bytes using unwrapped DEK."""
    dek = unwrap_dek(wrapped_dek_b64)
    nonce = encrypted_payload[:12]
    ciphertext = encrypted_payload[12:]
    aesgcm = AESGCM(dek)
    return aesgcm.decrypt(nonce, ciphertext, None)

def encrypt_nonce(nonce32: bytes, master_key: bytes = APP_MASTER_KEY) -> str:
    """Encrypt consent nonce for off-chain storage."""
    aesgcm = AESGCM(master_key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, nonce32, None)
    return base64.b64encode(nonce + ciphertext).decode('utf-8')

def decrypt_nonce(enc_nonce_b64: str, master_key: bytes = APP_MASTER_KEY) -> bytes:
    """Decrypt consent nonce."""
    raw = base64.b64decode(enc_nonce_b64)
    nonce = raw[:12]
    ciphertext = raw[12:]
    aesgcm = AESGCM(master_key)
    return aesgcm.decrypt(nonce, ciphertext, None)
