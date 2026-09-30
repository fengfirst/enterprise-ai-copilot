from backend.session.store import InMemorySessionStore


def test_session_store():
    store = InMemorySessionStore()

    store.add_message(
        "user_001",
        "user",
        "我的订单是12345",
    )

    store.add_message(
        "user_001",
        "assistant",
        "订单12345已发货。",
    )

    messages = store.get_messages("user_001")

    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[0].content == "我的订单是12345"
    assert messages[1].role == "assistant"
    assert messages[1].content == "订单12345已发货。"


def test_session_isolation():
    store = InMemorySessionStore()

    store.add_message(
        "user_001",
        "user",
        "你好",
    )

    messages = store.get_messages("user_002")

    assert messages == []

def test_session_context_isolation():
    store = InMemorySessionStore()

    store.set_context(
        "user_001",
        "current_order_id",
        "12345",
    )

    store.set_context(
        "user_002",
        "current_order_id",
        "67890",
    )

    context_001 = store.get_context("user_001")
    context_002 = store.get_context("user_002")

    assert context_001["current_order_id"] == "12345"
    assert context_002["current_order_id"] == "67890"
    