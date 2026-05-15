import type {
  DetectRequest,
  DetectResponse,
  CompareResponse,
  RewriteRequest,
  RewriteResponse,
  HistoryRecord,
  CNKIDetectRequest,
  CNKIDetectResponse,
  InfoDiffResponse,
  RewriteV2Request,
  RewriteV2Response,
  WeipuDetectResponse,
  WanfangDetectResponse,
  CrossPlatformResponse,
  CreditStats,
  QuotaResponse,
  FeedbackRequest,
  FeedbackResponse,
  CalibrationStats,
  AccuracyDashboardResponse,
  ErrorDistributionResponse,
  ReportParseRequest,
  ReportParseResponse,
  ReportRewriteRequest,
  ReportRewriteResponse,
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

export async function detectCompare(
  data: DetectRequest
): Promise<CompareResponse> {
  return request<CompareResponse>('/detect-compare', data);
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

// ---- CNKI-specific API calls ----

export async function detectCnki(data: CNKIDetectRequest): Promise<CNKIDetectResponse> {
  return request<CNKIDetectResponse>('/detect-cnki', data);
}

export async function detectInfoDiff(data: CNKIDetectRequest): Promise<InfoDiffResponse> {
  return request<InfoDiffResponse>('/detect-info-diff', data);
}

export async function rewriteV2(data: RewriteV2Request): Promise<RewriteV2Response> {
  return request<RewriteV2Response>('/rewrite-v2', data);
}

export async function detectWeipu(data: CNKIDetectRequest): Promise<WeipuDetectResponse> {
  return request<WeipuDetectResponse>('/detect-weipu', data);
}

export async function detectWanfang(data: CNKIDetectRequest): Promise<WanfangDetectResponse> {
  return request<WanfangDetectResponse>('/detect-wanfang', data);
}

export async function detectAllPlatforms(data: CNKIDetectRequest): Promise<CrossPlatformResponse> {
  return request<CrossPlatformResponse>('/detect-all-platforms', data);
}

// ---- Credit/Quota API calls ----

export async function getCreditsStats(): Promise<CreditStats> {
  return authGet<CreditStats>('/credits/stats');
}

export async function getCreditsQuota(): Promise<QuotaResponse> {
  return authGet<QuotaResponse>('/credits/quota');
}

export async function addCredits(amount: number): Promise<{ success: boolean; purchased_credits: number }> {
  return request('/credits/add', { amount });
}

// ---- Calibration / Feedback API calls ----

export async function submitFeedback(data: FeedbackRequest): Promise<FeedbackResponse> {
  return request<FeedbackResponse>('/calibration/feedback', data);
}

export async function getCalibrationStats(): Promise<CalibrationStats> {
  return authGet<CalibrationStats>('/calibration/stats');
}

// ---- Accuracy Dashboard API calls ----

export async function getAccuracyDashboard(): Promise<AccuracyDashboardResponse> {
  return authGet<AccuracyDashboardResponse>('/accuracy/dashboard');
}

export async function getErrorDistribution(platform: string): Promise<ErrorDistributionResponse> {
  return authGet<ErrorDistributionResponse>(`/accuracy/error-distribution/${platform}`);
}

// ---- Report Parse / Rewrite API calls ----

export async function parseReport(data: ReportParseRequest): Promise<ReportParseResponse> {
  return request<ReportParseResponse>('/report/parse', data);
}

export async function rewriteFromReport(data: ReportRewriteRequest): Promise<ReportRewriteResponse> {
  return request<ReportRewriteResponse>('/rewrite-from-report', data);
}
