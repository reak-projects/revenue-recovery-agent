from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class CustomerProfile:
    customer_id: str
    name: str
    email: str

    total_invoices: int = 0
    paid_invoices: int = 0
    late_invoices: int = 0

    average_payment_delay_days: float = 0.0

    disputes_count: int = 0

    reminders_sent: int = 0
    reminders_responded: int = 0


@dataclass
class RecoveryCase:
    case_id: str
    invoice_id: str
    customer_id: str

    invoice_amount: float
    amount_paid: float
    amount_due: float

    due_date: date
    days_overdue: int = 0

    recovery_probability: Optional[float] = None
    recommended_action: Optional[str] = None

    promise_date: Optional[date] = None
    promise_time: Optional[str] = None
    promise_evaluated: bool = False

    status: str = "OPEN"

    audit_log: list = field(default_factory=list)