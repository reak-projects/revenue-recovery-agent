FEATURE_ORDER = (
    "total_previous_invoices",
    "previous_paid_invoices",
    "previous_late_invoices",
    "previous_unresolved_invoices",
    "avg_payment_delay_days",
    "disputes_count",
    "reminders_sent",
    "reminders_responded",
    "previous_payment_failures",
    "previous_promises",
    "promises_kept",
    "promises_broken",
    "previous_reminders_successful",
    "customer_tenure_days",
    "average_invoice_amount",
    "previous_outstanding_amount",
    "invoice_amount",
    "days_overdue",
    "payment_success_rate",
    "reminder_response_rate",
    "reminder_success_rate",
    "promise_break_rate",
)


def build_features(customer: dict, invoice: dict) -> dict:
    total_previous_invoices = customer["total_invoices"]
    previous_paid_invoices = customer["paid_invoices"]
    previous_late_invoices = customer["late_invoices"]
    previous_unresolved_invoices = customer["unresolved_invoices"]

    avg_payment_delay_days = customer["average_payment_delay_days"]
    disputes_count = customer["disputes_count"]

    reminders_sent = customer["reminders_sent"]
    reminders_responded = customer["reminders_responded"]

    previous_payment_failures = customer["previous_payment_failures"]

    previous_promises = customer.get("previous_promises", 0)
    promises_kept = customer.get("promises_kept", 0)
    promises_broken = customer.get("promises_broken", 0)

    previous_reminders_successful = customer.get(
        "previous_reminders_successful", 0
    )

    customer_tenure_days = customer.get("customer_tenure_days", 0)
    average_invoice_amount = customer.get("average_invoice_amount", 0)
    previous_outstanding_amount = customer.get(
        "previous_outstanding_amount", 0
    )

    invoice_amount = invoice["amount"]
    days_overdue = invoice.get("days_overdue", 0)

    payment_success_rate = (
        previous_paid_invoices / total_previous_invoices
        if total_previous_invoices > 0
        else 0
    )

    reminder_response_rate = (
        reminders_responded / reminders_sent
        if reminders_sent > 0
        else 0
    )

    reminder_success_rate = (
        previous_reminders_successful / reminders_sent
        if reminders_sent > 0
        else 0
    )

    promise_break_rate = (
        promises_broken / previous_promises
        if previous_promises > 0
        else 0
    )

    return {
        "total_previous_invoices": total_previous_invoices,
        "previous_paid_invoices": previous_paid_invoices,
        "previous_late_invoices": previous_late_invoices,
        "previous_unresolved_invoices": previous_unresolved_invoices,
        "avg_payment_delay_days": avg_payment_delay_days,
        "disputes_count": disputes_count,
        "reminders_sent": reminders_sent,
        "reminders_responded": reminders_responded,
        "previous_payment_failures": previous_payment_failures,
        "previous_promises": previous_promises,
        "promises_kept": promises_kept,
        "promises_broken": promises_broken,
        "previous_reminders_successful": previous_reminders_successful,
        "customer_tenure_days": customer_tenure_days,
        "average_invoice_amount": average_invoice_amount,
        "previous_outstanding_amount": previous_outstanding_amount,
        "invoice_amount": invoice_amount,
        "days_overdue": days_overdue,
        "payment_success_rate": payment_success_rate,
        "reminder_response_rate": reminder_response_rate,
        "reminder_success_rate": reminder_success_rate,
        "promise_break_rate": promise_break_rate,
    }