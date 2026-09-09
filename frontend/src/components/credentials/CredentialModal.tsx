import { FormEvent, useState } from 'react';
import { api } from '../../api/client';
import { Credential } from '../../types';
import { Modal } from '../common/Modal';
import { Field } from '../common/Field';

type FormState = {
  name: string;
  type: string;
  username: string;
  domain: string;
  secret: string;
  port: string;
  verify_tls: boolean;
};

export function CredentialModal({ credential, onClose, onSaved }: { credential: Credential | null; onClose: () => void; onSaved: () => void }) {
  const [form, setForm] = useState<FormState>(
    credential
      ? { name: credential.name, type: credential.type, username: credential.username, domain: credential.domain || '', secret: '', port: credential.port ? String(credential.port) : '', verify_tls: credential.verify_tls }
      : { name: '', type: 'ssh_password', username: '', domain: '', secret: '', port: '', verify_tls: true }
  );
  const [err, setErr] = useState('');
  const [showSecret, setShowSecret] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      const payload = {
        name: form.name,
        type: form.type,
        username: form.username,
        domain: form.domain || null,
        port: form.port ? Number(form.port) : null,
        verify_tls: form.verify_tls,
        ...((!credential || form.secret) ? { secret: form.secret } : {}),
      };
      await api(credential ? `/credentials/${credential.id}` : '/credentials', {
        method: credential ? 'PUT' : 'POST',
        body: JSON.stringify(payload),
      });
      onSaved();
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Save failed');
    }
  };

  const isMultiline = form.type === 'ssh_private_key';

  return (
    <Modal title={credential ? 'Edit credential' : 'Add credential'} onClose={onClose}>
      <form onSubmit={submit} className="form-grid">
        <Field label="Name">
          <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        </Field>
        <Field label="Type">
          <select value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}>
            <option value="ssh_password">SSH password</option>
            <option value="ssh_private_key">SSH private key</option>
            <option value="winrm_password">WinRM username / password</option>
          </select>
        </Field>
        <Field label="Username">
          <input required value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} />
        </Field>
        <Field label="Domain">
          <input value={form.domain} onChange={(e) => setForm({ ...form, domain: e.target.value })} placeholder="Windows domain (optional)" />
        </Field>

        <Field label={credential ? 'New secret (optional)' : 'Secret'} full>
          <div className="secret-field">
            {isMultiline ? (
              <textarea
                required={!credential}
                rows={credential ? 3 : 5}
                value={form.secret}
                onChange={(e) => setForm({ ...form, secret: e.target.value })}
                placeholder="-----BEGIN PRIVATE KEY-----"
                className={showSecret ? '' : 'secret-hidden'}
                spellCheck={false}
                autoComplete="off"
              />
            ) : (
              <input
                type={showSecret ? 'text' : 'password'}
                required={!credential}
                value={form.secret}
                onChange={(e) => setForm({ ...form, secret: e.target.value })}
                autoComplete="new-password"
              />
            )}
            <button type="button" className="secret-toggle" onClick={() => setShowSecret((s) => !s)}>
              {showSecret ? 'Hide' : 'Show'}
            </button>
          </div>
        </Field>

        <Field label="Port">
          <input type="number" min="1" max="65535" value={form.port} onChange={(e) => setForm({ ...form, port: e.target.value })} />
        </Field>
        {form.type === 'winrm_password' && (
          <label className="check">
            <input type="checkbox" checked={form.verify_tls} onChange={(e) => setForm({ ...form, verify_tls: e.target.checked })} /> HTTPS / verify TLS
          </label>
        )}
        {err && <div className="alert error full">{err}</div>}
        <div className="modal-actions full">
          <button type="button" onClick={onClose}>Cancel</button>
          <button className="primary">{credential ? 'Save changes' : 'Create credential'}</button>
        </div>
      </form>
    </Modal>
  );
}