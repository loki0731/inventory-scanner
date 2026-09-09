import { useEffect, useState } from 'react';
import { api } from '../../api/client';
import { Asset, InventoryHistoryEvent } from '../../types';
import { fmt, statusClass } from '../../utils/format';
import { Modal } from '../common/Modal';
import { Empty } from '../common/Empty';
import { Loader } from '../common/Loader';

export function AssetDetails({ id, onClose }: { id: number; onClose: () => void }) {
  const [a, setA] = useState<Asset>();
  const [history, setHistory] = useState<InventoryHistoryEvent[]>([]);

  useEffect(() => {
    Promise.all([
      api<Asset>(`/assets/${id}`),
      api<{ items: InventoryHistoryEvent[] }>(`/assets/${id}/inventory/history?limit=50`),
    ]).then(([x, h]) => {
      setA(x);
      setHistory(h.items);
    });
  }, [id]);

  if (!a) return <Modal title="Asset details" onClose={onClose}><Loader /></Modal>;

  return (
    <Modal title={a.hostname} onClose={onClose} wide>
      <div className="detail-grid">
        <div>
          <span className="eyebrow">Endpoint</span>
          <h3>{a.ip_address}</h3>
          <p>{a.fqdn || 'No FQDN'} · {a.platform}</p>
        </div>
        <div>
          <span className="eyebrow">Scan status</span>
          <h3><span className={statusClass(a.last_scan_status ?? undefined)}>{a.last_scan_status || 'NEVER SCANNED'}</span></h3>
          <p>Last successful inventory: {fmt(a.last_scan_at)}</p>
        </div>
        <div>
          <span className="eyebrow">Configuration</span>
          <p>
            Credential: {a.credential_id ? `#${a.credential_id}` : 'Unassigned'}<br />
            Interval: {a.scan_interval}s<br />
            Enabled: {a.enabled ? 'yes' : 'no'}
          </p>
        </div>
        <div>
          <span className="eyebrow">Fingerprint</span>
          <code>{a.inventory_fingerprint || '—'}</code>
        </div>
      </div>
      <div className="subsection">
        <h3>Recent inventory changes</h3>
        {history.length ? (
          <div className="change-list">
            {history.map((x) => (
              <div key={x.id}>
                <span className={`event event-${x.event_type}`}>{x.event_type}</span>
                <strong>{x.name}</strong>
                <span>{x.old_version || '—'} → {x.new_version || '—'}</span>
                <small>{fmt(x.occurred_at)}</small>
              </div>
            ))}
          </div>
        ) : (
          <Empty text="No inventory changes recorded" />
        )}
      </div>
    </Modal>
  );
}