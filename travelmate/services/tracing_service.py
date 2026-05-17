import time
from typing import Callable
from travelmate.models.state import TravelState


def trace_agent(agent_name: str, state: TravelState, func: Callable[[TravelState], TravelState]) -> TravelState:
    start = time.time()

    try:
        result = func(state)
        status = "success"
    except Exception as exc:
        state.errors.append(f"{agent_name}: {str(exc)}")
        result = state
        status = "error"

    latency_ms = int((time.time() - start) * 1000)

    result.agent_trace.append(
        {
            "agent": agent_name,
            "status": status,
            "latency_ms": latency_ms,
        }
    )

    return result