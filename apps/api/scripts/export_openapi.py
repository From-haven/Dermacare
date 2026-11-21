"""
export_openapi.py — Exports OpenAPI 3.1.0 specification for DermaCare Agent REST API.
Writes to docs/OPENAPI.json.
"""
import json
import os

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
OUTPUT_PATH = os.path.join(WORKSPACE_ROOT, "docs/OPENAPI.json")

openapi_spec = {
    "openapi": "3.1.0",
    "info": {
        "title": "DermaCare Agent API",
        "version": "1.0.0",
        "description": "Privacy-Preserving Dermatology Tracking, Reference Lookup, and Consent-Based Clinic Matching API.",
        "contact": {
            "name": "DermaCare Research Team",
            "url": "https://dermacare.demo.test"
        }
    },
    "servers": [
        {"url": "http://localhost:8000", "description": "Local Development Server"},
        {"url": "http://localhost:3000", "description": "Frontend Dev Proxy"}
    ],
    "paths": {
        "/health": {
            "get": {
                "summary": "Health check",
                "responses": {
                    "200": {"description": "Service healthy"}
                }
            }
        },
        "/api/auth/register": {
            "post": {
                "summary": "Register patient",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["email", "password"],
                                "properties": {
                                    "email": {"type": "string", "format": "email"},
                                    "password": {"type": "string", "minLength": 8},
                                    "display_name": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "responses": {"201": {"description": "Patient registered successfully"}}
            }
        },
        "/api/auth/login": {
            "post": {
                "summary": "Login user",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["email", "password"],
                                "properties": {
                                    "email": {"type": "string"},
                                    "password": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "responses": {"200": {"description": "Access token issued"}}
            }
        },
        "/api/me": {
            "get": {
                "summary": "Get current user profile",
                "security": [{"bearerAuth": []}],
                "responses": {"200": {"description": "User profile data"}}
            },
            "delete": {
                "summary": "Delete user account and all personal data (GDPR / Law 91/2025)",
                "security": [{"bearerAuth": []}],
                "responses": {"200": {"description": "User deleted"}}
            }
        },
        "/api/cases": {
            "get": {
                "summary": "List cases for current patient",
                "security": [{"bearerAuth": []}],
                "responses": {"200": {"description": "List of cases"}}
            },
            "post": {
                "summary": "Create new skin tracking case",
                "security": [{"bearerAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["profile_type", "primary_site"],
                                "properties": {
                                    "profile_type": {"type": "string", "enum": ["acne", "eczema", "psoriasis", "other"]},
                                    "primary_site": {"type": "string"},
                                    "title": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "responses": {"201": {"description": "Case created"}}
            }
        },
        "/api/clinics/nearby": {
            "get": {
                "summary": "Find nearby dermatology clinics via GPS (no server-side coordinate storage)",
                "parameters": [
                    {"name": "lat", "in": "query", "required": True, "schema": {"type": "number"}},
                    {"name": "lng", "in": "query", "required": True, "schema": {"type": "number"}},
                    {"name": "radius_km", "in": "query", "schema": {"type": "number", "default": 10.0}}
                ],
                "responses": {"200": {"description": "Nearby clinics ordered by Verified Partner first then distance"}}
            }
        },
        "/api/consents": {
            "get": {
                "summary": "List consents granted by patient",
                "security": [{"bearerAuth": []}],
                "responses": {"200": {"description": "List of active and past consents"}}
            },
            "post": {
                "summary": "Grant access consent to clinic with CSPRNG commitment",
                "security": [{"bearerAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["recipient_clinic_id", "scope"],
                                "properties": {
                                    "recipient_clinic_id": {"type": "string"},
                                    "case_id": {"type": "string"},
                                    "scope": {"type": "string", "enum": ["full", "measurements_only"]},
                                    "expires_days": {"type": "integer", "default": 30}
                                }
                            }
                        }
                    }
                },
                "responses": {"201": {"description": "Consent granted"}}
            }
        }
    },
    "components": {
        "securitySchemes": {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            }
        }
    }
}

def export_openapi():
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(openapi_spec, f, indent=2, ensure_ascii=False)
    print(f"OpenAPI specification written to {OUTPUT_PATH}")

if __name__ == "__main__":
    export_openapi()
