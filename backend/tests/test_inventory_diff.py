from app.normalization.normalizer import diff_inventory, normalize
from app.domain.inventory import RawInventory, SoftwareItem


def test_diff_install_remove_and_version_change():
    old = {"software": [
        {"name": "nginx", "version": "1.24", "source": "dpkg"},
        {"name": "curl", "version": "8.0", "source": "dpkg"},
    ]}
    new = {"software": [
        {"name": "nginx", "version": "1.26", "source": "dpkg"},
        {"name": "git", "version": "2.4", "source": "dpkg"},
    ]}
    events = diff_inventory(old, new)
    assert {(e["event_type"], e["name"]) for e in events} == {
        ("version_changed", "nginx"), ("installed", "git"), ("removed", "curl")
    }


def test_normalize_deduplicates():
    raw = RawInventory()
    raw.software.extend([
        SoftwareItem("nginx", "1.24", source="dpkg"),
        SoftwareItem("nginx", "1.24", source="dpkg"),
    ])
    payload = normalize(raw)
    assert len(payload["software"]) == 1
