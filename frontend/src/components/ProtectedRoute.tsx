'use client';
import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
    const router = useRouter();
    const pathname = usePathname();

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (!token && pathname !== '/login') {
            router.push('/login');
        }
    }, [pathname, router]);

    return <>{children}</>;
}
