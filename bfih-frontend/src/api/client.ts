// API client with error handling and credential management

import type { ApiResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// localStorage keys for credentials
const STORAGE_KEYS = {
  API_KEY: 'bfih_openai_api_key',
  VECTOR_STORE_ID: 'bfih_vector_store_id',
  SETUP_COMPLETE: 'bfih_setup_complete',
};

// ============================================================================
// Credential Management
// ============================================================================

export function getStoredCredentials(): { apiKey: string | null; vectorStoreId: string | null } {
  return {
    apiKey: localStorage.getItem(STORAGE_KEYS.API_KEY),
    vectorStoreId: localStorage.getItem(STORAGE_KEYS.VECTOR_STORE_ID),
  };
}

export function saveCredentials(apiKey: string, vectorStoreId: string): void {
  localStorage.setItem(STORAGE_KEYS.API_KEY, apiKey);
  localStorage.setItem(STORAGE_KEYS.VECTOR_STORE_ID, vectorStoreId);
  localStorage.setItem(STORAGE_KEYS.SETUP_COMPLETE, 'true');
}

export function clearCredentials(): void {
  localStorage.removeItem(STORAGE_KEYS.API_KEY);
  localStorage.removeItem(STORAGE_KEYS.VECTOR_STORE_ID);
  localStorage.removeItem(STORAGE_KEYS.SETUP_COMPLETE);
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
      const { apiKey, vectorStoreId } = getStoredCredentials();
      if (apiKey) {
        headers['User-OpenAI-API-Key'] = apiKey;
      }
      if (vectorStoreId) {
        headers['User-Vector-Store-ID'] = vectorStoreId;
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

// GET request helper
export async function get<T>(endpoint: string): Promise<ApiResponse<T>> {
  return apiClient<T>(endpoint, { method: 'GET' });
}

// POST request helper
export async function post<T>(endpoint: string, body: unknown): Promise<ApiResponse<T>> {
  return apiClient<T>(endpoint, {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

// Health check
export async function checkHealth(): Promise<boolean> {
  const response = await get('/api/health');
  return response.status === 200;
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
 * Run first-time setup with user's API key.
 * Creates a vector store and uploads the BFIH methodology.
 */
export async function runSetup(apiKey: string): Promise<ApiResponse<SetupResponse>> {
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
    saveCredentials(apiKey, response.data.vector_store_id);
  }

  return response;
}
