'use client';

import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react';
import {
  Plus,
  Search,
  RefreshCw,
  UserPlus,
  Mail,
  Phone,
  Users,
  Loader2,
} from 'lucide-react';
import api from '@/lib/api';
import { Modal } from '@/components/ui/Modal';

interface Enquiry {
  id: string;
  organization_id: string;
  branch_id: string;
  academic_year_id: string;
  student_name: string;
  parent_name: string;
  email: string;
  phone: string;
  lead_source?: string | null;
  status: string;
}

interface Branch {
  id: string;
  name: string;
  code: string;
  is_active: boolean;
}

interface AcademicYear {
  id: string;
  name: string;
  start_date: string;
  end_date: string;
  is_active: boolean;
}

const emptyForm = {
  student_name: '',
  parent_name: '',
  email: '',
  phone: '',
  branch_id: '',
  academic_year_id: '',
  lead_source: '',
};

export default function AdmissionsPage() {
  const [enquiries, setEnquiries] = useState<Enquiry[]>([]);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [academicYears, setAcademicYears] = useState<AcademicYear[]>([]);

  const [form, setForm] = useState(emptyForm);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [formError, setFormError] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError('');

    try {
      const [enquiryRes, branchRes, yearRes] = await Promise.all([
        api.get('/admissions/enquiries'),
        api.get('/branches/'),
        api.get('/academic/'),
      ]);

      setEnquiries(enquiryRes.data);
      setBranches(branchRes.data);
      setAcademicYears(yearRes.data);
    } catch {
      setError('Unable to load admission information.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const filteredEnquiries = useMemo(() => {
    const query = search.trim().toLowerCase();

    return enquiries.filter((enquiry) => {
      const matchesSearch =
        !query ||
        enquiry.student_name.toLowerCase().includes(query) ||
        enquiry.parent_name.toLowerCase().includes(query) ||
        enquiry.email.toLowerCase().includes(query) ||
        enquiry.phone.toLowerCase().includes(query);

      const matchesStatus =
        statusFilter === 'all' ||
        enquiry.status.toLowerCase() === statusFilter.toLowerCase();

      return matchesSearch && matchesStatus;
    });
  }, [enquiries, search, statusFilter]);

  const statuses = useMemo(
    () =>
      Array.from(
        new Set(enquiries.map((item) => item.status).filter(Boolean)),
      ),
    [enquiries],
  );

  const branchName = (id: string) =>
    branches.find((branch) => branch.id === id)?.name ?? '—';

  const yearName = (id: string) =>
    academicYears.find((year) => year.id === id)?.name ?? '—';

  const openModal = () => {
    setForm(emptyForm);
    setFormError('');
    setIsModalOpen(true);
  };

  const closeModal = () => {
    if (submitting) return;
    setIsModalOpen(false);
    setFormError('');
  };

  const updateField = (field: keyof typeof emptyForm, value: string) => {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setFormError('');

    if (!form.branch_id || !form.academic_year_id) {
      setFormError('Please select a branch and academic year.');
      return;
    }

    setSubmitting(true);

    try {
      await api.post('/admissions/enquiries', {
        student_name: form.student_name.trim(),
        parent_name: form.parent_name.trim(),
        email: form.email.trim(),
        phone: form.phone.trim(),
        branch_id: form.branch_id,
        academic_year_id: form.academic_year_id,
        lead_source: form.lead_source.trim() || null,
      });

      setIsModalOpen(false);
      setForm(emptyForm);
      await loadData();
    } catch {
      setFormError(
        'Unable to create the enquiry. Please check the information and try again.',
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      <div className="mb-6 flex flex-col justify-between gap-4 lg:flex-row lg:items-center">
        <div>
          <h1 className="page-title">Admission Enquiries</h1>
          <p className="page-description">
            Manage prospective students and incoming admission enquiries.
          </p>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => void loadData()}
            disabled={loading}
            className="btn-secondary"
          >
            <RefreshCw
              size={16}
              className={loading ? 'animate-spin' : ''}
            />
            Refresh
          </button>

          <button onClick={openModal} className="btn-primary">
            <Plus size={17} />
            Add Enquiry
          </button>
        </div>
      </div>

      <div className="mb-5 grid gap-4 sm:grid-cols-3">
        <SummaryCard
          label="Total Enquiries"
          value={enquiries.length}
          icon={UserPlus}
        />
        <SummaryCard
          label="Active Branches"
          value={branches.filter((branch) => branch.is_active).length}
          icon={Users}
        />
        <SummaryCard
          label="Academic Years"
          value={academicYears.length}
          icon={Search}
        />
      </div>

      {error && (
        <div className="mb-5 flex items-center justify-between rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          <span>{error}</span>
          <button
            onClick={() => void loadData()}
            className="font-semibold hover:underline"
          >
            Retry
          </button>
        </div>
      )}

      <div className="card mb-4 p-4">
        <div className="flex flex-col gap-3 md:flex-row">
          <div className="relative flex-1">
            <Search
              size={17}
              className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
            />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search student, parent, email or phone..."
              className="input pl-10"
            />
          </div>

          <select
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value)}
            className="input md:w-52"
          >
            <option value="all">All statuses</option>
            {statuses.map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Student</th>
              <th>Parent / Contact</th>
              <th>Branch</th>
              <th>Academic Year</th>
              <th>Lead Source</th>
              <th>Status</th>
            </tr>
          </thead>

          <tbody>
            {loading ? (
              <tr>
                <td colSpan={6}>
                  <div className="flex items-center justify-center gap-2 py-12 text-slate-500">
                    <Loader2 size={19} className="animate-spin" />
                    Loading enquiries...
                  </div>
                </td>
              </tr>
            ) : filteredEnquiries.length === 0 ? (
              <tr>
                <td colSpan={6}>
                  <div className="py-14 text-center">
                    <div className="mx-auto mb-3 flex h-11 w-11 items-center justify-center rounded-full bg-slate-100 text-slate-400">
                      <UserPlus size={21} />
                    </div>
                    <div className="font-medium text-slate-700">
                      No enquiries found
                    </div>
                    <div className="mt-1 text-sm text-slate-400">
                      {search || statusFilter !== 'all'
                        ? 'Try changing your search or filter.'
                        : 'Create your first admission enquiry.'}
                    </div>
                  </div>
                </td>
              </tr>
            ) : (
              filteredEnquiries.map((enquiry) => (
                <tr key={enquiry.id}>
                  <td>
                    <div className="font-medium text-slate-900">
                      {enquiry.student_name}
                    </div>
                  </td>

                  <td>
                    <div className="font-medium text-slate-700">
                      {enquiry.parent_name}
                    </div>
                    <div className="mt-1 flex flex-col gap-1 text-xs text-slate-400">
                      <span className="flex items-center gap-1.5">
                        <Mail size={12} />
                        {enquiry.email}
                      </span>
                      <span className="flex items-center gap-1.5">
                        <Phone size={12} />
                        {enquiry.phone}
                      </span>
                    </div>
                  </td>

                  <td>{branchName(enquiry.branch_id)}</td>

                  <td>{yearName(enquiry.academic_year_id)}</td>

                  <td>{enquiry.lead_source || '—'}</td>

                  <td>
                    <StatusBadge status={enquiry.status} />
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <Modal
        isOpen={isModalOpen}
        onClose={closeModal}
        title="Add Admission Enquiry"
      >
        <form onSubmit={handleSubmit} className="space-y-5">
          {formError && (
            <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {formError}
            </div>
          )}

          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Student Name">
              <input
                required
                value={form.student_name}
                onChange={(e) => updateField('student_name', e.target.value)}
                className="input"
                placeholder="Student full name"
              />
            </Field>

            <Field label="Parent / Guardian">
              <input
                required
                value={form.parent_name}
                onChange={(e) => updateField('parent_name', e.target.value)}
                className="input"
                placeholder="Parent or guardian name"
              />
            </Field>

            <Field label="Email">
              <input
                required
                type="email"
                value={form.email}
                onChange={(e) => updateField('email', e.target.value)}
                className="input"
                placeholder="parent@example.com"
              />
            </Field>

            <Field label="Phone">
              <input
                required
                type="tel"
                value={form.phone}
                onChange={(e) => updateField('phone', e.target.value)}
                className="input"
                placeholder="Phone number"
              />
            </Field>

            <Field label="Branch">
              <select
                required
                value={form.branch_id}
                onChange={(e) => updateField('branch_id', e.target.value)}
                className="input"
              >
                <option value="">Select branch</option>
                {branches
                  .filter((branch) => branch.is_active)
                  .map((branch) => (
                    <option key={branch.id} value={branch.id}>
                      {branch.name} ({branch.code})
                    </option>
                  ))}
              </select>
            </Field>

            <Field label="Academic Year">
              <select
                required
                value={form.academic_year_id}
                onChange={(e) =>
                  updateField('academic_year_id', e.target.value)
                }
                className="input"
              >
                <option value="">Select academic year</option>
                {academicYears.map((year) => (
                  <option key={year.id} value={year.id}>
                    {year.name}
                    {year.is_active ? ' • Active' : ''}
                  </option>
                ))}
              </select>
            </Field>
          </div>

          <Field label="Lead Source">
            <select
              value={form.lead_source}
              onChange={(e) => updateField('lead_source', e.target.value)}
              className="input"
            >
              <option value="">Select lead source</option>
              <option value="Walk-in">Walk-in</option>
              <option value="Website">Website</option>
              <option value="Referral">Referral</option>
              <option value="Phone">Phone</option>
              <option value="Social Media">Social Media</option>
              <option value="Advertisement">Advertisement</option>
              <option value="Other">Other</option>
            </select>
          </Field>

          <div className="flex justify-end gap-2 border-t border-slate-100 pt-4">
            <button
              type="button"
              onClick={closeModal}
              disabled={submitting}
              className="btn-secondary"
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={submitting}
              className="btn-primary"
            >
              {submitting ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <Plus size={16} />
                  Create Enquiry
                </>
              )}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="label">{label}</label>
      {children}
    </div>
  );
}

function SummaryCard({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: number;
  icon: React.ElementType;
}) {
  return (
    <div className="card flex items-center gap-4 p-4">
      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
        <Icon size={19} />
      </div>
      <div>
        <div className="text-xs font-medium text-slate-500">{label}</div>
        <div className="mt-0.5 text-xl font-bold text-slate-900">{value}</div>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const normalized = status.toLowerCase();

  let classes = 'badge-info';

  if (
    normalized.includes('admit') ||
    normalized.includes('convert') ||
    normalized.includes('complete')
  ) {
    classes = 'badge-success';
  } else if (
    normalized.includes('reject') ||
    normalized.includes('cancel')
  ) {
    classes = 'badge-danger';
  } else if (
    normalized.includes('pending') ||
    normalized.includes('follow')
  ) {
    classes = 'badge-warning';
  }

  return <span className={classes}>{status}</span>;
}
