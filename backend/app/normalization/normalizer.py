import hashlib,json
from app.domain.inventory import RawInventory
from app.core.config import settings

def _software_key(x): return (x["name"].casefold(),x.get("source","unknown"),x.get("ecosystem","system"),x.get("architecture","unknown"))
def normalize(raw: RawInventory, *, scan_id=None, started_at=None, finished_at=None, status="SUCCESS"):
    unique={}
    for item in raw.software:
        name=item.name.strip()
        if not name: continue
        source=item.source or "unknown"; ecosystem=item.ecosystem or "system"; arch=item.architecture or "unknown"
        obj={"name":name,"version":item.version.strip() or "unknown","vendor":item.vendor.strip() if item.vendor else None,"source":source,"package_source":item.package_source,"ecosystem":ecosystem,"architecture":arch,"evidence":item.evidence}
        unique.setdefault(_software_key(obj),obj)
    s=raw.system
    return {"schema_version":"1.0","scanner":{"id":settings.scanner_id,"version":settings.scanner_version},"scan":{"id":str(scan_id) if scan_id is not None else None,"started_at":started_at.isoformat() if started_at else None,"finished_at":finished_at.isoformat() if finished_at else None,"status":status},"asset":{"hostname":s.hostname,"fqdn":s.fqdn,"ip_address":s.ip_address,"os":{"type":s.platform,"vendor":s.os_vendor,"name":s.os_name,"version":s.os_version,"architecture":s.architecture,"build":s.build,"kernel":s.kernel,"domain":s.domain}},"system":{"cpu":s.cpu,"ram_bytes":s.ram_bytes},"software":sorted(unique.values(),key=lambda x:(x["name"].casefold(),x["source"],x["architecture"])),"updates":raw.updates}

def fingerprint(payload):
    stable={"asset":payload.get("asset"),"system":payload.get("system"),"software":payload.get("software"),"updates":payload.get("updates")}
    return hashlib.sha256(json.dumps(stable,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def diff_inventory(previous,current):
    old={_software_key(x):x for x in (previous or {}).get("software",[])}; new={_software_key(x):x for x in current.get("software",[])}; events=[]
    for key,item in new.items():
        if key not in old: events.append({"event_type":"installed","name":item["name"],"old_version":None,"new_version":item["version"],"source":item.get("source")})
        elif old[key].get("version") != item.get("version"): events.append({"event_type":"version_changed","name":item["name"],"old_version":old[key].get("version"),"new_version":item["version"],"source":item.get("source")})
    for key,item in old.items():
        if key not in new: events.append({"event_type":"removed","name":item["name"],"old_version":item.get("version"),"new_version":None,"source":item.get("source")})
    return events
