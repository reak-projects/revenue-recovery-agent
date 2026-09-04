from datetime import datetime, timezone

from app.integrations.razorpay import (
    get_invoice_customer_id,
    invoice_dates,
    razorpay_client,
)
from app.database.customers import save_customer, update_customer_profile
from app.database.invoices import save_invoice
from app.database.payments import save_payment


def sync_customers():
    response = razorpay_client.customer.all()

    for customer in response["items"]:
        save_customer(
            customer_id=customer["id"],
            name=customer.get("name", ""),
            email=customer.get("email", ""),
            contact=customer.get("contact", ""),
        )

    print(f"Synced {len(response['items'])} customers")


def sync_invoices():
    processed_count = 0
    skip = 0
    page_size = 100

    while True:
        response = razorpay_client.invoice.all({
            "count": page_size,
            "skip": skip,
        })
        invoices = response.get("items", [])

        for invoice in invoices:
            issued_date, due_date = invoice_dates(invoice)
            amount = invoice["amount"] / 100
            amount_paid = min(invoice.get("amount_paid", 0) / 100, amount)
            amount_due = max(amount - amount_paid, 0)

            save_invoice(
                invoice_id=invoice["id"],
                customer_id=invoice["customer_id"],
                amount=amount,
                amount_paid=amount_paid,
                amount_due=amount_due,
                issued_date=issued_date,
                due_date=due_date,
                status=("paid" if amount_due == 0 else invoice["status"]),
            )

        processed_count += len(invoices)
        if len(invoices) < page_size:
            break

        skip += len(invoices)

    print(f"Synced {processed_count} invoices")

    response = razorpay_client.customer.all()

    for customer in response["items"]:
        update_customer_profile(customer["id"])


def sync_payments():
    processed_count = 0
    skip = 0
    page_size = 100

    while True:
        response = razorpay_client.payment.all({
            "count": page_size,
            "skip": skip,
        })
        payments = response.get("items", [])

        for payment in payments:
            invoice_id = payment.get("invoice_id")

            if not invoice_id:
                continue

            customer_id = get_invoice_customer_id(invoice_id)
            payment_date = datetime.fromtimestamp(
                payment["created_at"],
                tz=timezone.utc,
            )

            save_payment(
                payment_id=payment["id"],
                invoice_id=invoice_id,
                customer_id=customer_id,
                amount=payment["amount"] / 100,
                status=payment["status"],
                payment_date=payment_date,
            )

        processed_count += len(payments)
        if len(payments) < page_size:
            break

        skip += len(payments)

    print(f"Synced {processed_count} payments")


if __name__ == "__main__":
    sync_customers()
    sync_invoices()
    sync_payments()