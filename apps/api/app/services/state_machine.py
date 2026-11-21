"""
state_machine.py — Observation Workflow State Machine.
Defines valid transitions and enforces state transitions for each observation.
States:
  DRAFT -> AWAITING_CAPTURE -> QUALITY_REJECTED | READY_FOR_ANALYSIS
  -> OBSERVATION_CREATED -> NEEDS_REVIEW | TIMELINE_UPDATED
  -> REPORT_READY
"""
from typing import Dict, Set
from app.errors import ValidationException

VALID_STATES: Set[str] = {
    "DRAFT",
    "AWAITING_CAPTURE",
    "QUALITY_REJECTED",
    "READY_FOR_ANALYSIS",
    "OBSERVATION_CREATED",
    "NEEDS_REVIEW",
    "TIMELINE_UPDATED",
    "REPORT_READY",
}

TRANSITION_TABLE: Dict[str, Set[str]] = {
    "DRAFT": {"AWAITING_CAPTURE"},
    "AWAITING_CAPTURE": {"QUALITY_REJECTED", "READY_FOR_ANALYSIS"},
    "QUALITY_REJECTED": {"AWAITING_CAPTURE"},  # allow retake
    "READY_FOR_ANALYSIS": {"OBSERVATION_CREATED"},
    "OBSERVATION_CREATED": {"NEEDS_REVIEW", "TIMELINE_UPDATED", "REPORT_READY"},
    "NEEDS_REVIEW": {"TIMELINE_UPDATED", "REPORT_READY"},
    "TIMELINE_UPDATED": {"REPORT_READY"},
    "REPORT_READY": set(),  # terminal state
}

def can_transition(current_state: str, next_state: str) -> bool:
    """Check if transition from current_state to next_state is valid."""
    if current_state not in VALID_STATES or next_state not in VALID_STATES:
        return False
    return next_state in TRANSITION_TABLE.get(current_state, set())

def transition(current_state: str, next_state: str) -> str:
    """
    Execute a state transition. Raises ValidationException if invalid.
    Returns the new state.
    """
    if not can_transition(current_state, next_state):
        raise ValidationException(
            f"Chuyển trạng thái không hợp lệ: '{current_state}' -> '{next_state}'",
            details={
                "current_state": current_state,
                "target_state": next_state,
                "allowed_transitions": list(TRANSITION_TABLE.get(current_state, []))
            }
        )
    return next_state
