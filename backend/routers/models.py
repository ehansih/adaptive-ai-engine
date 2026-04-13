from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.database import get_db
from backend.db.models import User
from backend.services.gateway import gateway
from backend.services.security import get_current_user

router = APIRouter(prefix="/models", tags=["models"])


@router.get("/providers")
async def list_providers(user=Depends(get_current_user)):
    return gateway.available_providers()


@router.get("/health")
async def model_health():
    """Quick check of which providers are configured."""
    providers = gateway.available_providers()
    return {
        "configured_providers": len(providers),
        "providers": [p["id"] for p in providers],
        "status": "ready" if providers else "no_providers_configured",
    }
