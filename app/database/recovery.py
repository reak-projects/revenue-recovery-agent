from app.models import RecoveryCase
from app.database.connection import get_connection
from psycopg.rows import dict_row

def save_case(case: RecoveryCase):

    with get_connection() as conn:

        with conn.cursor() as cursor:

            cursor.execute(
                """
                INSERT INTO recovery_cases (
                    case_id,
                    invoice_id,
                    customer_id,
                    invoice_amount,
                    amount_paid,
                    amount_due,
                    due_date,
                    days_overdue,
                    recovery_probability,
                    recommended_action,
                    promise_date,
                    promise_time,
                    status,
                    audit_log,
                    promise_evaluated
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (case_id)
                DO UPDATE SET
                    recovery_probability = EXCLUDED.recovery_probability,
                    recommended_action = EXCLUDED.recommended_action,
                    promise_date = EXCLUDED.promise_date,
                    promise_time = EXCLUDED.promise_time,
                    status = EXCLUDED.status,
                    promise_evaluated = EXCLUDED.promise_evaluated
                """,
                (
                    case.case_id,
                    case.invoice_id,
                    case.customer_id,
                    case.invoice_amount,
                    case.amount_paid,
                    case.amount_due,
                    case.due_date,
                    case.days_overdue,
                    case.recovery_probability,
                    case.recommended_action,
                    case.promise_date,
                    case.promise_time,
                    case.status,
                    "[]",
                    case.promise_evaluated,
                ),
            )


def get_case(case_id: str):

    with get_connection() as conn:

        with conn.cursor(row_factory=dict_row) as cursor:

            cursor.execute(
                """
                SELECT
                    case_id,
                    invoice_id,
                    customer_id,
                    invoice_amount,
                    amount_paid,
                    amount_due,
                    due_date,
                    days_overdue,
                    recovery_probability,
                    recommended_action,
                    promise_date,
                    promise_time,
                    status,
                    audit_log,
                    promise_evaluated
                FROM recovery_cases
                WHERE case_id = %s
                """,
                (case_id,),
            )

            row = cursor.fetchone()

            if row is None:
                return None

            return RecoveryCase(
                case_id=row["case_id"],
                invoice_id=row["invoice_id"],
                customer_id=row["customer_id"],
                invoice_amount=float(row["invoice_amount"]),
                amount_paid=float(row["amount_paid"]),
                amount_due=float(row["amount_due"]),
                due_date=row["due_date"],
                days_overdue=row["days_overdue"],
                recovery_probability=row["recovery_probability"],
                recommended_action=row["recommended_action"],
                promise_date=row["promise_date"],
                promise_time=row["promise_time"],
                status=row["status"],
                audit_log=row["audit_log"],
                promise_evaluated=row["promise_evaluated"],
            )


def get_all_cases():

    with get_connection() as conn:

        with conn.cursor(row_factory=dict_row) as cursor:

            cursor.execute(
                """
                SELECT
                    case_id,
                    invoice_id,
                    customer_id,
                    invoice_amount,
                    amount_paid,
                    amount_due,
                    due_date,
                    days_overdue,
                    recovery_probability,
                    recommended_action,
                    promise_date,
                    promise_time,
                    status,
                    audit_log,
                    promise_evaluated
                FROM recovery_cases
                ORDER BY due_date DESC
                """
            )

            rows = cursor.fetchall()

            return [
                RecoveryCase(
                    case_id=row["case_id"],
                    invoice_id=row["invoice_id"],
                    customer_id=row["customer_id"],
                    invoice_amount=float(row["invoice_amount"]),
                    amount_paid=float(row["amount_paid"]),
                    amount_due=float(row["amount_due"]),
                    due_date=row["due_date"],
                    days_overdue=row["days_overdue"],
                    recovery_probability=row["recovery_probability"],
                    recommended_action=row["recommended_action"],
                    promise_date=row["promise_date"],
                    promise_time=row["promise_time"],
                    status=row["status"],
                    audit_log=row["audit_log"],
                )
                for row in rows
            ]