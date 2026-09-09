from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Independent Credentialed Asset Inventory Scanner"
    database_url: str = "postgresql+asyncpg://scanner:scanner@postgres:5432/inventory"
    api_token: SecretStr = Field(min_length=1)
    credential_encryption_key: SecretStr = Field(min_length=1)
    scanner_id: str = "scanner-01"
    scanner_version: str = "1.0.0"
    max_concurrent_scans: int = Field(default=5, ge=1, le=100)
    ssh_connect_timeout: float = Field(default=10, gt=0)
    winrm_connect_timeout: float = Field(default=15, gt=0)
    command_timeout: float = Field(default=30, gt=0)
    scan_timeout: float = Field(default=300, gt=0)
    scheduler_interval: int = Field(default=60, ge=10)
    scan_retention_days: int = Field(default=0, ge=0)
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
