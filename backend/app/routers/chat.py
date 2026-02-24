"""Chat router — handles conversational queries about uploaded datasets."""
import uuid
from fastapi import APIRouter, HTTPException
from app.models import ChatRequest, ChatResponse
from app.agents.query import answer_question
from app.agents.ingest import get_dataset

router = APIRouter(prefix="/api", tags=["chat"])

# Simple in-memory session store: { session_id: [messages] }
_sessions: dict[str, list[dict]] = {}


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message to the data assistant.
    Requires a dataset_id from a previous /upload call.
    """
    session_id = request.session_id or str(uuid.uuid4())
    
    # Get or create session history
    history = _sessions.get(session_id, [])
    
    # Validate dataset exists if provided
    if request.dataset_id:
        dataset = get_dataset(request.dataset_id)
        if not dataset:
            raise HTTPException(
                status_code=404,
                detail="Dataset not found. Please upload a CSV file first."
            )
    
    # Get the last user message
    user_messages = [m for m in request.messages if m.role == "user"]
    if not user_messages:
        raise HTTPException(status_code=400, detail="No user message provided.")
    
    question = user_messages[-1].content
    
    # Add to history
    history.append({"role": "user", "content": question})
    
    # Answer the question
    if request.dataset_id:
        result = answer_question(
            question=question,
            dataset_id=request.dataset_id,
            conversation_history=history[:-1],  # exclude current message
        )
    else:
        # No dataset — provide helpful guidance
        result = {
            "answer": (
                "👋 Hi! I'm Gradient Fisherman, your AI data assistant. "
                "Please upload a CSV file first using the upload button, "
                "and then I can answer questions about your data!"
            ),
            "table_data": None,
            "chart": None,
            "raw_code": None,
        }
    
    answer = result["answer"]
    
    # Add assistant response to history
    history.append({"role": "assistant", "content": answer})
    _sessions[session_id] = history[-20:]  # keep last 20 messages
    
    return ChatResponse(
        message=answer,
        chart=result.get("chart"),
        table_data=result.get("table_data"),
        session_id=session_id,
    )


@router.get("/chat/{session_id}/history")
async def get_history(session_id: str):
    """Get conversation history for a session."""
    return {"session_id": session_id, "messages": _sessions.get(session_id, [])}


@router.delete("/chat/{session_id}")
async def clear_session(session_id: str):
    """Clear conversation history for a session."""
    _sessions.pop(session_id, None)
    return {"status": "cleared", "session_id": session_id}


@router.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "gradient-fisherman-backend"}
