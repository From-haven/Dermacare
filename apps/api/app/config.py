"""
config.py — DermaCare Agent configuration.
Loads configuration from environment variables with safe defaults.
"""
import os
import base64

def get_env(key: str, default: str = "") -> str:
    return os.getenv(key, default)

APP_ENV = get_env("APP_ENV", "dev")
APP_MASTER_KEY_RAW = get_env("APP_MASTER_KEY", "GzgYBypUacbZPq2aG7/aPTuPDreBVCLtgtutKUteZCY=")
try:
    APP_MASTER_KEY = base64.b64decode(APP_MASTER_KEY_RAW)
    if len(APP_MASTER_KEY) != 32:
        raise ValueError("APP_MASTER_KEY must be 32 bytes")
except Exception:
    # Safe 32-byte fallback for dev
    APP_MASTER_KEY = b"\x00" * 32

JWT_SECRET = get_env("JWT_SECRET", "default_insecure_jwt_secret_for_dev_32_bytes_long_ok")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60 * 24  # 24 hours

DATABASE_URL = get_env("DATABASE_URL", "sqlite:///data/derma.db")
REDIS_URL = get_env("REDIS_URL", "redis://localhost:6379/0")

S3_ENDPOINT = get_env("S3_ENDPOINT", "http://localhost:9000")
S3_ACCESS_KEY = get_env("S3_ACCESS_KEY", "minio")
S3_SECRET_KEY = get_env("S3_SECRET_KEY", "minio12345")
S3_BUCKET = get_env("S3_BUCKET", "derma-private")

AUTH_MODE = get_env("AUTH_MODE", "local")  # local | privy
WALLET_MODE = get_env("WALLET_MODE", "local-dev")  # local-dev | privy
CHAIN_MODE = get_env("CHAIN_MODE", "mock")  # mock | anvil | fuji
LLM_PROVIDER = get_env("LLM_PROVIDER", "none")  # none | gemini | anthropic | openai
LLM_API_KEY = get_env("LLM_API_KEY", "")

FUJI_RPC_URL = get_env("FUJI_RPC_URL", "https://api.avax-test.network/ext/bc/C/rpc")
CHAIN_ID = int(get_env("CHAIN_ID", "43113"))
RELAYER_PRIVATE_KEY = get_env("RELAYER_PRIVATE_KEY", "")
CONSENT_REGISTRY_ADDRESS = get_env("CONSENT_REGISTRY_ADDRESS", "")
TEST_TOKEN_ADDRESS = get_env("TEST_TOKEN_ADDRESS", "")
SETTLEMENT_ADDRESS = get_env("SETTLEMENT_ADDRESS", "")
RELAYER_DAILY_TX_CAP = int(get_env("RELAYER_DAILY_TX_CAP", "200"))

CLINIC_SEARCH_DEFAULT_RADIUS_KM = float(get_env("CLINIC_SEARCH_DEFAULT_RADIUS_KM", "10"))
CLINIC_SEARCH_MAX_RADIUS_KM = float(get_env("CLINIC_SEARCH_MAX_RADIUS_KM", "50"))
PARTNER_PACKAGE_PRICE_TEST = float(get_env("PARTNER_PACKAGE_PRICE_TEST", "100"))
PARTNER_PACKAGE_DAYS = int(get_env("PARTNER_PACKAGE_DAYS", "30"))

LOOKUP_TOP_K = int(get_env("LOOKUP_TOP_K", "5"))
LOOKUP_MIN_COSINE = float(get_env("LOOKUP_MIN_COSINE", "0.35"))


# Settings object proxy
import sys
settings = sys.modules[__name__]
