'use client';

import { Settings, Building2, Shield, Bell } from 'lucide-react';

export default function SettingsPage() {
  return (
    <div>
      <div className="mb-6">
        <h1 className="page-title">Settings</h1>
        <p className="page-description">
          Manage Sampurna Gnana ERP configuration and preferences.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <SettingCard
          icon={Building2}
          title="Organization"
          description="School profile, organization details and configuration."
        />

        <SettingCard
          icon={Shield}
          title="Security & Access"
          description="Manage authentication, permissions and access policies."
        />

        <SettingCard
          icon={Bell}
          title="Notifications"
          description="Configure system and communication notifications."
        />
      </div>
    </div>
  );
}

function SettingCard({
  icon: Icon,
  title,
  description,
}: {
  icon: React.ElementType;
  title: string;
  description: string;
}) {
  return (
    <div className="card p-5 transition hover:-translate-y-0.5 hover:shadow-md">
      <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
        <Icon size={20} />
      </div>

      <h2 className="font-semibold text-slate-900">{title}</h2>
      <p className="mt-1 text-sm leading-6 text-slate-500">{description}</p>
    </div>
  );
}
