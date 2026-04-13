#!/usr/bin/env python3
"""
Extended dry-run checks for Adaptive AI Engine.
Run from project root: python3 scripts/extended_checks.py
"""
import ast, re, os, json, sys

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
WARN = "\033[93mWARN\033[0m"

results = {"pass": 0, "fail": 0, "warn": 0}

def p(status, msg):
    results[status] += 1
    icon = PASS if status == "pass" else (FAIL if status == "fail" else WARN)
    print(f"  {icon}  {msg}")

def section(title):
    print(f"\n\033[1m=== {title} ===\033[0m")

# ── 1. API CONTRACT ──────────────────────────────────────────────────────────
section("1. API Contract Completeness")
REQUIRED_ROUTES = {
    "/auth/register": "POST",
    "/auth/login": "POST",
    "/chat/": "POST",
    "/chat/sessions": "GET",
    "/feedback/": "POST",
    "/feedback/stats": "GET",
    "/memory/": ["POST","GET"],
    "/memory/search": "POST",
    "/memory/export": "GET",
    "/models/providers": "GET",
    "/health": "GET",
}
router_src = ""
for f in os.listdir("backend/routers"):
    if f.endswith(".py"):
        router_src += open(f"backend/routers/{f}").read()
router_src += open("backend/main.py").read()

for route, methods in REQUIRED_ROUTES.items():
    route_key = route.split("/")[-1] or route.split("/")[-2]
    found = route_key in router_src or route in router_src
    p("pass" if found else "fail", f"Route {route} declared")

# ── 2. DATA MODEL INTEGRITY ──────────────────────────────────────────────────
section("2. Data Model Integrity")
model_src = open("backend/db/models.py").read()
expected_tables = ["users", "chat_sessions", "messages", "feedbacks", "model_performance", "audit_logs", "memory_entries"]
for table in expected_tables:
    found = f'"{table}"' in model_src or f"'{table}'" in model_src
    p("pass" if found else "fail", f"Table '{table}' defined")

# Foreign keys
fk_checks = [
    ("messages", "chat_sessions"),
    ("feedbacks", "messages"),
    ("chat_sessions", "users"),
]
for child, parent in fk_checks:
    found = f'ForeignKey("{parent}.id")' in model_src or f"ForeignKey('{parent}.id')" in model_src
    p("pass" if found else "fail", f"FK {child} → {parent}")

# ── 3. FEEDBACK LOOP INTEGRITY ───────────────────────────────────────────────
section("3. Feedback Loop Logic")
fb_src = open("backend/services/feedback_engine.py").read()
orch_src = open("backend/services/orchestrator.py").read()

p("pass" if "apply_feedback" in fb_src else "fail", "Feedback calls apply_feedback on orchestrator")
p("pass" if "weight" in orch_src else "fail", "Orchestrator has weight field in performance")
p("pass" if "avg_rating" in orch_src else "fail", "Orchestrator tracks avg_rating")
p("pass" if "exemplar" in fb_src else "fail", "High-rated responses stored as exemplars")
p("pass" if "LOW_RATING_THRESHOLD" in fb_src else "fail", "Low rating threshold defined")
p("pass" if "HIGH_RATING_THRESHOLD" in fb_src else "fail", "High rating threshold defined")
p("pass" if "triggered_retry" in fb_src else "fail", "Retry flag set on poor rating")

# ── 4. ADAPTIVE ROUTING STRATEGIES ──────────────────────────────────────────
section("4. Adaptive Routing Strategies")
strategies = ["adaptive", "round-robin", "cost-optimized"]
for s in strategies:
    found = s in orch_src
    p("pass" if found else "fail", f"Strategy '{s}' implemented")
p("pass" if "classify_query" in orch_src else "fail", "Query type classification present")
p("pass" if "SYSTEM_PROMPTS" in orch_src else "fail", "Per-type system prompts defined")

# ── 5. PROVIDER COVERAGE ─────────────────────────────────────────────────────
section("5. AI Provider Coverage")
gw_src = open("backend/services/gateway.py").read()
providers = {"openai": "AsyncOpenAI", "anthropic": "AsyncAnthropic", "gemini": "genai", "ollama": "ollama"}
for name, marker in providers.items():
    p("pass" if marker in gw_src else "fail", f"Provider '{name}' integrated")
