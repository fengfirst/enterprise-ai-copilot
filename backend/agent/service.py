import re
import logging

from backend.core.llm import chat
from backend.rag.service import search_knowledge
from backend.tools.order import get_order_status
from backend.tools.refund import get_refund_status
from backend.agent.decision import decide

logger = logging.getLogger(__name__)

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


def format_history(history: list) -> str:
    if not history:
        return ""

    lines = []

    for message in history:
        lines.append(
            f"{message.role}: {message.content}"
        )

    return "\n".join(lines)

def handle_message(
    message: str,
    history: list | None = None,
    context: dict | None = None,
) -> dict:
    history = history or []
    history_text = format_history(history)
    context = context or {}

    decision = decide(message)

    request_type = decision["request_type"]
    needs_knowledge_base = decision["needs_knowledge_base"]

    logger.info(
        "[AGENT] decision request_type=%s needs_knowledge_base=%.2f",
        request_type,
        needs_knowledge_base,
    )

    # 如果当前消息没有明确意图，但会话已有订单上下文，
    # 则识别常见的订单跟进问法。
    if (
        request_type == "unknown"
        and context.get("current_order_id")
        and any(
            keyword in message
            for keyword in [
                "它什么时候到",
                "什么时候到",
                "什么时候送到",
                "物流到哪",
                "物流状态",
                "到哪了",
                "订单状态",
            ]
        )
    ):
        request_type = "order_status"

    order_id = extract_order_id(message)

    if not order_id:
        order_id = context.get("current_order_id")

    # 1. 查询订单
    if request_type == "order_status":
        if not order_id:
            return {
                "type": "unknown",
                "answer": "请提供需要查询的订单号。",
            }

        logger.info(
            "[AGENT] tool=get_order_status order_id=%s",
            order_id,
        )

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
                f"历史对话：\n{history_text}\n\n"
                f"用户当前问题：{message}\n\n"
                f"订单数据：{result['data']}"
            ),
        )
        

        return {
            "type": "tool",
            "answer": answer,
            "tool": "get_order_status",
            "data": result["data"],
            "context": {
                "current_order_id": order_id,
            },
        }

    # 2. 查询退款状态
    if request_type == "refund_status":
        if not order_id:
            return {
                "type": "unknown",
                "answer": "请提供需要查询退款状态的订单号。",
            }

        logger.info(
            "[AGENT] tool=get_refund_status order_id=%s",
            order_id,
        )

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
                f"历史对话：\n{history_text}\n\n"
                f"用户当前问题：{message}\n\n"
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
        logger.info("[AGENT] route=rag")

        knowledge = search_knowledge(message)

        if knowledge["found"]:
            context_parts = []

            for item in knowledge["results"]:
                context_parts.append(
                    f"来源：{item['metadata']['source']}\n"
                    f"内容：{item['content']}"
                )

            knowledge_context = "\n\n".join(context_parts)

            answer = chat(
                system_prompt=SYSTEM_PROMPT,
                user_message=(
                    f"历史对话：\n{history_text}\n\n"
                    f"用户当前问题：{message}\n\n"
                    f"检索到的知识库证据：\n"
                    f"{knowledge_context}"
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