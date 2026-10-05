from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.chat import router as chat_router
from backend.core.logging import setup_logging


setup_logging()


app = FastAPI(
    title="Enterprise AI Copilot",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)



@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "enterprise-ai-copilot",
    }