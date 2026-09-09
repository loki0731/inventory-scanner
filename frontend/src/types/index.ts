export type Page = 'dashboard' | 'assets' | 'credentials' | 'scans' | 'inventory' | 'audit';

export type Asset = {
  id: number;
  hostname: string;
  fqdn?: string | null;
  ip_address: string;
  platform: 'linux' | 'windows';
  credential_id?: number | null;
  enabled: boolean;
  scan_interval: number;
  description?: string | null;
  last_scan_at?: string | null;
  last_scan_attempt_at?: string | null;
  last_scan_status?: string | null;
  inventory_fingerprint?: string | null;
};

export type Credential = {
  id: number;
  name: string;
  type: string;
  username: string;
  domain?: string | null;
  port?: number | null;
  verify_tls: boolean;
  created_at: string;
  updated_at: string;
  last_used_at?: string | null;
};

export type Scan = {
  id: number;
  asset_id: number;
  started_at?: string | null;
  finished_at?: string | null;
  status: string;
  error?: string | null;
  software_count: number;
  collectors_ok: number;
  collectors_failed: number;
};

export type Software = {
  name: string;
  version: string;
  vendor?: string | null;
  source?: string | null;
  package_source?: string | null;
  ecosystem?: string | null;
  architecture?: string | null;
  evidence?: unknown;
  first_seen?: string;
  last_seen?: string;
};

export type InventoryHistoryEvent = {
  id: number | string;
  event_type: string;
  name: string;
  old_version?: string | null;
  new_version?: string | null;
  source?: string | null;
  occurred_at: string;
};

export type InventoryPayload = {
  asset?: {
    hostname?: string;
    os?: { name?: string; version?: string };
  };
  scan?: { finished_at?: string | null };
  schema_version?: string;
  software: Software[];
};

export type AuditEvent = {
  id: number | string;
  occurred_at: string;
  action: string;
  resource_type: string;
  resource_id?: number | string | null;
  outcome: string;
  details?: unknown;
};

export type Paginated<T> = { items: T[]; total?: number };