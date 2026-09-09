import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api, downloadExport } from '../api/client';
import { Asset, InventoryHistoryEvent, InventoryPayload, Software } from '../types';
import { Changes } from '../components/inventory/Changes';
import { Badge } from '../components/common/Badge';
import { Empty } from '../components/common/Empty';
import { fmt } from '../utils/format';

export function Inventory() {
  const navigate = useNavigate();
  const { assetId: routeAssetId } = useParams();

  const [assets, setAssets] = useState<Asset[]>([]);
  const [id, setId] = useState(routeAssetId || '');
  const [payload, setPayload] = useState<InventoryPayload>();
  const [history, setHistory] = useState<InventoryHistoryEvent[]>([]);
  const [tab, setTab] = useState<'software' | 'changes'>('software');
  const [search, setSearch] = useState('');
  const [source, setSource] = useState('');
  const [err, setErr] = useState('');

  useEffect(() => {
    api<{ items: Asset[] }>('/assets?limit=500').then((x) => setAssets(x.items)).catch((e) => setErr(e.message));
  }, []);

  useEffect(() => {
    if (routeAssetId) {
      setId(routeAssetId);
      load(Number(routeAssetId));
    }
  }, [routeAssetId]);

  const load = async (n?: number) => {
    const aid = n || Number(id);
    if (!aid) return;
    try {
      const [p, h] = await Promise.all([
        api<InventoryPayload>(`/assets/${aid}/inventory`),
        api<{ items: InventoryHistoryEvent[] }>(`/assets/${aid}/inventory/history?limit=100`),
      ]);
      setPayload(p);
      setHistory(h.items);
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Failed to load inventory');
    }
  };

  const software: Software[] = payload?.software || [];
  const sources = [...new Set(software.map((x) => x.source).filter(Boolean))] as string[];
  const filtered = software.filter((x) =>
    [x.name, x.version, x.vendor, x.source, x.package_source].join(' ').toLowerCase().includes(search.toLowerCase())
    && (source ? x.source === source : true) // was inverted in the original — this now shows the selected source
  );

  return (
    <>
      <div className="page-head">
        <div>
          <h2>Inventory</h2>
          <p>Normalized software inventory and observed changes.</p>
        </div>
        {id && (
          <div className="actions">
            <button onClick={() => downloadExport(Number(id), 'json')}>Export JSON</button>
            <button onClick={() => downloadExport(Number(id), 'csv')}>Export CSV</button>
          </div>
        )}
      </div>

      {err && <div className="alert error">{err}</div>}

      <section className="panel inventory-selector">
        <select value={id} onChange={(e) => { setId(e.target.value); if (e.target.value) navigate(`/inventory/${e.target.value}`); }}>
          <option value="">Select asset…</option>
          {assets.map((a) => <option key={a.id} value={a.id}>{a.hostname} · {a.ip_address}</option>)}
        </select>
        <button className="primary" disabled={!id} onClick={() => load()}>Load inventory</button>
      </section>

      {payload && (
        <>
          <div className="inventory-summary">
            <div><span>Asset</span><strong>{payload.asset?.hostname || `#${id}`}</strong></div>
            <div><span>OS</span><strong>{payload.asset?.os?.name || '—'} {payload.asset?.os?.version || ''}</strong></div>
            <div><span>Software</span><strong>{software.length}</strong></div>
            <div><span>Schema</span><strong>{payload.schema_version || '1.0'}</strong></div>
            <div><span>Collected</span><strong>{fmt(payload.scan?.finished_at)}</strong></div>
          </div>

          <section className="panel">
            <div className="tabs">
              <button className={tab === 'software' ? 'tab-active' : ''} onClick={() => setTab('software')}>Software <em>{software.length}</em></button>
              <button className={tab === 'changes' ? 'tab-active' : ''} onClick={() => setTab('changes')}>Changes <em>{history.length}</em></button>
            </div>

            {tab === 'software' ? (
              <>
                <div className="toolbar filters">
                  <input placeholder="Search software, vendor, version…" value={search} onChange={(e) => setSearch(e.target.value)} />
                  <select value={source} onChange={(e) => setSource(e.target.value)}>
                    <option value="">All sources</option>
                    {sources.map((s) => <option key={s}>{s}</option>)}
                  </select>
                  <span>{filtered.length} items</span>
                </div>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr><th>Software</th><th>Version</th><th>Vendor</th><th>Source</th><th>Package source</th><th>Arch</th><th>Last seen</th></tr>
                    </thead>
                    <tbody>
                      {filtered.map((x, i) => (
                        <tr key={`${x.name}-${x.source}-${x.architecture}-${i}`}>
                          <td><div className="primary-cell"><strong>{x.name}</strong><span>{x.ecosystem || 'system'}</span></div></td>
                          <td><code>{x.version}</code></td>
                          <td>{x.vendor || '—'}</td>
                          <td><Badge text={x.source || 'unknown'} /></td>
                          <td>{x.package_source || '—'}</td>
                          <td>{x.architecture || '—'}</td>
                          <td>{fmt(x.last_seen)}</td>
                        </tr>
                      ))}
                      {!filtered.length && <tr><td colSpan={7}><Empty text="No software matches filters" /></td></tr>}
                    </tbody>
                  </table>
                </div>
              </>
            ) : (
              <Changes events={history} />
            )}
          </section>
        </>
      )}
    </>
  );
}