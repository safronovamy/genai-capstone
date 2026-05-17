import json
from datetime import datetime
from pathlib import Path
from travelmate.services.privacy_service import anonymize_pii

FEEDBACK_FILE = Path("travelmate/data/feedback_log.jsonl")


def save_feedback(state, rating: int):
    FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)

    anonymized_message, pii_detected = anonymize_pii(state.user_message)

    record = {
        "timestamp": datetime.utcnow().isoformat(),

        "request_id": state.request_id,

        "user_message": anonymized_message,

        "pii_detected": pii_detected,

        "city": state.preferences.get("city"),

        "duration_days": state.preferences.get("duration_days"),

        "pace": state.preferences.get("pace"),

        "rating": rating,

        "warnings": state.warnings,

        "sources": [
            s.get("source") for s in state.sources
        ],

        "llm_usage": state.llm_usage,

        "weather_source": state.weather.get("source"),

        "agent_count": len(state.agent_trace),

        "answer_preview": state.final_answer[:300]
    }

    with open(FEEDBACK_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")