"""
Сервис для управления сканированием активов.

Включает функции для создания, запуска, отмены и управления скан-задачами.
Поддерживает асинхронное сканирование Linux (SSH) и Windows (WinRM) хостов.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Optional, Set

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decrypt_secret
from app.db.database import SessionLocal
from app.db.models import (
    Asset,
    Credential,
    InventoryEvent,
    InventorySnapshot,
    Scan,
    Software,
)
from app.domain.inventory import RawInventory
from app.connections.ssh import SSHConnection
from app.connections.winrm import WinRMConnection
from app.connections.base import Connection
from app.collectors.linux.system import LinuxSystemCollector
from app.collectors.linux.dpkg import DpkgCollector
from app.collectors.linux.rpm import RpmCollector
from app.collectors.windows.system import WindowsSystemCollector
from app.collectors.windows.registry import WindowsRegistryCollector
from app.collectors.windows.updates import WindowsUpdateCollector
from app.normalization.normalizer import (
    normalize,
    diff_inventory,
    fingerprint,
)
from app.services.audit import audit
from app.services.errors import classify_error

logger = logging.getLogger(__name__)

# Управление параллельными скан-задачами
_scan_semaphore = asyncio.Semaphore(settings.max_concurrent_scans)
_active_scan_tasks: Dict[int, asyncio.Task] = {}
_asset_locks: Dict[int, asyncio.Lock] = {}

# Статусы сканирования
TERMINAL_STATUSES = {
    "SUCCESS",
    "PARTIAL_SUCCESS",
    "AUTH_FAILED",
    "UNREACHABLE",
    "TIMEOUT",
    "FAILED",
    "CANCELLED",
}
ACTIVE_STATUSES = {"QUEUED", "RUNNING"}


class ScanFailure(Exception):
    """Исключение для контролируемых ошибок сканирования."""

    def __init__(self, status: str, message: str) -> None:
        """
        Args:
            status: Статус сканирования (AUTH_FAILED, UNREACHABLE, etc)
            message: Описание ошибки
        """
        self.status = status
        self.message = message
        super().__init__(message)


async def create_scan(asset_id: int) -> int:
    """
    Создает новую задачу сканирования для актива.
    
    Проверяет что актив существует и что для него нет активного сканирования.
    Использует блокировку на уровне актива для избежания race conditions.
    
    Args:
        asset_id: ID актива для сканирования
        
    Returns:
        ID созданной задачи сканирования
        
    Raises:
        ValueError: Если актив не найден
        RuntimeError: Если для актива уже есть активное сканирование
    """
    logger.debug(f"Creating scan for asset {asset_id}")
    
    # Получаем или создаем lock для актива
    lock = _asset_locks.setdefault(asset_id, asyncio.Lock())
    
    async with lock:
        async with SessionLocal() as db:
            # Проверяем что актив существует
            asset = await db.get(Asset, asset_id)
            if not asset:
                logger.error(f"Asset {asset_id} not found")
                raise ValueError(f"Asset {asset_id} not found")
            
            # Проверяем что нет активного сканирования
            active_scan = (
                await db.execute(
                    select(Scan).where(
                        Scan.asset_id == asset_id,
                        Scan.status.in_(ACTIVE_STATUSES),
                    ).limit(1)
                )
            ).scalar_one_or_none()
            
            if active_scan:
                logger.warning(
                    f"Asset {asset_id} already has active scan {active_scan.id}"
                )
                raise RuntimeError(
                    f"Asset {asset_id} already has active scan {active_scan.id}"
                )
            
            # Создаем новое сканирование
            scan = Scan(asset_id=asset_id, status="QUEUED")
            db.add(scan)
            await db.flush()
            
            logger.info(f"Scan {scan.id} created for asset {asset_id}")
            await audit(db, "scan.created", "scan", scan.id)
            await db.commit()
            
            return scan.id


async def _get_linux_collectors(
    raw_inventory: RawInventory,
) -> list:
    """
    Определяет какие сборщики пакетов использовать для Linux.
    
    Args:
        raw_inventory: Объект с информацией системы
        
    Returns:
        Список инстансов сборщиков пакетов
    """
    os_vendor = raw_inventory.system.os_vendor.lower()
    
    if os_vendor in {"debian", "ubuntu", "linuxmint"}:
        logger.debug(f"Using DpkgCollector for {os_vendor}")
        return [DpkgCollector()]
    else:
        logger.debug(f"Using RpmCollector for {os_vendor}")
        return [RpmCollector()]


async def _run_collector(
    collector,
    connection: Connection,
    raw_inventory: RawInventory,
) -> None:
    """
    Запускает одного сборщика данных с timeout.
    
    Args:
        collector: Инстанс сборщика
        connection: Объект соединения (SSH/WinRM)
        raw_inventory: Объект для накопления данных
        
    Raises:
        asyncio.TimeoutError: Если сборщик работает дольше timeout
    """
    logger.debug(f"Running collector {collector.name}")
    try:
        await asyncio.wait_for(
            collector.collect(connection, raw_inventory),
            settings.command_timeout,
        )
        logger.debug(f"Collector {collector.name} completed successfully")
    except asyncio.TimeoutError:
        logger.error(f"Collector {collector.name} timed out")
        raise


async def _collect_linux_inventory(
    asset: Asset,
    credential: Credential,
    connection: SSHConnection,
    raw_inventory: RawInventory,
) -> tuple[int, int]:
    """
    Собирает инвентарь Linux хоста.
    
    Args:
        asset: Объект актива
        credential: Объект учетных данных
        connection: SSH соединение
        raw_inventory: Объект для накопления данных
        
    Returns:
        Кортеж (успешно_собрано, ошибки)
        
    Raises:
        ScanFailure: Если сборка системной информации не удалась
    """
    logger.info(f"Starting Linux inventory collection for asset {asset.id}")
    ok = 0
    failed = 0
    
    try:
        # Сначала собираем системную информацию
        system_collector = LinuxSystemCollector()
        await _run_collector(system_collector, connection, raw_inventory)
        ok += 1
    except Exception as exc:
        logger.error(f"System collector failed: {exc}", exc_info=True)
        raise ScanFailure("FAILED", f"Failed to collect system info: {str(exc)[:500]}")
    
    # Затем пытаемся собрать пакеты (не критично если не получится)
    try:
        package_collectors = await _get_linux_collectors(raw_inventory)
        for pkg_collector in package_collectors:
            try:
                await _run_collector(pkg_collector, connection, raw_inventory)
                ok += 1
            except Exception as exc:
                logger.warning(
                    f"Package collector {pkg_collector.name} failed: {exc}"
                )
                failed += 1
                raw_inventory.collector_errors.append({
                    "collector": pkg_collector.name,
                    "error": classify_error(exc),
                })
    except Exception as exc:
        logger.warning(f"Failed to setup package collectors: {exc}")
        failed += 1
    
    return ok, failed


async def _collect_windows_inventory(
    asset: Asset,
    credential: Credential,
    connection: WinRMConnection,
    raw_inventory: RawInventory,
) -> tuple[int, int]:
    """
    Собирает инвентарь Windows хоста.
    
    Args:
        asset: Объект актива
        credential: Объект учетных данных
        connection: WinRM соединение
        raw_inventory: Объект для накопления данных
        
    Returns:
        Кортеж (успешно_собрано, ошибки)
    """
    logger.info(f"Starting Windows inventory collection for asset {asset.id}")
    ok = 0
    failed = 0
    
    collectors = [
        WindowsSystemCollector(),
        WindowsRegistryCollector(),
        WindowsUpdateCollector(),
    ]
    
    for collector in collectors:
        try:
            await _run_collector(collector, connection, raw_inventory)
            ok += 1
        except Exception as exc:
            logger.warning(
                f"Windows collector {collector.name} failed for asset {asset.id}: {exc}"
            )
            failed += 1
            raw_inventory.collector_errors.append({
                "collector": collector.name,
                "error": classify_error(exc),
            })
    
    return ok, failed


async def run_scan(scan_id: int) -> str:
    """
    Выполняет сканирование актива.
    
    Это основной метод сканирования. Он:
    1. Проверяет статус сканирования
    2. Получает учетные данные
    3. Подключается к хосту
    4. Собирает инвентарь
    5. Обновляет БД
    6. Записывает аудит
    
    Args:
        scan_id: ID задачи сканирования
        
    Returns:
        Финальный статус сканирования
    """
    # Ограничиваем количество параллельных сканов
    async with _scan_semaphore:
        async with SessionLocal() as db:
            scan = await db.get(Scan, scan_id)
            if not scan:
                logger.error(f"Scan {scan_id} not found")
                return "FAILED"
            
            asset = await db.get(Asset, scan.asset_id)
            if not asset:
                logger.error(f"Asset {scan.asset_id} not found for scan {scan_id}")
                scan.status = "FAILED"
                scan.error = "Asset not found"
                scan.finished_at = datetime.now(timezone.utc)
                await db.commit()
                return "FAILED"
            
            # Если статус не активный, возвращаем его как есть
            if scan.status not in ACTIVE_STATUSES:
                logger.debug(f"Scan {scan_id} has status {scan.status}, skipping")
                return scan.status
            
            # Начинаем сканирование
            started = datetime.now(timezone.utc)
            scan.started_at = started
            scan.status = "RUNNING"
            asset.last_scan_attempt_at = started
            asset.last_scan_status = "RUNNING"
            await db.commit()
            
            logger.info(f"Starting scan {scan_id} for asset {asset.id}")
            
            connection: Optional[Connection] = None
            raw_inventory = RawInventory()
            ok = 0
            failed = 0
            
            try:
                # Проверяем учетные данные
                if not asset.credential_id:
                    raise ScanFailure("AUTH_FAILED", "No credential assigned to asset")
                
                credential = await db.get(Credential, asset.credential_id)
                if not credential:
                    raise ScanFailure("AUTH_FAILED", "Assigned credential not found")
                
                secret = decrypt_secret(credential.encrypted_secret)
                credential.last_used_at = started
                
                # Собираем инвентарь в зависимости от платформы
                if asset.platform == "linux":
                    await _run_linux_scan(
                        asset, credential, secret, raw_inventory
                    )
                    ok, failed = await _collect_linux_inventory(
                        asset, credential, connection, raw_inventory
                    )
                
                elif asset.platform == "windows":
                    connection = _create_winrm_connection(asset, credential, secret)
                    await connection.connect()
                    ok, failed = await _collect_windows_inventory(
                        asset, credential, connection, raw_inventory
                    )
                
                else:
                    raise ScanFailure("FAILED", f"Unsupported platform: {asset.platform}")
                
                # Проверяем что система информация собрана
                if not raw_inventory.system.hostname:
                    raise ScanFailure("FAILED", "System collector returned no hostname")
                
                # Обновляем статус
                status = "PARTIAL_SUCCESS" if failed else "SUCCESS"
                finished = datetime.now(timezone.utc)
                
                # Нормализуем данные
                payload = normalize(
                    raw_inventory,
                    scan_id=scan.id,
                    started_at=started,
                    finished_at=finished,
                    status=status,
                )
                fp = fingerprint(payload)
                
                # Получаем предыдущий снимок
                previous = (
                    await db.execute(
                        select(InventorySnapshot)
                        .where(InventorySnapshot.asset_id == asset.id)
                        .order_by(InventorySnapshot.id.desc())
                        .limit(1)
                    )
                ).scalar_one_or_none()
                
                # Обновляем инвентарь только при успешном сканировании
                if status == "SUCCESS":
                    logger.info(f"Scan {scan_id} successful, updating inventory")
                    
                    # Создаем события изменений
                    for event in diff_inventory(
                        previous.payload if previous else None, payload
                    ):
                        db.add(InventoryEvent(
                            asset_id=asset.id,
                            scan_id=scan.id,
                            **event
                        ))
                    
                    # Обновляем текущий инвентарь
                    await _upsert_current_inventory(db, asset.id, payload["software"])
                    
                    # Сохраняем снимок
                    db.add(InventorySnapshot(
                        asset_id=asset.id,
                        scan_id=scan.id,
                        fingerprint=fp,
                        payload=payload,
                    ))
                    
                    asset.last_scan_at = finished
                    asset.inventory_fingerprint = fp
                
                # Обновляем статус сканирования
                scan.status = status
                scan.software_count = len(payload.get("software", []))
                scan.collectors_ok = ok
                scan.collectors_failed = failed
                scan.finished_at = finished
                asset.last_scan_status = status
                
                if status == "PARTIAL_SUCCESS":
                    scan.error = (
                        "One or more collectors failed; "
                        "last-known-good inventory preserved"
                    )
                
                await audit(
                    db,
                    "scan.completed",
                    "scan",
                    scan.id,
                    details={
                        "status": status,
                        "software_count": len(payload.get("software", [])),
                        "collectors_ok": ok,
                        "collectors_failed": failed,
                    },
                )
                
                logger.info(
                    f"Scan {scan_id} completed with status {status}, "
                    f"found {len(payload.get('software', []))} software items"
                )
                
            except ScanFailure as exc:
                logger.warning(
                    f"Scan {scan_id} failed with status {exc.status}: {exc.message}"
                )
                scan.status = exc.status
                scan.error = exc.message[:4000]
                scan.finished_at = datetime.now(timezone.utc)
                scan.collectors_ok = ok
                scan.collectors_failed = failed
                asset.last_scan_status = exc.status
                await audit(
                    db,
                    "scan.failed",
                    "scan",
                    scan.id,
                    outcome="failure",
                    details={"status": exc.status},
                )
            
            except asyncio.CancelledError:
                logger.info(f"Scan {scan_id} was cancelled")
                scan.status = "CANCELLED"
                scan.error = "Scan cancelled"
                scan.finished_at = datetime.now(timezone.utc)
                asset.last_scan_status = "CANCELLED"
                await db.commit()
                raise
            
            except Exception as exc:
                status = classify_error(exc)
                logger.error(
                    f"Scan {scan_id} failed with unexpected error: {exc}",
                    exc_info=True,
                )
                scan.status = status
                scan.error = f"{type(exc).__name__}: {str(exc)[:3900]}"
                scan.finished_at = datetime.now(timezone.utc)
                scan.collectors_ok = ok
                scan.collectors_failed = failed
                asset.last_scan_status = status
                await audit(
                    db,
                    "scan.failed",
                    "scan",
                    scan.id,
                    outcome="failure",
                    details={"status": status, "error": str(exc)[:200]},
                )
            
            finally:
                # Закрываем соединение
                if connection:
                    try:
                        await connection.close()
                        logger.debug(f"Connection for scan {scan_id} closed")
                    except Exception as e:
                        logger.warning(f"Error closing connection: {e}")
                
                # Убеждаемся что время завершения установлено
                if scan.status in TERMINAL_STATUSES and scan.finished_at is None:
                    scan.finished_at = datetime.now(timezone.utc)
                
                await db.commit()
            
            return scan.status


async def _run_linux_scan(
    asset: Asset,
    credential: Credential,
    secret: str,
    raw_inventory: RawInventory,
) -> None:
    """Вспомогательный метод для Linux сканирования."""
    if credential.type not in {"ssh_password", "ssh_private_key"}:
        raise ScanFailure(
            "AUTH_FAILED",
            "Credential type is not valid for Linux SSH"
        )
    
    connection = SSHConnection(
        asset.ip_address,
        credential.port or 22,
        credential.username,
        password=secret if credential.type == "ssh_password" else None,
        private_key=secret if credential.type == "ssh_private_key" else None,
        timeout=settings.ssh_connect_timeout,
        command_timeout=settings.command_timeout,
    )
    
    try:
        logger.debug(f"Connecting to Linux host {asset.ip_address}")
        await asyncio.wait_for(
            connection.connect(),
            settings.ssh_connect_timeout,
        )
    except asyncio.TimeoutError:
        raise ScanFailure("TIMEOUT", "SSH connection timed out")
    except Exception as e:
        raise ScanFailure("UNREACHABLE", f"Failed to connect via SSH: {str(e)[:200]}")


def _create_winrm_connection(
    asset: Asset,
    credential: Credential,
    secret: str,
) -> WinRMConnection:
    """Вспомогательный метод для создания WinRM соединения."""
    if credential.type != "winrm_password":
        raise ScanFailure(
            "AUTH_FAILED",
            "Credential type is not valid for Windows WinRM"
        )
    
    use_https = credential.verify_tls
    port = credential.port or (5986 if use_https else 5985)
    
    # Правильно формируем username
    username = credential.username
    if credential.domain and "\\" not in username and "@" not in username:
        username = f"{credential.domain}\\{username}"
    
    logger.debug(f"Creating WinRM connection for {asset.ip_address}")
    return WinRMConnection(
        asset.ip_address,
        port,
        username,
        secret,
        https=use_https,
        verify_tls=credential.verify_tls,
        timeout=settings.winrm_connect_timeout,
    )


async def execute_scan(scan_id: int) -> str:
    """
    Выполняет сканирование с timeout и управлением жизненным циклом задачи.
    
    Эта функция:
    1. Проверяет что не запущено другое сканирование с тем же ID
    2. Создает asyncio.Task для выполнения
    3. Ожидает завершения с глобальным timeout
    4. При timeout отменяет задачу
    
    Args:
        scan_id: ID задачи сканирования
        
    Returns:
        Финальный статус сканирования
    """
    logger.debug(f"Execute scan {scan_id}")
    
    # Проверяем не запущена ли уже эта задача
    existing = _active_scan_tasks.get(scan_id)
    if existing and not existing.done():
        logger.debug(f"Scan {scan_id} already running")
        return "RUNNING"
    
    # Создаем новую задачу
    task = asyncio.create_task(
        run_scan(scan_id),
        name=f"scan-{scan_id}",
    )
    _active_scan_tasks[scan_id] = task
    
    try:
        logger.debug(f"Waiting for scan {scan_id} with timeout {settings.scan_timeout}s")
        return await asyncio.wait_for(
            asyncio.shield(task),
            settings.scan_timeout,
        )
    
    except asyncio.TimeoutError:
        logger.error(f"Scan {scan_id} exceeded SCAN_TIMEOUT ({settings.scan_timeout}s)")
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        # Обновляем статус в БД
        async with SessionLocal() as db:
            scan = await db.get(Scan, scan_id)
            if scan and scan.status in ACTIVE_STATUSES | {"RUNNING"}:
                scan.status = "TIMEOUT"
                scan.error = f"Scan exceeded SCAN_TIMEOUT ({settings.scan_timeout}s)"
                scan.finished_at = datetime.now(timezone.utc)
                
                asset = await db.get(Asset, scan.asset_id)
                if asset:
                    asset.last_scan_status = "TIMEOUT"
                
                await db.commit()
                logger.info(f"Scan {scan_id} marked as TIMEOUT")
        
        return "TIMEOUT"
    
    finally:
        _active_scan_tasks.pop(scan_id, None)


async def cancel_scan(scan_id: int) -> bool:
    """
    Отменяет активное сканирование.
    
    Args:
        scan_id: ID задачи сканирования
        
    Returns:
        True если сканирование было отменено, False если уже завершено
    """
    logger.info(f"Cancelling scan {scan_id}")
    
    async with SessionLocal() as db:
        scan = await db.get(Scan, scan_id)
        if not scan or scan.status not in ACTIVE_STATUSES:
            logger.debug(f"Scan {scan_id} is not active, cannot cancel")
            return False
        
        scan.status = "CANCELLED"
        scan.error = "Scan cancelled by user"
        scan.finished_at = datetime.now(timezone.utc)
        
        asset = await db.get(Asset, scan.asset_id)
        if asset:
            asset.last_scan_status = "CANCELLED"
        
        await audit(db, "scan.cancelled", "scan", scan.id)
        await db.commit()
    
    # Отменяем asyncio задачу если она запущена
    task = _active_scan_tasks.get(scan_id)
    if task and not task.done():
        logger.debug(f"Cancelling asyncio task for scan {scan_id}")
        task.cancel()
    
    return True


async def _upsert_current_inventory(
    db: AsyncSession,
    asset_id: int,
    items: list[dict],
) -> None:
    """
    Обновляет текущий инвентарь актива.
    
    Для каждого элемента из нового инвентаря:
    - Если существует - обновляем версию и время последнего обнаружения
    - Если новый - добавляем в БД
    
    Отмечаем элементы которых больше нет как неактивные.
    
    Args:
        db: Сессия БД
        asset_id: ID актива
        items: Список элементов инвентаря (словари)
    """
    logger.debug(f"Updating inventory for asset {asset_id} with {len(items)} items")
    
    # Загружаем текущий инвентарь
    current = (
        await db.execute(select(Software).where(Software.asset_id == asset_id))
    ).scalars().all()
    
    # Создаем mapping по уникальному ключу
    by_key = {
        (
            x.name.casefold(),
            x.source,
            x.ecosystem,
            x.architecture,
        ): x
        for x in current
    }
    
    seen: Set = set()
    now = datetime.now(timezone.utc)
    
    for item in items:
        # Создаем уникальный ключ для идентификации программы
        key = (
            item["name"].casefold(),
            item.get("source", "unknown"),
            item.get("ecosystem", "system"),
            item.get("architecture", "unknown"),
        )
        seen.add(key)
        
        obj = by_key.get(key)
        if obj:
            # Обновляем существующий элемент
            obj.version = item["version"]
            obj.vendor = item.get("vendor")
            obj.package_source = item.get("package_source")
            obj.last_seen = now
            obj.active = True
            obj.evidence = item.get("evidence")
        else:
            # Добавляем новый элемент
            db.add(Software(
                asset_id=asset_id,
                name=item["name"],
                version=item["version"],
                vendor=item.get("vendor"),
                source=item.get("source", "unknown"),
                package_source=item.get("package_source"),
                ecosystem=item.get("ecosystem", "system"),
                architecture=item.get("architecture", "unknown"),
                evidence=item.get("evidence"),
                first_seen=now,
                last_seen=now,
                active=True,
            ))
    
    # Отмечаем удаленные элементы как неактивные
    for key, obj in by_key.items():
        if key not in seen:
            logger.debug(f"Marking {obj.name} as inactive for asset {asset_id}")
            obj.active = False


async def shutdown_scan_tasks() -> None:
    """
    Отменяет все активные сканирования.
    
    Используется при graceful shutdown приложения.
    Ждет завершения всех задач с CancelledError.
    """
    logger.info(f"Shutting down {len(_active_scan_tasks)} scan tasks")
    
    tasks = [t for t in _active_scan_tasks.values() if not t.done()]
    
    for task in tasks:
        logger.debug(f"Cancelling task {task.get_name()}")
        task.cancel()
    
    if tasks:
        # Ждем завершения всех задач, перехватывая CancelledError
        await asyncio.gather(*tasks, return_exceptions=True)
    
    logger.info("All scan tasks shut down")
