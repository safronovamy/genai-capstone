from travelmate.agents.base_agent import BaseAgent
from travelmate.models.state import TravelState
from travelmate.services.rag_service import query_travel_patterns
from travelmate.services.rag_service import query_city_guide


class ItineraryAgent(BaseAgent):
    name = "ItineraryAgent"

    def run(self, state: TravelState) -> TravelState:
        duration = state.preferences.get("duration_days", 1)
        pois = state.retrieved_pois
        weather = state.weather

        city = state.preferences.get("city", "")

        children = state.preferences.get("travelers", {}).get("children", 0)
        pace = state.preferences.get("pace", "medium")
        interests = state.preferences.get("interests", [])

        interest_text = " ".join(interests)

        if children > 0:
            traveler_context = "family-friendly travel with children"
        else:
            traveler_context = "adult travel nightlife food culture"

        guide_query = (
            f"{city} {traveler_context} "
            f"{pace} pace "
            f"{interest_text} "
            f"areas walking transport itinerary"
        )

        guide_results = query_city_guide(
            query_text=guide_query,
            city=city,
        )

        guide_texts = []

        existing_guide_keys = {
            (
                item.get("metadata", {}).get("doc_type"),
                item.get("metadata", {}).get("city"),
                item.get("metadata", {}).get("chunk_index"),
            )
            for item in state.retrieved_context
        }

        for doc, meta in zip(
            guide_results["documents"][0],
            guide_results["metadatas"][0],
        ):
            guide_texts.append(doc)

            guide_key = (
                meta.get("doc_type"),
                meta.get("city"),
                meta.get("chunk_index"),
            )

            if guide_key not in existing_guide_keys:
                state.retrieved_context.append(
                    {
                        "content": doc,
                        "metadata": meta,
                    }
                )
                existing_guide_keys.add(guide_key)

        if not any(
            source.get("source") == "City guide RAG"
            and source.get("city") == city
            for source in state.sources
        ):
            state.sources.append(
                {
                    "source": "City guide RAG",
                    "city": city,
                    "items": len(guide_texts),
                }
            )

        if not state.preferences.get("supported", False):
            state.draft_itinerary = {"days": []}
            state.validated_itinerary = {"days": []}
            state.agent_trace.append({
                "agent": self.name,
                "event_type": "decision",
                "decision": "unsupported city → itinerary generation skipped",
            })
            return state

        revision = state.revision_request or {}
        revision_actions = revision.get("actions", [])

        force_slow_pace = "add_rest_breaks" in revision_actions
        force_indoor = "prioritize_indoor_activities" in revision_actions

        daily_forecast = weather.get("daily_forecast", [])
        season = weather.get("season", "unknown")

        children = state.preferences.get("travelers", {}).get("children", 0)
        pace = state.preferences.get("pace", "medium")
        interests = state.preferences.get("interests", [])
        interest_text = " ".join(interests)

        if children > 0:
            traveler_context = "family travel with children"
        else:
            traveler_context = "adult travel"

        travel_patterns = query_travel_patterns(
            query_text=(
                f"{season} {traveler_context} "
                f"{pace} pace "
                f"{interest_text} itinerary pattern"
            ),
            city=state.preferences.get("city", ""),
            n_results=1,
        )

        existing_contents = {item.get("content") for item in state.retrieved_context}
        new_items = []

        for doc, meta in zip(
            travel_patterns["documents"][0],
            travel_patterns["metadatas"][0],
        ):
            if doc not in existing_contents:
                new_items.append({"content": doc, "metadata": meta})

        state.retrieved_context.extend(new_items)

        if weather.get("source") == "fallback":
            state.warnings.append("Weather data is not live, fallback used.")

        if weather.get("source") == "seasonal fallback":
            state.warnings.append(
                f"Exact forecast unavailable. Using {season} seasonal travel assumptions."
            )

        if not state.retrieved_pois:
            days = []
            for day in range(1, duration + 1):
                days.append({
                    "day": day,
                    "weather": {},
                    "season": season,
                    "morning": "Visit a central park or outdoor area",
                    "afternoon": "Explore a local museum or indoor attraction",
                    "evening": "Rest and local dining",
                })

            state.draft_itinerary = {"days": days}
            return state

        child_count = state.preferences.get("travelers", {}).get("children", 0)
        budget = state.preferences.get("budget", "medium")

        indoor_pois = [p for p in pois if p.get("indoor")]
        outdoor_pois = [p for p in pois if not p.get("indoor")]

        evening_pois = [
            p for p in pois
            if p.get("type") in [
                "cafe",
                "bakery",
                "market",
                "cultural center",
            ]
        ]

        evening_indoor_pois = [
            p for p in evening_pois
            if p.get("indoor")
        ]

        evening_outdoor_pois = [
            p for p in evening_pois
            if not p.get("indoor")
        ]

        if budget == "low":
            indoor_pois = [
                p for p in indoor_pois
                if p.get("budget_level") != "high"
            ]

            outdoor_pois = [
                p for p in outdoor_pois
                if p.get("budget_level") != "high"
            ]

            budget_priority = {
                "free": 0,
                "low": 1,
                "medium": 2,
            }

            indoor_pois = sorted(
                indoor_pois,
                key=lambda p: budget_priority.get(
                    p.get("budget_level"),
                    99
                )
            )

            outdoor_pois = sorted(
                outdoor_pois,
                key=lambda p: budget_priority.get(
                    p.get("budget_level"),
                    99
                )
            )

        if budget == "high":
            indoor_pois = sorted(
                indoor_pois,
                key=lambda x: x.get("budget_level") == "high",
                reverse=True,
            )

        used = set()
        days = []

        def unused_pois(poi_list):
            return [
                p for p in poi_list
                if p["name"] not in used
            ]

        def pick(poi_list, allow_reuse=False):
            sorted_pois = sorted(
                poi_list,
                key=lambda p: p.get("priority_score", 0),
                reverse=True,
            )

            for p in sorted_pois:
                if allow_reuse or p["name"] not in used:
                    used.add(p["name"])
                    return p["name"]
            return None

        def rain_safe_pois(poi_list):
            return [
                p for p in poi_list
                if p.get("indoor") or not p.get("avoid_in_rain", False)
            ]

        guide_context = " ".join(guide_texts).lower()
        prefer_walkable = "walk" in guide_context or "compact" in guide_context

        def build_evening_activity(
            pace,
            is_rain,
            child_present,
            season,
            prefer_walkable,
            day_number,
        ):
            # Families still get lighter evenings
            if child_present:
                if is_rain:
                    return "Relaxed indoor family evening"
                return "Light evening walk and flexible family time"

            # Active pace → real evening activity
            if pace == "active":

                if is_rain:
                    evening_choice = (
                        pick(evening_indoor_pois)
                        or pick(indoor_pois)
                    )
                else:
                    evening_choice = (
                        pick(evening_outdoor_pois)
                        or pick(evening_indoor_pois)
                        or pick(outdoor_pois)
                    )

                if evening_choice:
                    return evening_choice

            # Medium pace
            if pace == "medium":
                if is_rain:
                    return "Relaxed indoor evening activity"

                options = [
                    "Evening walk in a central district",
                    "Flexible evening exploration",
                    "Relaxed city-center walk",
                ]

                return options[(day_number - 1) % len(options)]

            # Slow pace
            if is_rain:
                return "Quiet indoor evening and recovery time"

            return "Relaxed evening walk and early rest"

        for day in range(1, duration + 1):
            day_weather = (
                daily_forecast[day - 1]
                if day - 1 < len(daily_forecast)
                else {}
            )

            actual_rain = day_weather.get("rain_expected", False)

            is_rain = actual_rain

            if is_rain:
                safe_indoor = rain_safe_pois(indoor_pois)
                safe_outdoor = rain_safe_pois(outdoor_pois)

                if force_indoor:
                    safe_outdoor = [
                        p for p in safe_outdoor
                        if p.get("priority_score", 0) >= 9
                    ]

                morning = pick(safe_indoor) or pick(safe_outdoor)

                afternoon = (
                    pick(safe_indoor)
                    or pick(safe_outdoor)
                )

                fallback_indoor = [
                    p for p in pois
                    if p.get("indoor") and p["name"] not in used
                ]

                fallback_outdoor = [
                    p for p in pois
                    if not p.get("indoor")
                    and not p.get("avoid_in_rain", False)
                    and p["name"] not in used
                ]

                if not morning:
                    morning = (
                        pick(fallback_indoor)
                        or pick(fallback_outdoor)
                        or "Cafe stop and indoor recovery break"
                    )

                if not afternoon:
                    afternoon = (
                        pick(fallback_indoor)
                        or pick(fallback_outdoor)
                        or "Museum or indoor cultural activity"
                    )
            else:

                available_outdoor = [
                    p for p in outdoor_pois
                    if p["name"] not in used
                ]

                available_indoor = [
                    p for p in indoor_pois
                    if p["name"] not in used
                ]

                available_any = [
                    p for p in pois
                    if p["name"] not in used
                ]

                morning = (
                    pick(available_outdoor)
                    or pick(available_indoor)
                    or pick(available_any)
                )

                afternoon = (
                    pick(available_indoor)
                    or pick(available_outdoor)
                    or pick(available_any)
                )

                if not morning:
                    morning = "Free time / rest"

                if not afternoon:
                    afternoon = "Free time / rest"

            evening = build_evening_activity(
                pace=pace,
                is_rain=is_rain,
                child_present=child_count > 0 or force_slow_pace,
                season=season,
                prefer_walkable=prefer_walkable,
                day_number=day,
            )

            days.append({
                "day": day,
                "weather": day_weather,
                "season": season,
                "morning": morning,
                "afternoon": afternoon,
                "evening": evening,
            })

        state.draft_itinerary = {"days": days}

        state.agent_trace.append(
            {
                "agent": "ItineraryAgent",
                "status": "decision",
                "latency_ms": 0,
                "decision": "weather-aware and city-guide-aware itinerary generation",
                "details": {
                    "rain": state.weather.get("rain_expected"),
                    "indoor_count": len(indoor_pois),
                    "outdoor_count": len(outdoor_pois),
                    "city_guide_used": len(guide_texts) > 0,
                    "prefer_walkable": prefer_walkable,
                    "revision_applied": state.revision_count > 0,
                },
            }
        )

        return state