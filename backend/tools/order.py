import json

from backend.cache.redis_cache import RedisCache


ORDERS = {
    "12345": {
        "order_id": "12345",
        "status": "shipped",
        "estimated_delivery": "2026-09-20",
    },
    "12346": {
        "order_id": "12346",
        "status": "processing",
        "estimated_delivery": "2026-09-23",
    },
}


cache = RedisCache()


def get_order_status(order_id: str) -> dict:
    cache_key = f"order:{order_id}"

    # 1. Cache Hit
    cached = cache.get(cache_key)

    if cached is not None:
        return json.loads(cached)

    # 2. Cache Miss → 查询订单数据
    order = ORDERS.get(order_id)

    if order is None:
        return {
            "success": False,
            "error": f"订单 {order_id} 不存在",
        }

    result = {
        "success": True,
        "data": order,
    }

    # 3. 写入 Redis，缓存 60 秒
    cache.set(
        cache_key,
        json.dumps(result, ensure_ascii=False),
        ttl=60,
    )

    return result