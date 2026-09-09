import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../api/client';
import { Asset } from '../types';
import { useReload } from '../hooks/useReload';
import { AssetTable } from '../components/assets/AssetTable';
import { AssetModal } from '../components/assets/AssetModal';
import { AssetDetails } from '../components/assets/AssetDetails';
import { Loader } from '../components/common/Loader';

export function Assets() {
  const navigate = useNavigate();
  const { id } = useParams();
  const selectedAsset = id ? Number(id) : null;

  const [rows, setRows] = useState<Asset[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [modal, setModal] = useState<Asset | null | false>(false);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState('');
  const [reload, bump] = useReload();

  const load = () => {
    setLoading(true);
    api<{ items: Asset[]; total: number }>('/assets?limit=500')
      .then((x) => { setRows(x.items); setTotal(x.total); })
      .catch((e) => setErr(e.message))
      .finally(() => setLoading(false));
  };
  useEffect(load, [reload]);

  const filtered = rows.filter((a) =>
    [a.hostname, a.fqdn, a.ip_address, a.platform].join(' ').toLowerCase().includes(search.toLowerCase())
  );

  return (
    <>
      <div className="page-head">
        <div>
          <h2>Assets <em>{total}</em></h2>
          <p>Target machines and scan configuration.</p>
        </div>
        <div className="actions">
          <button onClick={load}>Refresh</button>
          <button className="primary" onClick={() => setModal(null)}>＋ Add asset</button>
        </div>
      </div>

      {err && <div className="alert error">{err}</div>}

      <section className="panel">
        <div className="toolbar">
          <input placeholder="Search hostname, IP, platform…" value={search} onChange={(e) => setSearch(e.target.value)} />
          <span>{filtered.length} of {total}</span>
        </div>
        {loading ? (
          <Loader />
        ) : (
          <AssetTable
            rows={filtered}
            onScan={async (id) => { await api(`/assets/${id}/scan`, { method: 'POST' }); bump(); }}
            onEdit={(a) => setModal(a)}
            onToggle={async (a) => { await api(`/assets/${a.id}/${a.enabled ? 'disable' : 'enable'}`, { method: 'POST' }); bump(); }}
            onDelete={async (a) => { if (confirm(`Delete ${a.hostname}?`)) { await api(`/assets/${a.id}`, { method: 'DELETE' }); bump(); } }}
            onInventory={(a) => navigate(`/inventory/${a.id}`)}
          />
        )}
      </section>

      {modal !== false && <AssetModal asset={modal} onClose={() => setModal(false)} onSaved={() => { setModal(false); bump(); }} />}
      {selectedAsset && <AssetDetails id={selectedAsset} onClose={() => navigate('/assets')} />}
    </>
  );
}