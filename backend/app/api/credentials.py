"""
API endpoints для управления учетными данными сканирования.

Поддерживает CRUD операции для:
- SSH паролей
- SSH приватных ключей
- WinRM паролей
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_api_token
from app.core.security import encrypt_secret
from app.db.database import get_session
from app.db.models import Asset, Credential
from app.schemas import (
    CredentialCreate,
    CredentialOut,
    CredentialUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/credentials",
    tags=["Credentials"],
    dependencies=[Depends(require_api_token)],
)


@router.get("", response_model=Dict[str, Any])
async def list_credentials(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_session),
) -> Dict[str, Any]:
    total = await db.scalar(
        select(func.count()).select_from(Credential)
    )

    rows = (
        await db.execute(
            select(Credential)
            .order_by(Credential.id)
            .limit(limit)
            .offset(offset)
        )
    ).scalars().all()

    return {
        "items": [CredentialOut.model_validate(row) for row in rows],
        "total": total or 0,
        "limit": limit,
        "offset": offset,
    }


@router.post("", response_model=CredentialOut, status_code=201)
async def create_credential(
    data: CredentialCreate,
    db: AsyncSession = Depends(get_session),
) -> CredentialOut:
    """
    Создать новые учетные данные.
    
    Пароль/приватный ключ шифруется перед сохранением.
    
    Args:
        data: Данные для создания учетных данных
        db: Сессия БД
        
    Returns:
        Созданные учетные данные (без пароля)
        
    Raises:
        HTTPException: 409 если имя учетных данных уже существует
    """
    logger.info(f"Creating credential: {data.name} (type={data.type})")
    
    obj = Credential(**data.model_dump(exclude={"secret"}))
    obj.encrypted_secret = encrypt_secret(data.secret)
    db.add(obj)
    
    try:
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to create credential {data.name}: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Credential name already exists",
        )
    
    await db.refresh(obj)
    logger.info(f"Credential {data.name} created successfully")
    return obj


@router.put("/{credential_id}", response_model=CredentialOut)
async def update_credential(
    credential_id: int,
    data: CredentialUpdate,
    db: AsyncSession = Depends(get_session),
) -> CredentialOut:
    """
    Обновить учетные данные.
    
    Если передан новый пароль/ключ, он будет зашифрован.
    
    Args:
        credential_id: ID учетных данных
        data: Данные для обновления
        db: Сессия БД
        
    Returns:
        Обновленные учетные данные (без пароля)
        
    Raises:
        HTTPException: 404 если учетные данные не найдены
        HTTPException: 409 если новое имя уже существует
    """
    logger.info(f"Updating credential {credential_id}")
    
    obj = await db.get(Credential, credential_id)
    if not obj:
        logger.warning(f"Credential {credential_id} not found")
        raise HTTPException(status_code=404, detail="Credential not found")
    
    values = data.model_dump(exclude_unset=True)
    
    # Если обновляется пароль/ключ, шифруем его
    if "secret" in values and values["secret"] is not None:
        logger.debug(f"Updating secret for credential {credential_id}")
        obj.encrypted_secret = encrypt_secret(values.pop("secret"))
    
    # Применяем остальные изменения
    for key, value in values.items():
        setattr(obj, key, value)
    
    try:
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to update credential {credential_id}: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Credential name already exists or other conflict",
        )
    
    await db.refresh(obj)
    logger.info(f"Credential {credential_id} updated successfully")
    return obj


@router.delete("/{credential_id}", status_code=204)
async def delete_credential(
    credential_id: int,
    db: AsyncSession = Depends(get_session),
) -> None:
    """
    Удалить учетные данные.
    
    Учетные данные не могут быть удалены если они назначены на актив.
    
    Args:
        credential_id: ID учетных данных
        db: Сессия БД
        
    Raises:
        HTTPException: 404 если учетные данные не найдены
        HTTPException: 409 если учетные данные назначены на актив
    """
    logger.info(f"Deleting credential {credential_id}")
    
    obj = await db.get(Credential, credential_id)
    if not obj:
        logger.warning(f"Credential {credential_id} not found")
        raise HTTPException(status_code=404, detail="Credential not found")
    
    # Проверяем что нет активных скан-задач использующих эти учетные данные
    used = await db.scalar(
        select(Asset.id)
        .where(Asset.credential_id == credential_id)
        .limit(1)
    )
    
    if used:
        logger.warning(
            f"Cannot delete credential {credential_id}, it's assigned to asset {used}"
        )
        raise HTTPException(
            status_code=409,
            detail="Credential is assigned to an asset",
        )
    
    await db.delete(obj)
    await db.commit()
    logger.info(f"Credential {credential_id} deleted successfully")
