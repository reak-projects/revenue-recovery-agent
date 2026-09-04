from app.database.connection import get_connection


def save_agent_action(
    action_id: str,
    case_id: str,
    action: str,
    reason: str | None = None, # type: ignore
):

    with get_connection() as conn:

        with conn.cursor() as cursor:

            cursor.execute(
                """
                INSERT INTO agent_actions (
                    action_id,
                    case_id,
                    action,
                    reason
                )
                VALUES (
                    %s, %s, %s, %s
                )
                """,
                (
                    action_id,
                    case_id,
                    action,
                    reason,
                ),
            )