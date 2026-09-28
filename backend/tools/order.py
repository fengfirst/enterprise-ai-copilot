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


def get_order_status(order_id: str) -> dict:
    order = ORDERS.get(order_id)

    if order is None:
        return {
            "success": False,
            "error": f"订单 {order_id} 不存在",
        }

    return {
        "success": True,
        "data": order,
    }