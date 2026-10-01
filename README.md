# Enterprise AI Copilot

一个面向企业业务场景的 AI Copilot 后端项目。

项目以真实企业业务场景为基础，逐步构建从 **LLM → Agent → RAG → Session → PostgreSQL → Redis → Observability → Docker → Docker Compose → Secrets Management** 的完整 AI 应用工程链路。

---

## 1. 项目简介

Enterprise AI Copilot 是一个企业级 AI 助手后端原型，支持通过自然语言处理企业业务问题。

当前系统已经具备：

* LLM 对话
* Agent 决策
* Tool Calling
* 企业知识库 RAG
* 多轮对话
* Session 管理
* PostgreSQL 持久化
* Redis 缓存
* 请求与响应日志
* Docker 容器化
* Docker Compose 编排
* PostgreSQL / Redis Health Check
* Secrets Management
* 自动化测试

项目当前重点围绕两个典型业务场景：

1. 订单状态查询
2. 退款状态与企业知识库查询

---

## 2. 项目目标

这个项目的目标不是简单调用一个 LLM API，而是构建一个具备真实业务系统基本能力的 AI Copilot。

整体演进路线：

```text
真实业务需求
      ↓
LLM
      ↓
Agent
      ↓
Tool Calling
      ↓
RAG / Knowledge Base
      ↓
Session / Multi-turn Conversation
      ↓
PostgreSQL Persistence
      ↓
Redis Cache
      ↓
Observability
      ↓
Docker
      ↓
Docker Compose
      ↓
Secrets Management
      ↓
Production Deployment
```

---

## 3. 当前架构

```text
                         Client
                           │
                           ▼
                     ┌───────────┐
                     │  FastAPI  │
                     └─────┬─────┘
                           │
                           ▼
                     ┌───────────┐
                     │   Agent   │
                     └─────┬─────┘
                           │
             ┌─────────────┼─────────────┐
             │             │             │
             ▼             ▼             ▼
          ┌──────┐      ┌──────┐      ┌──────┐
          │ LLM  │      │ Tools│      │ RAG  │
          └──────┘      └──┬───┘      └──────┘
                           │
                    ┌──────┴──────┐
                    │             │
                    ▼             ▼
               Order Tool    Refund Tool
                    │
                    ▼
              ┌────────────┐
              │ Redis Cache│
              └────────────┘

                     Session
                        │
                        ▼
                 ┌────────────┐
                 │ PostgreSQL │
                 └────────────┘
```

---

## 4. 技术栈

### Backend

* Python 3.13+
* FastAPI
* Uvicorn

### AI

* OpenRouter-compatible LLM API
* Agent
* Tool Calling
* RAG
* FastEmbed
* BAAI/bge-small-zh-v1.5
* Chroma

### Data

* PostgreSQL 16
* Redis 8

### Infrastructure

* Docker
* Docker Compose

### Development

* uv
* pytest
* Git

---

## 5. 项目结构

```text
enterprise-ai-copilot/
│
├── backend/
│   ├── agent/
│   │   └── decision.py
│   │
│   ├── api/
│   │   └── chat.py
│   │
│   ├── cache/
│   │   └── redis_cache.py
│   │
│   ├── core/
│   │   ├── llm.py
│   │   └── logging.py
│   │
│   ├── db/
│   │   └── init_db.py
│   │
│   ├── rag/
│   │   └── service.py
│   │
│   ├── session/
│   │   ├── postgres_store.py
│   │   └── ...
│   │
│   ├── tools/
│   │   ├── order.py
│   │   └── refund.py
│   │
│   └── main.py
│
├── tests/
│   ├── evaluation/
│   ├── test_session.py
│   ├── test_conversation.py
│   ├── test_postgres_session.py
│   └── ...
│
├── data/
│   └── chroma/
│
├── .dockerignore
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── uv.lock
└── README.md
```

---

# 6. 核心功能

## 6.1 LLM

系统通过统一的 LLM 接口调用模型。

核心职责：

```text
用户问题
   ↓
LLM
   ↓
结构化决策
   ↓
Agent
```

LLM 不直接负责数据库操作或业务执行。

---

## 6.2 Agent

Agent 根据用户问题决定应该执行什么操作。

例如：

