import os

import psycopg
from dotenv import load_dotenv

from backend.session.store import Message

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not configured")


class PostgreSQLSessionStore:
    def __init__(self, database_url: str = DATABASE_URL):
        self.database_url = database_url

    def _connect(self):
        return psycopg.connect(self.database_url)

    def _ensure_session(self, session_id: str) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO sessions (session_id)
                    VALUES (%s)
                    ON CONFLICT (session_id) DO NOTHING
                    """,
                    (session_id,),
                )

    def get_messages(self, session_id: str) -> list[Message]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT role, content
                    FROM messages
                    WHERE session_id = %s
                    ORDER BY id
                    """,
                    (session_id,),
                )

                rows = cur.fetchall()

        return [
            Message(role=role, content=content)
            for role, content in rows
        ]

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
    ) -> None:
        self._ensure_session(session_id)

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO messages (
                        session_id,
                        role,
                        content
                    )
                    VALUES (%s, %s, %s)
                    """,
                    (session_id, role, content),
                )

    def get_context(self, session_id: str) -> dict:
        self._ensure_session(session_id)

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT context
                    FROM sessions
                    WHERE session_id = %s
                    """,
                    (session_id,),
                )

                row = cur.fetchone()

        if row is None:
            return {}

        return row[0] or {}


    def set_context(
        self,
        session_id: str,
        key: str,
        value,
    ) -> None:
        self._ensure_session(session_id)

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE sessions
                    SET context = context || %s::jsonb
                    WHERE session_id = %s
                    """,
                    (
                        psycopg.types.json.Jsonb({key: value}),
                        session_id,
                    ),
                )

    def clear(self, session_id: str) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM sessions
                    WHERE session_id = %s
                    """,
                    (session_id,),
                )