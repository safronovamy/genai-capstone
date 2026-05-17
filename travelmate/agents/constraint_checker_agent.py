from travelmate.agents.base_agent import BaseAgent
from travelmate.models.state import TravelState
from travelmate.services.rag_service import query_rules


class ConstraintCheckerAgent(BaseAgent):
    name = "ConstraintCheckerAgent"

    def run(self, state: TravelState) -> TravelState:
        def add_warning_once(warning: str) -> None:
            if warning not in state.warnings:
                state.warnings.append(warning)

        def add_rule_context_once(content: str, metadata: dict) -> None:
            rule_file = metadata.get("rule_file")
            already_exists = any(
                ctx.get("metadata", {}).get("rule_file") == rule_file
                for ctx in state.retrieved_context
            )
            if not already_exists:
                state.retrieved_context.append(
                    {
                        "content": content,
                        "metadata": metadata,
                    }
                )

        def add_rules_source_once(retrieved_rules: list[dict]) -> None:
            existing_rule_source = any(
                source.get("source") == "Travel rules RAG"
                for source in state.sources
            )

            if not existing_rule_source:
                state.sources.append(
                    {
                        "source": "Travel rules RAG",
                        "items": len(retrieved_rules),
                        "rule_files": [
                            rule["metadata"].get("rule_file")
                            for rule in retrieved_rules
                        ],
                    }
                )

        itinerary = state.draft_itinerary.copy()

        child_count = state.preferences.get("travelers", {}).get("children", 0)
        budget = state.preferences.get("budget", "medium")
        pace = state.preferences.get("pace", "medium")
        weather = state.weather or {}
        season = weather.get("season", "unknown")

        daily_forecast = weather.get("daily_forecast", [])
        rain_expected = any(day.get("rain_expected") for day in daily_forecast)

        # --- 1. Retrieve travel rules from RAG ---

        if child_count > 0:
            traveler_context = (
                f"family trip with {child_count} children child_under_6"
            )
        else:
            traveler_context = (
                "adult travel culture city exploration"
            )

        rule_query = (
            f"travel planning rules for {pace} pace, {budget} budget, "
            f"{traveler_context}, "
            f"season {season}, rain expected {rain_expected}, "
            f"weather, pacing, seasonality, budget constraints"
        )

        rule_results = query_rules(rule_query)

        retrieved_rules = []
        rule_texts = []

        for doc, meta in zip(
            rule_results["documents"][0],
            rule_results["metadatas"][0],
        ):
            retrieved_rules.append({"content": doc, "metadata": meta})
            rule_texts.append(doc.lower())
            add_rule_context_once(doc, meta)

        add_rules_source_once(retrieved_rules)

        # --- 2. Apply retrieved rules dynamically ---
        applied_rules = []

        if child_count > 0:
            for rule in rule_texts:
                if "no more than 2" in rule or "2 major activities" in rule:
                    add_warning_once(
                        "Applied rule: no more than 2 major activities per day for families with children."
                    )
                    applied_rules.append("family_pacing_limit")
                    break

        if rain_expected:
            for rule in rule_texts:
                if "indoor" in rule and ("rain" in rule or "rainy" in rule):
                    add_warning_once(
                        "Applied rule: rainy weather → prioritize indoor activities and backup options."
                    )
                    applied_rules.append("weather_indoor_priority")
                    break

        if pace == "slow":
            for rule in rule_texts:
                if "slow pace" in rule or "reduced fatigue" in rule or "no more than 2" in rule:
                    add_warning_once(
                        "Applied rule: slow pace → reduced number of activities and more rest time."
                    )
                    applied_rules.append("slow_pace_limit")
                    break

        if budget == "low":
            for rule in rule_texts:
                if "low budget" in rule or "free attractions" in rule or "public spaces" in rule:
                    add_warning_once(
                        "Applied rule: low budget → prioritize free or low-cost attractions."
                    )
                    applied_rules.append("low_budget_priority")
                    break

        if season in {"summer", "winter", "spring", "autumn"}:
            for rule in rule_texts:
                if season in rule or "season" in rule or "seasonal" in rule:
                    add_warning_once(
                        f"Applied rule: seasonality considered for {season} itinerary planning."
                    )
                    applied_rules.append("seasonality_considered")
                    break

        if "10 places" in state.user_message.lower() or "12 places" in state.user_message.lower():
            add_warning_once(
                "Applied rule: overloaded itinerary request detected → plan should be reduced to a realistic number of activities."
            )
            applied_rules.append("overload_reduction")

        # --- 3. Decide whether a single revision is required ---
        needs_revision = False
        actions = []
        reasons = []

        if child_count > 0:
            needs_revision = True
            reasons.append("family-friendly pacing")
            actions.append("limit_major_activities_per_day")

        if pace == "slow":
            needs_revision = True
            reasons.append("slow travel pace")
            actions.append("add_rest_breaks")

        if rain_expected:
            needs_revision = True
            reasons.append("rainy weather")
            actions.append("prioritize_indoor_activities")

        if budget == "low":
            needs_revision = True
            reasons.append("low budget")
            actions.append("avoid_high_budget_pois")

        if "overload_reduction" in applied_rules:
            needs_revision = True
            reasons.append("overloaded itinerary request")
            actions.append("reduce_activity_count")

        if needs_revision and state.revision_count == 0:
            state.revision_request = {
                "required": True,
                "reason": "Plan should be adjusted for: " + ", ".join(reasons),
                "actions": list(dict.fromkeys(actions)),
            }
        else:
            state.revision_request = {
                "required": False,
                "reason": "No further revision required.",
                "actions": [],
            }

                # --- 3.5 Hallucination grounding check ---

        retrieved_names = {
            poi["name"]
            for poi in state.retrieved_pois
        }

        hallucinated_items = []

        for day in itinerary.get("days", []):

            for field in ["morning", "afternoon"]:

                activity = day.get(field)

                if not activity:
                    continue

                normalized = activity.lower()

                allowed_generic = [
                    "free time",
                    "rest",
                    "walk",
                    "dinner",
                    "museum",
                    "cafe",
                    "cultural activity",
                    "recovery break",
                ]

                is_generic = any(
                    token in normalized
                    for token in allowed_generic
                )

                if (
                    activity not in retrieved_names
                    and not is_generic
                ):
                    hallucinated_items.append(activity)

        if hallucinated_items:

            add_warning_once(
                "Potential hallucinated itinerary items detected: "
                + ", ".join(sorted(set(hallucinated_items)))
            )

            state.agent_trace.append(
                {
                    "agent": "ConstraintCheckerAgent",
                    "event_type": "hallucination_detection",
                    "details": {
                        "hallucinated_items": sorted(
                            set(hallucinated_items)
                        )
                    },
                }
            )

        state.validated_itinerary = itinerary

        # --- 4. Add reasoning to trace ---
        state.agent_trace.append(
            {
                "agent": "ConstraintCheckerAgent",
                "event_type": "decision",
                "decision": "RAG-based constraint validation applied",
                "details": {
                    "child_count": child_count,
                    "pace": pace,
                    "budget": budget,
                    "season": season,
                    "rain_expected": rain_expected,
                    "retrieved_rule_files": [
                        rule["metadata"].get("rule_file")
                        for rule in retrieved_rules
                    ],
                    "applied_rules": applied_rules,
                    "revision_required": state.revision_request.get("required"),
                    "revision_reason": state.revision_request.get("reason"),
                    "revision_actions": state.revision_request.get("actions", []),
                },
                "used_rule_snippets": [
                    text[:500] + "..." if len(text) > 500 else text
                    for text in rule_texts[:2]
                ],
            }
        )

        return state