'use client';

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import api, { clearAccessToken, setAccessToken } from '@/lib/api';

export interface AuthBranch { id: string; name: string; code: string }
export interface CurrentUser {
  id: string;
  email: string;
  full_name?: string | null;
  organization_id: string;
  is_active: boolean;
  is_superuser: boolean;
  permissions: string[];
  branches: AuthBranch[];
}

interface AuthContextValue {
  user: CurrentUser | null;
  loading: boolean;
  can: (permission?: string) => boolean;
  refresh: () => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue>({
  user: null,
  loading: true,
  can: () => false,
  refresh: async () => undefined,
  logout: async () => undefined,
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const tokenResponse = await api.post('/auth/refresh');
      const token = tokenResponse.data?.access_token;
      if (typeof token !== 'string') throw new Error('No access token');
      setAccessToken(token);
      const response = await api.get<CurrentUser>('/auth/me');
      setUser(response.data);
    } catch {
      clearAccessToken();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await api.post('/auth/logout');
    } finally {
      clearAccessToken();
      setUser(null);
    }
  }, []);

  useEffect(() => { void refresh(); }, [refresh]);

  const value = useMemo(() => ({
    user,
    loading,
    can: (permission?: string) => !permission || Boolean(user?.is_superuser || user?.permissions.includes(permission)),
    refresh,
    logout,
  }), [user, loading, refresh, logout]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() { return useContext(AuthContext); }
