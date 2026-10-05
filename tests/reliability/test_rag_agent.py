from backend.agent.service import handle_message


def test_agent_abstains_when_knowledge_is_missing():
    result = handle_message("公司明年会不会涨价？")

    assert result["type"] == "unknown"
    assert result["answer"]


def test_agent_abstains_for_irrelevant_question():
    result = handle_message("英国的天气怎么样？")

    assert result["type"] == "unknown"
    assert result["answer"]


def test_agent_does_not_invent_company_profit():
    result = handle_message("你们公司今年的利润是多少？")

    assert result["type"] == "unknown"
    assert result["answer"]