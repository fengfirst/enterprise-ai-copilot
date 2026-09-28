REFUNDS = {
    "12345": {
        "order_id": "12345",
        "status": "approved",
        "amount": 99.90,
        "estimated_arrival": "3-7个工作日",
    },
    "12346": {
        "order_id": "12346",
        "status": "pending",
        "amount": 199.00,
        "estimated_arrival": None,
    },
    "12347": {
        "order_id": "12347",
        "status": "rejected",
        "amount": 0,
        "estimated_arrival": None,
    },
}


def get_refund_status(order_id: str) -> dict:
    refund = REFUNDS.get(order_id)

    if refund is None:
        return {
            "success": False,
            "error": f"订单 {order_id} 没有退款记录",
        }

    return {
        "success": True,
        "data": refund,
    }