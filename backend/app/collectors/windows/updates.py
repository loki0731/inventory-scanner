import json

from app.collectors.base import Collector
from app.domain.inventory import RawInventory


class WindowsUpdateCollector(Collector):
    name = "windows.updates"

    async def collect(self, connection, inventory: RawInventory) -> None:
        commands = [
            (
                "Get-HotFix | "
                "Select-Object HotFixID,InstalledOn | "
                "ConvertTo-Json -Compress",
                "Get-HotFix",
            ),
            (
                "Get-CimInstance Win32_QuickFixEngineering | "
                "Select-Object HotFixID,InstalledOn | "
                "ConvertTo-Json -Compress",
                "Win32_QuickFixEngineering",
            ),
        ]

        last_error = None

        for ps, source in commands:
            try:
                raw = await connection.run(ps)

                if not raw.strip():
                    inventory.updates = []
                    return

                data = json.loads(raw)
                data = data if isinstance(data, list) else [data]

                inventory.updates = [
                    {
                        "kb": x.get("HotFixID"),
                        "installed": True,
                        "installed_on": (
                            str(x.get("InstalledOn"))
                            if x.get("InstalledOn")
                            else None
                        ),
                        "evidence": {
                            "type": "powershell",
                            "source": source,
                        },
                    }
                    for x in data
                    if x.get("HotFixID")
                ]

                return

            except Exception as exc:
                last_error = exc

        # Updates are optional inventory data.
        # Do not fail the whole Windows scan if the account
        # has insufficient privileges to query them.
        inventory.updates = []

        # Deliberately do not raise last_error.