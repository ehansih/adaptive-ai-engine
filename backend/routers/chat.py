from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from backend.db.database import get_db
from backend.db.models import ChatSession, Message, User
from backend.services.orchestrator import orchestrator
from backend.services.security import sanitize_input, get_current_user, audit

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048
    strategy: Optional[str] = None  # adaptive | round-robin | cost-optimized


class ChatResponse(BaseModel):
    session_id: str
    message_id: str
    content: str
    provider: str
    model: str
    tokens_in: int
    tokens_out: int
    latency_ms: float
    cost_usd: float
    attempt: int
    query_type: str


@router.post("/", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    clean_message = sanitize_input(req.message)

    # Get or create session
    session = None
    if req.session_id:
        result = await db.execute(select(ChatSession).where(ChatSession.id == req.session_id))
        session = result.scalar_one_or_none()

    if not session:
        session = ChatSession(
            user_id=user.id if user else None,
            title=clean_message[:60] + ("..." if len(clean_message) > 60 else ""),
        )
        db.add(session)
        await db.flush()

    # Build message history for context
    history_result = await db.execute(
        select(Message)
        .where(Message.session_id == session.id)
        .order_by(Message.created_at)
        .limit(20)
    )
    history = history_result.scalars().all()
    messages = [{"role": m.role, "content": m.content} for m in history]
    messages.append({"role": "user", "content": clean_message})

    # Store user message
    user_msg = Message(
        session_id=session.id,
        role="user",
        content=clean_message,
    )
    db.add(user_msg)
    await db.flush()

    # Run orchestrator
    response = await orchestrator.run(
        messages=messages,
        db=db,
        preferred_provider=req.provider,
        preferred_model=req.model,
        temperature=req.temperature,
        max_tokens=req.max_tokens,
        strategy=req.strategy,
    )

    # Store assistant message
    ai_msg = Message(
        session_id=session.id,
        role="assistant",
        content=response.content,
        model_used=response.model,
        provider=response.provider,
        tokens_in=response.tokens_in,
        tokens_out=response.tokens_out,
        latency_ms=response.latency_ms,
        cost_usd=response.cost_usd,
        attempt=response.metadata.get("attempt", 1),
        metadata_=response.metadata,
    )
    db.add(ai_msg)
    await db.commit()

    ip = request.client.host if request.client else None
    await audit(db, "chat", user_id=user.id if user else None, ip_address=ip,
                details={"session_id": session.id, "provider": response.provider})

    return ChatResponse(
        session_id=session.id,
        message_id=ai_msg.id,
        content=response.content,
        provider=response.provider,
        model=response.model,
        tokens_in=response.tokens_in,
        tokens_out=response.tokens_out,
        latency_ms=round(response.latency_ms, 2),
        cost_usd=round(response.cost_usd, 6),
        attempt=response.metadata.get("attempt", 1),
        query_type=response.metadata.get("query_type", "general"),
    )


@router.get("/sessions")
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    q = select(ChatSession).order_by(ChatSession.updated_at.desc()).limit(50)
    if user:
        q = q.where(ChatSession.user_id == user.id)
    result = await db.execute(q)
    sessions = result.scalars().all()
    return [{"id": s.id, "title": s.title, "created_at": s.created_at, "updated_at": s.updated_at}
            for s in sessions]


@router.get("/sessions/{session_id}/messages")
async def get_messages(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    result = await db.execute(
        select(Message).where(Message.session_id == session_id).order_by(Message.created_at)
    )
    messages = result.scalars().all()
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "model_used": m.model_used,
            "provider": m.provider,
            "tokens_in": m.tokens_in,
            "tokens_out": m.tokens_out,
            "latency_ms": m.latency_ms,
            "cost_usd": m.cost_usd,
            "attempt": m.attempt,
            "created_at": m.created_at,
        }
        for m in messages
    ]


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    await db.delete(session)
    await db.commit()
    return {"status": "deleted"}
