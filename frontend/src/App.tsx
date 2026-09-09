import { useEffect, useState } from 'react';
import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { Login } from './pages/Login';
import { Sidebar } from './components/layout/Sidebar';
import { Topbar } from './components/layout/Topbar';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { getToken, setToken as persistToken, clearToken } from './api/client';

// Pages below will be added next — placeholders keep App.tsx wiring buildable meanwhile.
import { Dashboard } from './pages/Dashboard';
import { Assets } from './pages/Assets';
import { Credentials } from './pages/Credentials';
import { Scans } from './pages/Scans';
import { Inventory } from './pages/Inventory';
import { Audit } from './pages/Audit';

function Shell({ onLogout }: { onLogout: () => void }) {
  const location = useLocation();
  return (
    <div className="shell">
      <Sidebar onLogout={onLogout} />
      <main className="main">
        <Topbar />
        <ErrorBoundary resetKey={location.pathname}>
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/assets" element={<Assets />} />
            <Route path="/assets/:id" element={<Assets />} />
            <Route path="/credentials" element={<Credentials />} />
            <Route path="/scans" element={<Scans />} />
            <Route path="/inventory" element={<Inventory />} />
            <Route path="/inventory/:assetId" element={<Inventory />} />
            <Route path="/audit" element={<Audit />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </ErrorBoundary>
      </main>
    </div>
  );
}

export function App() {
  const [token, setTokenState] = useState(getToken());

  useEffect(() => {
    const onExpire = () => setTokenState('');
    window.addEventListener('auth-expired', onExpire);
    return () => window.removeEventListener('auth-expired', onExpire);
  }, []);

  return (
    <BrowserRouter>
      {token ? (
        <Shell
          onLogout={() => {
            clearToken();
            setTokenState('');
          }}
        />
      ) : (
        <Login
          onLogin={(t) => {
            persistToken(t);
            setTokenState(t);
          }}
        />
      )}
    </BrowserRouter>
  );
}