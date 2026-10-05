# Enterprise AI Copilot

> A production-oriented enterprise AI assistant built with **Agent + RAG + Tool Calling + Evaluation + Reliability + Docker**.

Enterprise AI Copilot 是一个面向企业业务场景的全栈 AI 应用原型。

项目不是简单调用 LLM API，而是围绕真实业务问题构建了一条完整的 AI 应用工程链路：

```text
User Request
     ↓
React Frontend
     ↓
Nginx
     ↓
FastAPI
     ↓
Agent Routing
 ┌───┼────────────┐
 ↓   ↓            ↓
Tool RAG       Abstention
 ↓   ↓
Business Knowledge
     ↓
PostgreSQL / Redis / Chroma
```

当前系统已经完成：

* Agent Routing
* Tool Calling
* 企业知识库 RAG
* Multi-turn Conversation
* PostgreSQL Session Persistence
* Redis Cache
* Agent Abstention
* Evaluation / Quality Gate
* Reliability Testing
* Observability
* React Frontend
* Nginx
* Docker
* Docker Compose
* Secrets Management

---

## 1. Project Highlights

### 1.1 Agent + Tool Calling

系统能够根据用户意图选择正确的业务工具。

例如：

```text
用户：
帮我查询订单12345的状态

        ↓

Agent Routing

        ↓

get_order_status("12345")

        ↓

业务结果
```

当前主要业务 Tool：

* `get_order_status`
* `get_refund_status`

LLM 负责理解和决策，Tool 负责执行确定性的业务逻辑。

---

### 1.2 Enterprise RAG

对于企业政策、业务规则等知识型问题，Agent 将请求路由到企业知识库。

```text
User Query
    ↓
Agent
    ↓
Embedding
    ↓
Vector Search
    ↓
Relevant Documents
    ↓
LLM
    ↓
Grounded Answer
```

当前技术：

* Chroma
* FastEmbed
* `BAAI/bge-small-zh-v1.5`

示例：

```text
退款审核通过后一般几天可以到账？
```

系统能够基于企业退款政策回答：

```text
退款审核通过后，一般会在 3—7 个工作日内
按原支付方式原路到账。
```

同时返回 Knowledge Sources。

---

### 1.3 Agent Abstention

系统不会对未知问题强行生成答案。

当知识库没有足够证据、业务 Tool 无法处理请求时，Agent 可以主动拒答：

```text
Known Business Request
        ↓
Tool / RAG
        ↓
Answer

Unknown / Unsupported Request
        ↓
Abstention
        ↓
明确告知无法提供可靠答案
```

这是项目 Reliability 设计的重要组成部分。

---

### 1.4 Evaluation & Quality Gate

项目包含独立 Evaluation Dataset 和自动化评估。

当前 Evaluation：

```text
24 test cases
24 passed

Pass Rate: 100%
```

RAG Grounding：

```text
10 / 10 grounded
Grounding Pass Rate: 100%
```

同时建立了 Quality Gate：

```text
Evaluation
    ↓
Metrics
    ↓
Quality Gate
    ↓
PASS / FAIL
```

只有通过质量门禁，系统才认为当前版本满足验收标准。

---

### 1.5 Agent Reliability

项目针对 Agent 的实际运行风险增加了 Reliability 测试。

覆盖：

* Tool Exception
* Invalid Order
* Redis Failure
* RAG Failure
* Knowledge Not Found
* Agent Abstention
* Agent Routing
* Context / Multi-turn Edge Cases

最终测试：

```text
32 passed
0 failed
```

---

## 2. Architecture

```text
                         Browser
                            │
                            ▼
                    ┌──────────────┐
                    │ React + Vite │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │    Nginx     │
                    │ Static + API │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   FastAPI    │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │    Agent     │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
          ┌────────┐   ┌────────┐  ┌────────────┐
          │  Tool  │   │  RAG   │  │ Abstention │
          └───┬────┘   └───┬────┘  └────────────┘
              │            │
       ┌──────┴──────┐     ▼
       │             │  ┌─────────┐
       ▼             ▼  │ Chroma  │
   Order Tool   Refund  └─────────┘
                  Tool
       │
       ▼
    Redis

       Session / Messages
              │
              ▼
        PostgreSQL
```

---

## 3. Technology Stack

### Frontend

* React
* TypeScript
* Vite
* React Markdown
* Nginx

### Backend

* Python 3.13+
* FastAPI
* Uvicorn

### AI

* OpenAI-compatible LLM API
* Agent Routing
* Tool Calling
* RAG
* FastEmbed
* `BAAI/bge-small-zh-v1.5`
* Chroma

### Data

* PostgreSQL 16
* Redis 8

### Infrastructure

* Docker
* Docker Compose
* Nginx

### Development & Testing

* uv
* pytest
* Git

---

## 4. Core Business Scenarios

当前系统围绕两个典型企业业务场景：

### Order Status

```text
用户：
查询订单12345

        ↓

Agent

        ↓

get_order_status

        ↓

订单状态
```

示例：

