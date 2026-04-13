"""Security layer: input validation, prompt injection defense, rate limiting, JWT auth."""
import re
import html
import hashlib
import time
from typing import Optional
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.config import settings
from backend.db.database import get_db
from backend.db.models import User, AuditLog

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)

# --- Prompt injection patterns -------------------------------------------------
INJECTION_PATTERNS = [
    r"ignore\s+(previous|all|above)\s+instructions",
    r"disregard\s+(your|the)\s+(instructions|rules|guidelines)",
    r"you\s+are\s+now\s+(a|an)\s+\w+\s*(AI|assistant|model)?",
    r"pretend\s+you\s+(are|have\s+no)",
    r"act\s+as\s+(if\s+you\s+(are|were)|a\s+jailbroken)",
    r"DAN\s*mode",
    r"developer\s+mode",
    r"jailbreak",
    r"<\s*script[^>]*>",
    r"(system\s*:|SYSTEM\s*:)\s*(you|ignore|forget)",
    r"\[\s*INST\s*\]",
]
_compiled_patterns = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


def detect_prompt_injection(text: str) -> bool:
    for pattern in _compiled_patterns:
        if pattern.search(text):
            return True
    return False


def sanitize_input(text: str) -> str:
    text = html.escape(text.strip())
    if len(text) > settings.MAX_PROMPT_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Prompt exceeds maximum length of {settings.MAX_PROMPT_LENGTH} characters",
        )
    if detect_prompt_injection(text):
        raise HTTPException(
            status_code=400,
            detail="Potential prompt injection detected. Please rephrase your request.",
        )
    return text


# --- Password utils ------------------------------------------------------------
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# --- JWT utils ----------------------------------------------------------------
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# --- Auth dependency ----------------------------------------------------------
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    if not credentials:
        return None
    payload = decode_token(credentials.credentials)
    user_id: str = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


async def require_user(
    user: Optional[User] = Depends(get_current_user),
) -> User:
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


async def require_admin(user: User = Depends(require_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# --- Audit logging ------------------------------------------------------------
async def audit(
    db: AsyncSession,
    event_type: str,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    details: Optional[dict] = None,
):
    if not settings.ENABLE_AUDIT_LOG:
        return
    entry = AuditLog(
        event_type=event_type,
        user_id=user_id,
        ip_address=ip_address,
        details=details or {},
    )
    db.add(entry)
    await db.commit()


# --- API key hash helper -------------------------------------------------------
def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()
