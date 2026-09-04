from unittest import case

from app.models import RecoveryCase
from datetime import date, datetime
from app.database.payments import payment_exists, save_payment
from app.database.invoices import update_invoice_payment
from app.database.customers import record_successful_payment
from app.database.recovery import get_case, save_case
from app.database.customers import get_customer
from app.services.invoice_service import get_invoice
from app.ml.features import build_features
from app.ml.predict import predict_recovery
from app.integrations.razorpay import invoice_dates, sync_invoice_to_database
from app.database.customers import save_customer
from app.database.invoices import save_invoice

recovery_cases = {}


def ensure_recovery_prediction(case: RecoveryCase) -> float:
    customer = get_customer(case.customer_id)
    invoice = get_invoice(case.invoice_id)

    if customer is None:
        raise ValueError(
            f"Customer not found for recovery case: {case.customer_id}"
        )

    if invoice is None:
        raise ValueError(
            f"Invoice not found for recovery case: {case.invoice_id}"
        )

    features = build_features(customer, invoice)
    probability = predict_recovery(
        features=features,
        case_id=case.case_id,
    )

    case.recovery_probability = probability
    save_case(case)
    return probability


def create_recovery_case(
    payment_id: str,
    customer_id: str,
    invoice_id: str,
    amount: float,
) -> RecoveryCase:
    existing_case = get_case(f"case_{payment_id}")
    if existing_case is not None:
        return existing_case

    customer, invoice = sync_invoice_to_database(invoice_id)
    issued_date, due_date = invoice_dates(invoice)
    invoice_amount = invoice["amount"] / 100
    amount_paid = invoice.get("amount_paid", 0) / 100
    amount_due = max(invoice_amount - amount_paid, 0)

    save_customer(
        customer_id=customer["id"],
        name=customer.get("name", ""),
        email=customer.get("email", ""),
        contact=customer.get("contact", ""),
    )
    save_invoice(
        invoice_id=invoice["id"],
        customer_id=invoice["customer_id"],
        amount=invoice_amount,
        amount_paid=amount_paid,
        amount_due=amount_due,
        issued_date=issued_date,
        due_date=due_date,
        status=("paid" if amount_due == 0 else invoice.get("status", "issued")),
    )

    case = RecoveryCase(
        case_id=f"case_{payment_id}",
        invoice_id=invoice_id,
        customer_id=customer_id,
        invoice_amount=invoice_amount,
        amount_paid=amount_paid,
        amount_due=amount_due,
        due_date=due_date,
    )

    case.audit_log.append({
        "event": "RECOVERY_CASE_CREATED",
        "payment_id": payment_id,
        "reason": "PAYMENT_FAILED"
    })

    recovery_cases[case.case_id] = case
    print("CREATING CASE:", case.case_id)
    print("INVOICE:", case.invoice_id)
    print("CUSTOMER:", case.customer_id)
    save_case(case)
    print("CASE SAVED:", case.case_id)
    customer = get_customer(customer_id)
    invoice = get_invoice(invoice_id)
    print("CUSTOMER DATA:", customer)
    print("INVOICE DATA:", invoice)

    if customer and invoice:
        print("BUILDING ML FEATURES")
        probability = ensure_recovery_prediction(case)
        print("ML PROBABILITY:", probability)

    return case

def record_payment(
    payment_id: str,
    invoice_id: str,
    customer_id: str,
    amount: float,
):
    if payment_exists(payment_id):
        return

    invoice = get_invoice(invoice_id)
    if invoice is None:
        raise ValueError(f"Invoice not found: {invoice_id}")

    total_paid = min(
        float(invoice["amount_paid"]) + amount,
        float(invoice["amount"]),
    )
    amount_due = max(float(invoice["amount"]) - total_paid, 0)
    status = "paid" if amount_due == 0 else "partially_paid"

    save_payment(
        payment_id=payment_id,
        invoice_id=invoice_id,
        customer_id=customer_id,
        amount=amount,
        status=status,
        payment_date=datetime.now(),
    )

    update_invoice_payment(
        invoice_id=invoice_id,
        amount_paid=total_paid,
        amount_due=amount_due,
        status=status,
    )

    if status == "paid":
        record_successful_payment(customer_id)