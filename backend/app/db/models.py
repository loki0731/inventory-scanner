from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

def utcnow(): return datetime.now(timezone.utc)
class Base(DeclarativeBase): pass

class Credential(Base):
    __tablename__ = "credentials"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    type: Mapped[str] = mapped_column(String(32), index=True)
    username: Mapped[str] = mapped_column(String(255))
    domain: Mapped[str | None] = mapped_column(String(255))
    encrypted_secret: Mapped[str] = mapped_column(Text)
    port: Mapped[int | None] = mapped_column(Integer)
    verify_tls: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

class Asset(Base):
    __tablename__ = "assets"
    id: Mapped[int] = mapped_column(primary_key=True)
    hostname: Mapped[str] = mapped_column(String(255), index=True)
    fqdn: Mapped[str | None] = mapped_column(String(255), index=True)
    ip_address: Mapped[str] = mapped_column(String(64), index=True)
    platform: Mapped[str] = mapped_column(String(32), index=True)
    credential_id: Mapped[int | None] = mapped_column(ForeignKey("credentials.id", ondelete="SET NULL"), index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    scan_interval: Mapped[int] = mapped_column(Integer, default=86400)
    description: Mapped[str | None] = mapped_column(Text)
    last_scan_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_scan_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_scan_status: Mapped[str | None] = mapped_column(String(32))
    inventory_fingerprint: Mapped[str | None] = mapped_column(String(64), index=True)
    credential = relationship("Credential")

class Scan(Base):
    __tablename__ = "scans"
    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"), index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), default="QUEUED", index=True)
    error: Mapped[str | None] = mapped_column(Text)
    software_count: Mapped[int] = mapped_column(Integer, default=0)
    collectors_ok: Mapped[int] = mapped_column(Integer, default=0)
    collectors_failed: Mapped[int] = mapped_column(Integer, default=0)
    __table_args__ = (Index("ix_scans_asset_started", "asset_id", "started_at"), Index("ix_scans_asset_status", "asset_id", "status"))

class Software(Base):
    __tablename__ = "software"
    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(512))
    version: Mapped[str] = mapped_column(String(512))
    vendor: Mapped[str | None] = mapped_column(String(512))
    source: Mapped[str] = mapped_column(String(128), default="unknown")
    package_source: Mapped[str | None] = mapped_column(String(128))
    ecosystem: Mapped[str] = mapped_column(String(128), default="system")
    architecture: Mapped[str] = mapped_column(String(64), default="unknown")
    evidence: Mapped[dict | None] = mapped_column(JSON)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    __table_args__ = (
        UniqueConstraint("asset_id", "name", "source", "ecosystem", "architecture", name="uq_asset_software_identity"),
        Index("ix_software_asset_name", "asset_id", "name"),
        Index("ix_software_lookup", "name", "version"),
    )

class InventorySnapshot(Base):
    __tablename__ = "inventory_snapshots"
    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"), index=True)
    scan_id: Mapped[int] = mapped_column(ForeignKey("scans.id", ondelete="CASCADE"), index=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    fingerprint: Mapped[str] = mapped_column(String(64), index=True)
    payload: Mapped[dict] = mapped_column(JSON)

class InventoryEvent(Base):
    __tablename__ = "inventory_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"), index=True)
    scan_id: Mapped[int] = mapped_column(ForeignKey("scans.id", ondelete="CASCADE"), index=True)
    event_type: Mapped[str] = mapped_column(String(32), index=True)
    name: Mapped[str] = mapped_column(String(512))
    old_version: Mapped[str | None] = mapped_column(String(512))
    new_version: Mapped[str | None] = mapped_column(String(512))
    source: Mapped[str | None] = mapped_column(String(128))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    action: Mapped[str] = mapped_column(String(128), index=True)
    resource_type: Mapped[str] = mapped_column(String(64))
    resource_id: Mapped[str | None] = mapped_column(String(128))
    outcome: Mapped[str] = mapped_column(String(32), default="success")
    details: Mapped[dict | None] = mapped_column(JSON)
