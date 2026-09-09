import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { Credential } from '../types';
import { useReload } from '../hooks/useReload';
import { CredentialModal } from '../components/credentials/CredentialModal';
import { Badge } from '../components/common/Badge';
import { Empty } from '../components/common/Empty';
import { fmt } from '../utils/format';

export function Credentials() {
  const [rows, setRows] = useState<Credential[]>([]);
  const [modal, setModal] = useState(false);
  const [edit, setEdit] = useState<Credential | null>(null);
  const [err, setErr] = useState('');
  const [reload, bump] = useReload();

  const load = () => { api<{ items: Credential[] }>('/credentials?limit=500').then((x) => setRows(x.items)).catch((e) => setErr(e.message)); };
+ useEffect(() => { load(); }, [reload]);

  return (
    <>
      <div className="page-head">
        <div>
          <h2>Credentials <em>{rows.length}</em></h2>
          <p>Encrypted connection secrets for remote collection.</p>
        </div>
        <button className="primary" onClick={() => { setEdit(null); setModal(true); }}>＋ Add credential</button>
      </div>

      {err && <div className="alert error">{err}</div>}

      <section className="panel">
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Name</th><th>Type</th><th>Username</th><th>Domain</th><th>Port / TLS</th><th>Last used</th><th></th></tr>
            </thead>
            <tbody>
              {rows.map((c) => (
                <tr key={c.id}>
                  <td><strong>{c.name}</strong></td>
                  <td><Badge text={c.type} /></td>
                  <td>{c.username}</td>
                  <td>{c.domain || '—'}</td>
                  <td>{c.port || 'default'} {c.type === 'winrm_password' && <span className="muted">· {c.verify_tls ? 'TLS' : 'HTTP'}</span>}</td>
                  <td>{fmt(c.last_used_at)}</td>
                  <td>
                    <div className="row-actions">
                      <button onClick={() => { setEdit(c); setModal(true); }}>Edit</button>
                      <button className="danger-text" onClick={async () => {
                        if (confirm(`Delete ${c.name}?`)) {
                          try { await api(`/credentials/${c.id}`, { method: 'DELETE' }); bump(); }
                          catch (e) { setErr(e instanceof Error ? e.message : 'Delete failed'); }
                        }
                      }}>Delete</button>
                    </div>
                  </td>
                </tr>
              ))}
              {!rows.length && <tr><td colSpan={7}><Empty text="No credentials configured" /></td></tr>}
            </tbody>
          </table>
        </div>
      </section>

      {modal && <CredentialModal credential={edit} onClose={() => setModal(false)} onSaved={() => { setModal(false); bump(); }} />}
    </>
  );
}