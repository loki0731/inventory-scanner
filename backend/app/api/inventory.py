import csv,io
from fastapi import APIRouter,Depends,HTTPException,Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func,select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.auth import require_api_token
from app.db.database import get_session
from app.db.models import Asset,InventoryEvent,InventorySnapshot,Software
router=APIRouter(prefix="/api/v1",dependencies=[Depends(require_api_token)])
async def _asset(db,asset_id):
    obj=await db.get(Asset,asset_id)
    if not obj: raise HTTPException(404,"Asset not found")
    return obj
async def _latest(db,asset_id): return (await db.execute(select(InventorySnapshot).where(InventorySnapshot.asset_id==asset_id).order_by(InventorySnapshot.id.desc()).limit(1))).scalar_one_or_none()
@router.get("/assets/{asset_id}/inventory")
async def inventory(asset_id:int,db:AsyncSession=Depends(get_session)):
    await _asset(db,asset_id); row=await _latest(db,asset_id); return row.payload if row else {"schema_version":"1.0","software":[]}
@router.get("/assets/{asset_id}/inventory/history")
async def history(asset_id:int,limit:int=Query(100,ge=1,le=1000),offset:int=Query(0,ge=0),db:AsyncSession=Depends(get_session)):
    await _asset(db,asset_id); q=select(InventoryEvent).where(InventoryEvent.asset_id==asset_id); total=await db.scalar(select(func.count()).select_from(InventoryEvent).where(InventoryEvent.asset_id==asset_id)); rows=(await db.execute(q.order_by(InventoryEvent.occurred_at.desc()).limit(limit).offset(offset))).scalars().all(); return {"items":[{"id":x.id,"scan_id":x.scan_id,"event_type":x.event_type,"name":x.name,"old_version":x.old_version,"new_version":x.new_version,"source":x.source,"occurred_at":x.occurred_at} for x in rows],"total":total or 0,"limit":limit,"offset":offset}
@router.get("/assets/{asset_id}/inventory.json")
async def inventory_json(asset_id:int,db:AsyncSession=Depends(get_session)): return await inventory(asset_id,db)
@router.get("/exports/assets/{asset_id}.json")
async def export_json(asset_id:int,db:AsyncSession=Depends(get_session)): return await inventory(asset_id,db)
@router.get("/exports/assets/{asset_id}.csv")
async def export_csv(asset_id:int,db:AsyncSession=Depends(get_session)):
    await _asset(db,asset_id); rows=(await db.execute(select(Software).where(Software.asset_id==asset_id,Software.active.is_(True)).order_by(Software.name))).scalars().all(); buf=io.StringIO(); w=csv.writer(buf); w.writerow(["name","version","vendor","source","package_source","ecosystem","architecture","first_seen","last_seen"])
    for x in rows:w.writerow([x.name,x.version,x.vendor,x.source,x.package_source,x.ecosystem,x.architecture,x.first_seen.isoformat(),x.last_seen.isoformat()])
    return StreamingResponse(iter([buf.getvalue()]),media_type="text/csv",headers={"Content-Disposition":f"attachment; filename=asset-{asset_id}-inventory.csv"})
