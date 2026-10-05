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
5. 如果用户询问某项政策，回答中要明确指出对应的政策名称。
6. 回答必须直接回应用户的问题，不要只罗列知识库内容。
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

def build_trace(
    *,
    request_type: str | None = None,
    needs_knowledge_base: float | None = None,
    tool_name: str | None = None,
    tool_success: bool | None = None,
    order_id: str | None = None,
    retrieval: dict | None = None,
) -> dict:
    trace = {
        "decision": {
            "request_type": request_type,
            "needs_knowledge_base": needs_knowledge_base,
        },
        "tool": None,
        "retrieval": None,
    }

    if tool_name:
        trace["tool"] = {
            "name": tool_name,
            "success": tool_success,
            "order_id": order_id,
        }

    if retrieval is not None:
        trace["retrieval"] = retrieval

    return trace

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

    # 多轮退款 follow-up：
    # 当前消息没有明确订单号，但会话已有订单上下文，
    # 且用户在询问退款到账时间，则继续走退款政策知识库。
    if (
        request_type in ("unknown", "refund_status")
        and context.get("current_order_id")
        and any(
            keyword in message
            for keyword in [
                "什么时候到账",
                "多久到账",
                "几天到账",
                "到账时间",
                "多久能到账",
                "大概什么时候",
            ]
        )
    ):
        request_type = "knowledge"
        needs_knowledge_base = 1.0

    # 多轮退款资格 follow-up：
    # 当前消息没有明确订单号，但会话已有订单上下文，
    # 且用户询问当前订单是否可以退款。
    if (
        context.get("current_order_id")
        and any(
            keyword in message
            for keyword in [
                "可以退款",
                "能退款",
                "能不能退款",
                "还能退款",
                "是否可以退款",
                "是否能退款",
                "可以申请退款",
                "能申请退款",
                "还能申请退款",
            ]
        )
    ):
        request_type = "refund_eligibility"

    order_id = extract_order_id(message)

    if not order_id:
        order_id = context.get("current_order_id")

    # 1. 查询订单
    if request_type == "order_status":
        if not order_id:
            return {
                "type": "unknown",
                "answer": "请提供需要查询的订单号。",
                "abstention_reason": "missing_input",
                "trace": build_trace(
                    request_type=request_type,
                    needs_knowledge_base=needs_knowledge_base,
                ),
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
                "abstention_reason": "tool_not_found",
                "trace": build_trace(
                    request_type=request_type,
                    needs_knowledge_base=needs_knowledge_base,
                    tool_name="get_order_status",
                    tool_success=False,
                    order_id=order_id,
                ),
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
            "trace": build_trace(
                request_type=request_type,
                needs_knowledge_base=needs_knowledge_base,
                tool_name="get_order_status",
                tool_success=True,
                order_id=order_id,
            ),
        }

        # 2. 多轮退款资格判断
    #
    # 当前订单上下文 + 用户询问“是否可以退款”
    # 需要同时结合：
    # 1. 当前退款状态
    # 2. 退款政策
    if request_type == "refund_eligibility":

        if not order_id:
            return {
                "type": "unknown",
                "answer": "请提供需要查询的订单号。",
                "abstention_reason": "missing_input",
                "trace": build_trace(
                    request_type=request_type,
                    needs_knowledge_base=needs_knowledge_base,
                ),
            }

        logger.info(
            "[AGENT] tool=get_refund_status order_id=%s",
            order_id,
        )

        refund_result = get_refund_status(order_id)

        if not refund_result["success"]:
            return {
                "type": "tool",
                "answer": refund_result["error"],
                "tool": "get_refund_status",
                "abstention_reason": "tool_not_found",
                "trace": build_trace(
                    request_type=request_type,
                    needs_knowledge_base=needs_knowledge_base,
                    tool_name="get_refund_status",
                    tool_success=False,
                    order_id=order_id,
                ),
            }

        # 查询退款政策
        logger.info(
            "[AGENT] route=rag refund_policy"
        )

        knowledge = search_knowledge(
            "退款政策 退款申请 审核通过 是否可以退款"
        )

        if not knowledge["found"]:
            return {
                "type": "unknown",
                "answer": (
                    "当前可以查询到该订单的退款状态，"
                    "但知识库中没有找到足够的退款政策信息，"
                    "因此无法确认是否可以再次申请退款。"
                ),
                "abstention_reason": "knowledge_not_found",
                "tool": "get_refund_status",
                "data": refund_result["data"],
                "context": {
                    "current_order_id": order_id,
                },
                "trace": build_trace(
                    request_type=request_type,
                    needs_knowledge_base=1.0,
                    tool_name="get_refund_status",
                    tool_success=True,
                    order_id=order_id,
                    retrieval={
                        "found": False,
                        "count": 0,
                        "sources": [],
                    },
                ),
            }

        context_parts = []

        for item in knowledge["results"]:
            context_parts.append(
                f"来源：{item['metadata']['source']}\n"
                f"内容：{item['content']}"
            )

        knowledge_context = "\n\n".join(
            context_parts
        )

        answer = chat(
            system_prompt=SYSTEM_PROMPT,
            user_message=(
                f"历史对话：\n{history_text}\n\n"
                f"用户当前问题：{message}\n\n"
                f"当前退款数据：\n"
                f"{refund_result['data']}\n\n"
                f"退款政策知识库证据：\n"
                f"{knowledge_context}\n\n"
                "请结合当前订单退款状态和退款政策回答用户。"
                "如果政策证据不足以判断是否可以再次申请退款，"
                "必须明确说明无法确认，不要自行推断。"
            ),
        )

        return {
            "type": "hybrid",
            "answer": answer,
            "tool": "get_refund_status",
            "data": refund_result["data"],
            "results": knowledge["results"],
            "context": {
                "current_order_id": order_id,
            },
            "trace": build_trace(
                request_type=request_type,
                needs_knowledge_base=1.0,
                tool_name="get_refund_status",
                tool_success=True,
                order_id=order_id,
                retrieval={
                    "found": knowledge["found"],
                    "count": len(
                        knowledge["results"]
                    ),
                    "sources": [
                        {
                            "document_id": item.get(
                                "document_id"
                            ),
                            "source": (
                                item.get("metadata") or {}
                            ).get("source"),
                            "distance": item.get(
                                "distance"
                            ),
                        }
                        for item in knowledge["results"]
                    ],
                },
            ),
        }

    # 2. 查询退款状态
    if request_type == "refund_status":
        if not order_id:
            return {
                "type": "unknown",
                "answer": "请提供需要查询退款状态的订单号。",
                "abstention_reason": "missing_input",
                "trace": build_trace(
                    request_type=request_type,
                    needs_knowledge_base=needs_knowledge_base,
                ),
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
                "abstention_reason": "tool_not_found",
                "trace": build_trace(
                    request_type=request_type,
                    needs_knowledge_base=needs_knowledge_base,
                    tool_name="get_refund_status",
                    tool_success=False,
                    order_id=order_id,
                ),
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
            "context": {
                "current_order_id": order_id,
            },
            "trace": build_trace(
                request_type=request_type,
                needs_knowledge_base=needs_knowledge_base,
                tool_name="get_refund_status",
                tool_success=True,
                order_id=order_id,
            ),
        }

    # 3. 企业知识库问题
    if (
        request_type == "knowledge"
        or needs_knowledge_base >= 0.8
    ):
        logger.info("[AGENT] route=rag")

        rag_query = message

        if context.get("current_order_id"):
            rag_query = (
                f"退款到账时间政策。"
                f"用户问题：{message}"
            )

        knowledge = search_knowledge(rag_query)

        # return {
        #     "type": "rag",
        #     "answer": answer,
        #     "results": knowledge["results"],
        # }

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
                "trace": build_trace(
                    request_type=request_type,
                    needs_knowledge_base=needs_knowledge_base,
                    retrieval={
                        "found": knowledge["found"],
                        "count": len(knowledge["results"]),
                        "sources": [
                            {
                                "document_id": item.get("document_id"),
                                "source": (item.get("metadata") or {}).get("source"),
                                "distance": item.get("distance"),
                            }
                            for item in knowledge["results"]
                        ],
                    },
                ),
            }
        if not knowledge["found"]:
            return {
                "type": "unknown",
                "answer": (
                    "抱歉，当前知识库和业务系统中"
                    "没有找到足够的信息来回答这个问题。"
                ),
                "abstention_reason": "knowledge_not_found",
                "trace": build_trace(
                    request_type=request_type,
                    needs_knowledge_base=needs_knowledge_base,
                    retrieval={
                        "found": False,
                        "count": len(knowledge.get("results", [])),
                        "sources": [],
                    },
                ),
            }

    # 4. 无法处理
    return {
        "type": "unknown",
        "answer": (
            "抱歉，当前知识库和业务系统中"
            "没有找到足够的信息来回答这个问题。"
        ),
        "trace": build_trace(
            request_type=request_type,
            needs_knowledge_base=needs_knowledge_base,
        ),
    }