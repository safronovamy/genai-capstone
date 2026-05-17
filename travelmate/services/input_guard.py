import re


MAX_INPUT_LENGTH = 1000


def sanitize_user_input(text: str) -> str:
    if not text or not text.strip():
        raise ValueError("User input is empty.")

    text = text.strip()

    if len(text) > MAX_INPUT_LENGTH:
        raise ValueError(f"User input is too long. Max length is {MAX_INPUT_LENGTH} characters.")

    # Remove control characters
    text = re.sub(r"[\x00-\x1f\x7f-\x9f]", " ", text)

    # Collapse excessive whitespace
    text = re.sub(r"\s+", " ", text)

    return text


def validate_weather_response(data: dict) -> dict:
    if not isinstance(data, dict):
        return {
            "summary": "Invalid weather response",
            "temperature_c": None,
            "rain_expected": False,
            "classification": "unknown",
            "source": "fallback",
        }

    return data