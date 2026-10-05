import pytest

from backend.tools.order import get_order_status, cache


def test_existing_order_returns_success():
    result = get_order_status("12345")

    assert result["success"] is True
    assert result["data"]["order_id"] == "12345"


def test_nonexistent_order_returns_controlled_failure():
    result = get_order_status("99999")

    assert result["success"] is False
    assert "99999" in result["error"]


def test_invalid_order_id_returns_controlled_failure():
    result = get_order_status("ABC123")

    assert result["success"] is False
    assert "ABC123" in result["error"]


def test_redis_get_failure_does_not_break_order_query(monkeypatch):
    def broken_get(_key):
        raise ConnectionError("Redis unavailable")

    monkeypatch.setattr(cache, "get", broken_get)

    result = get_order_status("12345")

    assert result["success"] is True
    assert result["data"]["order_id"] == "12345"


def test_redis_set_failure_does_not_break_order_query(monkeypatch):
    def broken_get(_key):
        return None

    def broken_set(*args, **kwargs):
        raise ConnectionError("Redis unavailable")

    monkeypatch.setattr(cache, "get", broken_get)
    monkeypatch.setattr(cache, "set", broken_set)

    result = get_order_status("12345")

    assert result["success"] is True
    assert result["data"]["order_id"] == "12345"