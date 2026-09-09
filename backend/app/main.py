"""
FastAPI приложение для сканирования инвентаря активов.

Управляет жизненным циклом приложения, регистрирует маршруты API
и предоставляет health check endpoints.
"""

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI

from app.core.logging import configure_logging
from app.db.database import engine
from app.api.assets import router as assets_router
from app.api.credentials import router as credentials_router
from app.api.scans import router as scans_router
from app.api.inventory import router as inventory_router
from app.api.dashboard import router as dashboard_router
from app.api.audit import router as audit_router
from app.scheduler.scheduler import (
    start_scheduler,
    shutdown_scheduler_and_scans,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управляет жизненным циклом приложения.
    
    Инициализирует логирование и планировщик при старте,
    корректно завершает работу при остановке.
    """
    try:
        logger.info("Starting application")
        configure_logging()
        start_scheduler()
        logger.info("Scheduler started successfully")
        yield
    finally:
        try:
            logger.info("Shutting down application")
            await shutdown_scheduler_and_scans()
            logger.info("Scheduler shutdown complete")
        except Exception as e:
            logger.error(f"Error during scheduler shutdown: {e}", exc_info=True)
        finally:
            try:
                await engine.dispose()
                logger.info("Database engine disposed")
            except Exception as e:
                logger.error(f"Error disposing database engine: {e}", exc_info=True)


# Создание FastAPI приложения
app = FastAPI(
    title="Independent Credentialed Asset Inventory Scanner",
    version="1.0.0",
    description="Сканирует инвентарь активов на Linux (SSH) и Windows (WinRM)",
    lifespan=lifespan,
)

# Регистрация маршрутов
routers = [
    assets_router,
    credentials_router,
    scans_router,
    inventory_router,
    dashboard_router,
    audit_router,
]

for router in routers:
    app.include_router(router)


@app.get("/health", tags=["Health"])
async def health() -> Dict[str, str]:
    """
    Проверка здоровья приложения.
    
    Возвращает статус "ok" если приложение работает.
    Эта проверка НЕ проверяет подключение к БД.
    """
    return {"status": "ok"}


@app.get("/ready", tags=["Health"])
async def ready() -> Dict[str, str]:
    """
    Проверка готовности приложения к работе.
    
    Проверяет подключение к БД. Возвращает статус "ready"
    если приложение готово обрабатывать запросы.
    
    Raises:
        Exception: Если не удается подключиться к БД
    """
    try:
        async with engine.connect() as conn:
            await conn.exec_driver_sql("SELECT 1")
        logger.debug("Database health check passed")
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Database health check failed: {e}", exc_info=True)
        raise
