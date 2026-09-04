def decide_action(
    recovery_probability: float,
    days_overdue: int,
    amount_due: float,
    promise_to_pay: bool = False,
    amount_paid: float = 0,
    previous_promises: int = 0,
    promises_kept: int = 0,
    promises_broken: int = 0,
):
    # Payment already recovered
    if amount_due <= amount_paid:
        return "RECOVERED"

    # Customer has promised to pay
    if promise_to_pay:
        unreliable_promise_history = (
            previous_promises > 0
            and promises_broken > promises_kept
        )
        weak_recovery_case = (
            recovery_probability < 0.40
            or days_overdue > 30
        )

        if unreliable_promise_history and weak_recovery_case:
            return "ESCALATE"

        return "TRACK_PROMISE"

    # High recovery probability
    if recovery_probability >= 0.70 and days_overdue <= 30:
        return "SEND_REMINDER"

    # Moderate recovery probability
    if recovery_probability >= 0.40:
        return "SEND_PAYMENT_LINK"

    # Low recovery probability
    return "ESCALATE"