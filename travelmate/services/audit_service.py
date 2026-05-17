import json
from datetime import datetime
from pathlib import Path

from travelmate.services.privacy_service import anonymize_pii


AUDIT_FILE = Path("travelmate/data/audit_log.jsonl")


def save_audit_event(state, event_type: str = "plan_trip_completed"):
    AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)

    anonymized_message, pii_detected = anonymize_pii(state.user_message)

    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "request_id": state.request_id,

        "user_message_anonymized": anonymized_message,
        "pii_detected": pii_detected,

        "city": state.preferences.get("city"),
        "supported": state.preferences.get("supported"),
        "duration_days": state.preferences.get("duration_days"),
        "pace": state.preferences.get("pace"),
        "budget": state.preferences.get("budget"),

        "agent_trace": state.agent_trace,
        "warnings": state.warnings,
        "errors": state.errors,
        "sources": state.sources,

        "weather_source": state.weather.get("source"),
        "llm_usage": state.llm_usage,
        "resource_usage": state.resource_usage,

        "final_status": "error" if state.errors else "success",
        "answer_preview": state.final_answer[:300],
    }

    with open(AUDIT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")