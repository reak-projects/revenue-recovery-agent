import os

import psycopg # type: ignore
from dotenv import load_dotenv # type: ignore


load_dotenv()


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://localhost:5432/revenue_recovery"
)


def get_connection():
    return psycopg.connect(DATABASE_URL)