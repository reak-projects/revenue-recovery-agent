import logging
import os
from typing import Optional, Literal
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class AIAnalysisError(RuntimeError):
    """Raised when Gemini cannot provide a valid customer analysis."""


AI_ANALYSIS_UNAVAILABLE_MESSAGE = (
    "AI analysis is temporarily unavailable. Please retry later."
)

class AgentDecision(BaseModel):
    intent: Literal[
        "PAYMENT_PROMISE",
        "PAYMENT_ISSUE",
        "DISPUTE",
        "REQUEST_PAYMENT_LINK",
        "REFUSAL",
        "UNKNOWN",
    ]

    action: Literal[
        "SEND_REMINDER",
        "SEND_PAYMENT_LINK",
        "TRACK_PROMISE",
        "ESCALATE",
        "CLOSE_CASE",
    ]

    reason: str

    confidence: float

    promised_date: Optional[str] = None
    promised_time: Optional[str] = None

    reminder_count: int = 0
    reminder_interval_hours: Optional[int] = None

from google import genai


client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def analyze_customer_message(
    customer_message: str,
    recovery_probability: float,
    customer_history: dict,
):
    prompt = f"""
You are a B2B revenue recovery assistant.

Analyze the customer's message and choose exactly one
intent and one allowed action.

Customer message:
{customer_message}

Customer history:
{customer_history}

Recovery probability:
{recovery_probability}

Allowed intents:
PAYMENT_PROMISE
PAYMENT_ISSUE
DISPUTE
REQUEST_PAYMENT_LINK
REFUSAL
UNKNOWN

Allowed actions:
SEND_REMINDER
SEND_PAYMENT_LINK
TRACK_PROMISE
ESCALATE
CLOSE_CASE

Recovery strategy rules:

- If the customer promises to pay, set reminder_count to 0.
- If the customer has a payment issue but intends to pay, suggest 1 to 3 reminders.
- If the customer refuses to pay or repeatedly ignores reminders, prefer ESCALATE.
- Do not suggest more than 3 reminders.
- reminder_interval_hours must be between 12 and 72 when reminders are suggested.
- Do not send a reminder immediately if the customer has made a payment promise.

Return ONLY valid JSON with:
intent
action
reason
confidence
promised_date
promised_time
reminder_count
reminder_interval_hours
"""

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json"
            }
        )
    except Exception as error:
        logger.error(
            "Gemini analysis failed: category=%s error_type=%s",
            _gemini_error_category(error),
            type(error).__name__,
        )
        raise AIAnalysisError(
            AI_ANALYSIS_UNAVAILABLE_MESSAGE
        ) from error

    try:
        response_text = response.text
        if not response_text:
            raise ValueError("Gemini returned an empty response")

        return AgentDecision.model_validate_json(response_text)
    except Exception as error:
        logger.error(
            "Gemini returned malformed analysis: error_type=%s",
            type(error).__name__,
        )
        raise AIAnalysisError(
            AI_ANALYSIS_UNAVAILABLE_MESSAGE
        ) from error


def _gemini_error_category(error: Exception) -> str:
    status_code = getattr(error, "status_code", None)
    error_text = str(error).upper()

    if (
        status_code == 429
        or "429" in error_text
        or "RESOURCE_EXHAUSTED" in error_text
    ):
        return "rate_limited"
    if (
        status_code == 403
        or "403" in error_text
        or "PERMISSION_DENIED" in error_text
    ):
        return "permission_denied"
    if any(
        value in error_text
        for value in ("TIMEOUT", "TIMED OUT", "NETWORK")
    ):
        return "network_or_timeout"
    return "provider_error"