from backend.rag.service import search_knowledge


def test_rag_returns_result_for_known_knowledge():
    result = search_knowledge("退款审核通过后多久到账？")

    assert result["found"] is True
    assert result["results"]


def test_rag_abstains_when_knowledge_is_missing():
    result = search_knowledge("公司明年会不会涨价？")

    assert result["found"] is False


def test_rag_abstains_for_irrelevant_question():
    result = search_knowledge("英国的天气怎么样？")

    assert result["found"] is False


def test_rag_abstains_for_nonexistent_company_information():
    result = search_knowledge("你们公司今年的利润是多少？")

    assert result["found"] is False