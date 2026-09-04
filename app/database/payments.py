from app.database.connection import get_connection


def payment_exists(payment_id: str) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM payments WHERE payment_id = %s LIMIT 1",
                (payment_id,),
            )
            return cursor.fetchone() is not None


def save_payment(
    payment_id: str,
    invoice_id: str,
    customer_id: str,
    amount: float,
    status: str,
    payment_date,
):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO payments (
                    payment_id,
                    invoice_id,
                    customer_id,
                    amount,
                    status,
                    payment_date
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (payment_id)
                DO UPDATE SET
                    invoice_id = EXCLUDED.invoice_id,
                    customer_id = EXCLUDED.customer_id,
                    amount = EXCLUDED.amount,
                    status = EXCLUDED.status,
                    payment_date = EXCLUDED.payment_date
                """,
                (
                    payment_id,
                    invoice_id,
                    customer_id,
                    amount,
                    status,
                    payment_date,
                ),
            )