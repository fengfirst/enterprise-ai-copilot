from backend.agent.decision import decide


messages = [
    "帮我查询订单12345",
    "帮我查询订单12345的退款状态",
    "退款审核通过后多久可以到账？",
    "退款申请怎么操作？",
    "公司附近有什么咖啡店？",
]


for message in messages:
    result = decide(message)

    print("\n====================")
    print("用户：", message)
    print("Decision：", result)