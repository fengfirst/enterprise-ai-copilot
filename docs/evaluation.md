# Agent Evaluation & Reliability

## 1. Evaluation Overview

Enterprise AI Copilot uses an automated evaluation dataset to validate Agent behavior across business scenarios.

The evaluation focuses on:

* Correct tool routing
* RAG retrieval and grounding
* Session context
* Business response correctness
* Agent abstention
* Edge cases

### Overall Results

| Metric           |     Result |
| ---------------- | ---------: |
| Evaluation Cases |         24 |
| Passed           |         24 |
| Failed           |          0 |
| Pass Rate        |   **100%** |
| Quality Gate     | **PASSED** |

---

## 2. RAG Grounding

RAG responses are evaluated separately to verify that answers are supported by retrieved enterprise knowledge.

| Metric              |   Result |
| ------------------- | -------: |
| RAG Cases           |       10 |
| Grounded            |       10 |
| Ungrounded          |        0 |
| Grounding Pass Rate | **100%** |

The evaluation covers questions related to:

* Refund policy
* Return policy
* Knowledge retrieval
* Irrelevant queries
* Missing knowledge

The goal is not only to retrieve documents, but to ensure the final answer is grounded in the retrieved evidence.

---

## 3. Agent Routing

The evaluation verifies that different user intents are routed to the correct execution path.

| User Intent          | Expected Path       |
| -------------------- | ------------------- |
| Order query          | `get_order_status`  |
| Refund status        | `get_refund_status` |
| Enterprise knowledge | RAG                 |
| Unsupported question | Abstention          |

Example:

```text
用户：
帮我查询订单12345

Agent:
    ↓
Order Intent
    ↓
get_order_status
    ↓
Business Result
    ↓
Final Answer
```

---

## 4. Agent Abstention

An enterprise Agent should not invent information when the system has no reliable evidence.

Example:

```text
用户：
你们公司今年利润是多少？
```

If the information is not available through tools or the knowledge base, the Agent returns:

```text
type = unknown
```

instead of generating an unsupported answer.

This behavior is explicitly covered by the reliability tests.

---

## 5. Reliability Testing

The project includes automated tests for common Agent failure scenarios.

### Tool Reliability

Test cases include:

* Non-existent order
* Invalid order ID
* Redis GET failure
* Redis SET failure

Redis is treated as a non-critical dependency so temporary Redis failures do not unnecessarily break the main Agent flow.

---

### RAG Reliability

Test cases include:

* Known knowledge
* Missing knowledge
* Irrelevant question
* Non-existent company information

The Agent should abstain when sufficient evidence is unavailable.

---

### Context Reliability

The system verifies that relevant business context can be preserved across a Session.

Example:

```text
用户：
帮我查询订单12345

AI：
订单12345当前状态：已发货……

用户：
那什么时候送到？
```

The Agent can use the previously established order context to resolve the follow-up question.

---

## 6. Automated Test Results

The final reliability test suite:

```text
32 passed
0 failed
```

Result:

> **All automated reliability tests passed.**

---

## 7. Quality Gate

The project uses a quality gate to prevent an evaluation regression from being treated as a successful release.

Current result:

```text
Evaluation Cases:       24
Passed:                 24
Pass Rate:              100%

RAG Cases:              10
Grounded:               10
Grounding Pass Rate:    100%

Automated Tests:        32 passed

QUALITY GATE:           PASSED
```

---

## 8. Evaluation Philosophy

The evaluation is designed around a simple principle:

> **An AI Agent should be evaluated by its behavior, not only by whether the LLM produces fluent text.**

Therefore the project evaluates:

```text
                    Agent
                      │
          ┌───────────┼───────────┐
          ↓           ↓           ↓
       Routing       RAG       Abstention
          │           │           │
          ↓           ↓           ↓
       Tool        Grounding   No Hallucination
          │           │           │
          └───────────┼───────────┘
                      ↓
                Final Answer
```

This makes evaluation closer to real enterprise AI engineering requirements.

---

## 9. Running Evaluation

From the project root:

```bash
python tests/evaluation/run_eval.py
```

Run the full automated test suite:

```bash
pytest
```

Expected results:

```text
24 / 24 evaluation cases passed

10 / 10 RAG cases grounded

32 automated tests passed

QUALITY GATE: PASSED
```
