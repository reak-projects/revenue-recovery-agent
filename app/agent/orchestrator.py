from app.recovery.promise import (
    check_promise_status,
    parse_promise_time,
    resolve_promise_date,
)
from app.database.recovery import save_case
from typing import TypedDict
from pprint import pprint
from datetime import datetime

from app.database.recovery import get_case
from app.database.customers import get_customer
from app.services.invoice_service import get_invoice
from app.ml.features import build_features
from app.ml.predict import predict_recovery
from app.agent.analyzer import analyze_customer_message
from app.agent.decision import decide_action
from app.services.customer_service import execute_customer_action
from app.recovery.promise import check_promise_status


class RecoveryState(TypedDict):
    case_id: str
    customer_message: str

    case: dict

    customer_history: dict
    invoice_history: list
    payment_history: list

    intent: str
    confidence: float
    promised_date: str | None
    promised_time: str | None
    reminder_count: int
    reminder_interval_hours: int | None

    recovery_probability: float
    promise_status: str
    promise_is_new: bool

    action: str
    candidate_action: str
    reason: str

    execution_result: dict
    human_review_required: bool


def load_case(state: RecoveryState) -> RecoveryState:

    case = get_case(state["case_id"])

    if case is None:
        raise ValueError(
            f"Recovery case not found: {state['case_id']}"
        )

    invoice = get_invoice(case.invoice_id)
    if invoice is not None:
        case.invoice_amount = float(invoice["amount"])
        case.amount_paid = float(invoice["amount_paid"])
        case.amount_due = float(invoice["amount_due"])

    state["case"] = {
        "case_id": case.case_id,
        "invoice_id": case.invoice_id,
        "customer_id": case.customer_id,
        "invoice_amount": case.invoice_amount,
        "amount_paid": case.amount_paid,
        "amount_due": case.amount_due,
        "due_date": (
            case.due_date.isoformat()
            if case.due_date
            else None
        ),
        "days_overdue": case.days_overdue,
        "recovery_probability": case.recovery_probability,
        "recommended_action": case.recommended_action,
        "promise_date": (
            case.promise_date.isoformat()
            if case.promise_date
            else None
        ),
        "promise_time": case.promise_time,
        "status": case.status,
    }

    return state

def load_customer_history(state: RecoveryState) -> RecoveryState:

    customer_id = state["case"]["customer_id"]

    customer = get_customer(customer_id)

    if customer is None:
        state["customer_history"] = {}
        return state

    state["customer_history"] = customer

    return state


def load_ml_prediction(state: RecoveryState) -> RecoveryState:

    customer = state["customer_history"]
    if not customer:
        raise ValueError(
            f"Customer history not found for recovery case: "
            f"{state['case']['customer_id']}"
        )

    invoice_id = state["case"].get("invoice_id")
    if not invoice_id:
        raise ValueError(
            f"Invoice ID missing for recovery case: "
            f"{state['case']['case_id']}"
        )

    invoice = get_invoice(invoice_id)
    if invoice is None:
        raise ValueError(
            f"Invoice not found for recovery case: {invoice_id}"
        )

    features = build_features(customer, invoice)
    probability = predict_recovery(
        features=features,
        case_id=state["case"]["case_id"],
    )

    state["recovery_probability"] = probability
    state["case"]["recovery_probability"] = probability

    return state


def analyze_customer_message_node(state: RecoveryState) -> RecoveryState:

    decision = analyze_customer_message(
        customer_message=state["customer_message"],
        recovery_probability=state["recovery_probability"],
        customer_history=state["customer_history"],
    )

    state["intent"] = decision.intent
    state["confidence"] = decision.confidence
    state["promised_date"] = decision.promised_date
    state["promised_time"] = decision.promised_time
    state["reminder_count"] = decision.reminder_count
    state["reminder_interval_hours"] = decision.reminder_interval_hours
    state["reason"] = decision.reason
    state["candidate_action"] = decision.action
    state["action"] = decision.action

    return state


def apply_policy(state: RecoveryState) -> RecoveryState:

    promise_status = state.get("promise_status")

    if promise_status == "RECOVERED":
        final_action = "RECOVERED"
    elif promise_status == "PROMISE_PENDING":
        final_action = "TRACK_PROMISE"
    else:
        final_action = decide_action(
            recovery_probability=state["recovery_probability"],
            days_overdue=state["case"]["days_overdue"],
            amount_due=state["case"]["amount_due"],
            promise_to_pay=(
                promise_status != "PROMISE_BROKEN"
                and state["intent"] == "PAYMENT_PROMISE"
            ),
            amount_paid=state["case"]["amount_paid"],
            previous_promises=state["customer_history"].get(
                "previous_promises", 0
            ),
            promises_kept=state["customer_history"].get(
                "promises_kept", 0
            ),
            promises_broken=state["customer_history"].get(
                "promises_broken", 0
            ),
        )

    state["action"] = final_action

    return state


