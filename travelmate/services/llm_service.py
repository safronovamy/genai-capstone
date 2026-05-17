import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PREFERENCE_MODEL = os.getenv("OPENAI_PREFERENCE_MODEL", "gpt-4.1-mini")
SYNTHESIS_MODEL = os.getenv("OPENAI_SYNTHESIS_MODEL", "gpt-4.1-nano")


def generate_itinerary_response(prompt: str):
    response = client.chat.completions.create(
        model=SYNTHESIS_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful travel planning assistant. "
                    "Generate realistic, family-friendly travel itineraries. "
                    "Use only provided information and do not invent unsupported facts."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    return {
        "text": response.choices[0].message.content,
        "model": SYNTHESIS_MODEL,
        "usage": {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        },
    }