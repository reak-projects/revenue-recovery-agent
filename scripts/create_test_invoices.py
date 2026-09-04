import time

from app.integrations.razorpay import razorpay_client


customers = [
    "cust_TWN0ZkRK6rp3DM",
    "cust_TWN0YgyXBiyBFr",
    "cust_TWN0YlzmbUjjfb",
    "cust_TWN0YsZ4MXDM16",
    "cust_TWN0Z5jsliVWIZ",
    "cust_TWN0ZAyGkH8gws",
    "cust_TWN0ZbR97xgNRj",
    "cust_TWN0ZFXu3ZSpwY",
    "cust_TWN0ZKcb41O3sE",
    "cust_TWN0ZUUJCsJ7bS",
]

TARGET_PER_CUSTOMER = 7


for customer_id in customers:

    invoices = razorpay_client.invoice.all({
        "customer_id": customer_id
    })

    current_count = len(invoices["items"])
    missing = TARGET_PER_CUSTOMER - current_count

    print(
        f"{customer_id}: "
        f"{current_count} existing, "
        f"{max(missing, 0)} needed"
    )

    for _ in range(max(missing, 0)):

        try:
            invoice = razorpay_client.invoice.create({
                "type": "invoice",
                "description": "Demo invoice for Revenue Recovery Agent",
                "customer_id": customer_id,
                "line_items": [
                    {
                        "name": "Monthly SaaS Subscription",
                        "description": "Demo subscription",
                        "amount": 10000000,
                        "currency": "INR",
                        "quantity": 1,
                    }
                ],
                "sms_notify": 0,
                "email_notify": 0,
            })

            print(f"Created: {invoice['id']}")

            time.sleep(5)

        except Exception as e:
            print(f"Stopped: {e}")
            break