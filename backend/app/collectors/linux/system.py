from app.collectors.base import Collector
from app.domain.inventory import RawInventory
class LinuxSystemCollector(Collector):
    name="linux.system"
    async def collect(self, connection, inventory: RawInventory) -> None:
        cmd="""printf '__OS__\\n'; cat /etc/os-release; printf '__HOST__\\n'; hostname -f 2>/dev/null || hostname; printf '__KERNEL__\\n'; uname -sr; printf '__ARCH__\\n'; uname -m; printf '__CPU__\\n'; nproc; printf '__RAM__\\n'; awk '/MemTotal:/ {print $2*1024}' /proc/meminfo"""
        data=await connection.run(cmd); sections={}; current=None
        for line in data.splitlines():
            marker=line.strip()
            if marker.startswith("__") and marker.endswith("__"):
                current=marker.strip("_").lower(); sections[current]=[]; continue
            if current: sections[current].append(line)
        osdata={}
        for line in sections.get("os",[]):
            if "=" in line:
                k,v=line.split("=",1); osdata[k]=v.strip().strip('"')
        host="\n".join(sections.get("host",[])).strip() or None
        s=inventory.system; s.platform="linux"; s.os_vendor=osdata.get("ID"); s.os_name=osdata.get("PRETTY_NAME",osdata.get("NAME")); s.os_version=osdata.get("VERSION_ID"); s.hostname=host; s.fqdn=host; s.kernel="\n".join(sections.get("kernel",[])).strip() or None; s.architecture="\n".join(sections.get("arch",[])).strip() or None; s.cpu="\n".join(sections.get("cpu",[])).strip() or None
        ram="\n".join(sections.get("ram",[])).strip(); s.ram_bytes=int(ram) if ram.isdigit() else None
