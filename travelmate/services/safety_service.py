BLOCKED_KEYWORDS = [
    "illegal",
    "drugs",
    "weapon",
    "self-harm",
    "suicide",
    "sexual",
    "porn",
    "hate",
    "violence",
]


def validate_user_input(user_message: str) -> tuple[bool, str | None]:
    if not user_message or not user_message.strip():
        return False, "Please describe your trip: destination, duration, and preferences."

    if len(user_message) > 1000:
        return False, "Your request is too long. Please shorten it."

    lowered = user_message.lower()

    for keyword in BLOCKED_KEYWORDS:
        if keyword in lowered:
            return False, (
                "This request cannot be processed because it appears to contain "
                "unsafe or inappropriate content for a family travel planner."
            )

    return True, None