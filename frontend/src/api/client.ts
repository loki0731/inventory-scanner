const API = '/api/v1';
const TOKEN_KEY = 'api_token';

export const getToken = () => sessionStorage.getItem(TOKEN_KEY) || '';
export const setToken = (t: string) => sessionStorage.setItem(TOKEN_KEY, t);
export const clearToken = () => sessionStorage.removeItem(TOKEN_KEY);

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers = new Headers(options.headers);
  if (options.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  headers.set('Authorization', `Bearer ${token}`);

  const r = await fetch(API + path, { ...options, headers });

  if (r.status === 401) {
    clearToken();
    window.dispatchEvent(new Event('auth-expired'));
  }

  if (!r.ok) {
    let msg = await r.text();
    try {
      msg = JSON.parse(msg).detail || msg;
    } catch {
      // response wasn't JSON — keep raw text
    }
    throw new Error(msg || `HTTP ${r.status}`);
  }

  return r.status === 204 ? (null as T) : ((await r.json()) as T);
}

export async function downloadExport(assetId: number, ext: 'json' | 'csv') {
  const r = await fetch(`${API}/exports/assets/${assetId}.${ext}`, {
    headers: { Authorization: `Bearer ${getToken()}` },
  });
  if (!r.ok) throw new Error(await r.text());
  const blob = await r.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `asset-${assetId}-inventory.${ext}`;
  a.click();
  URL.revokeObjectURL(url);
}