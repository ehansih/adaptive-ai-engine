# Adaptive AI Engine

A secure, adaptive AI orchestration platform that integrates multiple AI providers, learns from user feedback, and stores portable local memory.

## Architecture

```
User → React UI → FastAPI → Security Layer → Adaptive Orchestrator
                                               ↓
                              OpenAI / Claude / Gemini / Ollama
                                               ↓
                              Response Filter → User → ★ Feedback
                                               ↓
                              Model Weights Updated → Memory Stored
```

## Features

| Feature | Details |
|---|---|
| **Multi-AI Gateway** | OpenAI, Anthropic Claude, Google Gemini, Local Ollama |
| **Adaptive Routing** | Feedback-driven model weights — best models get more traffic |
| **Feedback Loop** | 1-5 star rating + tags, triggers retry on low scores |
| **Local Memory** | SQLite + Chroma vector DB, portable via folder copy/export |
| **Security** | JWT auth, RBAC, prompt injection defense, rate limiting, audit log |
| **Cost Tracking** | Per-message USD cost, latency, token counts |
| **Strategy Control** | Adaptive / Round-robin / Cost-optimized routing |

## Quick Start

### 1. Clone & Configure

```bash
git clone https://github.com/ehansih/adaptive-ai-engine
cd adaptive-ai-engine
cp .env.example .env
# Edit .env — add at least one API key
```

### 2. Backend

```bash
cd adaptive-ai-engine
python -m venv venv && source venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

### 4. Or run both at once

```bash
chmod +x scripts/run_dev.sh
./scripts/run_dev.sh
```

### 5. Docker (all services)

```bash
cp .env.example .env   # edit API keys
docker compose up --build
# UI: http://localhost:5173
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

## Configuration

Edit `.env` (all options documented in `.env.example`):

```env
# Add at least one:
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AIza...

# Routing strategy (default: adaptive)
MODEL_SELECTION_STRATEGY=adaptive
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/auth/register` | Create account |
| `POST` | `/auth/login` | Get JWT token |
| `POST` | `/chat/` | Send message (auto-selects model) |
| `GET` | `/chat/sessions` | List chat sessions |
| `POST` | `/feedback/` | Rate a response (1-5 stars) |
| `GET` | `/feedback/stats` | Model performance metrics |
| `POST` | `/memory/` | Store a memory entry |
| `POST` | `/memory/search` | Semantic vector search |
| `GET` | `/memory/export` | Export all memory as JSON |
| `GET` | `/models/providers` | List configured providers |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Swagger UI |

## Adaptive Orchestrator Logic

```
1. Classify query type (code / math / creative / analysis / factual)
2. Look up historical model weights for that query type
3. Select best model (or round-robin / cost-optimized)
4. Apply system prompt tailored to query type
5. Generate response — retry with next model if quality check fails
6. Return response + metadata (cost, latency, tokens)
7. User rates response → weights updated for that provider/type
8. High-rated responses auto-stored as exemplars in memory
```

## Memory System

Memory is stored locally at `./memory/` and can be moved/copied between machines:

- `memory/chroma/` — vector embeddings (semantic search)
- `adaptive_ai.db` — SQLite (structured data, sessions, feedback)

Export via UI or `GET /memory/export`.

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy (async), aiosqlite / PostgreSQL
- **Frontend**: React 18, Vite, Tailwind CSS, Zustand, Recharts
- **Vector DB**: Chroma + sentence-transformers (all-MiniLM-L6-v2)
- **Cache**: Redis (optional)
- **Auth**: JWT (HS256), bcrypt, RBAC
- **Security**: slowapi rate limiting, prompt injection detection, audit logging

## Version History

### v1.0.0
- Initial release
- Multi-provider gateway: OpenAI, Claude, Gemini, Ollama
- Adaptive feedback-driven routing
- Local memory with vector search
- JWT auth, RBAC, audit logging
- React UI with metrics dashboard
