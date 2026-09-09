import json
from app.collectors.base import Collector
from app.domain.inventory import RawInventory, SoftwareItem
class WindowsRegistryCollector(Collector):
    name="windows.registry"
    async def collect(self, connection, inventory: RawInventory) -> None:
        ps=r"""$p=@('HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*','HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*');Get-ItemProperty $p -ErrorAction SilentlyContinue|Where-Object {$_.DisplayName}|Select-Object DisplayName,DisplayVersion,Publisher,InstallDate,PSPath|ConvertTo-Json -Compress"""
        raw=await connection.run(ps); data=json.loads(raw) if raw.strip() else []; data=data if isinstance(data,list) else [data]
        for x in data: inventory.software.append(SoftwareItem(x.get("DisplayName",""),x.get("DisplayVersion") or "unknown",vendor=x.get("Publisher"),source="registry",ecosystem="windows",architecture="unknown",evidence={"type":"registry","source":"uninstall","path":x.get("PSPath")}))
