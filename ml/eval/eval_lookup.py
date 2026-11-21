#!/usr/bin/env python3
"""
eval_lookup.py — Evaluation script for Knowledge Base lookup.
Sanity Test:
- Queries each of the 20 conditions with its own prototype feature vector.
- Asserts that every condition retrieves itself in top-5 with cosine similarity = 1.0.
"""
import sys
import os
import yaml
import json

sys.path.insert(0, os.path.abspath("apps/api"))

from app.core.db import cosine_similarity
from app.services.embedder import FeatureVectorEmbedder

CONDITIONS_PATH = "apps/api/app/knowledge/conditions.yaml"

def run_eval():
    with open(CONDITIONS_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    conditions = data.get("conditions", [])
    print(f"Loaded {len(conditions)} conditions from {CONDITIONS_PATH}")

    prototypes = {}
    for c in conditions:
        slug = c["slug"]
        vec = FeatureVectorEmbedder.embed_prototype(c.get("body_sites", []), c.get("weights", {}))
        prototypes[slug] = vec

    passed = 0
    total = len(conditions)

    for slug, q_vec in prototypes.items():
        sims = []
        for other_slug, other_vec in prototypes.items():
            sim = cosine_similarity(q_vec, other_vec)
            sims.append((other_slug, sim))

        sims.sort(key=lambda x: x[1], reverse=True)
        top5 = [x[0] for x in sims[:5]]

        if slug == top5[0] and abs(sims[0][1] - 1.0) < 1e-4:
            passed += 1
        else:
            print(f"FAILED for {slug}: top match was {top5[0]} with sim {sims[0][1]}")

    print(f"Lookup Sanity Eval Result: {passed}/{total} prototypes retrieved themselves at rank 1 with cosine=1.0")
    if passed == total:
        print("ALL PROTOTYPE EVALUATION TESTS PASSED!")
        return 0
    else:
        print("EVALUATION FAILED!")
        return 1

if __name__ == "__main__":
    sys.exit(run_eval())
