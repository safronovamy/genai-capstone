from travelmate.models.state import TravelState
from travelmate.services.tracing_service import trace_agent

from travelmate.agents.preference_agent import PreferenceAgent
from travelmate.agents.location_agent import LocationAgent
from travelmate.agents.weather_agent import WeatherAgent
from travelmate.agents.itinerary_agent import ItineraryAgent
from travelmate.agents.constraint_checker_agent import ConstraintCheckerAgent
from travelmate.agents.synthesis_agent import SynthesisAgent

from travelmate.services.input_guard import sanitize_user_input
from travelmate.services.safety_service import validate_user_input


class TravelOrchestrator:
    def __init__(self):
        self.preference_agent = PreferenceAgent()
        self.location_agent = LocationAgent()
        self.weather_agent = WeatherAgent()
        self.itinerary_agent = ItineraryAgent()
        self.constraint_checker_agent = ConstraintCheckerAgent()
        self.synthesis_agent = SynthesisAgent()

    def plan_trip(self, user_message: str) -> TravelState:
        try:
            clean_message = sanitize_user_input(user_message)
        except ValueError as exc:
            state = TravelState(user_message=user_message or "")
            state.errors.append(str(exc))
            state.warnings.append("Please provide a valid travel planning request.")
            state.final_answer = (
                "I could not process the request because the input is empty or invalid."
            )
            return state

        state = TravelState(user_message=clean_message)

        is_valid, error_message = validate_user_input(clean_message)

        if not is_valid:
            state.errors.append(error_message)
            state.warnings.append(error_message)
            state.final_answer = error_message

            state.agent_trace.append(
                {
                    "agent": "SafetyGuard",
                    "status": "blocked",
                    "latency_ms": 0,
                    "reason": error_message,
                }
            )

            return state
            
        state = TravelState(user_message=clean_message)

        state = trace_agent(
            self.preference_agent.name,
            state,
            self.preference_agent.run,
        )

        state = trace_agent(
            self.location_agent.name,
            state,
            self.location_agent.run,
        )

        state = trace_agent(
            self.weather_agent.name,
            state,
            self.weather_agent.run,
        )

        # --- First itinerary generation ---
        state = trace_agent(
            self.itinerary_agent.name,
            state,
            self.itinerary_agent.run,
        )

        state = trace_agent(
            self.constraint_checker_agent.name,
            state,
            self.constraint_checker_agent.run,
        )

        # --- Controlled single revision loop ---
        if state.revision_request.get("required") and state.revision_count < 1:
            state.revision_count += 1

            state.agent_trace.append(
                {
                    "agent": "TravelOrchestrator",
                    "status": "revision",
                    "latency_ms": 0,
                    "reason": state.revision_request.get("reason"),
                    "actions": state.revision_request.get("actions", []),
                }
            )

            # Re-run itinerary with revision constraints already stored in state.
            state = trace_agent(
                self.itinerary_agent.name,
                state,
                self.itinerary_agent.run,
            )

            state = trace_agent(
                self.constraint_checker_agent.name,
                state,
                self.constraint_checker_agent.run,
            )

            # Explicitly close revision loop after the second check.
            state.revision_request = {
                "required": False,
                "reason": "Revision loop completed.",
                "actions": [],
            }

        # --- Final LLM synthesis ---
        state = trace_agent(
            self.synthesis_agent.name,
            state,
            self.synthesis_agent.run,
        )

        return state