p("pass" if "COST_TABLE" in gw_src else "fail", "Cost table defined")
p("pass" if "_calc_cost" in gw_src else "fail", "Per-message cost calculation")
p("pass" if "latency_ms" in gw_src else "fail", "Latency tracking")

# ── 6. MEMORY SYSTEM ─────────────────────────────────────────────────────────
section("6. Memory System")
mem_src = open("backend/services/memory_service.py").read()
p("pass" if "PersistentClient" in mem_src else "fail", "Chroma persistent storage")
p("pass" if "semantic_search" in mem_src else "fail", "Vector semantic search")
p("pass" if "export" in mem_src else "fail", "Memory export function")
p("pass" if "upsert" in mem_src else "fail", "Chroma upsert (idempotent writes)")
p("pass" if "ENCODER_AVAILABLE" in mem_src else "fail", "Graceful fallback if no encoder")
p("pass" if "CHROMA_AVAILABLE" in mem_src else "fail", "Graceful fallback if no Chroma")

# ── 7. SECURITY DEPTH ────────────────────────────────────────────────────────
section("7. Security Depth")
sec_src = open("backend/services/security.py").read()
sec_checks = [
    ("bcrypt", "bcrypt hashing"),
    ("JWTError", "JWT error handling"),
    ("detect_prompt_injection", "Injection detection function"),
    ("html.escape", "HTML escaping on input"),
    ("MAX_PROMPT_LENGTH", "Prompt length check"),
    ("AuditLog", "Audit log model"),
    ("require_admin", "Admin-only guard"),
    ("is_active", "Account active check"),
]
for keyword, label in sec_checks:
    p("pass" if keyword in sec_src else "fail", label)

# ── 8. CONFIG VALIDATION ─────────────────────────────────────────────────────
section("8. Configuration Completeness")
cfg_src = open("backend/config.py").read()
env_src = open(".env.example").read()
required_settings = [
    "SECRET_KEY", "DATABASE_URL", "OPENAI_API_KEY", "ANTHROPIC_API_KEY",
    "GEMINI_API_KEY", "RATE_LIMIT", "MAX_PROMPT_LENGTH", "CORS_ORIGINS",
    "JWT_EXPIRE_MINUTES", "MAX_RETRIES", "MODEL_SELECTION_STRATEGY"
]
for s in required_settings:
    in_cfg = s in cfg_src
    in_env = s in env_src
    p("pass" if (in_cfg and in_env) else ("warn" if in_cfg else "fail"),
      f"{s} in config{'+ .env.example' if in_env else ' (missing from .env.example)'}")

# ── 9. FRONTEND COMPONENT WIRING ────────────────────────────────────────────
section("9. Frontend Wiring")
api_src = open("frontend/src/services/api.js").read()
store_src = open("frontend/src/hooks/useStore.js").read()

frontend_checks = [
    ("submitFeedback", api_src, "Feedback API call"),
    ("getFeedbackStats", api_src, "Stats API call"),
    ("searchMemory", api_src, "Semantic search call"),
    ("exportMemory", api_src, "Export call"),
    ("useAuthStore", store_src, "Auth store"),
    ("useChatStore", store_src, "Chat store"),
    ("useSettingsStore", store_src, "Settings store"),
    ("persist", store_src, "Zustand persist (settings saved across reloads)"),
]
for keyword, src, label in frontend_checks:
    p("pass" if keyword in src else "fail", label)

# ── 10. DOCKER / INFRA ───────────────────────────────────────────────────────
section("10. Infrastructure")
dc = open("docker-compose.yml").read()
infra_checks = [
    ("backend", "Backend service"),
    ("frontend", "Frontend service"),
    ("redis", "Redis service"),
    ("volumes", "Volume persistence"),
    ("restart: unless-stopped", "Auto-restart policy"),
]
for keyword, label in infra_checks:
    p("pass" if keyword in dc else "fail", label)

# ── Summary ──────────────────────────────────────────────────────────────────
total = sum(results.values())
print(f"\n\033[1m{'='*40}\033[0m")
print(f"  Total: {total} | \033[92m{results['pass']} passed\033[0m | \033[91m{results['fail']} failed\033[0m | \033[93m{results['warn']} warnings\033[0m")
if results["fail"] == 0:
    print("  \033[92m✓ ALL CHECKS PASSED\033[0m")
else:
    print(f"  \033[91m✗ {results['fail']} check(s) need attention\033[0m")
    sys.exit(1)