```text
订单 12345 当前状态：已发货
预计送达日期：2026年9月20日
```

### Refund

退款相关请求可以进入：

* Refund Tool
* Refund Knowledge Base

例如：

```text
退款审核通过后一般几天可以到账？
```

系统通过 RAG 查询企业退款政策并生成带知识来源的回答。

---

## 5. Multi-turn Conversation

系统支持基于 Session 的多轮对话。

Session 包含：

```text
session_id
context
messages
```

例如：

```text
用户：
查询订单12346

AI：
订单12346目前正在处理中。

用户：
那退款呢？

AI：
根据当前订单上下文继续查询订单12346的退款状态。
```

Session 数据持久化到 PostgreSQL，因此 FastAPI 重启后仍然可以恢复历史会话。

---

## 6. PostgreSQL Persistence

PostgreSQL 用于持久化：

```text
sessions
messages
```

数据关系：

```text
sessions
    │
    │ session_id
    ▼
messages
```

核心目标：

* Session 持久化
* Message 持久化
* Multi-turn Context
* 服务重启后恢复会话

---

## 7. Redis Cache

Redis 用于缓存高频业务查询。

当前主要应用于订单查询：

```text
Order Query
     ↓
   Redis
     │
 ┌───┴────┐
 │        │
HIT      MISS
 │        │
 ↓        ▼
Return   Business Source
          │
          ▼
       Redis SET
          │
          ▼
        Return
```

当前订单缓存 TTL：

```text
60 seconds
```

Redis 主要用于：

* 降低重复查询成本
* 减少业务查询压力
* 提高高频查询响应速度

同时，Redis 故障不会让整个 Agent 不可用，系统对缓存进行了非关键依赖处理。

---

## 8. Observability

系统加入了基础请求级 Observability。

### Request

```text
[REQUEST]
session_id
message
```

### Agent

```text
[AGENT]
request_type
needs_knowledge_base
```

### Tool

```text
[AGENT]
tool
order_id
```

### Cache

```text
[CACHE]
HIT
MISS
SET
```

### Response

```text
[RESPONSE]
session_id
type
tool
latency
```

例如：

```text
[REQUEST] session_id=demo message=订单12345现在是什么状态？

[AGENT] decision request_type=order_status

[AGENT] tool=get_order_status order_id=12345

[CACHE] HIT key=order:12345

[RESPONSE] session_id=demo type=tool tool=get_order_status latency=...
```

---

## 9. Evaluation

Evaluation Dataset 位于：

```text
evaluation/dataset.json
```

当前包含：

```text
24 cases
```

运行：

```bash
python tests/evaluation/run_eval.py
```

当前验收结果：

```text
24 / 24 passed
Pass Rate: 100%

RAG:
10 / 10 grounded
Grounding Pass Rate: 100%

Quality Gate:
PASSED
```

Evaluation 覆盖：

* Order Tool
* Refund Tool
* RAG
* Unknown Request
* Contextual Requests
* Edge Cases

---

## 10. Reliability Testing

Reliability 测试位于：

```text
tests/reliability/
```

覆盖：

```text
Tool Exceptions
RAG Exceptions
Agent Abstention
Agent Routing
Redis Failures
Context Edge Cases
```

最终测试：

```bash
uv run pytest -q
```

结果：

```text
32 passed
```

---

## 11. Docker

Backend 使用 Docker 容器化。

Dockerfile：

```text
Python 3.13
    +
uv
    +
FastAPI
```

构建：

```bash
docker build -t enterprise-ai-copilot-backend .
```

---

## 12. Docker Compose

完整系统使用 Docker Compose 编排：

```text
┌────────────────────────────────────────────┐
│              Docker Compose                │
│                                            │
│  ┌──────────────┐      ┌──────────────┐   │
│  │   Frontend   │      │   Backend    │   │
│  │ Nginx :5174  │ ───► │ FastAPI :8000│   │
│  └──────────────┘      └──────┬───────┘   │
│                               │           │
│                         ┌─────┴─────┐     │
│                         ▼           ▼     │
│                    PostgreSQL     Redis   │
│                       :5432       :6379   │
│                                            │
└────────────────────────────────────────────┘
```

当前 Compose 服务：

```text
frontend
app
postgres
redis
```

宿主机端口：

```text
Frontend     5174
FastAPI      8000
PostgreSQL   5433
Redis        6380
```

---

## 13. Health Checks

PostgreSQL：

```text
pg_isready
```

Redis：

```text
redis-cli ping
```

Compose 会等待 PostgreSQL 和 Redis 进入 healthy 状态后再启动 App。

查看：

```bash
docker compose ps
```

---

## 14. Frontend

Frontend 使用：

```text
React
TypeScript
Vite
React Markdown
Nginx
```

当前 UI 支持：

* Chat
* New Session
* Session ID
* Loading State
* Error State
* Markdown Response
* Tool Badge
* RAG Badge
* Abstention Badge
* Knowledge Sources
* Source Distance
* Responsive Layout

Frontend production build：

```bash
cd frontend
pnpm build
```

