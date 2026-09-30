from backend.agent.service import handle_message


def test_multi_turn_order_context(monkeypatch):
    def fake_decide(message):
        if "12345" in message:
            return {
                "request_type": "order_status",
                "request_confidence": 1.0,
                "request_probabilities": {},
                "needs_knowledge_base": 0.0,
            }

        return {
            "request_type": "unknown",
            "request_confidence": 1.0,
            "request_probabilities": {},
            "needs_knowledge_base": 0.0,
        }

    def fake_get_order_status(order_id):
        return {
            "success": True,
            "data": {
                "order_id": order_id,
                "status": "已发货",
                "estimated_delivery": "2026-09-20",
            },
        }

    def fake_chat(system_prompt, user_message):
        return "订单12345预计于2026年9月20日送达。"

    monkeypatch.setattr(
        "backend.agent.service.decide",
        fake_decide,
    )

    monkeypatch.setattr(
        "backend.agent.service.get_order_status",
        fake_get_order_status,
    )

    monkeypatch.setattr(
        "backend.agent.service.chat",
        fake_chat,
    )

    # 第一轮：明确提供订单号
    result1 = handle_message(
        message="帮我查询订单12345",
        history=[],
        context={},
    )

    assert result1["type"] == "tool"
    assert result1["context"]["current_order_id"] == "12345"

    # 第二轮：不再提供订单号，
    # 由 Session Context 恢复
    result2 = handle_message(
        message="它什么时候到？",
        history=[],
        context={
            "current_order_id": "12345",
        },
    )

    assert result2["type"] == "tool"
    assert result2["tool"] == "get_order_status"
    assert result2["data"]["order_id"] == "12345"

def test_new_order_overwrites_previous_context(monkeypatch):
    def fake_decide(message):
        return {
            "request_type": "order_status",
            "request_confidence": 1.0,
            "request_probabilities": {},
            "needs_knowledge_base": 0.0,
        }

    def fake_get_order_status(order_id):
        return {
            "success": True,
            "data": {
                "order_id": order_id,
                "status": "已发货",
                "estimated_delivery": "2026-09-20",
            },
        }

    def fake_chat(system_prompt, user_message):
        return "订单查询结果"

    monkeypatch.setattr(
        "backend.agent.service.decide",
        fake_decide,
    )

    monkeypatch.setattr(
        "backend.agent.service.get_order_status",
        fake_get_order_status,
    )

    monkeypatch.setattr(
        "backend.agent.service.chat",
        fake_chat,
    )

    # 当前 Session 原本正在讨论订单 12345
    old_context = {
        "current_order_id": "12345",
    }

    result = handle_message(
        message="帮我查询订单67890",
        history=[],
        context=old_context,
    )

    assert result["type"] == "tool"
    assert result["data"]["order_id"] == "67890"

    # Agent 返回的新 Context 应该覆盖旧订单
    assert result["context"]["current_order_id"] == "67890"


def test_updated_order_context_is_used_in_follow_up(monkeypatch):
    def fake_decide(message):
        if "订单" in message:
            return {
                "request_type": "order_status",
                "request_confidence": 1.0,
                "request_probabilities": {},
                "needs_knowledge_base": 0.0,
            }

        return {
            "request_type": "unknown",
            "request_confidence": 1.0,
            "request_probabilities": {},
            "needs_knowledge_base": 0.0,
        }

    queried_orders = []

    def fake_get_order_status(order_id):
        queried_orders.append(order_id)

        return {
            "success": True,
            "data": {
                "order_id": order_id,
                "status": "已发货",
                "estimated_delivery": "2026-09-20",
            },
        }

    def fake_chat(system_prompt, user_message):
        return "订单查询结果"

    monkeypatch.setattr(
        "backend.agent.service.decide",
        fake_decide,
    )

    monkeypatch.setattr(
        "backend.agent.service.get_order_status",
        fake_get_order_status,
    )

    monkeypatch.setattr(
        "backend.agent.service.chat",
        fake_chat,
    )

    # 第一轮：12345
    result1 = handle_message(
        message="查询订单12345",
        history=[],
        context={},
    )

    context = result1["context"]

    assert context["current_order_id"] == "12345"

    # 第二轮：切换到67890
    result2 = handle_message(
        message="查询订单67890",
        history=[],
        context=context,
    )

    context = result2["context"]

    assert context["current_order_id"] == "67890"

    # 第三轮：不提供订单号
    result3 = handle_message(
        message="它什么时候到？",
        history=[],
        context=context,
    )

    assert result3["type"] == "tool"
    assert result3["data"]["order_id"] == "67890"

    assert queried_orders == [
        "12345",
        "67890",
        "67890",
    ]