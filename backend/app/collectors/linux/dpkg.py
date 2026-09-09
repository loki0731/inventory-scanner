from app.collectors.base import Collector
from app.domain.inventory import RawInventory, SoftwareItem
class DpkgCollector(Collector):
    name="linux.dpkg"
    async def collect(self, connection, inventory: RawInventory) -> None:
        out=await connection.run("dpkg-query -W -f='${Package}\\t${Version}\\t${Architecture}\\n'")
        for line in out.splitlines():
            p=line.split("\t",2)
            if len(p)==3 and p[0]: inventory.software.append(SoftwareItem(p[0],p[1] or "unknown",source="dpkg",package_source=inventory.system.os_vendor,ecosystem="system",architecture=p[2],evidence={"type":"package_manager","source":"dpkg"}))
