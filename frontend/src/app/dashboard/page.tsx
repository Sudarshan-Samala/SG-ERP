'use client';

import { useCallback, useEffect, useState } from 'react';
import {
  GraduationCap,
  Users,
  Headphones,
  ArrowUpRight,
  RefreshCw,
  School,
  ClipboardCheck,
  IndianRupee,
} from 'lucide-react';
import api from '@/lib/api';

interface DashboardStats {
  students: number;
  employees: number;
  open_tickets: number;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.get('/dashboard/summary');
      setStats(response.data);
    } catch {
      setError('Unable to load dashboard information.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchStats();
  }, [fetchStats]);

  const cards = [
    {
      label: 'Total Students',
      value: stats?.students,
      icon: GraduationCap,
      description: 'Enrolled students',
    },
    {
      label: 'Total Employees',
      value: stats?.employees,
      icon: Users,
      description: 'Teaching & non-teaching staff',
    },
    {
      label: 'Open Helpdesk Tickets',
      value: stats?.open_tickets,
      icon: Headphones,
      description: 'Tickets requiring attention',
    },
  ];

  return (
    <div>
      <div className="mb-6 flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-description">
            Welcome back. Here&apos;s an overview of Sampurna Gnana.
          </p>
        </div>

        <button
          onClick={() => void fetchStats()}
          disabled={loading}
          className="btn-secondary self-start"
        >
          <RefreshCw
            size={16}
            className={loading ? 'animate-spin' : ''}
          />
          Refresh
        </button>
      </div>

      {error && (
        <div className="mb-6 flex items-center justify-between rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          <span>{error}</span>
          <button
            onClick={() => void fetchStats()}
            className="font-semibold hover:underline"
          >
            Retry
          </button>
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {cards.map((card) => {
          const Icon = card.icon;

          return (
            <div
              key={card.label}
              className="card p-5 transition hover:-translate-y-0.5 hover:shadow-md"
            >
              <div className="flex items-start justify-between">
                <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
                  <Icon size={22} />
                </div>

                <ArrowUpRight size={17} className="text-slate-300" />
              </div>

              <div className="mt-5 text-sm font-medium text-slate-500">
                {card.label}
              </div>

              <div className="mt-1 text-3xl font-bold tracking-tight text-slate-900">
                {loading ? (
                  <div className="h-9 w-20 animate-pulse rounded bg-slate-200" />
                ) : (
                  card.value ?? '—'
                )}
              </div>

              <div className="mt-1 text-xs text-slate-400">
                {card.description}
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-3">
        <div className="card p-5 xl:col-span-2">
          <div className="mb-5 flex items-center justify-between">
            <div>
              <h2 className="font-semibold text-slate-900">
                School Overview
              </h2>
              <p className="mt-1 text-sm text-slate-500">
                Quick access to daily operations
              </p>
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <QuickItem
              icon={School}
              label="Academics"
              description="Grades & subjects"
            />
            <QuickItem
              icon={ClipboardCheck}
              label="Attendance"
              description="Daily attendance"
            />
            <QuickItem
              icon={IndianRupee}
              label="Fees"
              description="Fee management"
            />
            <QuickItem
              icon={Headphones}
              label="Helpdesk"
              description="Support tickets"
            />
          </div>
        </div>

        <div className="card p-5">
          <h2 className="font-semibold text-slate-900">System</h2>
          <p className="mt-1 text-sm text-slate-500">
            ERP service information
          </p>

          <div className="mt-5 space-y-4">
            <StatusRow label="ERP Status" value="Online" success />
            <StatusRow label="Organization" value="Sampurna Gnana" />
            <StatusRow label="Access Level" value="Super Admin" />
          </div>
        </div>
      </div>
    </div>
  );
}

function QuickItem({
  icon: Icon,
  label,
  description,
}: {
  icon: React.ElementType;
  label: string;
  description: string;
}) {
  return (
    <div className="rounded-lg border border-slate-200 p-4 transition hover:border-blue-200 hover:bg-blue-50/40">
      <Icon size={20} className="mb-3 text-blue-600" />
      <div className="text-sm font-semibold text-slate-800">{label}</div>
      <div className="mt-1 text-xs text-slate-500">{description}</div>
    </div>
  );
}

function StatusRow({
  label,
  value,
  success = false,
}: {
  label: string;
  value: string;
  success?: boolean;
}) {
  return (
    <div className="flex items-center justify-between border-b border-slate-100 pb-3 last:border-0 last:pb-0">
      <span className="text-sm text-slate-500">{label}</span>

      <span
        className={
          success
            ? 'badge-success'
            : 'text-sm font-medium text-slate-700'
        }
      >
        {value}
      </span>
    </div>
  );
}
