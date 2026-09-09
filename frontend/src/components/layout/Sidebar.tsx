import { NavLink } from 'react-router-dom';

const ITEMS: [string, string, string][] = [
  ['/dashboard', 'Dashboard', '⌂'],
  ['/assets', 'Assets', '▣'],
  ['/credentials', 'Credentials', '◆'],
  ['/scans', 'Scans', '◷'],
  ['/inventory', 'Inventory', '☷'],
  ['/audit', 'Audit Log', '≡'],
];

export function Sidebar({ onLogout }: { onLogout: () => void }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark small">IS</div>
        <div>
          <strong>Inventory Scanner</strong>
          <span>Asset inventory</span>
        </div>
      </div>
      <nav>
        {ITEMS.map(([to, label, icon]) => (
          <NavLink key={to} to={to} className={({ isActive }) => (isActive ? 'nav-active' : '')}>
            <span>{icon}</span>
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="sidebar-bottom">
        <div className="secure">
          <span>●</span> API secured
        </div>
        <button className="logout" onClick={onLogout}>Sign out</button>
      </div>
    </aside>
  );
}