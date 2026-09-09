from abc import ABC, abstractmethod
from app.domain.inventory import RawInventory
class Collector(ABC):
    name: str = "collector"
    @abstractmethod
    async def collect(self, connection, inventory: RawInventory) -> None: ...
