from app.database.connection import get_connection
from psycopg.rows import dict_row


def get_invoice(invoice_id: str):
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT
                    invoice_id,
                    customer_id,
                    amount,
                    amount_paid,
                    amount_due,
                    issued_date,
                    due_date,
                    status
                FROM invoices
                WHERE invoice_id = %s
                """,
                (invoice_id,),
            )

            return cursor.fetchone()