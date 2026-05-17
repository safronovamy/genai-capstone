import asyncio
import json
import sys
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from travelmate.services.metrics_service import MetricsService


SERVER_PATH = (
    Path(__file__).resolve().parents[1]
    / "mcp_servers"
    / "weather_server.py"
)


def _extract_text_content(tool_result: Any) -> str:
    if not getattr(tool_result, "content", None):
        return ""

    first = tool_result.content[0]

    if hasattr(first, "text"):
        return first.text

    if hasattr(first, "model_dump"):
        data = first.model_dump()
        if "text" in data:
            return data["text"]
        return json.dumps(data)

    if isinstance(first, dict):
        return first.get("text") or json.dumps(first)

    return str(first)


def _safe_json_loads(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except Exception:
        return {"raw": text}


def _detect_season(start_date: str | None = None) -> str:
    if start_date:
        try:
            month = datetime.fromisoformat(start_date).month
        except ValueError:
            month = datetime.now().month
    else:
        month = datetime.now().month

    if month in (12, 1, 2):
        return "winter"
    if month in (3, 4, 5):
        return "spring"
    if month in (6, 7, 8):
        return "summer"
    return "autumn"


def _normalize_forecast(
    city: str,
    forecast_data: Dict[str, Any],
    duration_days: int,
    start_date: str | None = None,
) -> Dict[str, Any]:
    daily = forecast_data.get("daily", {})
    current = forecast_data.get("current_weather", {}) or forecast_data.get("current", {})

    temperatures = daily.get("temperature_2m_max") or daily.get("temperature_max") or []
    rain_probs = daily.get("precipitation_probability_max") or daily.get("rain_probability") or []
    weather_codes = daily.get("weather_code") or daily.get("weathercode") or []

    limited_temps = temperatures[:duration_days] if isinstance(temperatures, list) else []
    limited_rain_probs = rain_probs[:duration_days] if isinstance(rain_probs, list) else []
    limited_codes = weather_codes[:duration_days] if isinstance(weather_codes, list) else []

    current_temp = (
        current.get("temperature")
        or current.get("temperature_2m")
        or (limited_temps[0] if limited_temps else None)
    )

    rain_expected = False

    if limited_rain_probs:
        rain_expected = any((p or 0) >= 50 for p in limited_rain_probs)

    rain_codes = {51, 53, 55, 61, 63, 65, 80, 81, 82, 95, 96, 99}
    if limited_codes:
        rain_expected = rain_expected or any(
            code in rain_codes for code in limited_codes if code is not None
        )

    classification = "rainy" if rain_expected else "good"

    daily_forecast = []
    dates = daily.get("time", [])

    requested_dates = []
    forecast_matches_requested_dates = True

    if start_date:
        try:
            start = datetime.fromisoformat(start_date).date()
            requested_dates = [
                (start + timedelta(days=i)).isoformat()
                for i in range(duration_days)
            ]
            forecast_matches_requested_dates = dates[:duration_days] == requested_dates
        except ValueError:
            forecast_matches_requested_dates = False

    forecast_length = min(
        duration_days,
        max(
            len(limited_temps),
            len(limited_rain_probs),
            len(limited_codes),
            len(dates),
        ),
    )

    for idx in range(forecast_length):
        rain_probability = (
            limited_rain_probs[idx] if idx < len(limited_rain_probs) else None
        )

        weather_code = (
            limited_codes[idx] if idx < len(limited_codes) else None
        )

        day_rain_expected = (
            (rain_probability is not None and rain_probability >= 50)
            or (weather_code in rain_codes if weather_code is not None else False)
        )

        daily_forecast.append(
            {
                "date": dates[idx] if idx < len(dates) else None,
                "temperature_max_c": limited_temps[idx] if idx < len(limited_temps) else None,
                "rain_probability": rain_probability,
                "weather_code": weather_code,
                "rain_expected": day_rain_expected,
            }
        )

    return {
        "summary": f"Forecast for {city} from Open-Meteo MCP",
        "classification": classification,
        "rain_expected": rain_expected,
        "temperature_c": current_temp,
        "season": _detect_season(start_date),
        "daily_forecast": daily_forecast,
        "requested_start_date": start_date,
        "requested_dates": requested_dates,
        "forecast_matches_requested_dates": forecast_matches_requested_dates,
        "source": "Open-Meteo MCP Server",
    }


async def _call_weather_mcp_async(
    city: str,
    duration_days: int = 1,
    start_date: str | None = None,
) -> Dict[str, Any]:
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_PATH)],
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            geocode_result = await session.call_tool(
                "geocode",
                {"city": city},
            )

            geocode_text = _extract_text_content(geocode_result)
            geocode_data = _safe_json_loads(geocode_text)

            latitude = geocode_data.get("latitude") or geocode_data.get("lat")
            longitude = geocode_data.get("longitude") or geocode_data.get("lon")
            resolved_city = geocode_data.get("name") or geocode_data.get("city") or city

            if latitude is None or longitude is None:
                return _fallback_weather(
                    city=city,
                    reason="Geocoding failed through MCP",
                )

            forecast_args = {
                "latitude": latitude,
                "longitude": longitude,
                "days": duration_days,
            }

            if start_date:
                forecast_args["start_date"] = start_date

            forecast_result = await session.call_tool(
                "forecast",
                forecast_args,
            )

            forecast_text = _extract_text_content(forecast_result)
            forecast_data = _safe_json_loads(forecast_text)

            return _normalize_forecast(
                city=resolved_city,
                forecast_data=forecast_data,
                duration_days=duration_days,
                start_date=start_date,
            )


def _fallback_weather(city: str, reason: Optional[str] = None) -> Dict[str, Any]:
    return {
        "summary": reason or "Weather MCP unavailable, fallback used",
        "classification": "unknown",
        "rain_expected": False,
        "temperature_c": None,
        "season": "unknown",
        "daily_forecast": [],
        "source": "fallback",
    }


@lru_cache(maxsize=32)
def get_weather(
    city: str,
    duration_days: int = 1,
    start_date: str | None = None,
) -> Dict[str, Any]:
    MetricsService.increment_weather_calls()

    try:
        return asyncio.run(_call_weather_mcp_async(city, duration_days, start_date))
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(
                _call_weather_mcp_async(city, duration_days, start_date)
            )
        finally:
            loop.close()
    except Exception as exc:
        return _fallback_weather(
            city=city,
            reason=(
                "Weather MCP unavailable, fallback used: "
                f"{type(exc).__name__}: {repr(exc)}"
            ),
        )