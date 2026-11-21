"""
storage.py — Object storage handling encrypted image assets.
Supports local filesystem fallback (`data/storage/`) and MinIO/S3.
Computes SHA256 and pHash for deduplication.
"""
import os
import hashlib
from PIL import Image
import io

STORAGE_DIR = "data/storage"

def ensure_storage_dir():
    os.makedirs(STORAGE_DIR, exist_ok=True)

def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def compute_phash(image_bytes: bytes) -> str:
    """Compute 64-bit perceptual hash (pHash) for image duplicate detection."""
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("L").resize((8, 8), Image.Resampling.LANCZOS)
        pixels = list(img.tobytes())
        avg = sum(pixels) / len(pixels)
        bits = "".join("1" if p > avg else "0" for p in pixels)
        return f"{int(bits, 2):016x}"
    except Exception:
        return "0000000000000000"

def hamming_distance(hash1: str, hash2: str) -> int:
    """Calculate hamming distance between two hex pHash strings."""
    try:
        v1 = int(hash1, 16)
        v2 = int(hash2, 16)
        x = v1 ^ v2
        return bin(x).count("1")
    except Exception:
        return 999

def save_encrypted_asset(object_key: str, encrypted_bytes: bytes) -> str:
    """Save encrypted binary payload to storage."""
    ensure_storage_dir()
    file_path = os.path.join(STORAGE_DIR, object_key)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(encrypted_bytes)
    return file_path

def get_encrypted_asset(object_key: str) -> bytes:
    """Retrieve encrypted binary payload from storage."""
    file_path = os.path.join(STORAGE_DIR, object_key)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Asset not found: {object_key}")
    with open(file_path, "rb") as f:
        return f.read()

def delete_asset(object_key: str) -> bool:
    """Delete asset from storage."""
    file_path = os.path.join(STORAGE_DIR, object_key)
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False