def update_promise(state: RecoveryState) -> RecoveryState:
    case = get_case(state["case_id"])

    if case is None:
        raise ValueError(
            f"Recovery case not found: {state['case_id']}"
        )

    state["promise_is_new"] = False

    if case.status == "RECOVERED":
        return state

    if state["intent"] != "PAYMENT_PROMISE":
        return state

    promised_date = state.get("promised_date")
    promised_time = state.get("promised_time")

    if not promised_date or not promised_time:
        return state

    resolved_date = resolve_promise_date(
        promised_date=promised_date,
        today=datetime.now().date(),
    )

    if resolved_date is None:
        return state

    incoming_time = parse_promise_time(promised_time)
    normalized_incoming_time = (
        incoming_time.strftime("%H:%M")
        if incoming_time
        else promised_time
    )
    stored_time = parse_promise_time(case.promise_time)
    normalized_stored_time = (
        stored_time.strftime("%H:%M")
        if stored_time
        else case.promise_time
    )

    if (
        case.promise_date == resolved_date
        and normalized_stored_time == normalized_incoming_time
    ):
        state["case"]["promise_date"] = resolved_date.isoformat()
        state["case"]["promise_time"] = normalized_stored_time
        return state

    case.promise_date = resolved_date
    case.promise_time = normalized_incoming_time
    case.promise_evaluated = False

    save_case(case)

    state["case"]["promise_date"] = resolved_date.isoformat()
    state["case"]["promise_time"] = normalized_incoming_time
    state["promise_is_new"] = True

    return state


def check_promise(state: RecoveryState) -> RecoveryState:

    invoice_id = state["case"].get("invoice_id")
    if not invoice_id:
        raise ValueError(
            f"Invoice ID missing for recovery case: "
            f"{state['case_id']}"
        )

    invoice = get_invoice(invoice_id)

    if invoice is None:
        raise ValueError(
            f"Invoice not found for recovery case: {invoice_id}"
        )

    case = get_case(state["case_id"])
    if case is None:
        raise ValueError(
            f"Recovery case not found: {state['case_id']}"
        )

    if not case.promise_date or not case.promise_time:
        state["promise_status"] = "NO_PROMISE"
        return state

    state["promise_status"] = check_promise_status(
        case=case,
        current_datetime=datetime.now(),
        amount_paid=invoice["amount_paid"],
    )

    return state


def determine_human_review(state: RecoveryState) -> RecoveryState:
    state["human_review_required"] = (
        state["confidence"] < 0.60
        or state["intent"] == "UNKNOWN"
        or state["promise_status"] == "INVALID_PROMISE_TIME"
    )

    return state


def execute_action(state: RecoveryState) -> RecoveryState:
    if state["case"].get("status") == "RECOVERED":
        state["execution_result"] = {
            "status": "SKIPPED",
            "action": state["action"],
            "message": "Execution skipped because the case is already recovered.",
        }
        return state

    if state["human_review_required"]:
        state["execution_result"] = {
            "status": "SKIPPED",
            "action": state["action"],
            "message": "Execution skipped because human review is required.",
        }
        return state

    result = execute_customer_action(
        action=state["action"],
        case_id=state["case_id"],
        customer_id=state["case"]["customer_id"],
        reason=state.get("reason"),
    )

    state["execution_result"] = result
    return state


from langgraph.graph import StateGraph, START, END # type: ignore
def build_recovery_graph():

    graph = StateGraph(RecoveryState)

    graph.add_node("load_case", load_case)
    graph.add_node("load_customer_history", load_customer_history)
    graph.add_node("load_ml_prediction", load_ml_prediction)
    graph.add_node("analyze_customer_message", analyze_customer_message_node)
    graph.add_node("update_promise", update_promise)
    graph.add_node("apply_policy", apply_policy)
    graph.add_node("check_promise", check_promise)
    graph.add_node("determine_human_review", determine_human_review)
    graph.add_node("execute_action", execute_action)

    graph.add_edge(START, "load_case")
    graph.add_edge("load_case", "load_customer_history")
    graph.add_edge("load_customer_history", "load_ml_prediction")
    graph.add_edge("load_ml_prediction", "analyze_customer_message")
    graph.add_edge("analyze_customer_message", "update_promise")
    graph.add_edge("update_promise", "check_promise")
    graph.add_edge("check_promise", "determine_human_review")
    graph.add_edge("determine_human_review", "apply_policy")
    graph.add_edge("apply_policy", "execute_action")
    graph.add_edge("execute_action", END)

    return graph.compile()

if __name__ == "__main__":

    graph = build_recovery_graph()

    result = graph.invoke({
        "case_id": "case_inv_TVcUJxQASXd9Jp",
        "customer_message": "I will pay tomorrow at 3 PM.",
    })

    pprint(result, sort_dicts=False)

