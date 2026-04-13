"""Feedback Engine — processes user feedback and drives learning."""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.db.models import Feedback, Message, MemoryEntry
from backend.services.orchestrator import orchestrator
from backend.services.memory_service import memory_service

LOW_RATING_THRESHOLD = 2   # trigger retry / flag
HIGH_RATING_THRESHOLD = 4  # mark as exemplar


class FeedbackEngine:
    async def process(
        self,
        db: AsyncSession,
        message_id: str,
        rating: int,
        tags: Optional[list[str]] = None,
        comment: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> dict:
        # Load the message
        result = await db.execute(select(Message).where(Message.id == message_id))
        message = result.scalar_one_or_none()
        if not message:
            return {"status": "error", "detail": "Message not found"}

        # Check for existing feedback
        result2 = await db.execute(select(Feedback).where(Feedback.message_id == message_id))
        existing = result2.scalar_one_or_none()
        triggered_retry = rating <= LOW_RATING_THRESHOLD

        if existing:
            existing.rating = rating
            existing.tags = tags or []
            existing.comment = comment
            existing.triggered_retry = triggered_retry
        else:
            fb = Feedback(
                message_id=message_id,
                user_id=user_id,
                rating=rating,
                tags=tags or [],
                comment=comment,
                triggered_retry=triggered_retry,
            )
            db.add(fb)

        await db.commit()

        # Update adaptive model weights
        query_type = message.metadata_.get("query_type", "general") if message.metadata_ else "general"
        await orchestrator.apply_feedback(
            db=db,
            provider=message.provider or "unknown",
            model=message.model_used or "unknown",
            query_type=query_type,
            rating=rating,
            triggered_retry=triggered_retry,
        )

        # Auto-store highly-rated responses as memory exemplars
        if rating >= HIGH_RATING_THRESHOLD and message.content:
            session_result = await db.execute(
                select(Message)
                .where(Message.session_id == message.session_id, Message.role == "user")
                .order_by(Message.created_at.desc())
                .limit(1)
            )
            user_msg = session_result.scalar_one_or_none()
            if user_msg:
                key = f"exemplar:{message.provider}:{query_type}:{message_id[:8]}"
                await memory_service.store(
                    db=db,
                    key=key,
                    value=f"Q: {user_msg.content[:500]}\nA: {message.content[:1000]}",
                    user_id=user_id,
                    tags=["exemplar", query_type, message.provider or "unknown"],
                    source="feedback",
                )

        actions = []
        if triggered_retry:
            actions.append("retry_suggested")
        if rating >= HIGH_RATING_THRESHOLD:
            actions.append("exemplar_stored")

        return {
            "status": "ok",
            "rating": rating,
            "triggered_retry": triggered_retry,
            "actions": actions,
        }


feedback_engine = FeedbackEngine()
