FROM python:3.13-slim

WORKDIR /app

# 安装 uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 优先复制依赖文件，便于利用 Docker 构建缓存
COPY pyproject.toml uv.lock ./

# 在容器中安装项目依赖，不安装开发依赖
RUN uv sync --frozen --no-dev

# 复制后端代码
COPY backend/ ./backend/

# Python 使用容器内的虚拟环境
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
