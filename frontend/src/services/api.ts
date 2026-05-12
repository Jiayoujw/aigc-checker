import type {
  DetectRequest,
  DetectResponse,
  PlagiarismRequest,
  PlagiarismResponse,
  RewriteRequest,
  RewriteResponse,
} from '../types';

const BASE = import.meta.env.PROD
  ? 'https://aigc-checker.onrender.com/api'
  : '/api';

async function request<T>(url: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
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
