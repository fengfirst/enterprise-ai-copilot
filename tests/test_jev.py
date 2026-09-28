from backend.core.jev import classify_intent, classify_request


messages = [
    "帮我查询订单12345",
    "帮我查询订单12345的退款状态",
    "退款审核通过后多久可以到账？",
    "公司附近有什么咖啡店？",
]


# for message in messages:
#     answer = classify_intent(message)

#     print("\n====================")
#     print("用户：", message)
#     print("Intent：", answer.choice)
#     print("Confidence：", answer.confidence)
#     print("Probabilities：", answer.probabilities)

for message in messages:
    answers = classify_request(message)

    request_type = answers["request_type"]
    needs_kb = answers["needs_knowledge_base"]

    print("\n====================")
    print("用户：", message)

    print("\n[request_type]")
    print("Choice：", request_type.choice)
    print("Confidence：", request_type.confidence)
    print("Probabilities：", request_type.probabilities)

    print("\n[needs_knowledge_base]")
    print("Noul：", needs_kb.noul)