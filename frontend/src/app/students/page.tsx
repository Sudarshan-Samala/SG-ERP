'use client';

import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react';
import {
  Plus,
  Search,
  RefreshCw,
  Users,
  UserRound,
  Pencil,
  Trash2,
  Loader2,
  Mail,
  Phone,
  Building2,
  CalendarDays,
} from 'lucide-react';

import api from '@/lib/api';
import { Modal } from '@/components/ui/Modal';

interface Student {
  id: string;
  organization_id: string;
  branch_id: string;
  academic_year_id: string;
  admission_number: string;
  student_name: string;
  date_of_birth: string;
  gender: string;
  email?: string | null;
  phone?: string | null;
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
  admission_number: '',
  date_of_birth: '',
  gender: 'M',
  email: '',
  phone: '',
  branch_id: '',
  academic_year_id: '',
};

export default function StudentsPage() {
  const [students, setStudents] = useState<Student[]>([]);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [academicYears, setAcademicYears] = useState<AcademicYear[]>([]);

  const [form, setForm] = useState(emptyForm);

  const [editingId, setEditingId] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const [search, setSearch] = useState('');
  const [branchFilter, setBranchFilter] = useState('all');

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const [error, setError] = useState('');
  const [formError, setFormError] = useState('');

  const loadData = useCallback(async () => {
    setLoading(true);
    setError('');

    try {
      const [studentRes, branchRes, yearRes] = await Promise.all([
        api.get('/students/'),
        api.get('/branches/'),
        api.get('/academic/'),
      ]);

      setStudents(studentRes.data);
      setBranches(branchRes.data);
      setAcademicYears(yearRes.data);
    } catch {
      setError('Unable to load student information.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const filteredStudents = useMemo(() => {
    const query = search.trim().toLowerCase();

    return students.filter((student) => {
      const matchesSearch =
        !query ||
        student.student_name.toLowerCase().includes(query) ||
        student.admission_number.toLowerCase().includes(query) ||
        (student.email || '').toLowerCase().includes(query) ||
        (student.phone || '').toLowerCase().includes(query);

      const matchesBranch =
        branchFilter === 'all' || student.branch_id === branchFilter;

      return matchesSearch && matchesBranch;
    });
  }, [students, search, branchFilter]);

  const branchName = (id: string) =>
    branches.find((branch) => branch.id === id)?.name ?? '—';

  const academicYearName = (id: string) =>
    academicYears.find((year) => year.id === id)?.name ?? '—';

  const updateField = (field: keyof typeof emptyForm, value: string) => {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));
  };

  const openCreateModal = () => {
    setEditingId(null);
    setForm(emptyForm);
    setFormError('');
    setIsModalOpen(true);
  };

  const openEditModal = (student: Student) => {
    setEditingId(student.id);

    setForm({
      student_name: student.student_name,
      admission_number: student.admission_number,
      date_of_birth: student.date_of_birth
        ? student.date_of_birth.slice(0, 10)
        : '',
      gender: student.gender,
      email: student.email || '',
      phone: student.phone || '',
      branch_id: student.branch_id,
      academic_year_id: student.academic_year_id,
    });

    setFormError('');
    setIsModalOpen(true);
  };

  const closeModal = () => {
    if (submitting) return;

    setIsModalOpen(false);
    setEditingId(null);
    setFormError('');
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setFormError('');

    if (!form.branch_id || !form.academic_year_id) {
      setFormError('Please select a branch and academic year.');
      return;
    }

    if (!form.date_of_birth) {
      setFormError('Please select the student date of birth.');
      return;
    }

    setSubmitting(true);

    const payload = {
      student_name: form.student_name.trim(),
      admission_number: form.admission_number.trim(),

      // Backend schema expects date-time rather than a plain date.
      date_of_birth: new Date(
        `${form.date_of_birth}T00:00:00`,
      ).toISOString(),

      gender: form.gender,
      branch_id: form.branch_id,
      academic_year_id: form.academic_year_id,
      email: form.email.trim() || null,
      phone: form.phone.trim() || null,
    };

    try {
      if (editingId) {
        await api.put(`/students/${editingId}`, payload);
      } else {
        await api.post('/students/', payload);
      }

      setIsModalOpen(false);
      setEditingId(null);
      setForm(emptyForm);

      await loadData();
    } catch {
      setFormError(
        editingId
          ? 'Unable to update the student. Please check the information.'
          : 'Unable to create the student. Please check the information.',
      );
    } finally {
      setSubmitting(false);
    }
  };

  const deleteStudent = async (student: Student) => {
    const confirmed = window.confirm(
      `Delete ${student.student_name} (${student.admission_number})?\n\nThis action cannot be undone.`,
    );

    if (!confirmed) return;

    setDeletingId(student.id);
    setError('');

    try {
      await api.delete(`/students/${student.id}`);
      await loadData();
    } catch {
      setError('Unable to delete the student.');
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div>
      <div className="mb-6 flex flex-col justify-between gap-4 lg:flex-row lg:items-center">
        <div>
          <h1 className="page-title">Students</h1>
          <p className="page-description">
            Manage student profiles, admissions and academic records.
          </p>
        </div>

        <div className="flex gap-2">
          <button
            type="button"
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

          <button
            type="button"
            onClick={openCreateModal}
            className="btn-primary"
          >
            <Plus size={17} />
            Add Student
          </button>
        </div>
      </div>

      <div className="mb-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <SummaryCard
          label="Total Students"
          value={students.length}
          icon={Users}
        />

        <SummaryCard
          label="Male Students"
          value={
            students.filter(
              (student) => student.gender.toUpperCase() === 'M',
            ).length
          }
          icon={UserRound}
        />

        <SummaryCard
          label="Female Students"
          value={
            students.filter(
              (student) => student.gender.toUpperCase() === 'F',
            ).length
          }
          icon={UserRound}
        />

        <SummaryCard
          label="Active Branches"
          value={branches.filter((branch) => branch.is_active).length}
          icon={Building2}
        />
      </div>

      {error && (
        <div className="mb-5 flex items-center justify-between rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          <span>{error}</span>

          <button
            type="button"
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
              placeholder="Search name, admission number, email or phone..."
              className="input pl-10"
            />
          </div>

          <select
            value={branchFilter}
            onChange={(event) => setBranchFilter(event.target.value)}
            className="input md:w-56"
          >
            <option value="all">All branches</option>

            {branches.map((branch) => (
              <option key={branch.id} value={branch.id}>
                {branch.name}
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
              <th>Admission No.</th>
              <th>Contact</th>
              <th>Branch</th>
              <th>Academic Year</th>
              <th>DOB</th>
              <th>Gender</th>
              <th className="text-right">Actions</th>
            </tr>
          </thead>

          <tbody>
            {loading ? (
              <tr>
                <td colSpan={8}>
                  <div className="flex items-center justify-center gap-2 py-14 text-slate-500">
                    <Loader2 size={19} className="animate-spin" />
                    Loading students...
                  </div>
                </td>
              </tr>
            ) : filteredStudents.length === 0 ? (
              <tr>
                <td colSpan={8}>
                  <div className="py-14 text-center">
                    <div className="mx-auto mb-3 flex h-11 w-11 items-center justify-center rounded-full bg-slate-100 text-slate-400">
                      <Users size={21} />
                    </div>

                    <div className="font-medium text-slate-700">
                      No students found
                    </div>

                    <div className="mt-1 text-sm text-slate-400">
                      {search || branchFilter !== 'all'
                        ? 'Try changing your search or branch filter.'
                        : 'Add your first student record.'}
                    </div>
                  </div>
                </td>
              </tr>
            ) : (
              filteredStudents.map((student) => (
                <tr key={student.id}>
                  <td>
                    <div className="flex items-center gap-3">
                      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-blue-50 text-sm font-semibold text-blue-600">
                        {student.student_name
                          .split(' ')
                          .slice(0, 2)
                          .map((part) => part.charAt(0))
                          .join('')
                          .toUpperCase()}
                      </div>

                      <div className="font-medium text-slate-900">
                        {student.student_name}
                      </div>
                    </div>
                  </td>

                  <td>
                    <span className="font-medium text-slate-700">
                      {student.admission_number}
                    </span>
                  </td>

                  <td>
                    {student.email || student.phone ? (
                      <div className="space-y-1 text-xs text-slate-500">
                        {student.email && (
                          <div className="flex items-center gap-1.5">
                            <Mail size={12} />
                            {student.email}
                          </div>
                        )}

                        {student.phone && (
                          <div className="flex items-center gap-1.5">
                            <Phone size={12} />
                            {student.phone}
                          </div>
                        )}
                      </div>
                    ) : (
                      '—'
                    )}
                  </td>

                  <td>
                    <div className="flex items-center gap-1.5">
                      <Building2 size={14} className="text-slate-400" />
                      {branchName(student.branch_id)}
                    </div>
                  </td>

                  <td>
                    <div className="flex items-center gap-1.5">
                      <CalendarDays size={14} className="text-slate-400" />
                      {academicYearName(student.academic_year_id)}
                    </div>
                  </td>

                  <td>
                    {student.date_of_birth
                      ? new Date(student.date_of_birth).toLocaleDateString(
                          'en-IN',
                        )
                      : '—'}
                  </td>

                  <td>
                    <GenderBadge gender={student.gender} />
                  </td>

                  <td>
                    <div className="flex justify-end gap-1">
                      <button
                        type="button"
                        onClick={() => openEditModal(student)}
                        title="Edit student"
                        className="rounded-md p-2 text-slate-500 transition hover:bg-blue-50 hover:text-blue-600"
                      >
                        <Pencil size={16} />
                      </button>

                      <button
                        type="button"
                        onClick={() => void deleteStudent(student)}
                        disabled={deletingId === student.id}
                        title="Delete student"
                        className="rounded-md p-2 text-slate-500 transition hover:bg-red-50 hover:text-red-600 disabled:opacity-50"
                      >
                        {deletingId === student.id ? (
                          <Loader2 size={16} className="animate-spin" />
                        ) : (
                          <Trash2 size={16} />
                        )}
                      </button>
                    </div>
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
        title={editingId ? 'Edit Student' : 'Add Student'}
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
                onChange={(e) =>
                  updateField('student_name', e.target.value)
                }
                className="input"
                placeholder="Student full name"
              />
            </Field>

            <Field label="Admission Number">
              <input
                required
                value={form.admission_number}
                onChange={(e) =>
                  updateField('admission_number', e.target.value)
                }
                className="input"
                placeholder="e.g. SG2026001"
              />
            </Field>

            <Field label="Date of Birth">
              <input
                required
                type="date"
                value={form.date_of_birth}
                onChange={(e) =>
                  updateField('date_of_birth', e.target.value)
                }
                className="input"
              />
            </Field>

            <Field label="Gender">
              <select
                required
                value={form.gender}
                onChange={(e) => updateField('gender', e.target.value)}
                className="input"
              >
                <option value="M">Male</option>
                <option value="F">Female</option>
                <option value="O">Other</option>
              </select>
            </Field>

            <Field label="Email">
              <input
                type="email"
                value={form.email}
                onChange={(e) => updateField('email', e.target.value)}
                className="input"
                placeholder="student@example.com"
              />
            </Field>

            <Field label="Phone">
              <input
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
                onChange={(e) =>
                  updateField('branch_id', e.target.value)
                }
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
                  {editingId ? 'Updating...' : 'Creating...'}
                </>
              ) : editingId ? (
                <>
                  <Pencil size={16} />
                  Update Student
                </>
              ) : (
                <>
                  <Plus size={16} />
                  Create Student
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
        <div className="text-xs font-medium text-slate-500">
          {label}
        </div>

        <div className="mt-0.5 text-xl font-bold text-slate-900">
          {value}
        </div>
      </div>
    </div>
  );
}

function GenderBadge({ gender }: { gender: string }) {
  const normalized = gender.toUpperCase();

  const label =
    normalized === 'M'
      ? 'Male'
      : normalized === 'F'
        ? 'Female'
        : 'Other';

  return (
    <span className="badge-info">
      {label}
    </span>
  );
}
