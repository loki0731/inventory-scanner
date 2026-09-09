import { Asset } from '../../types';
import { fmt, statusClass } from '../../utils/format';
import { Badge } from '../common/Badge';
import { Empty } from '../common/Empty';

type Props = {
  rows: Asset[];
  onScan: (id: number) => Promise<void>;
  onEdit: (a: Asset) => void;
  onToggle: (a: Asset) => Promise<void>;
  onDelete: (a: Asset) => Promise<void>;
  onInventory: (a: Asset) => void;
};

export function AssetTable({ rows, onScan, onEdit, onToggle, onDelete, onInventory }: Props) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Asset</th><th>Platform</th><th>Credential</th><th>Status</th>
            <th>Last scan</th><th>Interval</th><th></th>
          </tr>
        </thead>
        <tbody>
          {rows.map((a) => (
            <tr key={a.id}>
              <td>
                <div className="primary-cell">
                  <strong>{a.hostname}</strong>
                  <span>{a.ip_address}{a.fqdn ? ` · ${a.fqdn}` : ''}</span>
                </div>
              </td>
              <td><Badge text={a.platform.toUpperCase()} /></td>
              <td>{a.credential_id ? `#${a.credential_id}` : <span className="muted">Unassigned</span>}</td>
              <td><span className={statusClass(a.last_scan_status ?? undefined)}>{a.last_scan_status || 'NEVER SCANNED'}</span></td>
              <td>{fmt(a.last_scan_at)}</td>
              <td>{Math.round(a.scan_interval / 3600)}h</td>
              <td>
                <div className="row-actions">
                  <button title="Scan" onClick={() => onScan(a.id)}>Scan</button>
                  <button title="Inventory" onClick={() => onInventory(a)}>View</button>
                  <button title="Edit" onClick={() => onEdit(a)}>Edit</button>
                  <button onClick={() => onToggle(a)}>{a.enabled ? 'Disable' : 'Enable'}</button>
                  <button className="danger-text" onClick={() => onDelete(a)}>Delete</button>
                </div>
              </td>
            </tr>
          ))}
          {!rows.length && <tr><td colSpan={7}><Empty text="No matching assets" /></td></tr>}
        </tbody>
      </table>
    </div>
  );
}