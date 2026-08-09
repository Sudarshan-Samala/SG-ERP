'use client';

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import api, { clearAccessToken, refreshAccessToken, setAccessToken } from '@/lib/api';

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
    // Login has no refresh session yet. Avoid an unnecessary refresh request
    // and, more importantly, avoid an in-flight unauthenticated refresh racing
    // with a successful login and clearing the newly issued access token.
    if (typeof window !== 'undefined' && window.location.pathname === '/login') {
      setLoading(false);
      return;
    }

    try {
      const token = await refreshAccessToken();
      if (!token) throw new Error('No refresh session');
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
