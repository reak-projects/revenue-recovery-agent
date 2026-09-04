from app.database.recovery import get_case
from app.recovery.workflow import handle_promise_status

CASE_ID = "case_inv_TVcUJxQASXd9Jp"

case = get_case(CASE_ID)

if case is None:
    raise ValueError(f"Case not found: {CASE_ID}")

result = handle_promise_status(
    case=case,
    promise_status="PROMISE_PENDING",
)

print("\n--- PROMISE HANDLER TEST ---")
print(result)