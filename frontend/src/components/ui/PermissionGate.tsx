'use client';

import { useAuth } from '@/lib/auth-context';

export function PermissionGate({ permission, children, fallback = null }: { permission: string; children: React.ReactNode; fallback?: React.ReactNode }) {
  const { loading, can } = useAuth();
  if (loading) return null;
  return can(permission) ? <>{children}</> : <>{fallback}</>;
}
