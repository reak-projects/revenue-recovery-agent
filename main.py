from datetime import date, datetime

from uuid import uuid4

from app.database.audit import save_audit_event
from fastapi import FastAPI # type: ignore
from pydantic import BaseModel # type: ignore
from uuid import uuid4
from app.database.reviews import save_human_review
from app.database.interactions import (
    get_customer_interaction,
    save_customer_interaction,
)

from app.agent.analyzer import analyze_customer_message
from app.agent.analyzer import (
    AI_ANALYSIS_UNAVAILABLE_MESSAGE,
    AIAnalysisError,
)
from app.agent.orchestrator import build_recovery_graph
from app.services.customer_service import (
    SUPPORTED_ACTIONS,
    execute_customer_action,
)
from app.recovery.workflow import handle_promise_status
from datetime import datetime
from app.database.recovery import get_case
from app.services.invoice_service import get_invoice
from app.recovery.promise import check_promise_status
from app.recovery.workflow import handle_promise_status
from app.database.reviews import save_human_review, get_human_reviews

from app.database.recovery import (
    get_case,
    save_case,
)

from app.integrations.razorpay import (
    get_invoice_payment_status,
    invoice_to_recovery_case,
    razorpay_client,
)

from app.recovery.promise import (
    check_promise_status,
    parse_promise_time,
    resolve_promise_date,
)

from app.services.recovery_service import (
    create_recovery_case,
)
from app.integrations.razorpay import get_invoice_customer_id



app = FastAPI()
class WebhookPayload(BaseModel):
    entity: str
    event: str
    payload: dict




@app.get("/")
def health_check():
    return {"status": "Revenue Recovery Agent is running"}


