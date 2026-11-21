"""
jobs.py — Background Worker Jobs for DermaCare Agent.
Tasks:
- Periodic Merkle audit batch anchoring
- Overdue consent cleanup
- Reminder notifications
"""
import sys
import os
import time
import datetime

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, os.path.join(WORKSPACE_ROOT, "apps/api"))
sys.path.insert(0, WORKSPACE_ROOT)

from app.core.db import get_db
from app.services.chain.client import get_chain_client
from app.services.chain.merkle import compute_leaf, build_merkle_tree

def run_worker_loop():
    print("DermaCare Background Worker started.")
    db = get_db()
    client = get_chain_client()

    while True:
        try:
            # 1. Check for unanchored audit events
            unanchored = db.execute("""
                SELECT id, action, ts FROM audit_events 
                WHERE anchor_batch_id IS NULL 
                ORDER BY created_at ASC LIMIT 50
            """).fetchall()

            if unanchored:
                print(f"[Worker] Found {len(unanchored)} unanchored audit events. Anchoring...")
                leaves = []
                for ev in unanchored:
                    leaf, _ = compute_leaf(ev["id"], ev["action"], ev["ts"])
                    leaves.append(leaf)

                root, _ = build_merkle_tree(leaves)
                batch_id = int(time.time())
                tx = client.anchor_audit_batch(root, batch_id)

                if tx.status == "CONFIRMED":
                    batch_uuid = str(batch_id)
                    for ev in unanchored:
                        db.execute("UPDATE audit_events SET anchor_batch_id = ? WHERE id = ?", (batch_uuid, ev["id"]))
                    db.commit()
                    print(f"[Worker] Batch {batch_id} anchored successfully. TxHash: {tx.tx_hash}")

            # Sleep 30 seconds between cycles
            time.sleep(30)
        except KeyboardInterrupt:
            print("Worker shutting down gracefully.")
            break
        except Exception as e:
            print(f"[Worker Error] {e}")
            time.sleep(10)

if __name__ == "__main__":
    run_worker_loop()
