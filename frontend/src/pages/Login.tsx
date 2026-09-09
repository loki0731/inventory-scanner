import { FormEvent, useState } from 'react';
import { api, setToken, clearToken } from '../api/client';

export function Login({ onLogin }: { onLogin: (token: string) => void }) {
  const [value, setValue] = useState('');
  const [err, setErr] = useState('');

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const token = value.trim();
    if (!token) return;
    setErr('');
    try {
      // verify before persisting, so an invalid token never lands in storage
      sessionStorage.setItem('api_token', token);
      await api('/dashboard');
      onLogin(token);
    } catch (ex) {
      clearToken();
      setErr(ex instanceof Error ? ex.message : 'Authentication failed');
    }
  };

  return (
    <div className="login-page">
      <form className="login-card" onSubmit={submit}>
        <div className="brand-mark">IS</div>
        <h1>Inventory Scanner</h1>
        <p>Independent Asset & Software Inventory</p>
        <label>
          API Bearer Token
          <input autoFocus type="password" value={value} onChange={(e) => setValue(e.target.value)} placeholder="Enter API token" />
        </label>
        {err && <div className="alert error">{err}</div>}
        <button className="primary full">Connect</button>
      </form>
    </div>
  );
}