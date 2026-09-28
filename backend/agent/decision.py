from backend.core.jev import classify_request


def decide(message: str) -> dict:
    answers = classify_request(message)

    request_type = answers["request_type"]
    needs_kb = answers["needs_knowledge_base"]

    return {
        "request_type": request_type.choice,
        "request_confidence": request_type.confidence,
        "request_probabilities": request_type.probabilities,
        "needs_knowledge_base": needs_kb.noul,
    }