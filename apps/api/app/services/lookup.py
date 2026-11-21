"""
lookup.py — Vector Similarity Lookup on Knowledge Base (pgvector / SQLite).
Rules:
- Cosine similarity matching (threshold >= LOOKUP_MIN_COSINE 0.35).
- Output sorted ALPHABETICALLY by name_vi.
- NO percentages (%), NO probability scores, NO disease severity.
- Disclaimer mandatory: "Đây không phải chẩn đoán và không cho biết bạn có mắc bệnh. Hãy gặp bác sĩ da liễu để được đánh giá."
- If no match -> abstain_reason="no_similar_match".
"""
import os
import yaml
import json
import uuid
import datetime
from app.core.db import get_db, cosine_similarity
from app.core.audit import record_audit_event
from app.services.embedder import FeatureVectorEmbedder
from app.config import LOOKUP_TOP_K, LOOKUP_MIN_COSINE

CONDITIONS_YAML_PATH = "apps/api/app/knowledge/conditions.yaml"

_kb_synced = False

def sync_knowledge_base(force: bool = False):
    """Sync conditions from YAML into knowledge_conditions table once on boot."""
    global _kb_synced
    if _kb_synced and not force:
        return
    db = get_db()
    count = db.execute("SELECT count(*) as cnt FROM knowledge_conditions").fetchone()
    if count and count["cnt"] >= 20 and not force:
        _kb_synced = True
        return
    if not os.path.exists(CONDITIONS_YAML_PATH):
        return
    with open(CONDITIONS_YAML_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    db = get_db()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    version = data.get("kb_version", "v1.0")

    for c in data.get("conditions", []):
        slug = c["slug"]
        embedding = FeatureVectorEmbedder.embed_prototype(c.get("body_sites", []), c.get("weights", {}))
        emb_json = json.dumps(embedding)
        sites_json = json.dumps(c.get("body_sites", []))
        weights_json = json.dumps(c.get("weights", {}))
        sources_json = json.dumps(c.get("sources", []))

        existing = db.execute("SELECT id FROM knowledge_conditions WHERE slug = ?", (slug,)).fetchone()
        if existing:
            db.execute(
                """
                UPDATE knowledge_conditions
                SET name_vi = ?, name_en = ?, summary_vi = ?, summary_en = ?,
                    typical_features = ?, body_sites = ?, embedding = ?, sources = ?,
                    reviewed_by_clinician = 0, version = ?, active = 1, updated_at = ?
                WHERE slug = ?
                """,
                (c["name_vi"], c["name_en"], c["summary_vi"], c["summary_en"],
                 weights_json, sites_json, emb_json, sources_json, version, now, slug)
            )
        else:
            cond_id = str(uuid.uuid4())
            db.execute(
                """
                INSERT INTO knowledge_conditions (
                    id, slug, name_vi, name_en, summary_vi, summary_en,
                    typical_features, body_sites, embedding, sources,
                    reviewed_by_clinician, version, active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, 1, ?, ?)
                """,
                (cond_id, slug, c["name_vi"], c["name_en"], c["summary_vi"], c["summary_en"],
                 weights_json, sites_json, emb_json, sources_json, version, now, now)
            )
    db.commit()
    _kb_synced = True

def lookup_similar_conditions(
    observation_id: str,
    body_site: str,
    symptoms: dict,
    onset: str = None,
    measurements: dict = None,
    quality_status: str = "PASS",
    urgent_message_active: bool = False,
    user_id: str = "guest",
    ip: str = "127.0.0.1"
) -> dict:
    """
    Query similar conditions from Knowledge Base.
    If urgent_message_active -> halts and returns empty list with abstain_reason.
    """
    sync_knowledge_base()

    disclaimer = (
        "Các tình trạng da có biểu hiện tương đồng (chỉ để tham khảo). "
        "Đây không phải chẩn đoán và không cho biết bạn có mắc bệnh. "
        "Hãy gặp bác sĩ da liễu để được đánh giá."
    )

    # Urgent message cutoff (Rule 12.1 / Phụ lục C)
    if urgent_message_active:
        record_audit_event(user_id, "patient", "lookup_similar", "observation", observation_id, "allow", ip)
        return {
            "items": [],
            "disclaimer": disclaimer,
            "abstain_reason": "urgent_safety_cutoff",
            "message": "Đã phát hiện dấu hiệu khẩn cấp, ứng dụng dừng tra cứu để hướng dẫn y tế khẩn cấp."
        }

    image_used = (quality_status == "PASS")
    q_vec = FeatureVectorEmbedder.embed_features(
        body_site=body_site,
        symptoms=symptoms,
        onset=onset,
        measurements=measurements if image_used else None,
        image_pass=image_used
    )

    db = get_db()
    rows = db.execute("SELECT * FROM knowledge_conditions WHERE active = 1").fetchall()

    matches = []
    clean_site = body_site.replace("site_", "")

    for r in rows:
        sites = json.loads(r["body_sites"]) if r["body_sites"] else []
        # Filter by body site if specified (empty means applies anywhere)
        if sites and clean_site not in sites and clean_site != "other":
            continue

        emb = json.loads(r["embedding"])
        sim = cosine_similarity(q_vec, emb)
        if sim >= LOOKUP_MIN_COSINE:
            matches.append({
                "slug": r["slug"],
                "name_vi": r["name_vi"],
                "name_en": r["name_en"],
                "summary": r["summary_vi"],
                "reviewed_by_clinician": bool(r["reviewed_by_clinician"]),
                "_internal_sim": sim  # internal only, never exposed in response
            })

    # Sort internally by similarity to select top K
    matches.sort(key=lambda x: x["_internal_sim"], reverse=True)
    top_matches = matches[:LOOKUP_TOP_K]

    # Clean out internal similarity scores
    for item in top_matches:
        del item["_internal_sim"]

    # SORT ALPHABETICALLY BY name_vi (Mandatory requirement in Section 10.4 & 10.5)
    top_matches.sort(key=lambda x: x["name_vi"])

    abstain_reason = None
    if not top_matches:
        abstain_reason = "no_similar_match"

    # Save to similar_condition_results
    res_id = str(uuid.uuid4())
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    internal_results = [{"slug": m["slug"], "rank_internal": i+1} for i, m in enumerate(top_matches)]

    # Only save if observation exists in observations table (prevents FOREIGN KEY failed for guests / unpersisted obs)
    if db.execute("SELECT 1 FROM observations WHERE id = ?", (observation_id,)).fetchone():
        db.execute(
            """
            INSERT INTO similar_condition_results (id, observation_id, embedder_version, kb_version, results, abstain_reason, created_at, updated_at)
            VALUES (?, ?, 'fv-1', 'kb-2026.11-draft1', ?, ?, ?, ?)
            """,
            (res_id, observation_id, json.dumps(internal_results), abstain_reason, now, now)
        )
        db.commit()

    record_audit_event(user_id, "patient", "lookup_similar", "observation", observation_id, "allow", ip)

    return {
        "items": top_matches,
        "disclaimer": disclaimer,
        "image_used": image_used,
        "abstain_reason": abstain_reason
    }
