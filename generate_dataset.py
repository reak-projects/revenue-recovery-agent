import os
import random
import math
import pandas as pd


def generate_customer_history():
    total_invoices = random.randint(5, 30)

    # Generate a realistic payment pattern
    paid_invoices = random.randint(
        max(0, total_invoices - 10),
        total_invoices
    )

    remaining_invoices = total_invoices - paid_invoices

    late_invoices = random.randint(
        0,
        remaining_invoices
    )

    unresolved_invoices = remaining_invoices - late_invoices

    average_payment_delay = round(
        random.uniform(0, 30),
        1
    )

    disputes_count = random.randint(0, 5)

    reminders_sent = random.randint(0, 8)

    reminders_responded = random.randint(
        0,
        reminders_sent
    )

    previous_payment_failures = random.randint(0, 5)

    # NEW: promise behaviour
    previous_promises = random.randint(0, 6)

    if previous_promises > 0:

        promises_kept = random.randint(
            0,
            previous_promises
        )

        promises_broken = (
            previous_promises - promises_kept
        )

    else:

        promises_kept = 0
        promises_broken = 0

    # NEW: reminder effectiveness
    previous_reminders_successful = random.randint(
        0,
        reminders_sent
    )

    # NEW: customer age
    customer_tenure_days = random.randint(
        30,
        1800
    )

    # NEW: historical invoice size
    average_invoice_amount = random.choice([
        10000,
        25000,
        50000,
        75000,
        100000,
        250000,
        500000
    ])

    # NEW: historical outstanding amount
    previous_outstanding_amount = (
        unresolved_invoices
        * random.choice([
            10000,
            25000,
            50000,
            100000
        ])
    )

    return {
        "total_previous_invoices": total_invoices,
        "previous_paid_invoices": paid_invoices,
        "previous_late_invoices": late_invoices,
        "previous_unresolved_invoices": unresolved_invoices,
        "avg_payment_delay_days": average_payment_delay,
        "disputes_count": disputes_count,
        "reminders_sent": reminders_sent,
        "reminders_responded": reminders_responded,
        "previous_payment_failures": previous_payment_failures,

        "previous_promises": previous_promises,
        "promises_kept": promises_kept,
        "promises_broken": promises_broken,
        "previous_reminders_successful": (
            previous_reminders_successful
        ),
        "customer_tenure_days": customer_tenure_days,
        "average_invoice_amount": average_invoice_amount,
        "previous_outstanding_amount": (
            previous_outstanding_amount
        ),
    }


def generate_invoice():
    invoice_amount = random.choice([
        10000,
        25000,
        50000,
        75000,
        100000,
        250000,
        500000
    ])

    days_overdue = random.randint(0, 60)

    return {
        "invoice_amount": invoice_amount,
        "days_overdue": days_overdue
    }


def generate_recovery_outcome(customer, invoice):

    score = 0

    payment_rate = (
        customer["previous_paid_invoices"]
        / customer["total_previous_invoices"]
    )

    # Payment history
    if payment_rate >= 0.8:
        score += 3
    elif payment_rate >= 0.5:
        score += 1
    else:
        score -= 2

    # Overdue behaviour
    if invoice["days_overdue"] <= 7:
        score += 2
    elif invoice["days_overdue"] <= 30:
        score += 0
    else:
        score -= 2

    # Average payment delay
    if customer["avg_payment_delay_days"] <= 7:
        score += 2
    elif customer["avg_payment_delay_days"] > 20:
        score -= 2

    # Disputes
    score -= customer["disputes_count"]

    # Reminder response
    if customer["reminders_sent"] > 0:

        response_rate = (
            customer["reminders_responded"]
            / customer["reminders_sent"]
        )

        if response_rate >= 0.7:
            score += 2

        elif response_rate < 0.3:
            score -= 2

    # Payment failures
    score -= (
        customer["previous_payment_failures"]
        * 0.5
    )

    # NEW: broken promises
    score -= (
        customer["promises_broken"]
        * 1.0
    )

    # NEW: kept promises
    score += (
        customer["promises_kept"]
        * 0.5
    )

    # NEW: successful reminders
    score += (
        customer["previous_reminders_successful"]
        * 0.5
    )

    # NEW: outstanding debt
    if customer["previous_outstanding_amount"] > 200000:
        score -= 1

    # Convert score to probability
    probability = 1 / (
        1 + math.exp(-score)
    )

    recovered = (
        1
        if random.random() < probability
        else 0
    )

    return recovered


def generate_dataset(number_of_cases=5000):

    rows = []

    for i in range(number_of_cases):

        customer = generate_customer_history()

        invoice = generate_invoice()

        recovered = generate_recovery_outcome(
            customer,
            invoice
        )

        row = {
            "customer_id": f"CUST_{i + 1:05d}",
            **customer,
            **invoice,
            "recovered": recovered
        }

        rows.append(row)

    return pd.DataFrame(rows)


if __name__ == "__main__":

    os.makedirs("data", exist_ok=True)

    dataset = generate_dataset(5000)

    dataset.to_csv(
        "data/recovery_dataset_v2.csv",
        index=False
    )

    print("Dataset V2 generated successfully!")
    print(f"Rows: {len(dataset)}")
    print(f"Columns: {len(dataset.columns)}")
    print(dataset.columns.tolist())