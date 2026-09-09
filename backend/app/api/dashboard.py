from fastapi import APIRouter,Depends
from sqlalchemy import func,select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.auth import require_api_token
from app.db.database import get_session
from app.db.models import Asset,Scan,Software
from app.schemas import DashboardOut
router=APIRouter(prefix="/api/v1/dashboard",dependencies=[Depends(require_api_token)])
@router.get("",response_model=DashboardOut)
async def dashboard(db:AsyncSession=Depends(get_session)):
    total=await db.scalar(select(func.count()).select_from(Asset)) or 0
    never=await db.scalar(select(func.count()).select_from(Asset).where(Asset.last_scan_at.is_(None))) or 0
    failed=await db.scalar(select(func.count()).select_from(Asset).where(Asset.last_scan_status.in_(["AUTH_FAILED","UNREACHABLE","TIMEOUT","FAILED","CANCELLED"]))) or 0
    healthy=max(0,total-never-failed)
    sw=await db.scalar(select(func.count()).select_from(Software).where(Software.active.is_(True))) or 0
    last=await db.scalar(select(func.max(Scan.finished_at)).where(Scan.status.in_(["SUCCESS","PARTIAL_SUCCESS"])))
    return DashboardOut(total_assets=total,healthy_assets=healthy,failed_assets=failed,never_scanned=never,total_software=sw,last_scan_at=last)
