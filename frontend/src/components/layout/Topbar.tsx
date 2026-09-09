import { useLocation } from 'react-router-dom';
import { Page } from '../../types';

const TITLES: Record<Page, string> = {
  dashboard: 'Dashboard',
  assets: 'Assets',
  credentials: 'Credentials',
  scans: 'Scans',
  inventory: 'Inventory',
  audit: 'Audit Log',
};

export function Topbar() {
  const { pathname } = useLocation();
  const page = (pathname.split('/')[1] || 'dashboard') as Page;
  return (
    <header className="topbar">
      <div>
        <h1>{TITLES[page] ?? 'Inventory Scanner'}</h1>
        <span>Independent credentialed asset inventory</span>
      </div>
      <div className="live"><i /> System connected</div>
    </header>
  );
}