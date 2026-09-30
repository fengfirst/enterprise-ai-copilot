import time

from backend.cache.redis_cache import RedisCache
from backend.tools.order import ORDERS, get_order_status


def test_redis_set_and_get():
    cache = RedisCache()
    key = "test:set-get"

    cache.set(key, "hello", ttl=60)

    assert cache.get(key) == "hello"

    cache.delete(key)


def test_redis_exists_and_delete():
    cache = RedisCache()
    key = "test:exists"

    cache.set(key, "hello", ttl=60)

    assert cache.exists(key) is True

    cache.delete(key)

    assert cache.exists(key) is False


def test_redis_ttl_expiration():
    cache = RedisCache()
    key = "test:ttl"

    cache.set(key, "hello", ttl=1)

    assert cache.get(key) == "hello"

    time.sleep(2)

    assert cache.get(key) is None

def test_order_status_uses_cache():
    order_id = "12345"

    # 第一次查询：写入 Redis
    first_result = get_order_status(order_id)

    assert first_result["success"] is True
    assert first_result["data"]["status"] == "shipped"

    # 修改原始订单数据
    original_status = ORDERS[order_id]["status"]
    ORDERS[order_id]["status"] = "TEST_CHANGED"

    try:
        # 第二次查询应该从 Redis 获取
        second_result = get_order_status(order_id)

        assert second_result["success"] is True
        assert second_result["data"]["status"] == "shipped"
    finally:
        # 恢复测试数据
        ORDERS[order_id]["status"] = original_status