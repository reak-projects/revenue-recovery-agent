from uuid import uuid4

from app.database.recovery import save_case
from app.database.actions import save_agent_action
from app.database.audit import audit_event_exists, save_audit_event

from app.database.customers import (
    get_customer,
    record_kept_promise,
    record_broken_promise,
)
from app.agent.decision import decide_action


def handle_promise_status(
    case,
    promise_status: str,
):
    """
    Handle the result of promise tracking.

    This function records what happened to the promise
    and decides what recovery action should happen next.
    """

    # Payment already received
    if promise_status == "RECOVERED":
        if case.status == "RECOVERED":
            return {
                "status": "RECOVERED",
                "action": "CLOSE_CASE",
            }

        if case.promise_date and not case.promise_evaluated:
            record_kept_promise(case.customer_id)
            case.promise_evaluated = True

        case.status = "RECOVERED"
        case.recommended_action = "CLOSE_CASE"

        save_case(case)

        save_agent_action(
            action_id=str(uuid4()),
            case_id=case.case_id,
            action="CLOSE_CASE",
            reason="Payment was completely received.",
        )

        save_audit_event(
            event_id=str(uuid4()),
            case_id=case.case_id,
            event_type="PAYMENT_RECOVERED",
            description="Customer payment was completely received.",
            actor="SYSTEM",
            metadata={
                "promise_status": promise_status,
                "action": "CLOSE_CASE",
            },
        )

        return {
            "status": "RECOVERED",
            "action": "CLOSE_CASE",
        }

    # Promise deadline passed without payment
    if promise_status == "PROMISE_BROKEN":
        if case.promise_evaluated:
            return {
                "status": "PROMISE_BROKEN",
                "action": case.recommended_action or "SEND_REMINDER",
            }

        if not case.promise_evaluated:
            record_broken_promise(case.customer_id)
            case.promise_evaluated = True

        customer = get_customer(case.customer_id) or {}
        next_action = decide_action(
            recovery_probability=(
                case.recovery_probability
                if case.recovery_probability is not None
                else 0
            ),
            days_overdue=case.days_overdue,
            amount_due=case.amount_due,
            promise_to_pay=False,
            amount_paid=case.amount_paid,
            previous_promises=customer.get("previous_promises", 0),
            promises_kept=customer.get("promises_kept", 0),
            promises_broken=customer.get("promises_broken", 0),
        )

        case.status = "PROMISE_BROKEN"
        case.recommended_action = next_action

        save_case(case)

        save_agent_action(
            action_id=str(uuid4()),
            case_id=case.case_id,
            action=next_action,
            reason="Customer promised payment but the promised deadline passed without full payment.",
        )

        save_audit_event(
            event_id=str(uuid4()),
            case_id=case.case_id,
            event_type="PROMISE_BROKEN",
            description="Customer promise expired without complete payment.",
            actor="SYSTEM",
            metadata={
                "promise_status": promise_status,
                "action": next_action,
            },
        )

        return {
            "status": "PROMISE_BROKEN",
            "action": next_action,
        }

    # Promise still waiting
    if promise_status == "PROMISE_PENDING":
        pending_metadata = {
            "promise_status": promise_status,
            "promise_date": (
                case.promise_date.isoformat()
                if case.promise_date
                else None
            ),
            "promise_time": case.promise_time,
        }

        if audit_event_exists(
            case_id=case.case_id,
            event_type="PROMISE_PENDING",
            metadata=pending_metadata,
        ):
            return {
                "status": "PROMISE_PENDING",
                "action": "WAIT",
            }

        save_audit_event(
            event_id=str(uuid4()),
            case_id=case.case_id,
            event_type="PROMISE_PENDING",
            description="Customer payment promise has not expired yet.",
            actor="SYSTEM",
            metadata=pending_metadata,
        )

        return {
            "status": "PROMISE_PENDING",
            "action": "WAIT",
        }

    # No promise exists
    if promise_status == "NO_PROMISE":

        return {
            "status": "NO_PROMISE",
            "action": "NO_ACTION",
        }

    # Unknown / invalid status
    return {
        "status": promise_status,
        "action": "REVIEW",
    }