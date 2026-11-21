# DermaCare Agent — System Architecture Specification

## 1. System Overview

**DermaCare Agent** is a privacy-preserving system for longitudinal skin condition tracking, computer vision feature measurement, non-diagnostic reference lookup, and consent-controlled clinic referral anchored on the Avalanche blockchain.

```mermaid
graph TD
    User([Patient / User]) -->|HTTPS / WSS| WebUI[Frontend Web App /apps/web]
    Clinician([Dermatologist]) -->|HTTPS / WSS| WebUI
    Admin([System Admin]) -->|HTTPS / WSS| WebUI

    WebUI -->|REST API /api/| API[Unified Dispatcher & API Server /apps/api]
    
    subgraph "Core Backend Services"
        API --> Auth[Auth & RBAC Module]
        API --> StateMachine[Case Workflow State Machine]
        API --> QualityGate[Vision Quality Gate]
        API --> VectorLookup[Vector Cosine Reference Engine]
        API --> AgentEngine[LangGraph Safety & Triage Engine]
        API --> ConsentMgr[CSPRNG Consent Manager]
        API --> GPSMatcher[Privacy Haversine Clinic Matcher]
    end

    subgraph "Secure Storage Layer"
        QualityGate -->|AES-256-GCM Wrapped DEK| Storage[Local / S3 Encrypted Storage]
        API --> SQLite[(PostgreSQL / SQLite Database)]
    end

    subgraph "Blockchain Evidence Layer (Avalanche)"
        ConsentMgr -->|EIP-712 Signatures & Commitments| Relayer[Avalanche Relayer Client]
        Relayer --> ConsentRegistry[ConsentRegistry.sol]
        Relayer --> TestSettlement[TestSettlement.sol]
        Relayer --> MerkleAnchor[Merkle Audit Anchors]
    end
```

---

## 2. The Four Provenance Layers

To guarantee medical transparency and prevent machine learning hallucinations from being mistaken for clinical truth, every data point carries a strict **Provenance Badge**:

1. **AI Measured (`ai_measured`)**: Quantitative features computed directly by deterministic computer vision heuristics (sharpness Laplacian, erythema a* index, lesion area ratio). Never produces a definitive diagnosis.
2. **User Reported (`user_reported`)**: Subjective symptom timelines, onset durations, and red-flag answers provided directly by the patient through structured intake forms.
3. **Clinician Entered (`clinician_entered`)**: Formal clinical scores (IGA, EASI, PASI) and clinical observations entered by verified dermatologists after authenticated review.
4. **Synthetic Data (`synthetic`)**: Clear badge affixed to demo fixtures, calibrated baseline curves, or simulated records to ensure no synthetic sample is ever confused with real human health data.

---

## 3. Data Flow & Zero-PII Guarantee

```mermaid
sequenceDiagram
    autonumber
    actor Patient
    participant Web as Web Client
    participant API as DermaCare API
    participant ML as Vision Pipeline
    participant DB as Encrypted Storage & DB
    participant Chain as Avalanche C-Chain

    Patient->>Web: Select body site & answers symptoms
    Patient->>Web: Captures skin lesion photo
    Web->>API: Strips EXIF & uploads image
    API->>ML: Checks Sharpness, Exposure, Glare, Resolution
    alt Quality Gate Fails
        ML-->>Web: RETAKE advice (blurry / dark / glare)
    else Quality Gate Passes
        ML->>DB: Encrypt image with per-image DEK (AES-256-GCM)
        ML->>API: Measures Erythema & Lesion Area
        API->>API: Computes feature vector & queries Knowledge Base
        API-->>Web: Similar conditions (Alphabetical, NO %, Disclaimer)
    end

    Patient->>Web: Requests nearby clinic consultation
    Web->>API: Sends temporary device GPS (lat, lng)
    API->>API: Sorts Verified Partners first, Haversine distance
    API-->>Web: Returns matching clinics (GPS discarded from memory)
    
    Patient->>Web: Grants sharing consent
    Web->>API: Submits CSPRNG commitment hash
    API->>Chain: Anchors commitment on ConsentRegistry.sol (Zero PII)
```

---

## 4. Cryptographic Envelope Encryption

Images at rest are encrypted using envelope encryption:
- A unique **Data Encryption Key (DEK)** (256-bit AES) is generated for each uploaded image using a CSPRNG (`os.urandom(32)`).
- The raw image is encrypted with `AES-256-GCM`.
- The DEK is encrypted (wrapped) with the application's **Master Key** (`APP_MASTER_KEY`).
- Clinicians accessing the image receive a short-lived (60-second) JWT image token that permits one-time in-memory decryption.

---

## 5. Non-Diagnostic Safety Boundary

- **No Diagnostic Statements**: The system strictly forbids outputting words such as `"bạn bị mắc"`, `"khỏi bệnh"`, `"nặng hơn"`, `"nguy hiểm"`.
- **Zero Percentage Probabilities**: Similar conditions are displayed strictly for educational reference and sorted alphabetically. No percentages or disease ranking scores are exposed to the user.
- **Mandatory Disclaimers**: A persistent banner is permanently fixed across all web views:
  > *"LƯU Ý QUAN TRỌNG: Công cụ tham khảo & theo dõi tiến triển tổn thương da liễu, không phải chẩn đoán y khoa."*
