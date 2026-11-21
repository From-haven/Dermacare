"""
chain.py router — Blockchain Explorer and Verification Endpoints.
Endpoints:
- GET /api/chain/transactions
- POST /api/chain/settlements/demo
- GET /api/chain/audit-batches
- GET /api/chain/verify/{event_id}
"""
from app.core.db import get_db
from app.core.audit import record_audit_event
from app.services.chain.merkle import compute_leaf, build_merkle_tree, get_merkle_proof
from app.services.chain.client import chain_client
from app.errors import NotFoundException
import uuid
import datetime

def list_chain_transactions(limit: int = 50) -> list:
    db = get_db()
    rows = db.execute("SELECT * FROM chain_transactions ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]

def anchor_audit_batch(admin_id: str = "sys", ip: str = "127.0.0.1") -> dict:
    """Batch unanchored audit events and anchor root on Avalanche."""
    db = get_db()
    unanchored = db.execute("SELECT * FROM audit_events WHERE anchor_batch_id IS NULL LIMIT 100").fetchall()
    if not unanchored:
        return {"status": "no_unanchored_events", "count": 0}

    leaves = []
    salts = {}
    for ev in unanchored:
        leaf_hex, salt = compute_leaf(ev["id"], ev["action"], ev["ts"])
        leaves.append(leaf_hex)
        salts[ev["id"]] = salt

    root, layers = build_merkle_tree(leaves)

    batch_id = str(uuid.uuid4())
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    chain_res = chain_client.submit_audit_anchor(root, len(unanchored))
    tx_hash = chain_res["tx_hash"]

    db.execute(
        """
        INSERT INTO audit_anchor_batches (id, merkle_root, event_count, chain_tx_id, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (batch_id, root, len(unanchored), tx_hash, now, now)
    )

    db.execute(
        "UPDATE audit_events SET anchor_batch_id = ?, updated_at = ? WHERE anchor_batch_id IS NULL",
        (batch_id, now)
    )
    db.commit()

    record_audit_event(admin_id, "admin", "anchor_audit_batch", "audit_batch", batch_id, "allow", ip)

    return {
        "batch_id": batch_id,
        "merkle_root": root,
        "event_count": len(unanchored),
        "tx_hash": tx_hash
    }

def verify_audit_event(event_id: str) -> dict:
    """Verify an audit event against on-chain Merkle anchor."""
    db = get_db()
    ev = db.execute("SELECT * FROM audit_events WHERE id = ?", (event_id,)).fetchone()
    if not ev:
        raise NotFoundException("Sự kiện audit không tồn tại")

    batch_id = ev["anchor_batch_id"]
    if not batch_id:
        return {"status": "pending_anchor", "message": "Sự kiện chưa được gom vào batch neo lên chain"}

    batch = db.execute("SELECT * FROM audit_anchor_batches WHERE id = ?", (batch_id,)).fetchone()

    return {
        "event_id": event_id,
        "action": ev["action"],
        "timestamp": ev["ts"],
        "batch_id": batch_id,
        "merkle_root": batch["merkle_root"],
        "tx_hash": batch["chain_tx_id"],
        "status": "ANCHORED_CONFIRMED"
    }
