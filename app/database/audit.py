import json

from app.database.connection import get_connection


def save_audit_event(
    event_id: str,
    case_id: str,
    event_type: str,
    description: str,
    actor: str,
    metadata: dict | None = None, # type: ignore
):

    with get_connection() as conn:

        with conn.cursor() as cursor:

            cursor.execute(
                """
                INSERT INTO audit_events (
                    event_id,
                    case_id,
                    event_type,
                    description,
                    actor,
                    metadata
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s::jsonb
                )
                """,
                (
                    event_id,
                    case_id,
                    event_type,
                    description,
                    actor,
                    json.dumps(metadata or {}),
                ),
            )


def audit_event_exists(
    case_id: str,
    event_type: str,
    metadata: dict,
) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT metadata
                FROM audit_events
                WHERE case_id = %s
                  AND event_type = %s
                ORDER BY created_at DESC
                """,
                (case_id, event_type),
            )

            for (stored_metadata,) in cursor.fetchall():
                if all(
                    stored_metadata.get(key) == value
                    for key, value in metadata.items()
                ):
                    return True

            return False