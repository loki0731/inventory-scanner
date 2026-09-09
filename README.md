# Independent Credentialed Asset Inventory Scanner

Standalone credentialed asset/software inventory collector for Linux over SSH and Windows over WinRM. It intentionally has no CVE, NVD, CPE, CVSS, KEV or vulnerability-management dependency.

## Run

1. Copy `.env.example` to `.env`.
2. Generate a 32-byte URL-safe base64 key, for example:
   `python -c "import os,base64; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"`
3. Put the generated value in `CREDENTIAL_ENCRYPTION_KEY` and set `API_TOKEN`.
4. Start: `docker compose up --build`.
5. API: `http://localhost:8000/docs`; frontend: `http://localhost:3000`.

## Credential types

- `ssh_password`
- `ssh_private_key` (the secret is the private-key material)
- `winrm_password`

The API never returns encrypted secrets. Scan failures retain the last successful inventory; an unreachable/authentication failure never marks software as removed.

## Tests

`cd backend && pytest -q`
