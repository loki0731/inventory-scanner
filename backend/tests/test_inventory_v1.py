from app.normalization.normalizer import normalize,diff_inventory,fingerprint
from app.domain.inventory import RawInventory,SoftwareItem

def test_fingerprint_stable():
    raw=RawInventory(); raw.system.platform='linux'; raw.system.hostname='host'; raw.software=[SoftwareItem('nginx','1.2',source='dpkg',architecture='amd64')]
    a=normalize(raw); b=normalize(raw); assert fingerprint(a)==fingerprint(b)

def test_diff_install_upgrade_remove():
    old={'software':[{'name':'nginx','version':'1','source':'dpkg','ecosystem':'system','architecture':'amd64'}]}
    new={'software':[{'name':'nginx','version':'2','source':'dpkg','ecosystem':'system','architecture':'amd64'},{'name':'curl','version':'8','source':'dpkg','ecosystem':'system','architecture':'amd64'}]}
    types={x['event_type'] for x in diff_inventory(old,new)}; assert types=={'version_changed','installed'}
    newer={'software':[]}; assert diff_inventory(new,newer)[0]['event_type']=='removed'
