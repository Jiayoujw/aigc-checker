import type {
  DetectRequest,
  DetectResponse,
  PlagiarismRequest,
  PlagiarismResponse,
  RewriteRequest,
  RewriteResponse,
  HistoryRecord,
} from '../types';

const BASE = import.meta.env.PROD
  ? 'https://aigc-checker.onrender.com/api'
  : '/api';

function getToken(): string | null {
  return localStorage.getItem('auth_token');
}

async function request<T>(url: string, body: unknown): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  const token = getToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE}${url}`, {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Request failed: ${res.status}`);
  }

  return res.json();
}

async function authGet<T>(url: string): Promise<T> {
  const token = getToken();
  const res = await fetch(`${BASE}${url}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

async function authDelete<T>(url: string): Promise<T> {
  const token = getToken();
  const res = await fetch(`${BASE}${url}`, {
    method: 'DELETE',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export async function detectAigc(data: DetectRequest): Promise<DetectResponse> {
  return request<DetectResponse>('/detect-aigc', data);
}

export async function checkPlagiarism(
  data: PlagiarismRequest
): Promise<PlagiarismResponse> {
  return request<PlagiarismResponse>('/check-plagiarism', data);
}

export async function rewriteText(
  data: RewriteRequest
): Promise<RewriteResponse> {
  return request<RewriteResponse>('/rewrite', data);
}

export async function getHistory(
  type?: string,
  limit = 20
): Promise<HistoryRecord[]> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (type) params.set('record_type', type);
  return authGet<HistoryRecord[]>(`/history?${params}`);
}

export async function deleteHistory(id: string): Promise<void> {
  return authDelete(`/history/${id}`);
}
