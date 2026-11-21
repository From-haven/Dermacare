#!/usr/bin/env python3
"""
gen_keys.py — Generate cryptographic secrets for DermaCare Agent.
Produces:
- APP_MASTER_KEY: 32 bytes base64
- JWT_SECRET: 32 bytes hex
"""
import sys
import secrets
import base64
import os

def generate_keys():
    master_key = base64.b64encode(secrets.token_bytes(32)).decode('utf-8')
    jwt_secret = secrets.token_hex(32)
    return master_key, jwt_secret

def main():
    master_key, jwt_secret = generate_keys()
    print(f"APP_MASTER_KEY={master_key}")
    print(f"JWT_SECRET={jwt_secret}")

    if "--env" in sys.argv or not os.path.exists(".env"):
        env_example_path = ".env.example"
        env_path = ".env"
        if os.path.exists(env_example_path):
            with open(env_example_path, "r", encoding="utf-8") as f:
                content = f.read()
            content = content.replace("APP_MASTER_KEY=", f"APP_MASTER_KEY={master_key}")
            content = content.replace("JWT_SECRET=", f"JWT_SECRET={jwt_secret}")
            with open(env_path, "w", encoding="utf-8") as f:
                f.write(content)
            print("Successfully written keys to .env")

if __name__ == "__main__":
    main()
