'use client';

import { useState } from 'react';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { Eye, EyeOff, Loader2, LockKeyhole, Mail } from 'lucide-react';
import api, { TOKEN_STORAGE_KEY } from '@/lib/api';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const formData = new URLSearchParams();
      formData.append('username', email.trim());
      formData.append('password', password);

      const res = await api.post('/auth/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });

      localStorage.setItem(TOKEN_STORAGE_KEY, res.data.access_token);
      await api.get('/auth/me');
      router.replace('/dashboard');
    } catch {
      localStorage.removeItem(TOKEN_STORAGE_KEY);
      setError('Invalid email or password. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-slate-100 px-4 py-10">
      <div className="absolute left-[-120px] top-[-120px] h-80 w-80 rounded-full bg-blue-200/40 blur-3xl" />
      <div className="absolute bottom-[-150px] right-[-100px] h-96 w-96 rounded-full bg-indigo-200/40 blur-3xl" />
      <div className="relative w-full max-w-[430px]">
        <div className="card overflow-hidden">
          <div className="border-b border-slate-100 bg-white px-8 pb-6 pt-8 text-center">
            <div className="mx-auto mb-4 flex h-20 w-20 items-center justify-center overflow-hidden rounded-2xl bg-white p-1 shadow-sm ring-1 ring-slate-200">
              <Image src="/sampurna-gnana-logo.png" alt="Sampurna Gnana" width={80} height={80} priority className="h-full w-full object-contain" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">Sampurna Gnana <span className="text-blue-600">ERP</span></h1>
            <p className="mt-2 text-sm text-slate-500">Sign in to your school management account</p>
          </div>
          <div className="bg-white px-8 py-7">
            {error && <div role="alert" className="mb-5 rounded-md border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-700">{error}</div>}
            <form onSubmit={handleLogin} className="space-y-5">
              <div>
                <label htmlFor="email" className="label">Email address</label>
                <div className="relative">
                  <Mail size={17} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input id="email" type="email" autoComplete="username" required autoFocus value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Enter your email" className="input pl-10" />
                </div>
              </div>
              <div>
                <label htmlFor="password" className="label">Password</label>
                <div className="relative">
                  <LockKeyhole size={17} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input id="password" type={showPassword ? 'text' : 'password'} autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Enter your password" className="input pl-10 pr-11" />
                  <button type="button" onClick={() => setShowPassword((current) => !current)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 transition hover:text-slate-700" aria-label={showPassword ? 'Hide password' : 'Show password'}>
                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>
              <button type="submit" disabled={loading} className="btn-primary h-11 w-full">
                {loading ? <><Loader2 size={17} className="animate-spin" />Signing in...</> : 'Sign in'}
              </button>
            </form>
          </div>
          <div className="border-t border-slate-100 bg-slate-50 px-8 py-4 text-center"><p className="text-xs text-slate-400">Sampurna Gnana School Management System</p></div>
        </div>
        <p className="mt-5 text-center text-xs text-slate-400">Secure access • Authorized users only</p>
      </div>
    </main>
  );
}
