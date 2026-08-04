'use client';

import './globals.css';
import Image from 'next/image';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useState } from 'react';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import {
  LayoutDashboard,
  UserPlus,
  GraduationCap,
  BookOpen,
  ClipboardCheck,
  FileText,
  IndianRupee,
  Users,
  Bus,
  Package,
  Headphones,
  Building2,
  MessageSquare,
  FolderOpen,
  Settings,
  Menu,
  X,
  LogOut,
  ChevronRight,
} from 'lucide-react';

const navigation = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/admissions', label: 'Admissions', icon: UserPlus },
  { href: '/students', label: 'Students', icon: GraduationCap },
  { href: '/academic-mgmt', label: 'Academics', icon: BookOpen },
  { href: '/attendance', label: 'Attendance', icon: ClipboardCheck },
  { href: '/exams', label: 'Examinations', icon: FileText },
  { href: '/fees', label: 'Fees', icon: IndianRupee },
  { href: '/hr', label: 'HR & Payroll', icon: Users },
  { href: '/transport', label: 'Transport', icon: Bus },
  { href: '/inventory', label: 'Inventory', icon: Package },
  { href: '/helpdesk', label: 'IT Helpdesk', icon: Headphones },
  { href: '/organizations', label: 'Administration', icon: Building2 },
  { href: '/communication', label: 'Communication', icon: MessageSquare },
  { href: '/documents', label: 'Documents', icon: FolderOpen },
  { href: '/settings', label: 'Settings', icon: Settings },
];

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const pathname = usePathname();
  const router = useRouter();
  const [mobileOpen, setMobileOpen] = useState(false);

  const isLoginPage = pathname === '/login';

  const currentPage =
    navigation.find(
      (item) =>
        pathname === item.href ||
        (item.href !== '/dashboard' && pathname.startsWith(item.href + '/'))
    )?.label ?? 'Sampurna Gnana ERP';

  const logout = () => {
    localStorage.removeItem('token');
    router.push('/login');
  };

  if (isLoginPage) {
    return (
      <html lang="en">
        <body className="bg-slate-50 text-slate-900 antialiased">
          <ProtectedRoute>{children}</ProtectedRoute>
        </body>
      </html>
    );
  }

  return (
    <html lang="en">
      <body className="bg-slate-50 text-slate-900 antialiased">
        <ProtectedRoute>
          <div className="flex min-h-screen">
            {mobileOpen && (
              <button
                aria-label="Close navigation"
                className="fixed inset-0 z-40 bg-slate-950/50 lg:hidden"
                onClick={() => setMobileOpen(false)}
              />
            )}

            <aside
              className={`fixed inset-y-0 left-0 z-50 flex w-64 flex-col bg-slate-900 text-slate-100 transition-transform duration-200 lg:static lg:translate-x-0 ${
                mobileOpen ? 'translate-x-0' : '-translate-x-full'
              }`}
            >
              <div className="flex h-[76px] items-center gap-3 border-b border-slate-800 px-5">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center overflow-hidden rounded-xl bg-white p-1 shadow-sm">
                  <Image
                    src="/sampurna-gnana-logo.png"
                    alt="Sampurna Gnana"
                    width={44}
                    height={44}
                    priority
                    className="h-full w-full object-contain"
                  />
                </div>

                <div className="min-w-0">
                  <div className="truncate text-[15px] font-bold tracking-tight text-white">
                    Sampurna Gnana
                  </div>
                  <div className="text-xs font-medium text-blue-400">
                    School ERP
                  </div>
                </div>

                <button
                  onClick={() => setMobileOpen(false)}
                  className="ml-auto rounded-md p-1 text-slate-400 hover:bg-slate-800 hover:text-white lg:hidden"
                  aria-label="Close menu"
                >
                  <X size={20} />
                </button>
              </div>

              <nav className="flex-1 overflow-y-auto px-3 py-4">
                <div className="mb-2 px-3 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">
                  Main Menu
                </div>

                <div className="space-y-1">
                  {navigation.map((item) => {
                    const Icon = item.icon;
                    const active =
                      pathname === item.href ||
                      (item.href !== '/dashboard' &&
                        pathname.startsWith(item.href + '/'));

                    return (
                      <Link
                        key={item.href}
                        href={item.href}
                        onClick={() => setMobileOpen(false)}
                        className={`group flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition ${
                          active
                            ? 'bg-blue-600 text-white shadow-sm'
                            : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                        }`}
                      >
                        <Icon
                          size={18}
                          strokeWidth={1.9}
                          className={
                            active
                              ? 'text-white'
                              : 'text-slate-400 group-hover:text-slate-200'
                          }
                        />
                        <span className="flex-1">{item.label}</span>
                        {active && <ChevronRight size={15} />}
                      </Link>
                    );
                  })}
                </div>
              </nav>

              <div className="border-t border-slate-800 p-3">
                <div className="mb-2 px-3 py-2">
                  <div className="text-xs text-slate-500">Organization</div>
                  <div className="mt-0.5 truncate text-sm font-medium text-slate-200">
                    Sampurna Gnana
                  </div>
                </div>

                <button
                  onClick={logout}
                  className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-slate-300 transition hover:bg-slate-800 hover:text-white"
                >
                  <LogOut size={17} />
                  Logout
                </button>
              </div>
            </aside>

            <div className="flex min-w-0 flex-1 flex-col">
              <header className="sticky top-0 z-30 flex h-[76px] items-center justify-between border-b border-slate-200 bg-white px-4 sm:px-6">
                <div className="flex min-w-0 items-center gap-3">
                  <button
                    onClick={() => setMobileOpen(true)}
                    className="rounded-md border border-slate-200 p-2 text-slate-600 hover:bg-slate-50 lg:hidden"
                    aria-label="Open menu"
                  >
                    <Menu size={20} />
                  </button>

                  <div className="min-w-0">
                    <div className="text-xs font-medium text-slate-400">
                      Sampurna Gnana ERP
                    </div>
                    <div className="truncate text-base font-semibold text-slate-800">
                      {currentPage}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <div className="hidden text-right sm:block">
                    <div className="text-sm font-medium text-slate-700">
                      Super Administrator
                    </div>
                    <div className="text-xs text-slate-400">
                      Super Admin
                    </div>
                  </div>

                  <div className="flex h-9 w-9 items-center justify-center rounded-full bg-blue-600 text-sm font-bold text-white">
                    A
                  </div>
                </div>
              </header>

              <main className="flex-1 overflow-x-hidden p-4 sm:p-6 lg:p-7">
                <div className="mx-auto w-full max-w-[1600px]">
                  {children}
                </div>
              </main>
            </div>
          </div>
        </ProtectedRoute>
      </body>
    </html>
  );
}
