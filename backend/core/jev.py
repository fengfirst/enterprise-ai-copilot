from typesafe_sdk import Choice, Noul, TypeSafeClient


client = TypeSafeClient()


def classify_intent(message: str):
    response = client.system_one(
        state=message,
        questions={
            "intent": Choice(
                instructions="What is the primary intent of the user's message?",
                criteria={
                    "order": "The user wants to query an order's status or delivery information.",
                    "refund": "The user wants to query refund status or ask about refund-related information.",
                    "knowledge": "The user is asking a general question that should be answered using the enterprise knowledge base.",
                    "unknown": "The request cannot be handled by the current enterprise assistant capabilities.",
                },
            )
        },
    )

    return response.answers["intent"]


def classify_request(message: str):
    response = client.system_one(
        state=message,
        questions={
            "request_type": Choice(
                instructions="What is the primary type of request?",
                criteria={
                    "order_status": (
                        "The user wants to query the status, "
                        "delivery, or progress of a specific order."
                    ),
                    "refund_status": (
                        "The user wants to query the status or progress "
                        "of a refund for a specific order."
                    ),
                    "knowledge": (
                        "The user asks about enterprise policies, "
                        "procedures, rules, or other information "
                        "that can be answered from the enterprise knowledge base."
                    ),
                    "unknown": (
                        "The request is unrelated to the enterprise's "
                        "orders, refunds, policies, procedures, or knowledge."
                    ),
                },
            ),
            "needs_knowledge_base": Noul(
                instructions=(
                    "Does this user request require information "
                    "from the enterprise knowledge base?"
                ),
                criteria={
                    "true": (
                        "The request can be answered using enterprise "
                        "policies, procedures, rules, or documentation."
                    ),
                    "false": (
                        "The request does not require enterprise "
                        "knowledge base information."
                    ),
                },
            ),
        },
    )

    return response.answers