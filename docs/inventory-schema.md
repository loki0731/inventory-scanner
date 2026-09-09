# Inventory JSON Schema v1.0

The top-level document contains `schema_version`, `scanner`, `scan`, `asset`, `system`, `software`, and `updates`.

Software identity is based on normalized name plus source, architecture and ecosystem. `vendor` is factual vendor metadata; it is not a CPE vendor mapping. `evidence` records how the item was observed.

Minor schema versions must remain backward compatible. Breaking changes require a new major version.
