"""Model Gateway — unified interface to OpenAI, Anthropic, Gemini, Ollama."""
import time
import asyncio
from typing import AsyncIterator, Optional
from dataclasses import dataclass, field
import httpx
from backend.config import settings

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from anthropic import AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


@dataclass
class ModelResponse:
    content: str
    provider: str
    model: str
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)


# Cost per 1M tokens (input/output) USD — update as needed
COST_TABLE = {
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4-turbo": (10.00, 30.00),
    "gpt-3.5-turbo": (0.50, 1.50),
    "claude-opus-4-6": (15.00, 75.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-haiku-4-5-20251001": (0.25, 1.25),
    "gemini-2.0-flash": (0.075, 0.30),
    "gemini-1.5-pro": (1.25, 5.00),
}


def _calc_cost(model: str, tokens_in: int, tokens_out: int) -> float:
    key = model.split("/")[-1]
    for k, (cin, cout) in COST_TABLE.items():
        if k in key:
            return (tokens_in * cin + tokens_out * cout) / 1_000_000
    return 0.0


class ModelGateway:
    def __init__(self):
        self._openai: Optional[AsyncOpenAI] = None
        self._anthropic: Optional[AsyncAnthropic] = None
        self._gemini_configured = False

    def _get_openai(self) -> AsyncOpenAI:
        if not OPENAI_AVAILABLE:
            raise RuntimeError("openai package not installed")
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY not configured")
        if not self._openai:
            self._openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return self._openai

    def _get_anthropic(self) -> AsyncAnthropic:
        if not ANTHROPIC_AVAILABLE:
            raise RuntimeError("anthropic package not installed")
        if not settings.ANTHROPIC_API_KEY:
            raise RuntimeError("ANTHROPIC_API_KEY not configured")
        if not self._anthropic:
            self._anthropic = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        return self._anthropic

    def _configure_gemini(self):
        if not GEMINI_AVAILABLE:
            raise RuntimeError("google-generativeai package not installed")
        if not settings.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY not configured")
        if not self._gemini_configured:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self._gemini_configured = True

    def available_providers(self) -> list[dict]:
        providers = []
        if OPENAI_AVAILABLE and settings.OPENAI_API_KEY:
            providers.append({
                "id": "openai",
                "name": "OpenAI",
                "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
                "default": settings.OPENAI_DEFAULT_MODEL,
            })
        if ANTHROPIC_AVAILABLE and settings.ANTHROPIC_API_KEY:
            providers.append({
                "id": "anthropic",
                "name": "Anthropic Claude",
                "models": ["claude-opus-4-6", "claude-sonnet-4-6", "claude-haiku-4-5-20251001"],
                "default": settings.ANTHROPIC_DEFAULT_MODEL,
            })
        if GEMINI_AVAILABLE and settings.GEMINI_API_KEY:
            providers.append({
                "id": "gemini",
                "name": "Google Gemini",
                "models": ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
                "default": settings.GEMINI_DEFAULT_MODEL,
            })
        if settings.OLLAMA_ENABLED:
            providers.append({
                "id": "ollama",
                "name": "Local LLM (Ollama)",
                "models": [settings.OLLAMA_DEFAULT_MODEL],
                "default": settings.OLLAMA_DEFAULT_MODEL,
            })
        return providers

    async def generate(
        self,
        messages: list[dict],
        provider: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        system_prompt: Optional[str] = None,
    ) -> ModelResponse:
        t0 = time.monotonic()
        try:
            if provider == "openai":
                resp = await self._openai_generate(messages, model or settings.OPENAI_DEFAULT_MODEL,
                                                   temperature, max_tokens, system_prompt)
            elif provider == "anthropic":
                resp = await self._anthropic_generate(messages, model or settings.ANTHROPIC_DEFAULT_MODEL,
                                                      temperature, max_tokens, system_prompt)
            elif provider == "gemini":
                resp = await self._gemini_generate(messages, model or settings.GEMINI_DEFAULT_MODEL,
                                                   temperature, max_tokens, system_prompt)
            elif provider == "ollama":
                resp = await self._ollama_generate(messages, model or settings.OLLAMA_DEFAULT_MODEL,
                                                   temperature, max_tokens, system_prompt)
            else:
                raise ValueError(f"Unknown provider: {provider}")

            resp.latency_ms = (time.monotonic() - t0) * 1000
            resp.cost_usd = _calc_cost(resp.model, resp.tokens_in, resp.tokens_out)
            return resp
        except Exception as e:
            return ModelResponse(
                content="",
                provider=provider,
                model=model or "unknown",
                latency_ms=(time.monotonic() - t0) * 1000,
                error=str(e),
            )

    async def _openai_generate(self, messages, model, temperature, max_tokens, system_prompt):
        client = self._get_openai()
        all_messages = []
        if system_prompt:
            all_messages.append({"role": "system", "content": system_prompt})
        all_messages.extend(messages)

        resp = await client.chat.completions.create(
            model=model,
            messages=all_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return ModelResponse(
            content=resp.choices[0].message.content or "",
            provider="openai",
            model=model,
            tokens_in=resp.usage.prompt_tokens if resp.usage else 0,
            tokens_out=resp.usage.completion_tokens if resp.usage else 0,
        )

    async def _anthropic_generate(self, messages, model, temperature, max_tokens, system_prompt):
        client = self._get_anthropic()
        kwargs = dict(model=model, messages=messages, temperature=temperature, max_tokens=max_tokens)
        if system_prompt:
            kwargs["system"] = system_prompt

        resp = await client.messages.create(**kwargs)
        return ModelResponse(
            content=resp.content[0].text if resp.content else "",
            provider="anthropic",
            model=model,
            tokens_in=resp.usage.input_tokens,
            tokens_out=resp.usage.output_tokens,
        )

    async def _gemini_generate(self, messages, model, temperature, max_tokens, system_prompt):
        self._configure_gemini()
        gemini_model = genai.GenerativeModel(
            model_name=model,
            system_instruction=system_prompt,
            generation_config={"temperature": temperature, "max_output_tokens": max_tokens},
        )
        # Convert messages to Gemini format
        history = []
        last_user = ""
        for m in messages:
            if m["role"] == "user":
                last_user = m["content"]
            elif m["role"] == "assistant":
                history.append({"role": "model", "parts": [m["content"]]})

        chat = gemini_model.start_chat(history=history)
        resp = await asyncio.to_thread(chat.send_message, last_user)
        usage = resp.usage_metadata
        return ModelResponse(
            content=resp.text,
            provider="gemini",
            model=model,
            tokens_in=usage.prompt_token_count if usage else 0,
            tokens_out=usage.candidates_token_count if usage else 0,
        )

    async def _ollama_generate(self, messages, model, temperature, max_tokens, system_prompt):
        all_messages = []
        if system_prompt:
            all_messages.append({"role": "system", "content": system_prompt})
        all_messages.extend(messages)

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/chat",
                json={"model": model, "messages": all_messages, "stream": False,
                      "options": {"temperature": temperature, "num_predict": max_tokens}},
            )
            resp.raise_for_status()
            data = resp.json()
        content = data.get("message", {}).get("content", "")
        return ModelResponse(
            content=content,
            provider="ollama",
            model=model,
            tokens_in=data.get("prompt_eval_count", 0),
            tokens_out=data.get("eval_count", 0),
        )


gateway = ModelGateway()
