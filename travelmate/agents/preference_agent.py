import json
import re
from datetime import date
from typing import Any, Dict

from openai import OpenAI

from travelmate.agents.base_agent import BaseAgent
from travelmate.models.state import TravelState
from travelmate.services.privacy_service import anonymize_pii
from travelmate.services.llm_service import PREFERENCE_MODEL

from datetime import date, datetime


MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


class PreferenceAgent(BaseAgent):
    name = "PreferenceAgent"

    supported_cities = ["Prague", "Vienna", "Barcelona"]

    def __init__(self):
        self.client = OpenAI()

    def run(self, state: TravelState) -> TravelState:
        sanitized_message, pii_detected = anonymize_pii(state.user_message)

        if pii_detected:
            state.agent_trace.append({
                "agent": self.name,
                "event_type": "privacy_filter",
                "details": "PII anonymization applied to user input"
            })

        try:
            extraction_result = self._extract_with_llm(state, sanitized_message)

            preferences = extraction_result["preferences"]
            state.llm_usage["preference_agent"] = extraction_result["usage"]

            preferences = self._normalize_preferences(preferences)

            if not preferences.get("supported", False):
                state.warnings.append(
                    "City not supported. Available cities: Prague, Vienna, Barcelona."
                )

            state.agent_trace.append({
                "agent": self.name,
                "event_type": "decision",
                "decision": "preferences extracted with LLM structured output",
            })

        except Exception as exc:
            preferences = self._fallback_keyword_parsing(sanitized_message)

            state.warnings.append(
                f"LLM preference extraction failed, fallback parsing was used: {str(exc)}"
            )

            state.agent_trace.append({
                "agent": self.name,
                "event_type": "decision",
                "decision": "fallback keyword preference parsing used",
            })

        start_date = preferences.get("start_date")

        if not start_date:
            date_match = re.search(r"(\d{4}-\d{2}-\d{2})", sanitized_message)

            if date_match:
                start_date = date_match.group(1)
            else:
                inferred_month_date = self._infer_future_month_start(
                    sanitized_message
                )
                start_date = inferred_month_date or str(date.today())

        start_date = self._normalize_future_start_date(start_date)
        preferences["start_date"] = start_date
        state.preferences = preferences

        return state

    def _extract_with_llm(
        self,
        state: TravelState,
        message: str
    ) -> Dict[str, Any]:
        system_prompt = """
You are a travel preference extraction agent.

Extract structured travel preferences from the user request.

Return ONLY valid JSON with this exact structure:
{
  "city": "string",
  "start_date": "YYYY-MM-DD or null",
  "duration_days": integer,
  "budget": "low | medium | high",
  "pace": "slow | medium | active",
  "travelers": {
    "adults": integer,
    "children": integer,
    "child_age": integer or null
  },
  "interests": ["string"]
}

Rules:
- Always extract the city EXACTLY as mentioned by the user.
- Extract start_date in ISO format YYYY-MM-DD only when the user provides a specific date.
- If the user says "13th of May", "May 13", or "13 May", convert it to ISO format.
- If the user mentions only a month without a day or year, set start_date to the first day of the nearest future occurrence of that month.
- If no date is provided, return null.
- If duration is missing, use 3.
- If budget is missing, use "medium".
- If pace is missing, use "medium".
- If adults are missing, use 2.
- If a child is mentioned but age is missing, use 4.
- Extract interests from natural language, for example parks, museums, animals, food, history, old town, aquariums, playgrounds.
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ]

        state.llm_debug.append(
            {
                "agent": "PreferenceAgent",
                "stage": "intent_and_preference_extraction",
                "model": PREFERENCE_MODEL,
                "prompt_preview": {
                    "system": system_prompt[:1200],
                    "user": message,
                },
                "prompt_length": len(system_prompt) + len(message),
            }
        )

        response = self.client.chat.completions.create(
            model=PREFERENCE_MODEL,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0,
        )

        content = response.choices[0].message.content

        state.llm_debug.append(
            {
                "agent": "PreferenceAgent",
                "stage": "intent_extraction_result",
                "parsed_preferences": json.loads(content),
            }
        )

        return {
            "preferences": json.loads(content),
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
                "model": PREFERENCE_MODEL,
            }
        }

    def _infer_future_month_start(self, user_text: str) -> str | None:
        text = user_text.lower()

        detected_month = None

        for month_name, month_number in MONTHS.items():
            if re.search(rf"\b{month_name}\b", text):
                detected_month = month_number
                break

        if not detected_month:
            return None

        today = date.today()
        target_year = today.year

        if detected_month <= today.month:
            target_year += 1

        return f"{target_year}-{detected_month:02d}-01"

    def _normalize_preferences(self, prefs: Dict[str, Any]) -> Dict[str, Any]:
        detected_city = str(prefs.get("city", "unknown")).strip()

        supported = False
        normalized_city = detected_city

        if detected_city.lower() in [c.lower() for c in self.supported_cities]:
            normalized_city = next(
                c for c in self.supported_cities
                if c.lower() == detected_city.lower()
            )
            supported = True

        duration_days = prefs.get("duration_days", 3)
        try:
            duration_days = int(duration_days)
        except (TypeError, ValueError):
            duration_days = 3

        duration_days = max(1, min(duration_days, 7))

        budget = str(prefs.get("budget", "medium")).lower()
        if budget not in ["low", "medium", "high"]:
            budget = "medium"

        pace = str(prefs.get("pace", "medium")).lower()
        if pace not in ["slow", "medium", "active"]:
            pace = "medium"

        travelers = prefs.get("travelers", {}) or {}

        adults = travelers.get("adults", 2)
        children = travelers.get("children", 0)
        child_age = travelers.get("child_age", None)

        try:
            adults = int(adults)
        except (TypeError, ValueError):
            adults = 2

        try:
            children = int(children)
        except (TypeError, ValueError):
            children = 0

        if child_age is not None:
            try:
                child_age = int(child_age)
            except (TypeError, ValueError):
                child_age = None

        interests = prefs.get("interests", [])
        if not isinstance(interests, list) or not interests:
            interests = ["parks", "museums", "old town"]

        interests = list(dict.fromkeys(
            str(item).lower().strip()
            for item in interests
            if item
        ))

        start_date = prefs.get("start_date")
        if start_date in ["", "null", "None"]:
            start_date = None

        return {
            "city": normalized_city,
            "supported": supported,
            "start_date": start_date,
            "duration_days": duration_days,
            "budget": budget,
            "pace": pace,
            "travelers": {
                "adults": adults,
                "children": children,
                "child_age": child_age,
            },
            "interests": interests,
        }

    def _fallback_keyword_parsing(self, message: str) -> Dict[str, Any]:
        text = message.lower()

        city = "unknown"
        supported = False

        for candidate in self.supported_cities:
            if candidate.lower() in text:
                city = candidate
                supported = True
                break

        if city == "unknown":
            match = re.search(r"\bto\s+([A-Z][a-zA-Z]+)", message)
            if match:
                city = match.group(1)

        pace = "medium"
        if any(word in text for word in ["slow", "relaxed", "easy", "calm"]):
            pace = "slow"
        elif any(word in text for word in ["active", "intensive", "fast", "packed"]):
            pace = "active"

        duration_days = 3
        if any(phrase in text for phrase in ["1 day", "one day"]):
            duration_days = 1
        elif any(phrase in text for phrase in ["2 days", "two days"]):
            duration_days = 2
        elif any(phrase in text for phrase in ["3 days", "three days"]):
            duration_days = 3
        elif any(phrase in text for phrase in ["week", "7 days", "seven days"]):
            duration_days = 7

        budget = "medium"
        if any(phrase in text for phrase in ["low budget", "cheap", "affordable"]):
            budget = "low"
        elif any(phrase in text for phrase in ["high budget", "luxury", "premium"]):
            budget = "high"

        children = 0
        if any(word in text for word in ["child", "kid", "toddler", "teenager", "teen"]):
            children = 1

        if "toddler" in text and ("teenager" in text or "teen" in text):
            children = 2

        child_age = 4 if children else None

        start_date = self._infer_future_month_start(message)

        interest_keywords = [
            "parks",
            "museums",
            "cafes",
            "markets",
            "food",
            "restaurants",
            "history",
            "architecture",
            "zoo",
            "animals",
            "playgrounds",
            "shopping",
            "old town",
            "walks",
        ]

        interests = [
            keyword
            for keyword in interest_keywords
            if keyword in text
        ]

        return {
            "city": city,
            "supported": supported,
            "start_date": start_date,
            "duration_days": duration_days,
            "budget": budget,
            "pace": pace,
            "travelers": {
                "adults": 2,
                "children": children,
                "child_age": child_age,
            },
            "interests": interests,
        }
    
    def _normalize_future_start_date(self, start_date: str | None) -> str:
        if not start_date:
            return str(date.today())

        try:
            parsed = datetime.fromisoformat(start_date).date()
        except ValueError:
            return str(date.today())

        today = date.today()

        if parsed >= today:
            return str(parsed)

        target_year = today.year

        if parsed.month < today.month or (
            parsed.month == today.month and parsed.day < today.day
        ):
            target_year += 1

        return f"{target_year}-{parsed.month:02d}-{parsed.day:02d}"