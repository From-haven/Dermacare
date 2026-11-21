"""
graph.py — DermaCare Agent StateGraph Workflow.
Sequential pipeline:
intake_consent -> quality_gate -> vision_observation -> safety_router
-> lookup_similar -> comparator -> profile_engine -> report_assistant -> clinician_review_handoff
"""
from typing import Dict, Any
from app.agent.safety import evaluate_safety_rules
from ml.vision.quality import assess_image_quality
from ml.vision.measure import measure_observation
from ml.vision.compare import evaluate_comparability
from app.services.lookup import lookup_similar_conditions
from app.services.timeline import generate_timeline

def run_agent_workflow(
    case_id: str,
    observation_id: str,
    user_id: str,
    body_site: str,
    profile_type: str,
    symptoms: dict,
    image_bytes: bytes = None,
    previous_observation: dict = None,
    user_notes: str = ""
) -> Dict[str, Any]:
    """Execute complete LangGraph-style workflow for an observation."""
    state = {
        "case_id": case_id,
        "observation_id": observation_id,
        "workflow_state": "DRAFT",
        "errors": []
    }

    # Node 1: Quality Gate
    if image_bytes:
        q_rep = assess_image_quality(image_bytes)
        state["quality"] = q_rep
        quality_status = q_rep["status"]
    else:
        quality_status = "ABSTAIN"
        state["quality"] = {"status": "ABSTAIN", "reasons": ["Chưa tải ảnh"]}

    # Node 2: Vision Observation
    measurements = []
    if quality_status == "PASS" and image_bytes:
        try:
            measurements = measure_observation(image_bytes, body_site=body_site, profile_type=profile_type)
        except Exception as e:
            state["errors"].append(str(e))
    state["measurements"] = measurements

    # Node 3: Safety Router (runs BEFORE lookup & report, has power to cut flow!)
    safety_facts = dict(symptoms or {})
    safety_facts["profile_type"] = profile_type
    safety_facts["image_status"] = quality_status
    safety_eval = evaluate_safety_rules(safety_facts)
    state["safety"] = safety_eval

    # Node 4: Lookup Similar Conditions (Halts if urgent!)
    measure_dict = {m["metric_name"]: m["value"] for m in measurements}
    lookup_res = lookup_similar_conditions(
        observation_id=observation_id,
        body_site=body_site,
        symptoms=symptoms,
        onset=symptoms.get("onset"),
        measurements=measure_dict,
        quality_status=quality_status,
        urgent_message_active=safety_eval["is_urgent"],
        user_id=user_id
    )
    state["similar_conditions"] = lookup_res

    # Node 5: Comparator (if previous observation provided)
    if previous_observation and image_bytes and quality_status == "PASS":
        current_obs = {
            "case_id": case_id,
            "body_site": body_site,
            "quality_status": quality_status,
            "affected_area_ratio": measure_dict.get("affected_area_ratio", 0.0)
        }
        comp = evaluate_comparability(previous_observation, current_obs)
        state["comparison"] = comp
    else:
        state["comparison"] = {"flag": "NOT_COMPARABLE", "reasons": ["Chưa có ảnh đối chiếu trước đó"]}

    # Node 6: Profile & Report Readiness
    if safety_eval["is_urgent"]:
        state["workflow_state"] = "NEEDS_REVIEW"
    elif quality_status == "RETAKE":
        state["workflow_state"] = "QUALITY_REJECTED"
    else:
        state["workflow_state"] = "REPORT_READY"

    return state
