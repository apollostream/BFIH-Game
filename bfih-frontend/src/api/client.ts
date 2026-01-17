// API client with error handling and credential management

import type { ApiResponse } from '../types';

// Use relative URLs in production (same origin), localhost for development
const API_BASE_URL = import.meta.env.VITE_API_URL ?? '';

// localStorage keys for credentials
const STORAGE_KEYS = {
  API_KEY: 'bfih_openai_api_key',
  VECTOR_STORE_ID: 'bfih_vector_store_id',
  SETUP_COMPLETE: 'bfih_setup_complete',
  DISPLAY_NAME: 'bfih_display_name',
};

// ============================================================================
// Credential Management
// ============================================================================

export function getStoredCredentials(): { apiKey: string | null; vectorStoreId: string | null; displayName: string | null } {
  return {
    apiKey: localStorage.getItem(STORAGE_KEYS.API_KEY),
    vectorStoreId: localStorage.getItem(STORAGE_KEYS.VECTOR_STORE_ID),
    displayName: localStorage.getItem(STORAGE_KEYS.DISPLAY_NAME),
  };
}

export function saveCredentials(apiKey: string, vectorStoreId: string, displayName?: string): void {
  localStorage.setItem(STORAGE_KEYS.API_KEY, apiKey);
  localStorage.setItem(STORAGE_KEYS.VECTOR_STORE_ID, vectorStoreId);
  localStorage.setItem(STORAGE_KEYS.SETUP_COMPLETE, 'true');
  if (displayName) {
    localStorage.setItem(STORAGE_KEYS.DISPLAY_NAME, displayName);
  }
}

export function getDisplayName(): string {
  return localStorage.getItem(STORAGE_KEYS.DISPLAY_NAME) || 'anonymous';
}

export function setDisplayName(name: string): void {
  localStorage.setItem(STORAGE_KEYS.DISPLAY_NAME, name);
}

export function clearCredentials(): void {
  localStorage.removeItem(STORAGE_KEYS.API_KEY);
  localStorage.removeItem(STORAGE_KEYS.VECTOR_STORE_ID);
  localStorage.removeItem(STORAGE_KEYS.SETUP_COMPLETE);
  localStorage.removeItem(STORAGE_KEYS.DISPLAY_NAME);
}

export function isSetupComplete(): boolean {
  return localStorage.getItem(STORAGE_KEYS.SETUP_COMPLETE) === 'true';
}

// ============================================================================
// API Client
// ============================================================================

export async function apiClient<T>(
  endpoint: string,
  options: RequestInit = {},
  skipCredentials: boolean = false
): Promise<ApiResponse<T>> {
  try {
    const url = `${API_BASE_URL}${endpoint}`;

    // Build headers with credentials from localStorage
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    // Add credentials for authenticated endpoints (unless skipped)
    if (!skipCredentials) {
      const { apiKey, vectorStoreId, displayName } = getStoredCredentials();
      if (apiKey) {
        headers['User-OpenAI-API-Key'] = apiKey;
      }
      if (vectorStoreId) {
        headers['User-Vector-Store-ID'] = vectorStoreId;
      }
      if (displayName) {
        headers['User-Display-Name'] = displayName;
      }
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    const data = await response.json();

    if (!response.ok) {
      return {
        data: null,
        error: data.error || data.detail || `HTTP ${response.status}`,
        status: response.status,
      };
    }

    return {
      data: data as T,
      error: null,
      status: response.status,
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Network error';
    return {
      data: null,
      error: message,
      status: 0,
    };
  }
}

// GET request helper with cache busting for status polling
export async function get<T>(endpoint: string, bustCache: boolean = false): Promise<ApiResponse<T>> {
  // Add cache-busting timestamp for polling endpoints to avoid stale cached responses
  const url = bustCache ? `${endpoint}${endpoint.includes('?') ? '&' : '?'}_t=${Date.now()}` : endpoint;
  return apiClient<T>(url, {
    method: 'GET',
    // Add no-cache headers
    headers: bustCache ? { 'Cache-Control': 'no-cache' } : undefined,
  });
}

// POST request helper
export async function post<T>(endpoint: string, body: unknown): Promise<ApiResponse<T>> {
  return apiClient<T>(endpoint, {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

// Health check - returns full server status
interface HealthResponse {
  status: string;
  timestamp: string;
  service: string;
  requires_api_key: boolean;
}

export async function checkHealth(): Promise<{ healthy: boolean; requiresApiKey: boolean }> {
  const response = await get<HealthResponse>('/api/health');
  return {
    healthy: response.status === 200,
    requiresApiKey: response.data?.requires_api_key ?? true, // Default to requiring key if unknown
  };
}

// Check if setup is needed (considers both local storage AND server state)
export async function checkSetupNeeded(): Promise<boolean> {
  // Check server health and requirements
  const healthStatus = await checkHealth();

  if (!healthStatus.healthy) {
    // Server is down, can't determine - assume setup needed
    return true;
  }

  if (!healthStatus.requiresApiKey) {
    // Server has a default API key configured, no setup needed
    return false;
  }

  // Server requires API key - check if user has completed setup
  return !isSetupComplete();
}

// ============================================================================
// Setup API
// ============================================================================

interface SetupResponse {
  success: boolean;
  vector_store_id: string;
  message: string;
}

/**
 * Run first-time setup with user's API key and display name.
 * Creates a vector store and uploads the BFIH methodology.
 */
export async function runSetup(apiKey: string, displayName?: string): Promise<ApiResponse<SetupResponse>> {
  const response = await apiClient<SetupResponse>(
    '/api/setup',
    {
      method: 'POST',
      body: JSON.stringify({ api_key: apiKey }),
    },
    true // Skip adding credentials from localStorage
  );

  // If successful, save credentials
  if (response.data?.success && response.data.vector_store_id) {
    saveCredentials(apiKey, response.data.vector_store_id, displayName);
  }

  return response;
}
