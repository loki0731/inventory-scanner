import { FormEvent, useEffect, useState } from 'react';
import { api } from '../../api/client';
import { Asset, Credential } from '../../types';
import { Modal } from '../common/Modal';
import { Field } from '../common/Field';

type FormState = {
  hostname: string;
  fqdn: string;
  ip_address: string;
  platform: 'linux' | 'windows';
  credential_id: string;
  enabled: boolean;
  scan_interval: number | string;
  description: string;
};

export function AssetModal({ asset, onClose, onSaved }: { asset: Asset | null; onClose: () => void; onSaved: () => void }) {
  const [creds, setCreds] = useState<Credential[]>([]);
  const [form, setForm] = useState<FormState>(
    asset
      ? {
          hostname: asset.hostname,
          fqdn: asset.fqdn || '',
          ip_address: asset.ip_address,
          platform: asset.platform,
          credential_id: asset.credential_id ? String(asset.credential_id) : '',
          enabled: asset.enabled,
          scan_interval: asset.scan_interval,
          description: asset.description || '',
        }
      : { hostname: '', fqdn: '', ip_address: '', platform: 'linux', credential_id: '', enabled: true, scan_interval: 86400, description: '' }
  );
  const [err, setErr] = useState('');

  useEffect(() => {
    api<{ items: Credential[] }>('/credentials?limit=500').then((x) => setCreds(x.items)).catch(() => {});
  }, []);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      const payload = {
        ...form,
        credential_id: form.credential_id ? Number(form.credential_id) : null,
        scan_interval: Number(form.scan_interval),
      };
      if (asset) await api(`/assets/${asset.id}`, { method: 'PUT', body: JSON.stringify(payload) });
      else await api('/assets', { method: 'POST', body: JSON.stringify(payload) });
      onSaved();
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Save failed');
    }
  };

  return (
    <Modal title={asset ? 'Edit asset' : 'Add asset'} onClose={onClose}>
      <form onSubmit={submit} className="form-grid">
        <Field label="Hostname">
          <input required value={form.hostname} onChange={(e) => setForm({ ...form, hostname: e.target.value })} />
        </Field>
        <Field label="IP address">
          <input required value={form.ip_address} onChange={(e) => setForm({ ...form, ip_address: e.target.value })} />
        </Field>
        <Field label="FQDN">
          <input value={form.fqdn} onChange={(e) => setForm({ ...form, fqdn: e.target.value })} />
        </Field>
        <Field label="Platform">
          <select value={form.platform} onChange={(e) => setForm({ ...form, platform: e.target.value as 'linux' | 'windows' })}>
            <option value="linux">Linux / SSH</option>
            <option value="windows">Windows / WinRM</option>
          </select>
        </Field>
        <Field label="Credential">
          <select value={form.credential_id} onChange={(e) => setForm({ ...form, credential_id: e.target.value })}>
            <option value="">No credential</option>
            {creds.map((c) => <option key={c.id} value={c.id}>{c.name} · {c.type}</option>)}
          </select>
        </Field>
        <Field label="Scan interval (seconds)">
          <input type="number" min="60" value={form.scan_interval} onChange={(e) => setForm({ ...form, scan_interval: e.target.value })} />
        </Field>
        <Field label="Description" full>
          <textarea rows={3} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
        </Field>
        <label className="check full">
          <input type="checkbox" checked={form.enabled} onChange={(e) => setForm({ ...form, enabled: e.target.checked })} /> Asset enabled for scheduled scans
        </label>
        {err && <div className="alert error full">{err}</div>}
        <div className="modal-actions full">
          <button type="button" onClick={onClose}>Cancel</button>
          <button className="primary">{asset ? 'Save changes' : 'Create asset'}</button>
        </div>
      </form>
    </Modal>
  );
}