import json
import httpx
from datetime import datetime, timedelta
from mcp.server.fastmcp import FastMCP


app = FastMCP("open-meteo-mcp")


@app.tool()
async def geocode(city: str) -> str:
    """Convert city name to latitude and longitude using Open-Meteo geocoding."""
    url = "https://geocoding-api.open-meteo.com/v1/search"

    params = {
        "name": city,
        "count": 1,
        "language": "en",
        "format": "json",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

    results = data.get("results", [])

    if not results:
        return json.dumps(
            {
                "error": f"City not found: {city}",
                "city": city,
            }
        )

    first = results[0]

    return json.dumps(
        {
            "name": first.get("name"),
            "country": first.get("country"),
            "latitude": first.get("latitude"),
            "longitude": first.get("longitude"),
            "timezone": first.get("timezone"),
        }
    )


@app.tool()
async def forecast(
    latitude: float,
    longitude: float,
    days: int = 3,
    start_date: str | None = None,
) -> str:
    """Get weather forecast from Open-Meteo for requested travel dates when available."""
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current_weather": True,
        "daily": [
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_probability_max",
        ],
        "timezone": "auto",
    }

    if start_date:
        start = datetime.fromisoformat(start_date).date()
        end = start + timedelta(days=days - 1)
        params["start_date"] = start.isoformat()
        params["end_date"] = end.isoformat()
    else:
        params["forecast_days"] = days

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

    return json.dumps(data)



if __name__ == "__main__":
    app.run()