"""
merkle.py — Privacy-Preserving Merkle Audit Tree Builder.
Rules (Section 15.4 Master Spec):
- Leaf = sha256(event_id || action || ts || random_salt).
- Zero PII: no emails, no names, no raw health data.
- Generates root and cryptographic inclusion proofs.
"""
import hashlib
import secrets
from typing import List, Dict, Any, Tuple

def compute_leaf(event_id: str, action: str, ts: str, salt: str = None) -> Tuple[str, str]:
    """Compute leaf hash and return (leaf_hex, salt)."""
    salt = salt or secrets.token_hex(16)
    data = f"{event_id}:{action}:{ts}:{salt}".encode('utf-8')
    leaf = hashlib.sha256(data).hexdigest()
    return f"0x{leaf}", salt

def build_merkle_tree(leaf_hashes: List[str]) -> Tuple[str, List[List[str]]]:
    """Build Merkle tree from leaves and return (root, layers)."""
    if not leaf_hashes:
        empty_root = f"0x{hashlib.sha256(b'empty').hexdigest()}"
        return empty_root, []

    current_layer = [h.replace("0x", "") for h in leaf_hashes]
    layers = [current_layer]

    while len(current_layer) > 1:
        next_layer = []
        for i in range(0, len(current_layer), 2):
            left = current_layer[i]
            right = current_layer[i+1] if i+1 < len(current_layer) else left
            combined = hashlib.sha256(bytes.fromhex(left) + bytes.fromhex(right)).hexdigest()
            next_layer.append(combined)
        current_layer = next_layer
        layers.append(current_layer)

    root = f"0x{current_layer[0]}"
    return root, layers

def get_merkle_proof(leaf_index: int, layers: List[List[str]]) -> List[Dict[str, str]]:
    """Generate Merkle proof for a leaf index."""
    proof = []
    idx = leaf_index
    for layer in layers[:-1]:
        pair_idx = idx + 1 if idx % 2 == 0 else idx - 1
        if pair_idx < len(layer):
            sibling = f"0x{layer[pair_idx]}"
            direction = "right" if idx % 2 == 0 else "left"
            proof.append({"sibling": sibling, "direction": direction})
        idx //= 2
    return proof
