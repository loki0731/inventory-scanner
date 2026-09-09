from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_api_token
from app.db.database import get_session
from app.db.models import Asset, Credential
from app.schemas import (
    AssetCreate,
    AssetOut,
    AssetUpdate,
    Page,
    ScanCreateOut,
)
from app.services.scan_service import create_scan, execute_scan


router = APIRouter(
    prefix="/api/v1/assets",
    dependencies=[Depends(require_api_token)],
)


@router.get("", response_model=Page[AssetOut])
async def list_assets(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_session),
):
    total = await db.scalar(
        select(func.count()).select_from(Asset)
    )

    result = await db.execute(
        select(Asset)
        .order_by(Asset.id)
        .limit(limit)
        .offset(offset)
    )

    rows = result.scalars().all()

    return Page[AssetOut](
        items=[
            AssetOut.model_validate(asset)
            for asset in rows
        ],
        total=total or 0,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=AssetOut, status_code=201)
async def create_asset(
    data: AssetCreate,
    db: AsyncSession = Depends(get_session),
):
    if data.credential_id:
        credential = await db.get(
            Credential,
            data.credential_id,
        )

        if not credential:
            raise HTTPException(
                status_code=400,
                detail="Credential not found",
            )

    values = data.model_dump()

    values["ip_address"] = str(data.ip_address)

    obj = Asset(**values)

    db.add(obj)

    await db.commit()
    await db.refresh(obj)

    return AssetOut.model_validate(obj)


@router.get("/{asset_id}", response_model=AssetOut)
async def get_asset(
    asset_id: int,
    db: AsyncSession = Depends(get_session),
):
    obj = await db.get(Asset, asset_id)

    if not obj:
        raise HTTPException(
            status_code=404,
            detail="Asset not found",
        )

    return AssetOut.model_validate(obj)


@router.put("/{asset_id}", response_model=AssetOut)
async def update_asset(
    asset_id: int,
    data: AssetUpdate,
    db: AsyncSession = Depends(get_session),
):
    obj = await db.get(Asset, asset_id)

    if not obj:
        raise HTTPException(
            status_code=404,
            detail="Asset not found",
        )

    values = data.model_dump(exclude_unset=True)

    if (
        "credential_id" in values
        and values["credential_id"] is not None
    ):
        credential = await db.get(
            Credential,
            values["credential_id"],
        )

        if not credential:
            raise HTTPException(
                status_code=400,
                detail="Credential not found",
            )

    if (
        "ip_address" in values
        and values["ip_address"] is not None
    ):
        values["ip_address"] = str(values["ip_address"])

    for key, value in values.items():
        setattr(obj, key, value)

    await db.commit()
    await db.refresh(obj)

    return AssetOut.model_validate(obj)


@router.delete("/{asset_id}", status_code=204)
async def delete_asset(
    asset_id: int,
    db: AsyncSession = Depends(get_session),
):
    obj = await db.get(Asset, asset_id)

    if not obj:
        raise HTTPException(
            status_code=404,
            detail="Asset not found",
        )

    await db.delete(obj)
    await db.commit()

    return None


@router.post(
    "/{asset_id}/scan",
    response_model=ScanCreateOut,
    status_code=202,
)
async def manual_scan(
    asset_id: int,
    bg: BackgroundTasks,
    db: AsyncSession = Depends(get_session),
):
    asset = await db.get(Asset, asset_id)

    if not asset:
        raise HTTPException(
            status_code=404,
            detail="Asset not found",
        )

    try:
        scan_id = await create_scan(asset_id)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    bg.add_task(
        execute_scan,
        scan_id,
    )

    return ScanCreateOut(
        asset_id=asset_id,
        scan_id=scan_id,
        status="QUEUED",
    )


@router.post(
    "/{asset_id}/enable",
    response_model=AssetOut,
)
async def set_enabled(
    asset_id: int,
    db: AsyncSession = Depends(get_session),
):
    obj = await db.get(Asset, asset_id)

    if not obj:
        raise HTTPException(
            status_code=404,
            detail="Asset not found",
        )

    obj.enabled = True

    await db.commit()
    await db.refresh(obj)

    return AssetOut.model_validate(obj)


@router.post(
    "/{asset_id}/disable",
    response_model=AssetOut,
)
async def set_disabled(
    asset_id: int,
    db: AsyncSession = Depends(get_session),
):
    obj = await db.get(Asset, asset_id)

    if not obj:
        raise HTTPException(
            status_code=404,
            detail="Asset not found",
        )

    obj.enabled = False

    await db.commit()
    await db.refresh(obj)

    return AssetOut.model_validate(obj)