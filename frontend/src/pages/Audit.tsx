import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { AuditEvent } from '../types';
import { fmt, statusClass } from '../utils/format';
import { Empty } from '../components/common/Empty';

export function Audit() {
  const [rows, setRows] = useState<AuditEvent[]>([]);
  const [err, setErr] = useState('');

  useEffect(() => {
    api<AuditEvent[]>('/audit?limit=500').then(setRows).catch((e) => setErr(e.message));
  }, []);

  return (
    <>
      <div className="page-head">
        <div>
          <h2>Audit Log <em>{rows.length}</em></h2>
          <p>Security-relevant actions performed through the API.</p>
        </div>
      </div>

      {err && <div className="alert error">{err}</div>}

      <section className="panel">
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Time</th><th>Action</th><th>Resource</th><th>Outcome</th><th>Details</th></tr>
            </thead>
            <tbody>
              {rows.map((x) => (
                <tr key={x.id}>
                  <td>{fmt(x.occurred_at)}</td>
                  <td><strong>{x.action}</strong></td>
                  <td>{x.resource_type} #{x.resource_id ?? '—'}</td>
                  <td><span className={statusClass(x.outcome)}>{x.outcome}</span></td>
                  <td><code>{x.details ? JSON.stringify(x.details) : '—'}</code></td>
                </tr>
              ))}
              {!rows.length && <tr><td colSpan={5}><Empty text="No audit events" /></td></tr>}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}