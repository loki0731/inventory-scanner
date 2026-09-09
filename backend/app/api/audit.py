from fastapi import APIRouter,Depends,Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.auth import require_api_token
from app.db.database import get_session
from app.db.models import AuditEvent
router=APIRouter(prefix="/api/v1/audit",dependencies=[Depends(require_api_token)])
@router.get("")
async def audit_log(limit:int=Query(100,ge=1,le=500),offset:int=Query(0,ge=0),db:AsyncSession=Depends(get_session)):
    rows=(await db.execute(select(AuditEvent).order_by(AuditEvent.id.desc()).limit(limit).offset(offset))).scalars().all(); return [{"id":x.id,"occurred_at":x.occurred_at,"action":x.action,"resource_type":x.resource_type,"resource_id":x.resource_id,"outcome":x.outcome,"details":x.details} for x in rows]