@app.get("/razorpay/test")
def test_razorpay():
    try:
        razorpay_client.invoice.all()

        return {
            "success": True,
            "message": "Razorpay Test Mode connected successfully"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/invoices")
def get_invoices():
    try:
        response = razorpay_client.invoice.all()

        cases = []

        for invoice in response["items"]:

            case = invoice_to_recovery_case(invoice)

            save_case(case)

            cases.append(case)

        return {
            "success": True,
            "cases": [
                {
                    "case_id": case.case_id,
                    "invoice_id": case.invoice_id,
                    "customer_id": case.customer_id,
                    "invoice_amount": case.invoice_amount,
                    "amount_paid": case.amount_paid,
                    "amount_due": case.amount_due,
                    "status": case.status,
                }
                for case in cases
            ],
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }

@app.post("/invoices/test")
def create_test_invoice():
    try:
        invoice = razorpay_client.invoice.create({
            "type": "invoice",
            "description": "Test invoice for Revenue Recovery Agent",
            "customer": {
                "name": "ABC Pvt Ltd",
                "email": "test@example.com",
                "contact": "9999999999"
            },
            "line_items": [
                {
                    "name": "Monthly SaaS Subscription",
                    "description": "August subscription",
                    "amount": 10000000,
                    "currency": "INR",
                    "quantity": 1
                }
            ],
            "sms_notify": 0,
            "email_notify": 0
        })

        return {
            "success": True,
            "invoice": invoice
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.post("/webhooks/razorpay")
async def razorpay_webhook(data: WebhookPayload):
    print(data)
    event = data.event
    print("EVENT VALUE:", repr(event))
    print("EVENT MATCH:", event == "payment.failed")

    if event == "payment.failed":

        print("PAYMENT FAILED BLOCK ENTERED")
        payment = data.payload["payment"]["entity"]

        payment_id = payment["id"]
        existing_case = get_case(f"case_{payment_id}")
        if existing_case is not None:
            return {
                "success": True,
                "message": "Recovery case already exists",
                "case": {
                    "case_id": existing_case.case_id,
                    "amount": existing_case.invoice_amount,
                    "status": existing_case.status,
                },
            }

        amount = payment["amount"] / 100
        invoice_id = payment["invoice_id"]
        customer_id = get_invoice_customer_id(invoice_id)

        case = create_recovery_case(
            payment_id=payment_id,
            customer_id=customer_id,
            invoice_id= invoice_id,
            amount=amount,
        )

        return {
            "success": True,
            "message": "Recovery case created",
            "case": {
                "case_id": case.case_id,
                "amount": case.invoice_amount,
                "status": case.status,
            }
        }

    return {
        "success": True,
        "message": f"Event received: {event}"
    }

@app.post("/agent/test")
def test_agent(message: str):

    customer_history = {
        "previous_promises": 3,
        "promises_kept": 1,
        "promises_broken": 2,
        "previous_payment_failures": 10,
        "reminders_sent": 3,
        "reminders_responded": 1,
    }

    try:
        decision = analyze_customer_message(
            customer_message=message,
            recovery_probability=0.865,
            customer_history=customer_history,
        )
    except AIAnalysisError:
        return {
            "success": False,
            "message": AI_ANALYSIS_UNAVAILABLE_MESSAGE,
        }

    return {
        "success": True,
        "decision": decision.model_dump()
    }


@app.post("/recovery/decide")
def recovery_decide(case_id: str, message: str):
    from app.database.customers import record_promise

    existing_interaction = get_customer_interaction(case_id, message)
    if existing_interaction is not None:
        return {
            "success": True,
            "message": "Decision already processed for this case and message",
            "case_id": case_id,
            "interaction_id": existing_interaction[0],
        }

    try:
        graph = build_recovery_graph()
        graph_state = graph.invoke({
            "case_id": case_id,
            "customer_message": message,
        })
    except AIAnalysisError:
        return {
            "success": False,
            "message": AI_ANALYSIS_UNAVAILABLE_MESSAGE,
        }
    except Exception:
        return {
            "success": False,
            "message": "Recovery request could not be completed. Please retry later.",
        }

    case = get_case(case_id)
    if case is None:
        return {
            "success": False,
            "message": "Recovery case not found",
        }

    recovery_probability = graph_state["recovery_probability"]
    intent = graph_state["intent"]
    confidence = graph_state["confidence"]
    promised_date = graph_state["promised_date"]
    promised_time = graph_state["promised_time"]
    candidate_action = graph_state["candidate_action"]
    final_action = graph_state["action"]
    reason = graph_state["reason"]

    promise_date = (
        date.fromisoformat(graph_state["case"]["promise_date"])
        if graph_state["case"].get("promise_date")
        else None
    )
    normalized_promise_time = graph_state["case"].get("promise_time")

    if intent == "PAYMENT_PROMISE":
        if graph_state["promise_is_new"]:
            record_promise(case.customer_id)

    case.promise_date = promise_date
    case.promise_time = normalized_promise_time

    case.recommended_action = final_action

    save_case(case)
    save_customer_interaction(
        interaction_id=str(uuid4()),
        case_id=case.case_id,
        message=message,
        detected_intent=intent,
        ai_confidence=confidence,
    )
    save_audit_event(
        event_id=str(uuid4()),
        case_id=case.case_id,
        event_type="AI_DECISION",
        description=reason,
        actor="AI_AGENT",
        metadata={
            "intent": intent,
            "candidate_action": candidate_action,
            "action": final_action,
            "confidence": confidence,
            "promised_date": (
                promise_date.isoformat()
                if promise_date
                else None
            ),
            "promised_time": promised_time,
        },
    )

    return {
        "success": True,
        "ai_decision": {
            "intent": intent,
            "action": candidate_action,
            "reason": reason,
            "confidence": confidence,
            "promised_date": promised_date,
            "promised_time": promised_time,
            "reminder_count": graph_state["reminder_count"],
            "reminder_interval_hours": graph_state[
                "reminder_interval_hours"
            ],
        },
        "promise": {
            "date": (
                promise_date.isoformat()
                if promise_date
                else None
            ),
            "time": promised_time,
        },
        "final_action": final_action,
        "candidate_action": candidate_action,
        "recovery_probability": recovery_probability,
        "intent": intent,
        "confidence": confidence,
        "reason": reason,
        "human_review_required": graph_state[
            "human_review_required"
        ],
        "execution_result": graph_state["execution_result"],
        "case": {
            "case_id": case.case_id,
            "invoice_id": case.invoice_id,
            "customer_id": case.customer_id,
            "amount_due": case.amount_due,
            "promise_date": (
                case.promise_date.isoformat()
                if case.promise_date
                else None
            ),
            "promise_time": case.promise_time,
            "status": case.status,
        },
    }
  

@app.get("/recovery/cases/{case_id}")
def get_recovery_case(case_id: str):

    case = get_case(case_id)

    if case is None:
        return {
            "success": False,
            "message": "Recovery case not found"
        }

    return {
        "success": True,
        "case": {
            "case_id": case.case_id,
            "invoice_id": case.invoice_id,
            "customer_id": case.customer_id,
            "amount_due": case.amount_due,
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
    }

@app.get("/razorpay/invoice/{invoice_id}/status")
def check_invoice_status(invoice_id: str):
    try:
        result = get_invoice_payment_status(
            invoice_id,
            razorpay_client,
        )

        return {
            "success": True,
            "payment": result,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }

@app.get("/recovery/cases/{case_id}/promise-status")
def promise_status(case_id: str):

    case = get_case(case_id)

    if case is None:
        return {
            "success": False,
            "message": "Recovery case not found",
        }

    payment = get_invoice_payment_status(
        case.invoice_id,
        razorpay_client,
    )
    case.amount_paid = payment["amount_paid"]
    case.amount_due = payment["amount_due"]

    status = check_promise_status(
        case=case,
        current_datetime=datetime.now(),
        amount_paid=payment["amount_paid"],
    )

    workflow_result = handle_promise_status(
        case=case,
        promise_status=status,
    )

    return {
        "success": True,
        "case_id": case.case_id,
        "payment": payment,
        "promise_status": status,
        "workflow": workflow_result,
    }

@app.get("/recovery/cases/{case_id}/promise-status/test")
def test_promise_status(case_id: str):

    case = get_case(case_id)

    if case is None:
        return {
            "success": False,
            "message": "Recovery case not found",
        }

    payment = get_invoice_payment_status(
        case.invoice_id,
        razorpay_client,
    )
    case.amount_paid = payment["amount_paid"]
    case.amount_due = payment["amount_due"]

    # Promise ke baad ka time simulate kar rahe hain
    simulated_time = datetime(
        2026,
        9,
        1,
        16,
        0,
    )

    status = check_promise_status(
        case=case,
        current_datetime=simulated_time,
        amount_paid=payment["amount_paid"],
    )

    return {
        "success": True,
        "case_id": case.case_id,
        "simulated_time": simulated_time.isoformat(),
        "payment": payment,
        "promise_status": status,
    }

@app.post("/recovery/check-promise")
def check_recovery_promise(case_id: str):

    case = get_case(case_id)

    if case is None:
        return {
            "success": False,
            "message": "Recovery case not found",
        }

    invoice = get_invoice(case.invoice_id)

    if invoice is None:
        return {
            "success": False,
            "message": "Invoice not found",
        }

    amount_paid = float(invoice["amount_paid"])
    case.amount_paid = amount_paid
    case.amount_due = float(invoice["amount_due"])

    promise_status = check_promise_status(
        case=case,
        current_datetime=datetime.now(),
        amount_paid=amount_paid,
    )

    result = handle_promise_status(
        case=case,
        promise_status=promise_status,
    )

    return {
        "success": True,
        "promise_status": promise_status,
        "result": result,
        "case_id": case.case_id,
    }


@app.post("/recovery/review")
def recovery_review(
    case_id: str,
    human_decision: str,
    correct: bool,
    reason: str | None = None,
    reviewer: str | None = None,
):
    case = get_case(case_id)

    if case is None:
        return {
            "success": False,
            "message": "Recovery case not found",
        }

    if case.status == "RECOVERED":
        return {
            "success": False,
            "message": "Recovered cases cannot receive new recovery actions",
        }

    if human_decision not in SUPPORTED_ACTIONS:
        return {
            "success": False,
            "message": f"Unsupported recovery action: {human_decision}",
        }

    ai_action = case.recommended_action
    if not ai_action:
        return {
            "success": False,
            "message": "No AI action is available for review",
        }

    prior_reviews = get_human_reviews(case_id)
    repeated_human_decision = bool(
        prior_reviews
        and prior_reviews[0][3] == human_decision
        and case.recommended_action == human_decision
    )

    # Human decision becomes the final action
    case.recommended_action = human_decision

    save_case(case)

    save_human_review(
        case_id=case.case_id,
        ai_action=ai_action,
        human_decision=human_decision,
        correct=correct,
        reason=reason,
        reviewer=reviewer,
    )

    save_audit_event(
        event_id=str(uuid4()),
        case_id=case.case_id,
        event_type="HUMAN_REVIEW",
        description="Human reviewed and finalized the recovery action.",
        actor=reviewer or "HUMAN",
        metadata={
            "ai_action": ai_action,
            "human_decision": human_decision,
            "correct": correct,
            "reason": reason,
        },
    )

    if repeated_human_decision:
        execution_result = {
            "status": "SKIPPED",
            "action": human_decision,
            "message": "Human-approved action was already executed.",
        }
    else:
        execution_result = execute_customer_action(
            action=human_decision,
            case_id=case.case_id,
            customer_id=case.customer_id,
            reason=reason or "Human-approved recovery action.",
        )

    return {
        "success": True,
        "case_id": case.case_id,
        "ai_action": ai_action,
        "human_decision": human_decision,
        "final_action": case.recommended_action,
        "correct": correct,
        "execution_result": execution_result,
        "message": "Human review saved and final action updated",
    }

@app.get("/recovery/cases/{case_id}/reviews")
def recovery_reviews(case_id: str):
    case = get_case(case_id)

    if case is None:
        return {
            "success": False,
            "message": "Recovery case not found",
        }

    reviews = get_human_reviews(case_id)

    return {
        "success": True,
        "case_id": case_id,
        "reviews": reviews,
    }