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
let refreshPromise: Promise<string | null> | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
}

export function clearAccessToken() {
  accessToken = null;
}

function csrfToken() {
  if (typeof document === 'undefined') return null;
  const match = document.cookie.match(/(?:^|; )sg_csrf=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : null;
}

function isStateChanging(method?: string) {
  return Boolean(method && ['post', 'put', 'patch', 'delete'].includes(method.toLowerCase()));
}

async function refreshAccessToken() {
  if (!refreshPromise) {
    refreshPromise = api
      .post('/auth/refresh', undefined, { _skipAuthRefresh: true })
      .then((response) => {
        const token = response.data?.access_token;
        if (typeof token !== 'string') throw new Error('Refresh response did not contain an access token');
        accessToken = token;
        return token;
      })
      .catch(() => {
        accessToken = null;
        return null;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

api.interceptors.request.use((config) => {
  if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`;
  const csrf = csrfToken();
  if (csrf && isStateChanging(config.method)) config.headers['X-CSRF-Token'] = csrf;
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
