from travelmate.agents.base_agent import BaseAgent
from travelmate.models.state import TravelState
from travelmate.mcp_tools.weather_mcp_client import get_weather


class WeatherAgent(BaseAgent):
    name = "WeatherAgent"

    def run(self, state: TravelState) -> TravelState:
        city = state.preferences.get("city")
        duration_days = state.preferences.get("duration_days", 1)

        if not city or str(city).lower() == "unknown":
            state.weather = {
                "summary": "Weather unavailable: no valid city provided",
                "classification": "unknown",
                "rain_expected": False,
                "temperature_c": None,
                "season": "unknown",
                "daily_forecast": [],
                "source": "no city provided",
            }

            state.agent_trace.append(
                {
                    "agent": self.name,
                    "event_type": "decision",
                    "decision": "no valid city → skipping MCP weather retrieval",
                    "details": {
                        "source": "no city provided",
                    },
                }
            )

            return state

        weather = get_weather(
            city=city,
            duration_days=duration_days,
            start_date=state.preferences.get("start_date"),
        )

        state.weather = weather

        state.agent_trace.append(
            {
                "agent": self.name,
                "event_type": "decision",
                "decision": "weather retrieved through MCP client",
                "details": {
                    "city": city,
                    "duration_days": duration_days,
                    "season": weather.get("season"),
                    "classification": weather.get("classification"),
                    "rain_expected": weather.get("rain_expected"),
                    "source": weather.get("source"),
                },
            }
        )

        return state