from app.collectors.base import Collector
from app.domain.inventory import RawInventory, SoftwareItem
class RpmCollector(Collector):
    name="linux.rpm"
    async def collect(self, connection, inventory: RawInventory) -> None:
        out=await connection.run("rpm -qa --qf '%{NAME}\\t%{VERSION}-%{RELEASE}\\t%{ARCH}\\t%{VENDOR}\\n'")
        for line in out.splitlines():
            p=line.split("\t",3)
            if len(p)>=3 and p[0]: inventory.software.append(SoftwareItem(p[0],p[1] or "unknown",vendor=p[3] if len(p)>3 else None,source="rpm",package_source=inventory.system.os_vendor,ecosystem="system",architecture=p[2],evidence={"type":"package_manager","source":"rpm"}))
