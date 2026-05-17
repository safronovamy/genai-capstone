from travelmate.agents.base_agent import BaseAgent
from travelmate.models.state import TravelState
from travelmate.services.llm_service import generate_itinerary_response
from travelmate.services.resource_service import get_resource_usage


class SynthesisAgent(BaseAgent):
    name = "SynthesisAgent"

    def run(self, state: TravelState) -> TravelState:
        if not state.preferences.get("supported", False):
            state.final_answer = self._build_unsupported_city_answer(state)
            state.resource_usage = get_resource_usage()
            state.agent_trace.append({
                "agent": self.name,
                "event_type": "decision",
                "decision": "unsupported city → grounded answer returned without LLM generation",
            })
            return state

        fallback_answer = self._build_fallback_answer(state)
        prompt = self._build_llm_prompt(state)

        try:
            state.llm_debug.append({
                "agent": "SynthesisAgent",
                "stage": "concise_trip_explanation",
                "messages": prompt,
            })

            llm_result = generate_itinerary_response(prompt)

            state.final_answer = llm_result["text"]
            state.llm_usage["synthesis_agent"] = llm_result.get("usage", {})
            state.resource_usage = get_resource_usage()

            state.agent_trace.append({
                "agent": self.name,
                "status": "llm_generation",
                "latency_ms": 0,
                "model": llm_result.get("model"),
                "role": "concise_trip_explanation",
                "token_usage": state.llm_usage,
            })

        except Exception as exc:
            state.final_answer = fallback_answer
            state.errors.append(f"SynthesisAgent fallback used: {str(exc)}")
            state.resource_usage = get_resource_usage()

            state.agent_trace.append({
                "agent": self.name,
                "status": "fallback_generation",
                "latency_ms": 0,
                "error": str(exc),
            })

        return state

    def _build_llm_prompt(self, state: TravelState) -> str:
        preferences = state.preferences
        weather = state.weather
        itinerary = state.validated_itinerary.get("days", [])

        compact_weather = []
        for day in weather.get("daily_forecast", [])[:3]:
            compact_weather.append({
                "date": day.get("date"),
                "rain": day.get("rain_expected"),
                "temp_max": day.get("temperature_max_c"),
            })

        compact_pois = []
        for poi in state.retrieved_pois[:6]:
            compact_pois.append({
                "name": poi.get("name"),
                "type": poi.get("type"),
                "indoor": poi.get("indoor"),
                "budget": poi.get("budget_level"),
            })

        compact_itinerary = []
        for day in itinerary[:5]:
            compact_itinerary.append({
                "day": day.get("day"),
                "date": day.get("weather", {}).get("date"),
                "rain": day.get("weather", {}).get("rain_expected"),
                "morning": self._activity_name(day.get("morning")),
                "afternoon": self._activity_name(day.get("afternoon")),
                "evening": self._activity_name(day.get("evening")),
            })

        compact_sources = []
        for source in state.sources:
            if source.get("source") == "RAG knowledge base":
                compact_sources.append({
                    "source": "Curated POI dataset",
                    "city": source.get("city"),
                    "items": source.get("items"),
                })
            elif source.get("source") == "City guide RAG":
                compact_sources.append({
                    "source": "City guide RAG",
                    "city": source.get("city"),
                    "items": source.get("items"),
                })
            elif source.get("source") == "Travel rules RAG":
                compact_sources.append({
                    "source": "Travel rules RAG",
                    "rule_files": source.get("rule_files", []),
                })

        weather_source = weather.get("source", "unknown")
        forecast_matches_dates = weather.get("forecast_matches_requested_dates", False)
        requested_dates = weather.get("requested_dates", [])

        return f"""
You are TravelMate's final explanation agent.

Your task is NOT to rewrite the full day-by-day itinerary.
The UI renders the validated itinerary separately as structured cards.

Generate a concise Markdown explanation with exactly these sections:

## Trip Overview
3-5 short sentences explaining the plan at a high level.

## Weather Impact
2-3 bullet points explaining how weather affected planning.

## Planning Notes
2-3 bullet points explaining family pace, budget, seasonality, or constraints.

Rules:
- Do not generate a full day-by-day itinerary.
- Do not invent attractions, restaurants, prices, opening hours, routes, live events, or transport details.
- Only refer to the provided city, weather, constraints, selected POIs, itinerary, and sources.
- If weather source is "Open-Meteo MCP Server", call it "Open-Meteo MCP forecast".
- Requested travel dates: {requested_dates}.
- Forecast matches requested dates: {forecast_matches_dates}.
- Describe weather as applying to trip dates only if forecast_matches_requested_dates is True.
- Keep the whole answer concise.
- Never mention model training cutoff, knowledge cutoff, or training data.

User request:
{state.user_message}

Parsed preferences:
{preferences}

Weather source:
{weather_source}

Weather summary:
{compact_weather}

Selected POIs:
{compact_pois}

Validated itinerary summary:
{compact_itinerary}

Planning constraints:
{state.warnings}

Sources:
{compact_sources}
"""

    def _activity_name(self, activity):
        if isinstance(activity, dict):
            return activity.get("name")
        return activity

    def _build_unsupported_city_answer(self, state: TravelState) -> str:
        city = state.preferences.get("city", "this city")

        return "\n".join([
            f"# TravelMate cannot generate a grounded itinerary for {city}",
            "",
            "This destination is not currently supported in the curated TravelMate knowledge base.",
            "",
            "Supported cities:",
            "- Prague",
            "- Vienna",
            "- Barcelona",
            "",
            "Because there are no curated POI records, city guide, or travel patterns for this destination, the system avoids generating a specific itinerary.",
            "",
            "You can try the same request again with one of the supported cities.",
        ])

    def _build_fallback_answer(self, state: TravelState) -> str:
        preferences = state.preferences
        city = preferences.get("city", "unknown")
        duration = preferences.get("duration_days", 3)
        pace = preferences.get("pace", "medium")
        budget = preferences.get("budget", "medium")

        travelers = preferences.get("travelers", {})
        child_count = travelers.get("children", 0)
        weather = state.weather or {}

        daily_forecast = weather.get("daily_forecast", [])
        rainy_days = sum(1 for day in daily_forecast if day.get("rain_expected"))

        if rainy_days == 0:
            weather_impact = "Outdoor activities can be used more freely."
        elif rainy_days == len(daily_forecast) and daily_forecast:
            weather_impact = "Indoor activities and backup options are prioritized."
        else:
            weather_impact = "The plan balances indoor and outdoor options based on mixed weather."

        trip_type = "family trip" if child_count > 0 else "trip"

        lines = [
            "## Trip Overview",
            (
                f"This {duration}-day {trip_type} to {city} is planned with a "
                f"{pace} pace and {budget} budget level. The itinerary is based on "
                "validated POIs, travel rules, and weather-aware planning constraints."
            ),
            "",
            "## Weather Impact",
            f"- Weather source: {weather.get('source', 'unknown')}.",
            f"- {weather_impact}",
            "",
            "## Planning Notes",
            "- The plan avoids overloading the schedule.",
        ]

        if child_count > 0:
            lines.append("- Family pacing and rest time are considered.")

        lines.append("- Retrieved POIs and travel rules are used as grounding context.")

        return "\n".join(lines)