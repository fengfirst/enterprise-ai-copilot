
from uuid import uuid4

from backend.session.postgres_store import PostgreSQLSessionStore


def test_postgres_message_persistence():
    store = PostgreSQLSessionStore()
    session_id = f"test_message_{uuid4().hex}"

    try:
        store.add_message(session_id, "user", "查询订单12345")
        store.add_message(session_id, "assistant", "订单已发货")

        messages = store.get_messages(session_id)

        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[0].content == "查询订单12345"
        assert messages[1].role == "assistant"
        assert messages[1].content == "订单已发货"
    finally:
        store.clear(session_id)


def test_postgres_context_merge():
    store = PostgreSQLSessionStore()
    session_id = f"test_context_{uuid4().hex}"

    try:
        store.set_context(
            session_id,
            "current_order_id",
            "12345",
        )
        store.set_context(
            session_id,
            "last_intent",
            "order_status",
        )

        context = store.get_context(session_id)

        assert context["current_order_id"] == "12345"
        assert context["last_intent"] == "order_status"
    finally:
        store.clear(session_id)


def test_postgres_clear_deletes_session_and_messages():
    store = PostgreSQLSessionStore()
    session_id = f"test_clear_{uuid4().hex}"

    store.add_message(session_id, "user", "测试清理")
    store.set_context(
        session_id,
        "current_order_id",
        "12345",
    )

    store.clear(session_id)

    assert store.get_messages(session_id) == []
    assert store.get_context(session_id) == {}