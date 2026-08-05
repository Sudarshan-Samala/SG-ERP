'use client';

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import api from '@/lib/api';

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
}

const AuthContext = createContext<AuthContextValue>({ user: null, loading: true, can: () => false, refresh: async () => undefined });

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    if (typeof window === 'undefined' || !localStorage.getItem('token')) {
      setUser(null); setLoading(false); return;
    }
    try {
      const response = await api.get<CurrentUser>('/auth/me');
      setUser(response.data);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void refresh(); }, [refresh]);

  const value = useMemo(() => ({
    user,
    loading,
    can: (permission?: string) => !permission || Boolean(user?.is_superuser || user?.permissions.includes(permission)),
    refresh,
  }), [user, loading, refresh]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() { return useContext(AuthContext); }