Docker 中由 Nginx 提供静态文件，并通过 `/chat` 反向代理到 Backend。

---

## 15. API

### Health

```http
GET /health
```

Example:

```bash
curl http://localhost:8000/health
```

Response:

```json
{
  "status": "ok",
  "service": "enterprise-ai-copilot"
}
```

### Chat

```http
POST /chat
```

Example:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo",
    "message": "订单12345现在是什么状态？"
  }'
```

Response:

```json
{
  "session_id": "demo",
  "type": "tool",
  "answer": "订单 12345 当前状态：已发货",
  "sources": [],
  "tool": "get_order_status"
}
```

---

## 16. Project Structure

```text
enterprise-ai-copilot/
│
├── backend/
│   ├── agent/
│   ├── api/
│   ├── cache/
│   ├── core/
│   ├── db/
│   ├── rag/
│   ├── session/
│   ├── tools/
│   └── main.py
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── App.css
│   │   └── main.tsx
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   └── pnpm-lock.yaml
│
├── evaluation/
│   └── dataset.json
│
├── tests/
│   ├── evaluation/
│   ├── reliability/
│   └── ...
│
├── data/
│   └── chroma/
│
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── uv.lock
├── .env.example
├── .gitignore
└── README.md
```

本地 `data/chroma/` 和前端 `node_modules/`、`dist/` 不提交到 Git。

---

## 17. Environment Variables

项目使用环境变量管理 Secrets。

主要配置：

```text
DATABASE_URL
REDIS_HOST
REDIS_PORT
OPENROUTER_API_KEY
TYPESAFE_API_KEY
```

本地开发：

```bash
cp .env.example .env
```

然后填写实际配置。

**不要把真实 API Key 提交到 Git。**

检查：

```bash
git check-ignore -v .env
```

`.env` 已加入 `.gitignore`。

---

## 18. Run Locally

### Docker Compose

推荐使用完整 Docker 环境：

```bash
docker compose up -d --build
```

查看服务：

```bash
docker compose ps
```

查看 Backend：

```bash
docker compose logs -f app
```

访问 Frontend：

```text
http://127.0.0.1:5174
```

访问 Backend：

```text
http://127.0.0.1:8000
```

停止：

```bash
docker compose down
```

---

## 19. Testing

运行全部测试：

```bash
uv run pytest -q
```

当前结果：

```text
32 passed
```

运行 Evaluation：

```bash
python tests/evaluation/run_eval.py
```

当前结果：

```text
24 / 24 passed
Quality Gate: PASSED
```

Frontend production build：

```bash
cd frontend
pnpm build
```

---

## 20. Production Readiness

当前项目已经完成本地生产化验证：

```text
Backend Docker
       ↓
PostgreSQL
       ↓
Redis
       ↓
Frontend Docker
       ↓
Nginx
       ↓
Full-stack Compose
       ↓
End-to-end Verification
```

已经验证：

* Backend container
* Frontend container
* PostgreSQL health check
* Redis health check
* Nginx reverse proxy
* Frontend → Backend
* Agent → Tool
* Agent → RAG
* Session persistence
* Docker Compose full stack

当前状态：

> **Production-oriented local deployment verified.**

公网 Cloud Deployment 尚未作为当前版本的一部分完成。

---

## 21. Engineering Validation

项目当前关键指标：

| Area                      |    Result |
| ------------------------- | --------: |
| Evaluation Cases          |        24 |
| Evaluation Pass Rate      |      100% |
| RAG Grounding             |     10/10 |
| Quality Gate              |      PASS |
| Automated Tests           | 32 passed |
| Frontend Production Build |      PASS |
| Docker Compose            |      PASS |
| PostgreSQL Health Check   |      PASS |
| Redis Health Check        |      PASS |
| Full-stack E2E            |      PASS |

---

## 22. Engineering Highlights

这个项目重点展示的不是某一个 LLM API，而是 AI 应用工程能力：

### AI Application

* Agent Routing
* Tool Calling
* RAG
* Grounded Generation
* Abstention

### Reliability

* Evaluation Dataset
* Quality Gate
* Exception Handling
* Routing Tests
* Abstention Tests
* Context Tests

### Backend Engineering

* FastAPI
* PostgreSQL
* Redis
* Session Persistence
* Structured Logging

### Frontend Engineering

* React
* TypeScript
* Vite
* Markdown Rendering
* Agent Observability UI
* Nginx Reverse Proxy

### Infrastructure

* Docker
* Docker Compose
* Health Checks
* Secrets Management
* Full-stack Containerization

---

## 23. Roadmap

当前项目已经完成：

```text
RAG / Agent
      ↓
Evaluation
      ↓
Reliability
      ↓
Frontend Demo
      ↓
Docker
      ↓
Docker Compose
      ↓
Local Production Verification
```

后续重点：

```text
Cloud Deployment
      ↓
Public Demo
      ↓
GitHub Portfolio
      ↓
Resume / Interview
```

---

## License

This project is for learning, engineering practice, and portfolio development.
