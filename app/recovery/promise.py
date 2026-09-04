from datetime import datetime, date, time, timedelta
from typing import Optional

from app.models import RecoveryCase


def resolve_promise_date(
    promised_date: Optional[str],
    today: date,
) -> Optional[date]:

    if not promised_date:
        return None

    value = promised_date.lower().strip()

    if value == "today":
        return today

    if value == "tomorrow":
        return today + timedelta(days=1)

    if value == "day after tomorrow":
        return today + timedelta(days=2)

    return None


def parse_promise_time(
    promised_time: Optional[str],
) -> Optional[time]:

    if not promised_time:
        return None

    value = promised_time.strip().upper()

    # Example: "15:00"
    try:
        return time.fromisoformat(value)
    except ValueError:
        pass

    # Examples: "3 PM" or "3:30 PM"
    for fmt in ("%I %p", "%I:%M %p"):
        try:
            return datetime.strptime(value, fmt).time()
        except ValueError:
            continue

    return None


def check_promise_status(
    case: RecoveryCase,
    current_datetime: datetime,
    amount_paid: float,
) -> str:

    # Payment has been completely received
    if amount_paid >= case.amount_due:
        return "RECOVERED"

    # No promise exists
    if not case.promise_date or not case.promise_time:
        return "NO_PROMISE"

    # Convert "3 PM" / "15:00" into a Python time object
    promise_time = parse_promise_time(
        case.promise_time
    )

    # Could not understand the time
    if promise_time is None:
        return "INVALID_PROMISE_TIME"

    # Combine date + time
    promised_datetime = datetime.combine(
        case.promise_date,
        promise_time,
    )

    # Promise time hasn't arrived yet
    if current_datetime < promised_datetime:
        return "PROMISE_PENDING"

    # Promise time has passed and payment is still missing
    return "PROMISE_BROKEN"