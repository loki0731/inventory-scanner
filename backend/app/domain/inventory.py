from dataclasses import dataclass, field

@dataclass
class SystemInfo:
    platform: str = "unknown"
    os_vendor: str | None = None
    os_name: str | None = None
    os_version: str | None = None
    build: str | None = None
    kernel: str | None = None
    architecture: str | None = None
    hostname: str | None = None
    fqdn: str | None = None
    ip_address: str | None = None
    domain: str | None = None
    cpu: str | None = None
    ram_bytes: int | None = None

@dataclass
class SoftwareItem:
    name: str
    version: str
    vendor: str | None = None
    source: str = "unknown"
    package_source: str | None = None
    ecosystem: str = "system"
    architecture: str | None = None
    evidence: dict = field(default_factory=dict)

@dataclass
class RawInventory:
    system: SystemInfo = field(default_factory=SystemInfo)
    software: list[SoftwareItem] = field(default_factory=list)
    updates: list[dict] = field(default_factory=list)
    collector_errors: list[dict] = field(default_factory=list)
