from uuid import uuid4

from app.database.connection import get_connection


def save_human_review(
    case_id: str,
    ai_action: str,
    human_decision: str,
    correct: bool,
    reason: str | None = None,
    reviewer: str | None = None,
):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO human_reviews (
                    review_id,
                    case_id,
                    ai_action,
                    human_decision,
                    correct,
                    reason,
                    reviewer
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    str(uuid4()),
                    case_id,
                    ai_action,
                    human_decision,
                    correct,
                    reason,
                    reviewer,
                ),
            )


def get_human_reviews(case_id: str):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    review_id,
                    case_id,
                    ai_action,
                    human_decision,
                    correct,
                    reason,
                    reviewer,
                    created_at
                FROM human_reviews
                WHERE case_id = %s
                ORDER BY created_at DESC
                """,
                (case_id,),
            )

            return cursor.fetchall()