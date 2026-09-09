import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { Asset, Scan } from '../types';
import { fmt, statusClass } from '../utils/format';
import { Empty } from '../components/common/Empty';
import { Loader } from '../components/common/Loader';

type DashboardData = {
  total_assets: number;
  healthy_assets: number;
  failed_assets: number;
  never_scanned: number;
  total_software: number;
};

export function Dashboard() {
  const navigate = useNavigate();
  const [data, setData] = useState<DashboardData>();
  const [assets, setAssets] = useState<Asset[]>([]);
  const [scans, setScans] = useState<Scan[]>([]);
  const [err, setErr] = useState('');

  useEffect(() => {
    Promise.all([
      api<DashboardData>('/dashboard'),
      api<{ items: Asset[] }>('/assets?limit=8'),
      api<{ items: Scan[] }>('/scans?limit=8'),
    ])
      .then(([d, a, s]) => {
        setData(d);
        setAssets(a.items);
        setScans(s.items);
      })
      .catch((e) => setErr(e.message));
  }, []);

  if (err) return <div className="alert error">{err}</div>;
  if (!data) return <Loader />;

  const metrics: [string, number, string, string][] = [
    ['Total Assets', data.total_assets, 'Registered targets', ''],
    ['Healthy', data.healthy_assets, 'Last known scan healthy', 'good'],
    ['Failed', data.failed_assets, 'Latest scan failed', 'bad'],
    ['Never Scanned', data.never_scanned, 'Awaiting first scan', 'warn'],
    ['Software', data.total_software, 'Active inventory items', ''],
  ];

  return (
    <>
      <div className="page-head">
        <div>
          <h2>Inventory overview</h2>
          <p>Current state across registered assets.</p>
        </div>
        <button onClick={() => navigate('/assets')}>Manage assets →</button>
      </div>

      <div className="metric-grid">
        {metrics.map(([label, value, sub, cls]) => (
          <div className="metric" key={label}>
            <span>{label}</span>
            <strong className={cls}>{value}</strong>
            <small>{sub}</small>
          </div>
        ))}
      </div>

      <div className="grid-2">
        <section className="panel">
          <div className="panel-title">
            <div>
              <h3>Recent scans</h3>
              <span>Latest inventory collection jobs</span>
            </div>
            <button className="ghost" onClick={() => navigate('/scans')}>View all</button>
          </div>
          {scans.length ? (
            <div className="scan-list">
              {scans.slice(0, 6).map((s) => (
                <div className="scan-row" key={s.id}>
                  <div>
                    <strong>Scan #{s.id}</strong>
                    <span>Asset #{s.asset_id} · {fmt(s.started_at)}</span>
                  </div>
                  <span className={statusClass(s.status)}>{s.status}</span>
                </div>
              ))}
            </div>
          ) : (
            <Empty text="No scans yet" />
          )}
        </section>

        <section className="panel">
          <div className="panel-title">
            <div>
              <h3>Assets</h3>
              <span>Latest registered targets</span>
            </div>
            <button className="ghost" onClick={() => navigate('/assets')}>View all</button>
          </div>
          {assets.length ? (
            <div className="asset-list">
              {assets.slice(0, 6).map((a) => (
                <button key={a.id} onClick={() => navigate(`/assets/${a.id}`)}>
                  <div>
                    <strong>{a.hostname}</strong>
                    <span>{a.ip_address} · {a.platform}</span>
                  </div>
                  <span className={statusClass(a.last_scan_status ?? undefined)}>
                    {a.last_scan_status || 'NEVER SCANNED'}
                  </span>
                </button>
              ))}
            </div>
          ) : (
            <Empty text="No assets configured" />
          )}
        </section>
      </div>

      <section className="panel quick">
        <div>
          <h3>Quick actions</h3>
          <span>Common inventory operations</span>
        </div>
        <div className="quick-actions">
          <button onClick={() => navigate('/assets')}>＋ Add or manage assets</button>
          <button onClick={() => navigate('/credentials')}>＋ Create credential</button>
          <button onClick={() => navigate('/scans')}>◷ Review scans</button>
          <button onClick={() => navigate('/inventory')}>☷ Browse inventory</button>
        </div>
      </section>
    </>
  );
}