```text
用户：
订单12345现在是什么状态？

        ↓

Agent Decision

        ↓

request_type = order_status

        ↓

get_order_status("12345")

        ↓

返回订单状态
```

对于知识型问题，则进入 RAG：

```text
用户问题
   ↓
Agent
   ↓
Knowledge Base
   ↓
RAG Search
   ↓
相关知识
   ↓
LLM
   ↓
最终回答
```

---

## 6.3 Order Tool

当前包含订单数据示例：

```text
12345
status: shipped
estimated_delivery: 2026-09-20

12346
status: processing
estimated_delivery: 2026-09-23
```

订单查询支持 Redis Cache。

---

## 6.4 Refund Tool

退款查询支持：

* 退款状态
* 退款金额
* 退款预计到账时间

业务逻辑与 LLM 职责分离：

```text
LLM
 ↓
判断用户意图
 ↓
Tool
 ↓
执行真实业务逻辑
 ↓
返回结构化结果
```

---

# 7. RAG

项目集成企业知识库。

当前使用：

```text
Chroma
+
FastEmbed
+
BAAI/bge-small-zh-v1.5
```

知识库用于处理企业业务规则类问题，例如：

```text
退款审核通过后多久可以到账？

哪些商品不支持无理由退款？

信用卡退款多久到账？
```

基本流程：

```text
User Query
    ↓
Embedding
    ↓
Vector Search
    ↓
Relevant Documents
    ↓
LLM
    ↓
Answer
```

Chroma 数据目录：

```text
data/chroma/
```

该目录已加入 `.gitignore`，避免将本地向量数据库提交到 Git。

---

# 8. Multi-turn Conversation

系统支持多轮对话。

Conversation 数据分为：

```text
Session
 ├── session_id
 ├── context
 └── messages
```

消息包括：

```text
user
assistant
```

示例：

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

---

# 9. PostgreSQL Persistence

系统使用 PostgreSQL 保存 Session 和 Message。

当前数据库：

```text
PostgreSQL 16
```

核心数据表：

```text
sessions
messages
```

关系：

```text
sessions
   │
   │ session_id
   ▼
messages
```

Session 被持久化后，即使 FastAPI 进程重启，也可以从 PostgreSQL 恢复历史对话。

---

# 10. Redis Cache

系统使用 Redis 缓存高频业务查询。

当前主要用于订单查询。

流程：

```text
Order Query
     ↓
Redis
     │
     ├── HIT
     │    ↓
     │  直接返回
     │
     └── MISS
          ↓
      Order Source
          ↓
      写入 Redis
          ↓
        返回
```

当前订单缓存 TTL：

```text
60 seconds
```

Redis 的作用：

* 降低重复查询成本
* 减少后端业务查询压力
* 提高高频查询响应速度

---

# 11. Observability

项目已经加入基础日志系统。

日志记录包括：

### Request

```text
[REQUEST]
session_id
message
```

### Agent Decision

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

# 12. Docker

项目已经完成 Docker 容器化。

Dockerfile 使用：

```text
Python 3.13
+
uv
+
FastAPI
```

容器启动：

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

构建镜像：

```bash
docker build -t enterprise-ai-copilot .
```

---

# 13. Docker Compose

项目使用 Docker Compose 管理完整运行环境。

当前服务：

```text
enterprise-ai-copilot
enterprise-postgres
enterprise-redis
```

架构：

```text
┌──────────────────────────────┐
│        Docker Compose        │
│                              │
│  ┌──────────────┐            │
│  │ FastAPI App  │            │
│  │    :8000     │            │
│  └──────┬───────┘            │
│         │                    │
│    ┌────┴─────┐              │
│    ▼          ▼              │
│ PostgreSQL   Redis            │
│   :5432      :6379           │
│                              │
└──────────────────────────────┘
```

宿主机端口：

```text
FastAPI     8000
PostgreSQL  5433
Redis       6380
```

---

# 14. Health Check

Docker Compose 已经为 PostgreSQL 和 Redis 配置 Health Check。

PostgreSQL：

```text
pg_isready
```

Redis：

```text
redis-cli ping
```

App 依赖：

```text
PostgreSQL healthy
        +
Redis healthy
        ↓
     App start
```

