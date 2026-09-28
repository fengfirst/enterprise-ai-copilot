from fastapi import APIRouter
from pydantic import BaseModel

from backend.agent.service import handle_message

router = APIRouter()


class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    session_id: str
    type: str
    answer: str
    sources: list[dict] = []
    tool: str | None = None

@router.post("/chat", response_model=ChatResponse)
def chat_api(request: ChatRequest):
    result = handle_message(request.message)

    sources = []

    if result["type"] == "rag":
        sources = [
            {
                "document_id": item["document_id"],
                "source": item["metadata"]["source"],
                "distance": item["distance"],
            }
            for item in result["results"]
        ]

    return ChatResponse(
        session_id=request.session_id,
        type=result["type"],
        answer=result["answer"],
        sources=sources,
        tool=result.get("tool"),
    )