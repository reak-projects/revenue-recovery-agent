from pprint import pprint
from datetime import datetime

from app.database.recovery import get_case
from app.services.invoice_service import get_invoice
from app.recovery.promise import check_promise_status


CASE_ID = "case_inv_TVcUJxQASXd9Jp"


case = get_case(CASE_ID)

if case is None:
    raise ValueError(f"Case not found: {CASE_ID}")


invoice = get_invoice(case.invoice_id)

if invoice is None:
    raise ValueError(f"Invoice not found: {case.invoice_id}")


print("\n--- PROMISE TEST ---")

print("Case ID:", case.case_id)
print("Promise date:", case.promise_date)
print("Promise time:", case.promise_time)
print("Amount due:", case.amount_due)
print("Amount paid:", invoice["amount_paid"])


status = check_promise_status(
    case=case,
    current_datetime=datetime.now(),
    amount_paid=invoice["amount_paid"],
)


print("\nPromise status:")
pprint(status)