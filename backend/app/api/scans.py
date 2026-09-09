from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_api_token
from app.db.database import get_session
from app.db.models import Scan
from app.schemas import Page, ScanOut
from app.services.scan_service import cancel_scan


router = APIRouter(
    prefix="/api/v1/scans",
    dependencies=[Depends(require_api_token)],
)


@router.get("", response_model=Page[ScanOut])
async def scans(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    status: str | None = None,
    asset_id: int | None = None,
    db: AsyncSession = Depends(get_session),
):
    query = select(Scan)
    count_query = select(func.count()).select_from(Scan)

    if status:
        query = query.where(Scan.status == status)
        count_query = count_query.where(Scan.status == status)

    if asset_id is not None:
        query = query.where(Scan.asset_id == asset_id)
        count_query = count_query.where(Scan.asset_id == asset_id)

    total = await db.scalar(count_query)

    result = await db.execute(
        query
        .order_by(Scan.id.desc())
        .limit(limit)
        .offset(offset)
    )

    rows = result.scalars().all()

    return Page[ScanOut](
        items=[
            ScanOut.model_validate(scan)
            for scan in rows
        ],
        total=total or 0,
        limit=limit,
        offset=offset,
    )


@router.get("/{scan_id}", response_model=ScanOut)
async def get_scan(
    scan_id: int,
    db: AsyncSession = Depends(get_session),
):
    obj = await db.get(Scan, scan_id)

    if not obj:
        raise HTTPException(
            status_code=404,
            detail="Scan not found",
        )

    return ScanOut.model_validate(obj)


@router.post("/{scan_id}/cancel", response_model=ScanOut)
async def cancel(
    scan_id: int,
    db: AsyncSession = Depends(get_session),
):
    obj = await db.get(Scan, scan_id)

    if not obj:
        raise HTTPException(
            status_code=404,
            detail="Scan not found",
        )

    if obj.status not in {"QUEUED", "RUNNING"}:
        raise HTTPException(
            status_code=409,
            detail="Scan is already finished",
        )

    await cancel_scan(scan_id)

    await db.refresh(obj)

    return ScanOut.model_validate(obj)