"""
safety.py — Deterministic Safety Rules Evaluator.
Evaluates 21 rules from Appendix C using purely deterministic logic.
NO Python eval!
Priority: URGENT_MESSAGE > CLINICIAN_REVIEW (same_day > soon > routine) > ROUTINE.
"""
import os
import yaml
from typing import Dict, Any, List

SAFETY_RULES_PATH = "apps/api/app/agent/safety_rules.yaml"

def load_safety_rules() -> dict:
    if os.path.exists(SAFETY_RULES_PATH):
        with open(SAFETY_RULES_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {"rules": [], "default_action": "ROUTINE"}

def evaluate_condition(cond: dict, facts: dict) -> bool:
    """Evaluate a single rule condition (all, any, not, fact comparison)."""
    if "all" in cond:
        return all(evaluate_condition(c, facts) for c in cond["all"])
    if "any" in cond:
        return any(evaluate_condition(c, facts) for c in cond["any"])
    if "not" in cond:
        return not evaluate_condition(cond["not"], facts)

    fact_name = cond.get("fact")
    fact_val = facts.get(fact_name)

    if "eq" in cond:
        return fact_val == cond["eq"]
    if "in" in cond:
        allowed = cond["in"]
        # Handle string or list
        if isinstance(allowed, list):
            return fact_val in allowed
        return str(fact_val) in str(allowed)
    if "gte" in cond:
        try:
            return float(fact_val or 0) >= float(cond["gte"])
        except Exception:
            return False

    return False

def evaluate_safety_rules(facts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate all safety rules against facts.
    Returns:
    - action: URGENT_MESSAGE | CLINICIAN_REVIEW | ROUTINE
    - timeframe: same_day | soon | routine | None
    - messages: list of up to 3 messages sorted by urgency
    - triggered_rules: list of triggered rule IDs
    """
    data = load_safety_rules()
    rules = data.get("rules", [])

    action_rank = {"URGENT_MESSAGE": 3, "CLINICIAN_REVIEW": 2, "ROUTINE": 1}
    timeframe_rank = {"same_day": 3, "soon": 2, "routine": 1}

    highest_action = "ROUTINE"
    highest_timeframe = None
    triggered = []

    for r in rules:
        if evaluate_condition(r.get("when", {}), facts):
            act = r.get("action", "ROUTINE")
            tf = r.get("timeframe")

            triggered.append({
                "id": r["id"],
                "action": act,
                "timeframe": tf,
                "message_vi": r.get("message_vi", ""),
                "message_en": r.get("message_en", "")
            })

            if action_rank.get(act, 1) > action_rank.get(highest_action, 1):
                highest_action = act
                highest_timeframe = tf
            elif action_rank.get(act, 1) == action_rank.get(highest_action, 1):
                if tf and (highest_timeframe is None or timeframe_rank.get(tf, 1) > timeframe_rank.get(highest_timeframe, 1)):
                    highest_timeframe = tf

    # Sort triggered messages by priority
    triggered.sort(
        key=lambda x: (
            action_rank.get(x["action"], 1),
            timeframe_rank.get(x.get("timeframe"), 0)
        ),
        reverse=True
    )

    top_messages = [t["message_vi"] for t in triggered[:3]]

    return {
        "action": highest_action,
        "timeframe": highest_timeframe,
        "messages": top_messages,
        "triggered_rules": [t["id"] for t in triggered],
        "is_urgent": (highest_action == "URGENT_MESSAGE")
    }
