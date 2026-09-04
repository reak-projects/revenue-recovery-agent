from app.database.connection import get_connection


def save_customer_interaction(
    interaction_id: str,
    case_id: str,
    message: str,
    detected_intent: str | None, # type: ignore
    ai_confidence: float | None, # type: ignore
):

    with get_connection() as conn:

        with conn.cursor() as cursor:

            cursor.execute(
                """
                INSERT INTO customer_interactions (
                    interaction_id,
                    case_id,
                    message,
                    detected_intent,
                    ai_confidence
                )
                VALUES (
                    %s, %s, %s, %s, %s
                )
                """,
                (
                    interaction_id,
                    case_id,
                    message,
                    detected_intent,
                    ai_confidence,
                ),
            )


def get_customer_interaction(case_id: str, message: str):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    interaction_id,
                    case_id,
                    message,
                    detected_intent,
                    ai_confidence,
                    created_at
                FROM customer_interactions
                WHERE case_id = %s
                  AND message = %s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (case_id, message),
            )

            return cursor.fetchone()