from app.database.connection import get_connection

def save_invoice(
    invoice_id: str,
    customer_id: str,
    amount: float,
    amount_paid: float,
    amount_due: float,
    issued_date,
    due_date,
    status: str,
):
    with get_connection() as conn:

        with conn.cursor() as cursor:

            cursor.execute(
                """
                INSERT INTO invoices (
                    invoice_id,
                    customer_id,
                    amount,
                    amount_paid,
                    amount_due,
                    issued_date,
                    due_date,
                    status
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (invoice_id)
                DO UPDATE SET
                    customer_id = EXCLUDED.customer_id,
                    amount = EXCLUDED.amount,
                    amount_paid = EXCLUDED.amount_paid,
                    amount_due = EXCLUDED.amount_due,
                    issued_date = EXCLUDED.issued_date,
                    due_date = EXCLUDED.due_date,
                    status = EXCLUDED.status
                """,
                (
                    invoice_id,
                    customer_id,
                    amount,
                    amount_paid,
                    amount_due,
                    issued_date,
                    due_date,
                    status,
                ),
            )

        
def update_invoice_payment(
    invoice_id: str,
    amount_paid: float,
    amount_due: float,
    status: str,
):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE invoices
                SET
                    amount_paid = %s,
                    amount_due = %s,
                    status = %s
                WHERE invoice_id = %s
                """,
                (
                    amount_paid,
                    amount_due,
                    status,
                    invoice_id,
                ),
            )