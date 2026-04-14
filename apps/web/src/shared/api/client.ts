const base = import.meta.env.VITE_API_BASE ?? "";

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${base}${path}`);
  const body = await res.json();
  if (!res.ok || body.success === false) {
    throw new Error(body.error?.message ?? res.statusText);
  }
  return body.data as T;
}

export async function apiPost<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${base}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  const body = await res.json();
  if (!res.ok || body.success === false) {
    throw new Error(body.error?.message ?? res.statusText);
  }
  return body.data as T;
}
