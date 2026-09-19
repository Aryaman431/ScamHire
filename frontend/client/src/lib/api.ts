// API Client for HireShield Backend
// Matches the backend schemas from backend/app/api/schemas.py

// Type definitions matching backend response schemas
export interface Indicator {
  type: string;
  severity: string;
  evidence: string;
  explanation: string;
}

export interface AnalyzeTextRequest {
  text: string;
}

export interface AnalyzeTextResponse {
  analysis_id: string;
  risk_level: string;
  risk_score: number;
  summary: string;
  indicators: Indicator[];
  recommendations: string[];
}

export interface AnalysisHistoryItem {
  analysis_id: string;
  created_at: string;
  input_type: string;
  risk_score: number;
  risk_level: string;
  summary: string;
}

export interface AnalysisHistoryResponse {
  analyses: AnalysisHistoryItem[];
}

export interface AnalysisDetailResponse {
  analysis_id: string;
  created_at: string;
  input_type: string;
  source_info: Record<string, unknown> | null;
  risk_score: number;
  risk_level: string;
  summary: string;
  indicators: Indicator[];
  recommendations: string[];
  ai_findings: Record<string, unknown> | null;
  deterministic_findings: Record<string, unknown> | null;
}

// API Error class
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public data?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// Get API base URL from environment
function getApiBaseUrl(): string {
  const url = import.meta.env.VITE_API_URL || import.meta.env.NEXT_PUBLIC_API_URL;
  if (!url) {
    throw new Error('API URL not configured. Set VITE_API_URL or NEXT_PUBLIC_API_URL environment variable.');
  }
  // Remove trailing slash
  return url.replace(/\/+$/, '');
}

// Build full API URL
function buildUrl(endpoint: string): string {
  const base = getApiBaseUrl();
  // Ensure endpoint starts with /
  const path = endpoint.startsWith('/') ? endpoint : '/' + endpoint;
  return base + path;
}

// Generic fetch wrapper with error handling
async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = buildUrl(endpoint);
  
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    credentials: 'include',
  });

  if (!response.ok) {
    let errorData: unknown;
    try {
      errorData = await response.json();
    } catch {
      errorData = { detail: response.statusText };
    }
    
    const message = typeof errorData === 'object' && errorData !== null && 'detail' in errorData
      ? String((errorData as Record<string, unknown>).detail)
      : 'API error: ' + response.status + ' ' + response.statusText;
    
    throw new ApiError(message, response.status, errorData);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

// API Functions

export async function analyzeText(text: string): Promise<AnalyzeTextResponse> {
  return fetchApi<AnalyzeTextResponse>('/api/analyze', {
    method: 'POST',
    body: JSON.stringify({ text }),
  });
}

export async function analyzeFile(file: File): Promise<AnalyzeTextResponse> {
  const formData = new FormData();
  formData.append('file', file);
  
  const url = buildUrl('/api/analyze/file');
  const response = await fetch(url, {
    method: 'POST',
    body: formData,
    credentials: 'include',
  });

  if (!response.ok) {
    let errorData: unknown;
    try {
      errorData = await response.json();
    } catch {
      errorData = { detail: response.statusText };
    }
    
    const message = typeof errorData === 'object' && errorData !== null && 'detail' in errorData
      ? String((errorData as Record<string, unknown>).detail)
      : 'API error: ' + response.status + ' ' + response.statusText;
    
    throw new ApiError(message, response.status, errorData);
  }

  return response.json();
}

export async function getAnalyses(limit = 20): Promise<AnalysisHistoryResponse> {
  return fetchApi<AnalysisHistoryResponse>('/api/analyses?limit=' + limit);
}

export async function getAnalysis(id: string): Promise<AnalysisDetailResponse> {
  return fetchApi<AnalysisDetailResponse>('/api/analyses/' + id);
}

export async function healthCheck(): Promise<{ status: string }> {
  return fetchApi<{ status: string }>('/health');
}
