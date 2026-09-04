from datetime import datetime, timezone

from app.models import RecoveryCase
import os
import razorpay
from dotenv import load_dotenv # type: ignore

load_dotenv()

razorpay_client = razorpay.Client( # type: ignore
    auth=(
        os.getenv("RAZORPAY_KEY_ID"),
        os.getenv("RAZORPAY_KEY_SECRET"),
    )
)


def invoice_dates(invoice: dict):
    issued_timestamp = invoice.get("issued_at")
    due_timestamp = invoice.get("expire_by")

    issued_date = (
        datetime.fromtimestamp(issued_timestamp, tz=timezone.utc).date()
        if issued_timestamp
        else datetime.now(timezone.utc).date()
    )
    due_date = (
        datetime.fromtimestamp(due_timestamp, tz=timezone.utc).date()
        if due_timestamp
        else issued_date
    )

    return issued_date, due_date


def invoice_to_recovery_case(invoice: dict) -> RecoveryCase:
    issued_date, due_date = invoice_dates(invoice)

    return RecoveryCase(
        case_id=f"case_{invoice['id']}",
        invoice_id=invoice["id"],
        customer_id=invoice["customer_id"],

        invoice_amount=invoice["amount"] / 100,
        amount_paid=invoice["amount_paid"] / 100,
        amount_due=invoice["amount_due"] / 100,

        due_date=due_date,
    )

def get_invoice_payment_status(invoice_id: str, razorpay_client):

    invoice = razorpay_client.invoice.fetch(invoice_id)

    return {
        "invoice_id": invoice["id"],
        "status": invoice["status"],
        "amount_paid": invoice["amount_paid"] / 100,
        "amount_due": invoice["amount_due"] / 100,
        "payment_id": invoice.get("payment_id"),
    }

def create_test_customer(name, email, contact):
    return razorpay_client.customer.create({
        "name": name,
        "email": email,
        "contact": contact,
    })

def get_test_customers():
    return razorpay_client.customer.all()

def get_invoice_customer_id(invoice_id: str):
    invoice = razorpay_client.invoice.fetch(invoice_id)

    return invoice["customer_id"]

def sync_invoice_to_database(invoice_id: str):
    invoice = razorpay_client.invoice.fetch(invoice_id)

    customer_id = invoice["customer_id"]

    customer = razorpay_client.customer.fetch(customer_id)

    return customer, invoice


