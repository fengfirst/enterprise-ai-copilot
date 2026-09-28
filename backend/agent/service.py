import re

from backend.core.llm import chat
from backend.rag.service import search_knowledge
from backend.tools.order import get_order_status
from backend.tools.refund import get_refund_status
from backend.agent.decision import decide


SYSTEM_PROMPT = """
你是企业 AI 客服助手。

回答规则：

1. 优先使用提供的业务数据和知识库。
2. 不允许编造知识库中不存在的信息。
3. 如果证据不足，明确告诉用户当前无法确认。
4. 回答简洁、准确。
"""


def extract_order_id(message: str) -> str | None:
    match = re.search(r"(?<!\d)\d{5}(?!\d)", message)

    if not match:
        return None

    return match.group(0)

def handle_message(message: str) -> dict:
    decision = decide(message)

    request_type = decision["request_type"]
    needs_knowledge_base = decision["needs_knowledge_base"]

    order_id = extract_order_id(message)

    # 1. 查询订单
    if request_type == "order_status":
        if not order_id:
            return {
                "type": "unknown",
                "answer": "请提供需要查询的订单号。",
            }

        result = get_order_status(order_id)

        if not result["success"]:
            return {
                "type": "tool",
                "answer": result["error"],
                "tool": "get_order_status",
            }

        answer = chat(
            system_prompt=SYSTEM_PROMPT,
            user_message=(
                f"用户问题：{message}\n\n"
                f"订单数据：{result['data']}"
            ),
        )

        return {
            "type": "tool",
            "answer": answer,
            "tool": "get_order_status",
            "data": result["data"],
        }

    # 2. 查询退款状态
    if request_type == "refund_status":
        if not order_id:
            return {
                "type": "unknown",
                "answer": "请提供需要查询退款状态的订单号。",
            }

        result = get_refund_status(order_id)

        if not result["success"]:
            return {
                "type": "tool",
                "answer": result["error"],
                "tool": "get_refund_status",
            }

        answer = chat(
            system_prompt=SYSTEM_PROMPT,
            user_message=(
                f"用户问题：{message}\n\n"
                f"退款数据：{result['data']}"
            ),
        )

        return {
            "type": "tool",
            "answer": answer,
            "tool": "get_refund_status",
            "data": result["data"],
        }

    # 3. 企业知识库问题
    if (
        request_type == "knowledge"
        or needs_knowledge_base >= 0.8
    ):
        knowledge = search_knowledge(message)

        if knowledge["found"]:
            context_parts = []

            for item in knowledge["results"]:
                context_parts.append(
                    f"来源：{item['metadata']['source']}\n"
                    f"内容：{item['content']}"
                )

            context = "\n\n".join(context_parts)

            answer = chat(
                system_prompt=SYSTEM_PROMPT,
                user_message=(
                    f"用户问题：{message}\n\n"
                    f"检索到的知识库证据：\n"
                    f"{context}"
                ),
            )

            return {
                "type": "rag",
                "answer": answer,
                "results": knowledge["results"],
            }

    # 4. 无法处理
    return {
        "type": "unknown",
        "answer": (
            "抱歉，当前知识库和业务系统中"
            "没有找到足够的信息来回答这个问题。"
        ),
    }