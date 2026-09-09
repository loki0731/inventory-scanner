# Architecture

The scanner is a modular monolith. Its hard boundary is **asset inventory**, not vulnerability assessment.

`Asset -> ScanService -> Connection -> Collectors -> RawInventory -> Normalizer -> InventoryService/DB -> Diff/History -> API/Export/UI`

Connections and collectors are interfaces. Collectors return domain data and do not access PostgreSQL. The scan service owns orchestration, status, timeout and persistence. Scheduler calls the same scan engine as manual scans.

No CVE, NVD, CPE, CVSS, KEV, Telegram or vulnerability matching code is part of this product.
