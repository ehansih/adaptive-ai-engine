from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, Field
from typing import Optional
from backend.db.database import get_db
from backend.db.models import Feedback, Message, ModelPerformance, User
from backend.services.feedback_engine import feedback_engine
from backend.services.security import get_current_user

router = APIRouter(prefix="/feedback", tags=["feedback"])


class FeedbackRequest(BaseModel):
    message_id: str
    rating: int = Field(..., ge=1, le=5)
    tags: list[str] = []
    comment: Optional[str] = None


class RetryRequest(BaseModel):
    message_id: str
    provider: Optional[str] = None
    model: Optional[str] = None


@router.post("/")
async def submit_feedback(
    req: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    result = await feedback_engine.process(
        db=db,
        message_id=req.message_id,
        rating=req.rating,
        tags=req.tags,
        comment=req.comment,
        user_id=user.id if user else None,
    )
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result["detail"])
    return result


@router.get("/stats")
async def feedback_stats(
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    result = await db.execute(
        select(
            ModelPerformance.provider,
            ModelPerformance.query_type,
            ModelPerformance.avg_rating,
            ModelPerformance.total_queries,
            ModelPerformance.avg_latency_ms,
            ModelPerformance.avg_cost_usd,
            ModelPerformance.success_rate,
            ModelPerformance.weight,
        ).order_by(ModelPerformance.weight.desc())
    )
    rows = result.all()
    return [
        {
            "provider": r.provider,
            "query_type": r.query_type,
            "avg_rating": round(r.avg_rating, 2),
            "total_queries": r.total_queries,
            "avg_latency_ms": round(r.avg_latency_ms, 1),
            "avg_cost_usd": round(r.avg_cost_usd, 6),
            "success_rate": round(r.success_rate, 3),
            "routing_weight": round(r.weight, 4),
        }
        for r in rows
    ]


@router.get("/history")
async def feedback_history(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    q = (
        select(Feedback)
        .join(Message, Feedback.message_id == Message.id)
        .order_by(Feedback.created_at.desc())
        .limit(limit)
    )
    if user:
        q = q.where(Feedback.user_id == user.id)
    result = await db.execute(q)
    feedbacks = result.scalars().all()
    return [
        {
            "id": f.id,
            "message_id": f.message_id,
            "rating": f.rating,
            "tags": f.tags,
            "comment": f.comment,
            "triggered_retry": f.triggered_retry,
            "created_at": f.created_at,
        }
        for f in feedbacks
    ]
