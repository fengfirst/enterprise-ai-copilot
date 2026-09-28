import re

from backend.core.llm import chat
from backend.rag.service import search_knowledge
from backend.tools.order import get_order_status
from backend.tools.refund import get_refund_status


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

def is_refund_query(message: str) -> bool:
    refund_keywords = [
        "退款状态",
        "退款进度",
        "退款记录",
        # "退款申请",
        # "退款审核",
    ]

    return any(
        keyword in message
        for keyword in refund_keywords
    )


def handle_message(message: str) -> dict:
    order_id = extract_order_id(message)

    if order_id and is_refund_query(message):
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


    if order_id and "订单" in message:
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

    return {
        "type": "unknown",
        "answer": (
            "抱歉，当前知识库和业务系统中"
            "没有找到足够的信息来回答这个问题。"
        ),
    }