查看状态：

```bash
docker compose ps
```

正常情况下应该看到：

```text
enterprise-ai-copilot    Up
enterprise-postgres     Up (healthy)
enterprise-redis        Up (healthy)
```

---

# 15. Environment Variables

项目使用环境变量管理运行配置。

当前主要配置：

```text
DATABASE_URL
REDIS_HOST
REDIS_PORT
OPENROUTER_API_KEY
TYPESAFE_API_KEY
```

开发环境使用：

```text
.env
```

配置模板：

```text
.env.example
```

创建本地配置：

```bash
cp .env.example .env
```

然后在 `.env` 中填写真实配置。

> 不要把真实 API Key 提交到 Git。

`.env` 已加入：

```text
.gitignore
```

---

# 16. Docker Compose 配置

Docker Compose 会从环境变量读取 API Key：

```yaml
OPENROUTER_API_KEY: ${OPENROUTER_API_KEY}
TYPESAFE_API_KEY: ${TYPESAFE_API_KEY}
```

真实 Key 不写入：

```text
docker-compose.yml
```

也不应该写入：

```text
README.md
```

或者 Python 源代码。

---

# 17. 启动项目

## 方式一：Docker Compose

推荐用于完整环境测试。

启动：

```bash
docker compose up -d --build
```

查看状态：

```bash
docker compose ps
```

查看 App 日志：

```bash
docker compose logs -f app
```

停止：

```bash
docker compose down
```

---

# 18. Health Check API

启动成功后：

```bash
curl http://localhost:8000/health
```

预期：

```json
{
  "status": "ok"
}
```

---

# 19. Chat API

接口：

```text
POST /chat
```

请求示例：

```bash
curl -X POST http://localhost:8000/chat \\
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo",
    "message": "订单12345现在是什么状态？"
  }'
```

示例响应：

```json
{
  "session_id": "demo",
  "type": "tool",
  "answer": "订单12345目前状态为已发货。",
  "sources": [],
  "tool": "get_order_status"
}
```

---

# 20. Testing

项目使用 pytest。

运行全部测试：

```bash
pytest
```

也可以运行指定测试：

```bash
pytest tests/test_session.py
```

PostgreSQL Session 测试：

```bash
pytest tests/test_postgres_session.py
```

Evaluation：

```bash
pytest tests/evaluation/
```

---

# 21. Git Workflow

查看当前状态：

```bash
git status
```

查看提交历史：

```bash
git log --oneline
```

提交示例：

```bash
git add .
git commit -m "feat: ..."
```

---

# 22. Secrets Security

项目不会把真实 Secrets 提交到 Git。

当前策略：

```text
.env
 ↓
.gitignore
 ↓
不进入 Git
```

而：

```text
.env.example
 ↓
进入 Git
 ↓
只保存配置模板
```

检查 `.env` 是否被忽略：

```bash
git check-ignore -v .env
```

检查 `.env` 是否进入 Git 历史：

```bash
git log --all -- .env
```

如果没有输出，说明当前 Git 历史中没有 `.env`。

---

# 23. 当前开发进度

当前已经完成：

```text
Day 21  Session / Multi-turn Conversation
   ↓
Day 22  PostgreSQL Persistence
   ↓
Day 23  Redis Cache
   ↓
Day 24  Observability
   ↓
Day 25  Docker
   ↓
Day 26  Docker Compose
   ↓
Day 27  Health Checks
   ↓
Day 28  Secrets Management
   ↓
Day 29  Configuration & Documentation
```

---

# 24. 下一阶段

后续将继续向真正可部署的 AI 产品演进：

```text
Configuration
      ↓
Production Deployment
      ↓
Evaluation
      ↓
Quality Gate
      ↓
API / Frontend Demo
      ↓
Monitoring
      ↓
Cloud Deployment
      ↓
GitHub Portfolio
```

最终目标：

```text
真实业务需求
      ↓
AI System Architecture
      ↓
Coding
      ↓
RAG
      ↓
Agent
      ↓
Evaluation
      ↓
Docker
      ↓
Deployment
      ↓
Demo
      ↓
GitHub Project
      ↓
AI Engineer Portfolio
```

---

## License

This project is for learning, engineering practice, and portfolio development.
