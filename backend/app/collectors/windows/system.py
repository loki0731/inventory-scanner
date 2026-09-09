import json
from app.collectors.base import Collector
from app.domain.inventory import RawInventory
class WindowsSystemCollector(Collector):
    name="windows.system"
    async def collect(self, connection, inventory: RawInventory) -> None:
        ps="""$o=Get-CimInstance Win32_OperatingSystem;$c=Get-CimInstance Win32_ComputerSystem;$fqdn=[System.Net.Dns]::GetHostEntry($env:COMPUTERNAME).HostName;[pscustomobject]@{Hostname=$env:COMPUTERNAME;FQDN=$fqdn;Domain=$c.Domain;OS=$o.Caption;Version=$o.Version;Build=$o.BuildNumber;Architecture=$o.OSArchitecture;RAM=[int64]$c.TotalPhysicalMemory;CPU=$c.NumberOfLogicalProcessors}|ConvertTo-Json -Compress"""
        d=json.loads(await connection.run(ps)); inventory.system.platform="windows"; inventory.system.os_vendor="Microsoft"; inventory.system.os_name=d.get("OS"); inventory.system.os_version=d.get("Version"); inventory.system.build=str(d.get("Build")) if d.get("Build") is not None else None; inventory.system.architecture=d.get("Architecture"); inventory.system.hostname=d.get("Hostname"); inventory.system.fqdn=d.get("FQDN") or d.get("Hostname"); inventory.system.domain=d.get("Domain"); inventory.system.ram_bytes=d.get("RAM"); inventory.system.cpu=str(d.get("CPU")) if d.get("CPU") is not None else None
