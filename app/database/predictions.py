from app.database.connection import get_connection


def save_prediction(
    prediction_id: str,
    case_id: str,
    model_version: str,
    recovery_probability: float,
    predicted_class: int,
):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO model_predictions (
                    prediction_id,
                    case_id,
                    model_version,
                    recovery_probability,
                    predicted_class
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    prediction_id,
                    case_id,
                    model_version,
                    recovery_probability,
                    predicted_class,
                ),
            )