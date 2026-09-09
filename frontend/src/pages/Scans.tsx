import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { Asset, Scan } from '../types';
import { useReload } from '../hooks/useReload';
import { fmt, duration, statusClass } from '../utils/format';
import { Empty } from '../components/common/Empty';

const STATUSES = ['QUEUED', 'RUNNING', 'SUCCESS', 'PARTIAL_SUCCESS', 'AUTH_FAILED', 'UNREACHABLE', 'TIMEOUT', 'FAILED', 'CANCELLED'];

export function Scans() {
  const [rows, setRows] = useState<Scan[]>([]);
  const [assets, setAssets] = useState<Record<number, string>>({});
  const [status, setStatus] = useState('');
  const [asset, setAsset] = useState('');
  const [err, setErr] = useState('');
  const [reload, bump] = useReload();

  const load = () => Promise.all([
    api<{ items: Scan[] }>('/scans?limit=500' + (status ? `&status=${encodeURIComponent(status)}` : '') + (asset ? `&asset_id=${asset}` : '')),
    api<{ items: Asset[] }>('/assets?limit=500'),
  ]).then(([s, a]) => {
    setRows(s.items);
    setAssets(Object.fromEntries(a.items.map((x) => [x.id, x.hostname])));
  }).catch((e) => setErr(e.message));

  useEffect(() => { load(); }, [reload, status, asset]);

  return (
    <>
      <div className="page-head">
        <div>
          <h2>Scans <em>{rows.length}</em></h2>
          <p>Collection jobs and their execution state.</p>
        </div>
        <button onClick={load}>Refresh</button>
      </div>

      {err && <div className="alert error">{err}</div>}

      <section className="panel">
        <div className="toolbar filters">
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">All statuses</option>
            {STATUSES.map((x) => <option key={x}>{x}</option>)}
          </select>
          <input placeholder="Asset ID" value={asset} onChange={(e) => setAsset(e.target.value)} />
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Scan</th><th>Asset</th><th>Status</th><th>Started</th><th>Duration</th><th>Software</th><th>Collectors</th><th></th></tr>
            </thead>
            <tbody>
              {rows.map((s) => (
                <tr key={s.id}>
                  <td><strong>#{s.id}</strong></td>
                  <td>{assets[s.asset_id] || `#${s.asset_id}`}</td>
                  <td><span className={statusClass(s.status)}>{s.status}</span></td>
                  <td>{fmt(s.started_at)}</td>
                  <td>{duration(s)}</td>
                  <td>{s.software_count}</td>
                  <td>{s.collectors_ok}/{s.collectors_ok + s.collectors_failed}</td>
                  <td>
                    {['QUEUED', 'RUNNING'].includes(s.status) && (
                      <button onClick={async () => { await api(`/scans/${s.id}/cancel`, { method: 'POST' }); bump(); }}>Cancel</button>
                    )}
                    {s.error && <button title={s.error} onClick={() => alert(s.error)}>Details</button>}
                  </td>
                </tr>
              ))}
              {!rows.length && <tr><td colSpan={8}><Empty text="No scans found" /></td></tr>}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}