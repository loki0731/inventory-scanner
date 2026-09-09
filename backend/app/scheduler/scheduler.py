import asyncio, logging
from datetime import datetime,timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from app.core.config import settings
from app.db.database import SessionLocal
from app.db.models import Asset
from app.services.scan_service import create_scan,execute_scan,shutdown_scan_tasks
log=logging.getLogger(__name__)
scheduler=AsyncIOScheduler(timezone="UTC")
async def scheduled_scan_pass():
    now=datetime.now(timezone.utc)
    async with SessionLocal() as db:
        assets=(await db.execute(select(Asset).where(Asset.enabled.is_(True)))).scalars().all()
        due=[a.id for a in assets if not a.last_scan_attempt_at or (now-a.last_scan_attempt_at).total_seconds()>=a.scan_interval]
    for asset_id in due:
        try:
            scan_id=await create_scan(asset_id); asyncio.create_task(execute_scan(scan_id))
        except Exception as exc: log.warning("scheduled scan skipped: %s",type(exc).__name__)
def start_scheduler(): scheduler.add_job(scheduled_scan_pass,"interval",seconds=settings.scheduler_interval,id="inventory-scheduler",replace_existing=True,coalesce=True,max_instances=1); scheduler.start()
def stop_scheduler():
    if scheduler.running: scheduler.shutdown(wait=False)

async def shutdown_scheduler_and_scans():
    stop_scheduler(); await shutdown_scan_tasks()
