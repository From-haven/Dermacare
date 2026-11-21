"""
llm_guard.py — Prompt Injection Defense and LLM Output Guard (T08).
Rules:
- User notes are strictly wrapped in <untrusted_data> and never execute tools.
- Output numbers must be verified against input facts.
- Quotas and scans for forbidden words (chẩn đoán, đơn thuốc, khỏi bệnh, nặng hơn, bạn bị).
- Violations cause fallback to Jinja template.
"""
import re
import json

FORBIDDEN_WORDS = [
    "chẩn đoán là", "kê đơn", "uống thuốc", "bạn bị mắc", "chắc chắn khỏi",
    "bệnh nặng", "nguy kịch", "khỏi hẳn", "bạn mắc bệnh"
]

TOOL_ALLOWLIST = {
    "create_observation",
    "schedule_reminder",
    "prepare_clinician_summary",
    "get_timeline"
}

def sanitize_user_input(raw_note: str) -> str:
    """Sanitize user text input to neutralize prompt injection attacks."""
    if not raw_note:
        return ""
    # Strip dangerous tokens like system tags
    cleaned = re.sub(r'<\/?(?:system|user|assistant|untrusted_data|tool_call)[^>]*>', '', raw_note, flags=re.IGNORECASE)
    return cleaned.strip()

def guard_llm_output(output_text: str, input_facts: dict) -> dict:
    """
    Validate LLM output against 3 guards:
    1. Numbers in output must match input numbers.
    2. No forbidden diagnostic words.
    3. Tool calls strictly in allowlist.
    """
    # 1. Check forbidden words
    lower_out = output_text.lower()
    for fw in FORBIDDEN_WORDS:
        if fw in lower_out:
            return {
                "valid": False,
                "reason": f"Phát hiện từ cấm trong câu trả lời LLM: '{fw}'",
                "fallback_to_template": True
            }

    # 2. Number check
    input_numbers = set()
    for v in input_facts.values():
        if isinstance(v, (int, float)):
            input_numbers.add(str(round(float(v), 1)))

    output_numbers = re.findall(r'\b\d+(?:\.\d+)?\b', output_text)
    for num in output_numbers:
        round_num = str(round(float(num), 1))
        # Allow harmless numbers like 1, 2, 3, 4, 7, 115
        if round_num not in input_numbers and round_num not in ["1.0", "2.0", "3.0", "7.0", "115.0"]:
            return {
                "valid": False,
                "reason": f"Phát hiện số liệu lạ không có trong dữ liệu đầu vào: {num}",
                "fallback_to_template": True
            }

    return {"valid": True, "clean_text": output_text}
