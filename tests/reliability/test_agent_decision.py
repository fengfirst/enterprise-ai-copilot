from backend.agent.service import handle_message


def test_order_question_routes_to_order_tool():
    result = handle_message("帮我查询订单12345的状态")

    assert result["type"] == "tool"
    assert result["tool"] == "get_order_status"


def test_refund_status_routes_to_refund_tool():
    result = handle_message("订单12347的退款状态是什么？")

    assert result["type"] == "tool"
    assert result["tool"] == "get_refund_status"


def test_knowledge_question_routes_to_rag():
    result = handle_message("退款审核通过后一般几天可以到账？")

    assert result["type"] == "rag"
    assert result.get("results")


def test_irrelevant_question_does_not_call_business_tool():
    result = handle_message("英国的天气怎么样？")

    assert result["type"] == "unknown"

def test_mixed_refund_question_uses_current_order_context():
    result = handle_message(
        "还是刚才那个订单，它现在可以退款吗？",
        context={"current_order_id": "12346"},
    )

    assert result["type"] in {"tool", "rag", "hybrid"}
    assert result.get("answer")


def test_refund_arrival_followup_uses_knowledge_base():
    result = handle_message(
        "那大概什么时候能到账？",
        context={"current_order_id": "12346"},
    )

    assert result["type"] == "rag"
    assert result.get("results")