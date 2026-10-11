const API_KEY_STORAGE_KEY = "jarvis.apiKey";

export function getApiKey(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage.getItem(API_KEY_STORAGE_KEY);
  } catch {
    return null;
  }
}

export function setApiKey(key: string): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(API_KEY_STORAGE_KEY, key);
  } catch {
    // ignore -- per-viewer convenience only
  }
}

export function clearApiKey(): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.removeItem(API_KEY_STORAGE_KEY);
  } catch {
    // ignore
  }
}

export function reportUrl(scanId: string, format: "json" | "markdown" | "html"): string {
  const key = getApiKey();
  const keyParam = key ? `&api_key=${encodeURIComponent(key)}` : "";
  return `${apiBase()}/api/scans/${scanId}/report?format=${format}${keyParam}`;
}

export function wsUrl(path: string): string {
  const key = getApiKey();
  const keyParam = key ? `?api_key=${encodeURIComponent(key)}` : "";
  return `${wsBase()}${path}${keyParam}`;
}

export function apiBase(): string {
  if (typeof window !== "undefined") {
    return `http://${window.location.hostname}:8001`;
  }
  return "http://localhost:8001";
}

export function wsBase(): string {
  if (typeof window !== "undefined") {
    return `ws://${window.location.hostname}:8001`;
  }
  return "ws://localhost:8001";
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const key = getApiKey();
  const res = await fetch(`${apiBase()}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(key ? { "X-API-Key": key } : {}),
      ...(options?.headers || {}),
    },
  });
  if (res.status === 401) {
    clearApiKey();
    if (typeof window !== "undefined") window.location.reload();
    throw new Error("401 Unauthorized: API key rejected");
  }
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export type ScanStatus = "pending" | "running" | "paused" | "completed" | "failed" | "cancelled";
export type ScanProfile = "passive" | "standard" | "deep";

export interface Scan {
  id: string;
  target: string;
  profile: ScanProfile;
  status: ScanStatus;
  scope_config: Record<string, unknown>;
  error: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  updated_at: string;
}

export interface Asset {
  id: string;
  scan_id: string;
  asset_type: string;
  value: string;
  meta: Record<string, unknown>;
  discovered_at: string;
}

export interface Finding {
  id: string;
  scan_id: string;
  asset_id: string | null;
  category: string;
  severity: string;
  confidence: number;
  observation: string;
  evidence: Record<string, unknown>;
  remediation: string | null;
  human_review_required: boolean;
  created_at: string;
}

export interface ScanEvent {
  id: string;
  scan_id: string;
  event_type: string;
  payload: Record<string, unknown>;
  created_at: string;
}

export interface ActionProposal {
  id: string;
  scan_id: string;
  asset_id: string | null;
  action_type: string;
  rationale: string;
  confidence: number;
  source: string;
  status: "proposed" | "approved" | "rejected";
  policy_reason: string | null;
  created_at: string;
}

export interface AiStatus {
  provider: string;
  installed: boolean;
  reachable: boolean;
  base_url: string | null;
  error: string | null;
}

export interface AiModel {
  name: string;
  size_bytes: number | null;
  parameter_size: string | null;
  quantization: string | null;
}

export interface ScannerInfo {
  name: string;
  category: string;
  risk_level: string;
  enabled: boolean;
}

export interface AppSettings {
  app_name: string;
  environment: string;
  database_url: string;
  ollama_base_url: string;
  ollama_default_model: string;
  orchestration_budget: number;
  enable_cloud_ai: boolean;
  cloud_ai_provider: string;
  openai_default_model: string;
  openai_api_key_configured: boolean;
  anthropic_default_model: string;
  anthropic_api_key_configured: boolean;
  enabled_scanners: string[];
}

export const api = {
  health: () => request<{ status: string; app: string; environment: string; auth_enabled: boolean }>("/api/health"),

  aiStatus: () => request<AiStatus>("/api/ai/status"),
  aiProviders: () => request<AiStatus[]>("/api/ai/providers"),
  aiModels: () => request<AiModel[]>("/api/ai/models"),
  aiTest: (prompt?: string) =>
    request<{ success: boolean; response: string | null; error: string | null; duration_ms: number | null }>(
      "/api/ai/test",
      { method: "POST", body: JSON.stringify({ prompt: prompt || undefined }) }
    ),

  createScan: (target: string, profile: ScanProfile, scopeConfig?: Record<string, unknown>) =>
    request<Scan>("/api/scans", {
      method: "POST",
      body: JSON.stringify({ target, profile, scope_config: scopeConfig || {} }),
    }),
  listScans: (status?: ScanStatus) =>
    request<Scan[]>(`/api/scans${status ? `?status=${status}` : ""}`),
  getScan: (id: string) => request<Scan>(`/api/scans/${id}`),
  startScan: (id: string) => request<Scan>(`/api/scans/${id}/start`, { method: "POST" }),
  pauseScan: (id: string) => request<Scan>(`/api/scans/${id}/pause`, { method: "POST" }),
  resumeScan: (id: string) => request<Scan>(`/api/scans/${id}/resume`, { method: "POST" }),
  cancelScan: (id: string) => request<Scan>(`/api/scans/${id}/cancel`, { method: "POST" }),

  getScanEvents: (id: string) => request<ScanEvent[]>(`/api/scans/${id}/events`),
  getScanAssets: (id: string) => request<Asset[]>(`/api/scans/${id}/assets`),
  getScanFindings: (id: string) => request<Finding[]>(`/api/scans/${id}/findings`),

  orchestrate: (id: string) =>
    request<{ status: string; scan_id: string }>(`/api/scans/${id}/orchestrate`, { method: "POST" }),
  getProposals: (id: string) => request<ActionProposal[]>(`/api/scans/${id}/proposals`),

  triggerSecurityScan: (id: string) =>
    request<{ status: string; scan_id: string }>(`/api/scans/${id}/scan`, { method: "POST" }),

  listScanners: () => request<ScannerInfo[]>("/api/scanners"),
  getSettings: () => request<AppSettings>("/api/settings"),
};
