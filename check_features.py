from pprint import pprint

from app.database.customers import get_customer
from app.services.invoice_service import get_invoice
from app.ml.features import build_features


customer_id = "cust_TUpWQ5BA8PIBLc"
invoice_id = "inv_TXe6iU3IKzwfWy"

customer = get_customer(customer_id)
invoice = get_invoice(invoice_id)

features = build_features(customer, invoice)

print("\n" + "=" * 60)
print("CUSTOMER")
print("=" * 60)
pprint(customer)

print("\n" + "=" * 60)
print("INVOICE")
print("=" * 60)
pprint(invoice)

print("\n" + "=" * 60)
print("ML FEATURES")
print("=" * 60)

for name, value in features.items():
    print(f"{name:35} : {value}")

print("=" * 60)