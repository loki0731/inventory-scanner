# Security

- Secrets are encrypted at rest with AES-256-GCM.
- The encryption key is supplied only through `CREDENTIAL_ENCRYPTION_KEY` and is never stored in PostgreSQL.
- API access requires `Authorization: Bearer <API_TOKEN>`.
- Credential responses never contain the encrypted secret.
- Logs and errors must not include credential values.
- Linux collection uses read-only commands and does not require root by design.
- Windows collection uses read-only PowerShell/CIM/registry/update queries and does not use `Win32_Product`.
- Production deployments should terminate TLS in a trusted reverse proxy or load balancer.
