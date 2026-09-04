from app.database.connection import get_connection
from psycopg.rows import dict_row


def get_customer(customer_id: str):

    with get_connection() as conn:

        with conn.cursor(row_factory=dict_row) as cursor:

            cursor.execute(
                """
                SELECT
                    customer_id,
                    name,
                    email,
                    contact,
                    total_invoices,
                    paid_invoices,
                    late_invoices,
                    unresolved_invoices,
                    average_payment_delay_days,
                    disputes_count,
                    reminders_sent,
                    reminders_responded,
                    previous_payment_failures,
                    previous_promises,
                    promises_kept,
                    promises_broken,
                    previous_reminders_successful,
                    average_invoice_amount,
                    previous_outstanding_amount
                FROM customers
                WHERE customer_id = %s
                """,
                (customer_id,),
            )

            return cursor.fetchone()

def save_customer(
    customer_id: str,
    name: str,
    email: str,
    contact: str,
):
    with get_connection() as conn:

        with conn.cursor() as cursor:

            cursor.execute(
                """
                INSERT INTO customers (
                    customer_id,
                    name,
                    email,
                    contact,
                    total_invoices,
                    paid_invoices,
                    late_invoices,
                    unresolved_invoices,
                    average_payment_delay_days,
                    disputes_count,
                    reminders_sent,
                    reminders_responded,
                    previous_payment_failures
                )
                VALUES (
                    %s, %s, %s, %s,
                    0, 0, 0, 0, 0, 0, 0, 0, 0
                )
                ON CONFLICT (customer_id)
                DO NOTHING
                """,
                (
                    customer_id,
                    name,
                    email,
                    contact,
                ),
            )

def record_successful_payment(customer_id: str):
    with get_connection() as conn:

        with conn.cursor() as cursor:

            cursor.execute(
                """
                UPDATE customers
                SET
                    paid_invoices = paid_invoices + 1
                WHERE customer_id = %s
                """,
                (customer_id,),
            )

def record_promise(customer_id: str):
    with get_connection() as conn:

        with conn.cursor() as cursor:

            cursor.execute(
                """
                UPDATE customers
                SET
                    previous_promises = previous_promises + 1
                WHERE customer_id = %s
                """,
                (customer_id,),
            )

def update_customer_profile(customer_id: str):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE customers
                SET
                    total_invoices = (
                        SELECT COUNT(*)
                        FROM invoices
                        WHERE invoices.customer_id = customers.customer_id
                    ),

                    paid_invoices = (
                        SELECT COUNT(*)
                        FROM invoices
                        WHERE invoices.customer_id = customers.customer_id
                        AND invoices.status = 'paid'
                    ),

                    unresolved_invoices = (
                        SELECT COUNT(*)
                        FROM invoices
                        WHERE invoices.customer_id = customers.customer_id
                        AND invoices.amount_due > 0
                    ),

                    average_invoice_amount = (
                        SELECT COALESCE(AVG(amount), 0)
                        FROM invoices
                        WHERE invoices.customer_id = customers.customer_id
                    ),
                    previous_outstanding_amount = (
                        SELECT COALESCE(SUM(amount_due), 0)
                        FROM invoices
                        WHERE invoices.customer_id = customers.customer_id
                    ),
                    customer_tenure_days = (
                        SELECT COALESCE(
                            CURRENT_DATE - MIN(issued_date),
                            0
                        )
                        FROM invoices
                        WHERE invoices.customer_id = customers.customer_id
                    ),
                    previous_payment_failures = (
                        SELECT COUNT(*)
                        FROM payments
                        WHERE payments.customer_id = customers.customer_id
                        AND payments.status = 'failed'
                    ),

                    late_invoices = (
                        SELECT COUNT(*)
                        FROM invoices
                        WHERE invoices.customer_id = customers.customer_id
                        AND invoices.amount_due > 0
                        AND invoices.due_date < CURRENT_DATE
                    )

                WHERE customer_id = %s
                """,
                (customer_id,),
            )


def record_promise(customer_id: str):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE customers
                SET previous_promises = previous_promises + 1
                WHERE customer_id = %s
                """,
                (customer_id,),
            )

def record_broken_promise(customer_id: str):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE customers
                SET promises_broken = promises_broken + 1
                WHERE customer_id = %s
                """,
                (customer_id,),
            )

def record_kept_promise(customer_id: str):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE customers
                SET promises_kept = promises_kept + 1
                WHERE customer_id = %s
                """,
                (customer_id,),
            )