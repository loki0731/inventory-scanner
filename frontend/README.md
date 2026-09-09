# Inventory Scanner Frontend

React + TypeScript + Vite frontend for the independent Inventory Scanner backend.

## Pages

- Dashboard
- Assets: CRUD, enable/disable, manual scan, inventory details
- Credentials: create/update/delete without exposing secrets
- Scans: filtering, status, duration, collector results, cancellation
- Inventory: software search/filter, inventory summary, change history, JSON/CSV export
- Audit Log

## Authentication

The API bearer token is stored in `sessionStorage` only. It is never sent to logs or rendered as application data.

## Development

```bash
npm install
npm run dev
```

## Production

The supplied Dockerfile builds the Vite application and serves it with nginx. `/api/` is proxied to the backend service.
