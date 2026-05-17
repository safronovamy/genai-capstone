from concurrent.futures import ThreadPoolExecutor

from travelmate.orchestrator.travel_orchestrator import TravelOrchestrator


REQUESTS = [
    "Plan a family trip to Prague with museums",
    "Plan a low-budget trip to Vienna",
    "Plan a rainy-day trip to Barcelona",
    "Plan a slow-pace family trip to Prague",
    "Plan a 2-day trip to Vienna with children",
]


def run_request(message: str):
    orchestrator = TravelOrchestrator()
    state = orchestrator.plan_trip(message)

    return {
        "success": bool(state.final_answer),
        "errors": state.errors,
        "trace_len": len(state.agent_trace),
    }


def test_concurrent_requests():
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(run_request, REQUESTS))

    for result in results:
        assert result["success"]
        assert len(result["errors"]) == 0
        assert result["trace_len"] >= 6