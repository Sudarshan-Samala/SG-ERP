'use client';
import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
const PUBLIC_ROUTES=new Set(['/login','/signup']);
export function ProtectedRoute({children}:{children:React.ReactNode}){const router=useRouter();const pathname=usePathname();useEffect(()=>{const token=localStorage.getItem('token');if(!token&&!PUBLIC_ROUTES.has(pathname))router.push('/login');if(token&&PUBLIC_ROUTES.has(pathname))router.push('/dashboard');},[pathname,router]);return <>{children}</>}
