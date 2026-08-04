'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import api, { TOKEN_STORAGE_KEY } from '@/lib/api';

export type AuthenticatedUser = {
  id: string;
  email: string;
  full_name: string | null;
  organization_id: string;
  is_active: boolean;
  is_superuser: boolean;
};

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [checking, setChecking] = useState(pathname !== '/login');

  useEffect(() => {
    let cancelled = false;

    const checkSession = async () => {
      const token = localStorage.getItem(TOKEN_STORAGE_KEY);

      if (pathname === '/login') {
        if (!token) {
          setChecking(false);
          return;
        }

        try {
          await api.get('/auth/me');
          if (!cancelled) router.replace('/dashboard');
        } catch {
          localStorage.removeItem(TOKEN_STORAGE_KEY);
          if (!cancelled) setChecking(false);
        }
        return;
      }

      if (!token) {
        router.replace('/login');
        return;
      }

      try {
        await api.get('/auth/me');
        if (!cancelled) setChecking(false);
      } catch {
        localStorage.removeItem(TOKEN_STORAGE_KEY);
        if (!cancelled) router.replace('/login');
      }
    };

    void checkSession();
    return () => {
      cancelled = true;
    };
  }, [pathname, router]);

  if (checking) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 text-sm text-slate-500">
        Verifying secure session...
      </div>
    );
  }

  return <>{children}</>;
}
