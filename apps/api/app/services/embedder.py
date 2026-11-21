"""
embedder.py — Feature Vector Embedder (fv-1).
Constructs 64-dimensional feature vector:
- 12 body site dimensions (0 or 1)
- 28 user-reported symptom dimensions (0, 0.5, 1)
- 5 onset timing dimensions (0 or 1)
- 6 visual measurement dimensions (normalized 0 to 1)
- 13 reserved dimensions (= 0.0)
Total: 51 active + 13 reserved = 64 dimensions.
"""
import math
from typing import Dict, List, Any

FEATURE_KEYS_64 = [
    # 1. Body Sites (12)
    "site_face", "site_scalp", "site_neck", "site_trunk_front",
    "site_back", "site_arms", "site_hands", "site_legs",
    "site_feet", "site_folds", "site_nails", "site_other",
    # 2. Symptoms (28)
    "itch", "redness", "scaling", "dryness", "oozing", "crusting",
    "blisters", "pustules", "papules", "plaques", "pain", "burning",
    "bleeding", "cracking", "spreading", "recurrent", "ring_shape",
    "wheals", "pale_patch", "dark_patch", "night_itch_contacts",
    "one_sided_band", "warty_surface", "blackheads", "contact_trigger",
    "flushing", "sweat_heat_trigger", "greasy_scale",
    # 3. Onset (5)
    "onset_lt3d", "onset_3_14d", "onset_2_8w", "onset_gt2m", "onset_sudden",
    # 4. Image Features (6)
    "img_area", "img_red_contrast", "img_components",
    "img_dispersion", "img_texture", "img_light_contrast",
    # 5. Reserved (13)
    "reserved_00", "reserved_01", "reserved_02", "reserved_03",
    "reserved_04", "reserved_05", "reserved_06", "reserved_07",
    "reserved_08", "reserved_09", "reserved_10", "reserved_11", "reserved_12"
]

SYMPTOM_VALUE_MAP = {
    "none": 0.0,
    "false": 0.0,
    False: 0.0,
    0: 0.0,
    "some": 0.5,
    "few": 0.3,
    "many": 1.0,
    "true": 1.0,
    True: 1.0,
    1: 1.0
}

class FeatureVectorEmbedder:
    version = "fv-1"

    @classmethod
    def embed_features(
        cls,
        body_site: str = None,
        symptoms: Dict[str, Any] = None,
        onset: str = None,
        measurements: Dict[str, float] = None,
        image_pass: bool = False
    ) -> List[float]:
        """Construct normalized 64-dimensional feature vector."""
        vec = [0.0] * 64
        key_to_idx = {k: i for i, k in enumerate(FEATURE_KEYS_64)}
        symptoms = symptoms or {}
        measurements = measurements or {}

        # 1. Body Site
        if body_site:
            clean_site = body_site.replace("site_", "")
            site_key = f"site_{clean_site}"
            if site_key in key_to_idx:
                vec[key_to_idx[site_key]] = 1.0

        # 2. Symptoms
        for sym_key, val in symptoms.items():
            if sym_key in key_to_idx:
                num_val = SYMPTOM_VALUE_MAP.get(val, 0.0)
                if isinstance(val, (int, float)):
                    num_val = min(1.0, max(0.0, float(val)))
                vec[key_to_idx[sym_key]] = float(num_val)

        # 3. Onset
        if onset:
            onset_key = onset if onset.startswith("onset_") else f"onset_{onset}"
            if onset_key in key_to_idx:
                vec[key_to_idx[onset_key]] = 1.0

        # 4. Image features (only if quality gate passed)
        if image_pass and measurements:
            if "affected_area_ratio" in measurements:
                vec[key_to_idx["img_area"]] = min(1.0, measurements["affected_area_ratio"] / 100.0)
            if "redness_contrast" in measurements:
                vec[key_to_idx["img_red_contrast"]] = min(1.0, max(0.0, measurements["redness_contrast"] / 50.0))
            if "component_count" in measurements:
                vec[key_to_idx["img_components"]] = min(1.0, measurements["component_count"] / 20.0)
            if "dispersion" in measurements:
                vec[key_to_idx["img_dispersion"]] = min(1.0, measurements["dispersion"])
            if "texture" in measurements:
                vec[key_to_idx["img_texture"]] = min(1.0, measurements["texture"])

        # L2 normalize
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [round(x / norm, 5) for x in vec]
        return vec

    @classmethod
    def embed_prototype(cls, body_sites: list, weights: dict) -> List[float]:
        """Embed prototype knowledge condition from weights dict."""
        vec = [0.0] * 64
        key_to_idx = {k: i for i, k in enumerate(FEATURE_KEYS_64)}

        # Add sites
        for s in (body_sites or []):
            sk = f"site_{s}" if not s.startswith("site_") else s
            if sk in key_to_idx:
                vec[key_to_idx[sk]] = 1.0

        # Add weights
        for k, w in (weights or {}).items():
            if k in key_to_idx:
                vec[key_to_idx[k]] = float(w)

        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [round(x / norm, 5) for x in vec]
        return vec
