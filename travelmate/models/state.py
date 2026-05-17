from typing import Any, Dict, List
from pydantic import BaseModel, Field
from uuid import uuid4


class TravelState(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    user_message: str

    preferences: Dict[str, Any] = Field(default_factory=dict)

    retrieved_context: List[Dict[str, Any]] = Field(default_factory=list)
    retrieved_pois: List[Dict[str, Any]] = Field(default_factory=list)

    weather: Dict[str, Any] = Field(default_factory=dict)

    draft_itinerary: Dict[str, Any] = Field(default_factory=dict)
    validated_itinerary: Dict[str, Any] = Field(default_factory=dict)

    final_answer: str = ""

    warnings: List[str] = Field(default_factory=list)
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    agent_trace: List[Dict[str, Any]] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)

    llm_usage: Dict[str, Any] = Field(default_factory=dict)
    user_feedback: Dict[str, Any] = Field(default_factory=dict)
    resource_usage: Dict[str, Any] = Field(default_factory=dict)

    revision_required: bool = False
    revision_reason: str = ""
    revision_actions: List[str] = Field(default_factory=list)

    revision_request: Dict[str, Any] = Field(
        default_factory=lambda: {
            "required": False,
            "reason": "",
            "actions": [],
        }
    )
    revision_count: int = 0

    llm_debug: list[dict] = Field(default_factory=list)