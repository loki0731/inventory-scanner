import { Scan } from '../types';

export const fmt = (v?: string | null) => (v ? new Date(v).toLocaleString() : '—');

export const duration = (s: Scan) => {
  if (!s.started_at) return '—';
  if (!s.finished_at) return 'в процессе';
  const seconds = (new Date(s.finished_at).getTime() - new Date(s.started_at).getTime()) / 1000;
  return `${seconds.toFixed(1)}s`;
};

export const statusClass = (s?: string) => `status status-${(s || 'unknown').toLowerCase().replaceAll('_', '-')}`;