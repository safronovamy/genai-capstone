from travelmate.orchestrator.travel_orchestrator import TravelOrchestrator
from travelmate.services.rag_service import load_all_knowledge


def setup_module():
    load_all_knowledge()


def test_city_filtering_returns_only_requested_city():
    orchestrator = TravelOrchestrator()

    state = orchestrator.plan_trip(
        "Plan a 3-day trip to Vienna with parks and museums."
    )

    assert len(state.retrieved_pois) > 0

    for poi in state.retrieved_pois:
        assert poi["city"] == "Vienna"

def test_final_answer_uses_only_retrieved_pois():
    orchestrator = TravelOrchestrator()

    state = orchestrator.plan_trip(
        "Plan a 2-day trip to Prague with museums."
    )

    retrieved_names = {
        poi["name"]
        for poi in state.retrieved_pois
    }

    final_answer = state.final_answer.lower()

    allowed_mentions = 0

    for name in retrieved_names:
        if name.lower() in final_answer:
            allowed_mentions += 1

    # хотя бы один retrieved POI реально использован
    assert allowed_mentions > 0

    # пример простого hallucination check
    forbidden_examples = [
        "Eiffel Tower",
        "Louvre Museum",
        "Colosseum"
    ]

    for forbidden in forbidden_examples:
        assert forbidden.lower() not in final_answer

def test_unsupported_city_produces_warning():
    orchestrator = TravelOrchestrator()

    state = orchestrator.plan_trip(
        "Plan a trip to Atlantis with a child."
    )

    assert state.preferences["supported"] is False

    assert len(state.warnings) > 0

    assert any(
        "unsupported" in warning.lower()
        or "not supported" in warning.lower()
        or "unknown" in warning.lower()
        for warning in state.warnings
    )