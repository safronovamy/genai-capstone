import re


EMAIL_PATTERN = r'[\w\.-]+@[\w\.-]+\.\w+'
PHONE_PATTERN = r'\+?\d[\d\s\-\(\)]{7,}\d'


def anonymize_pii(text: str):
    """
    Replace obvious PII patterns with placeholders.
    Returns:
        sanitized_text,
        pii_detected (bool)
    """

    original = text

    text = re.sub(EMAIL_PATTERN, "[EMAIL]", text)
    text = re.sub(PHONE_PATTERN, "[PHONE]", text)

    pii_detected = text != original

    return text, pii_detected