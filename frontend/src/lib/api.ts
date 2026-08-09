import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';

declare module 'axios' {
  interface AxiosRequestConfig {
    _skipAuthRefresh?: boolean;
    _retry?: boolean;
  }
}

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
});

let accessToken: string | null = null;
let csrfToken: string | null = null;
let refreshPromise: Promise<string | null> | null = null;
let csrfPromise: Promise<string | null> | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
}

export function clearAccessToken() {
  accessToken = null;
}

export function setCsrfToken(token: string | null) {
  csrfToken = token;
}

export function clearCsrfToken() {
  csrfToken = null;
}

async function ensureCsrfToken() {
  if (csrfToken) return csrfToken;
  if (!csrfPromise) {
    csrfPromise = api
      .get('/auth/csrf', { _skipAuthRefresh: true })
      .then((response) => {
        const token = response.data?.csrf_token;
        if (typeof token !== 'string') throw new Error('CSRF bootstrap response did not contain a token');
        csrfToken = token;
        return token;
      })
      .catch(() => null)
      .finally(() => {
        csrfPromise = null;
      });
  }
  return csrfPromise;
}

function isStateChanging(method?: string) {
  return Boolean(method && ['post', 'put', 'patch', 'delete'].includes(method.toLowerCase()));
}

export async function refreshAccessToken() {
  if (!refreshPromise) {
    refreshPromise = (async () => {
      const csrf = await ensureCsrfToken();
      if (!csrf) return null;
      try {
        // Pass the CSRF header explicitly as well as through the interceptor.
        // This avoids relying on Axios request-interceptor ordering for the
        // cross-origin refresh request.
        const response = await api.post('/auth/refresh', undefined, {
          _skipAuthRefresh: true,
          headers: { 'X-CSRF-Token': csrf },
        });
        const token = response.data?.access_token;
        const nextCsrf = response.data?.csrf_token;
        if (typeof token !== 'string' || typeof nextCsrf !== 'string') throw new Error('Refresh response was incomplete');
        accessToken = token;
        csrfToken = nextCsrf;
        return token;
      } catch {
        accessToken = null;
        csrfToken = null;
        return null;
      }
    })().finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

api.interceptors.request.use((config) => {
  if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`;
  if (csrfToken && isStateChanging(config.method)) config.headers['X-CSRF-Token'] = csrfToken;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as (InternalAxiosRequestConfig & { _skipAuthRefresh?: boolean; _retry?: boolean }) | undefined;
    if (
      typeof window !== 'undefined' &&
      error.response?.status === 401 &&
      original &&
      !original._retry &&
      !original._skipAuthRefresh &&
      !String(original.url || '').includes('/auth/login')
    ) {
      original._retry = true;
      const token = await refreshAccessToken();
      if (token) {
        original.headers.Authorization = `Bearer ${token}`;
        return api(original);
      }
      clearAccessToken();
      clearCsrfToken();
      if (window.location.pathname !== '/login') {
        window.location.assign(`/login?next=${encodeURIComponent(window.location.pathname)}`);
      }
    }
    return Promise.reject(error);
  },
);

export function apiErrorMessage(error: unknown, fallback: string) {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string' && detail.trim()) return detail;
  }
  return fallback;
}

export default api;
