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


for customer_id in customers:

    invoices = razorpay_client.invoice.all({
        "customer_id": customer_id
    })

    count = len(invoices["items"])

    print(f"{customer_id} → {count} invoices")