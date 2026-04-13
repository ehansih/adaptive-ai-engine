from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from backend.db.database import get_db
from backend.db.models import User
from backend.services.memory_service import memory_service
from backend.services.security import get_current_user

router = APIRouter(prefix="/memory", tags=["memory"])


class MemoryStoreRequest(BaseModel):
    key: str
    value: str
    tags: list[str] = []
    source: str = "manual"


class MemorySearchRequest(BaseModel):
    query: str
    n_results: int = 5


@router.post("/")
async def store_memory(
    req: MemoryStoreRequest,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    entry = await memory_service.store(
        db=db,
        key=req.key,
        value=req.value,
        user_id=user.id if user else None,
        tags=req.tags,
        source=req.source,
    )
    return {"id": entry.id, "key": entry.key, "created_at": entry.created_at}


@router.get("/")
async def list_memory(
    tag: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    tags = [tag] if tag else None
    entries = await memory_service.retrieve(
        db=db,
        user_id=user.id if user else None,
        tags=tags,
        limit=limit,
    )
    return [
        {"id": e.id, "key": e.key, "value": e.value, "tags": e.tags,
         "source": e.source, "created_at": e.created_at, "updated_at": e.updated_at}
        for e in entries
    ]


@router.post("/search")
async def semantic_search(
    req: MemorySearchRequest,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    results = await memory_service.semantic_search(
        query=req.query,
        user_id=user.id if user else None,
        n_results=req.n_results,
    )
    return results


@router.delete("/{entry_id}")
async def delete_memory(
    entry_id: str,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    ok = await memory_service.delete(db=db, entry_id=entry_id,
                                     user_id=user.id if user else None)
    if not ok:
        raise HTTPException(status_code=404, detail="Memory entry not found")
    return {"status": "deleted"}


@router.get("/export")
async def export_memory(
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    data = await memory_service.export(db=db, user_id=user.id if user else None)
    return JSONResponse(content=data, headers={
        "Content-Disposition": "attachment; filename=memory_export.json"
    })
