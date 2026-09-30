from fastapi import APIRouter
from pydantic import BaseModel

from backend.agent.service import handle_message
from backend.session.store import InMemorySessionStore

router = APIRouter()

session_store = InMemorySessionStore()


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
    context = session_store.get_context(request.session_id)
    history = session_store.get_messages(request.session_id)

    result = handle_message(
        message=request.message,
        history=history,
        context=context,
    )

    if "context" in result:
        for key, value in result["context"].items():
            session_store.set_context(
                request.session_id,
                key,
                value,
            )

    session_store.add_message(
        request.session_id,
        "user",
        request.message,
    )

    session_store.add_message(
        request.session_id,
        "assistant",
        result["answer"],
    )

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