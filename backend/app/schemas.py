from datetime import datetime
from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, IPvAnyAddress


class Platform(str, Enum):
    linux = "linux"
    windows = "windows"


class CredentialType(str, Enum):
    ssh_password = "ssh_password"
    ssh_private_key = "ssh_private_key"
    winrm_password = "winrm_password"


class ScanStatus(str, Enum):
    queued = "QUEUED"
    running = "RUNNING"
    success = "SUCCESS"
    partial = "PARTIAL_SUCCESS"
    auth = "AUTH_FAILED"
    unreachable = "UNREACHABLE"
    timeout = "TIMEOUT"
    failed = "FAILED"
    cancelled = "CANCELLED"


class AssetBase(BaseModel):
    hostname: str = Field(min_length=1, max_length=255)
    fqdn: str | None = Field(None, max_length=255)
    ip_address: IPvAnyAddress
    platform: Platform
    credential_id: int | None = None
    enabled: bool = True
    scan_interval: int = Field(86400, ge=60)
    description: str | None = None


class AssetCreate(AssetBase):
    pass


class AssetUpdate(BaseModel):
    hostname: str | None = Field(None, min_length=1, max_length=255)
    fqdn: str | None = Field(None, max_length=255)
    ip_address: IPvAnyAddress | None = None
    platform: Platform | None = None
    credential_id: int | None = None
    enabled: bool | None = None
    scan_interval: int | None = Field(None, ge=60)
    description: str | None = None


class AssetOut(AssetBase):
    id: int
    ip_address: str
    last_scan_at: datetime | None
    last_scan_attempt_at: datetime | None
    last_scan_status: str | None
    inventory_fingerprint: str | None

    model_config = ConfigDict(from_attributes=True)


class CredentialCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    type: CredentialType
    username: str = Field(min_length=1, max_length=255)
    secret: str = Field(min_length=1)
    domain: str | None = None
    port: int | None = Field(None, ge=1, le=65535)
    verify_tls: bool = True


class CredentialUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    username: str | None = None
    secret: str | None = None
    domain: str | None = None
    port: int | None = Field(None, ge=1, le=65535)
    verify_tls: bool | None = None


class CredentialOut(BaseModel):
    id: int
    name: str
    type: str
    username: str
    domain: str | None
    port: int | None
    verify_tls: bool
    created_at: datetime
    updated_at: datetime
    last_used_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class ScanOut(BaseModel):
    id: int
    asset_id: int
    started_at: datetime | None
    finished_at: datetime | None
    status: str
    error: str | None
    software_count: int
    collectors_ok: int
    collectors_failed: int

    model_config = ConfigDict(from_attributes=True)


class ScanCreateOut(BaseModel):
    asset_id: int
    scan_id: int
    status: str


class InventoryEventOut(BaseModel):
    id: int
    scan_id: int
    event_type: str
    name: str
    old_version: str | None
    new_version: str | None
    source: str | None
    occurred_at: datetime


class DashboardOut(BaseModel):
    total_assets: int
    healthy_assets: int
    failed_assets: int
    never_scanned: int
    total_software: int
    last_scan_at: datetime | None


T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int
