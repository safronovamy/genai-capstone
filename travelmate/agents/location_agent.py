from travelmate.agents.base_agent import BaseAgent
from travelmate.models.state import TravelState
from travelmate.services.rag_service import query_pois


class LocationAgent(BaseAgent):
    name = "LocationAgent"

    def run(self, state: TravelState) -> TravelState:
        city = state.preferences.get("city", "")

        if not state.preferences.get("supported", False):
            state.retrieved_pois = []

            state.agent_trace.append(
                {
                    "agent": self.name,
                    "event_type": "decision",
                    "decision": "city not supported → skipping POI retrieval",
                }
            )

            return state

        query_text = self._build_query_text(state)

        duration_days = state.preferences.get("duration_days", 3)
        pace = state.preferences.get("pace", "medium")

        base_per_day = 3

        if pace == "slow":
            base_per_day = 4
        elif pace == "active":
            base_per_day = 6

        n_results = max(5, min(duration_days * base_per_day, 20))

        results = query_pois(
            query_text,
            city=city,
            n_results=n_results
        )

        pois = []
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            pois.append(meta)

        # ---------------------------------------------
        # Adults-only reranking
        # ---------------------------------------------
        children = state.preferences.get(
            "travelers",
            {}
        ).get("children", 0)

        if children == 0:

            for poi in pois:
                suitable_for = str(
                    poi.get("suitable_for", "")
                ).lower()

                tags = str(
                    poi.get("tags", "")
                ).lower()

                if (
                    "kids" in suitable_for
                    or "families" in suitable_for
                    or "kids" in tags
                ):
                    poi["priority_score"] = max(
                        poi.get("priority_score", 5) - 3,
                        1
                    )

            pois = sorted(
                pois,
                key=lambda x: x.get("priority_score", 0),
                reverse=True
            )

            state.agent_trace.append(
                {
                    "agent": self.name,
                    "event_type": "decision",
                    "decision": "adult-only reranking applied",
                }
            )

        state.retrieved_pois = pois

        poi_types = set()

        for poi in pois:
            poi_type = poi.get("type")
            if poi_type:
                poi_types.add(poi_type)

        if len(poi_types) <= 1:
            state.warnings.append(
                "Limited attraction diversity detected in retrieved results."
            )

        state.agent_trace.append(
            {
                "agent": "LocationAgent",
                "event_type": "bias_check",
                "details": {
                    "unique_poi_types": list(poi_types),
                    "diversity_warning": len(poi_types) <= 1
                }
            }
        )

        state.sources.append(
            {
                "source": "RAG knowledge base",
                "city": city,
                "items": len(pois),
                "poi_names": [p.get("name") for p in pois],
                "query_text": query_text,
            }
        )

        state.agent_trace.append(
            {
                "agent": self.name,
                "event_type": "decision",
                "query_text": query_text,
                "decision": "adaptive retrieval size selected",
                "details": {
                    "duration_days": duration_days,
                    "pace": pace,
                    "n_results": n_results,
                }
            }
        )

        return state

    def _build_query_text(self, state: TravelState) -> str:
        preferences = state.preferences

        city = preferences.get("city", "")

        raw_interests = preferences.get("interests", [])

        unique_interests = list(dict.fromkeys(raw_interests))

        pace = preferences.get("pace", "medium")
        budget = preferences.get("budget", "medium")

        travelers = preferences.get("travelers", {})
        children = travelers.get("children", 0)

        query_parts = [city]

        if unique_interests:
            query_parts.extend(unique_interests)
            # Repeat explicit user interests to make retrieval more interest-driven.
            query_parts.extend(unique_interests)            

        if children and children > 0:
            query_parts.extend(
                [
                    "family friendly",
                    "children",
                    "kids",
                    "stroller friendly",
                    "safe for children",
                ]
            )
        else:
            query_parts.extend(
                [
                    "adult travel",
                    "culture",
                    "history",
                    "restaurants",
                    "city walks",
                ]
            )

        query_parts.append(f"{pace} pace")
        query_parts.append(f"{budget} budget")

        deduped_query_parts = list(dict.fromkeys(
            str(part).strip()
            for part in query_parts
            if part
        ))

        return " ".join(deduped_query_parts)