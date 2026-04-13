"""Adaptive Orchestrator — selects models, retries, learns from feedback."""
import asyncio
import random
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from backend.config import settings
from backend.db.models import ModelPerformance, Message
from backend.services.gateway import gateway, ModelResponse


QUERY_TYPE_KEYWORDS = {
    "code": ["code", "function", "bug", "debug", "implement", "programming", "syntax"],
    "math": ["calculate", "solve", "equation", "formula", "math", "compute"],
    "creative": ["write", "story", "poem", "creative", "imagine", "fiction"],
    "analysis": ["analyze", "explain", "summarize", "compare", "evaluate", "assess"],
    "factual": ["what", "who", "when", "where", "define", "history"],
}


def classify_query(text: str) -> str:
    text_lower = text.lower()
    scores = {}
    for qtype, keywords in QUERY_TYPE_KEYWORDS.items():
        scores[qtype] = sum(1 for k in keywords if k in text_lower)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "general"


# System prompts per query type
SYSTEM_PROMPTS = {
    "code": "You are an expert software engineer. Provide precise, working code with brief explanations.",
    "math": "You are a mathematics expert. Show step-by-step reasoning and verify your answers.",
    "creative": "You are a creative writer. Craft engaging, original content.",
    "analysis": "You are an analytical expert. Provide structured, evidence-based analysis.",
    "factual": "You are a knowledgeable assistant. Provide accurate, concise factual information.",
    "general": "You are a helpful, honest, and precise AI assistant.",
}

RESPONSE_QUALITY_INDICATORS = {
    "too_short": lambda r: len(r.content) < 50,
    "no_content": lambda r: not r.content.strip(),
    "error": lambda r: r.error is not None,
}


class AdaptiveOrchestrator:
    def __init__(self):
        self._provider_order = ["anthropic", "openai", "gemini", "ollama"]

    async def _get_model_weights(self, db: AsyncSession, query_type: str) -> list[dict]:
        """Return providers sorted by adaptive weight for this query type."""
        available = gateway.available_providers()
        if not available:
            raise RuntimeError("No AI providers configured. Add at least one API key.")

        weights = []
        for provider in available:
            pid = provider["id"]
            result = await db.execute(
                select(ModelPerformance).where(
                    ModelPerformance.provider == pid,
                    ModelPerformance.query_type == query_type,
                )
            )
            perf = result.scalar_one_or_none()
            if perf:
                w = perf.weight * perf.avg_rating * perf.success_rate
            else:
                w = 1.0  # default weight for new providers

            weights.append({
                "provider": pid,
                "model": provider["default"],
                "weight": w,
            })

        weights.sort(key=lambda x: x["weight"], reverse=True)
        return weights

    async def run(
        self,
        messages: list[dict],
        db: AsyncSession,
        preferred_provider: Optional[str] = None,
        preferred_model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        strategy: Optional[str] = None,
    ) -> ModelResponse:
        query_type = classify_query(messages[-1]["content"] if messages else "")
        system_prompt = SYSTEM_PROMPTS.get(query_type, SYSTEM_PROMPTS["general"])
        strategy = strategy or settings.MODEL_SELECTION_STRATEGY

        if preferred_provider:
            provider_queue = [{"provider": preferred_provider, "model": preferred_model or ""}]
        elif strategy == "adaptive":
            provider_queue = await self._get_model_weights(db, query_type)
        elif strategy == "round-robin":
            available = gateway.available_providers()
            provider_queue = [{"provider": p["id"], "model": p["default"]} for p in available]
            random.shuffle(provider_queue)
        elif strategy == "cost-optimized":
            available = gateway.available_providers()
            # Prefer cheaper models
            cost_order = ["gemini", "openai", "anthropic", "ollama"]
            pid_map = {p["id"]: p for p in available}
            provider_queue = [
                {"provider": pid, "model": pid_map[pid]["default"]}
                for pid in cost_order if pid in pid_map
            ]
        else:
            available = gateway.available_providers()
            provider_queue = [{"provider": p["id"], "model": p["default"]} for p in available]

        last_response = None
        for attempt, candidate in enumerate(provider_queue[:settings.MAX_RETRIES], start=1):
            provider = candidate["provider"]
            model = preferred_model if (preferred_provider and attempt == 1) else candidate["model"]
            if not model:
                model = None  # gateway uses default

            response = await gateway.generate(
                messages=messages,
                provider=provider,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                system_prompt=system_prompt,
            )

            response.metadata["query_type"] = query_type
            response.metadata["attempt"] = attempt
            response.metadata["strategy"] = strategy

            # Update performance stats
            await self._update_performance(db, provider, model or provider, query_type,
                                           response, success=response.error is None)

            if not any(check(response) for check in RESPONSE_QUALITY_INDICATORS.values()):
                return response

            last_response = response

        return last_response or ModelResponse(
            content="All configured AI providers failed to respond. Please try again.",
            provider="orchestrator",
            model="none",
            error="All providers exhausted",
        )

    async def _update_performance(
        self,
        db: AsyncSession,
        provider: str,
        model: str,
        query_type: str,
        response: ModelResponse,
        success: bool,
        rating: Optional[float] = None,
    ):
        result = await db.execute(
            select(ModelPerformance).where(
                ModelPerformance.provider == provider,
                ModelPerformance.query_type == query_type,
            )
        )
        perf = result.scalar_one_or_none()

        if not perf:
            perf = ModelPerformance(
                provider=provider, model=model, query_type=query_type
            )
            db.add(perf)

        n = perf.total_queries
        perf.total_queries = n + 1
        perf.avg_latency_ms = (perf.avg_latency_ms * n + response.latency_ms) / (n + 1)
        perf.success_rate = (perf.success_rate * n + (1 if success else 0)) / (n + 1)
        if response.cost_usd:
            perf.avg_cost_usd = (perf.avg_cost_usd * n + response.cost_usd) / (n + 1)
        if rating is not None:
            perf.avg_rating = (perf.avg_rating * n + rating) / (n + 1)
            # Recalculate routing weight
            perf.weight = (perf.avg_rating / 5.0) * perf.success_rate

        await db.commit()

    async def apply_feedback(
        self,
        db: AsyncSession,
        provider: str,
        model: str,
        query_type: str,
        rating: int,
        triggered_retry: bool,
    ):
        """Update model weights based on user feedback."""
        dummy = ModelResponse(content="", provider=provider, model=model, latency_ms=0)
        await self._update_performance(db, provider, model, query_type, dummy,
                                       success=True, rating=float(rating))


orchestrator = AdaptiveOrchestrator()
