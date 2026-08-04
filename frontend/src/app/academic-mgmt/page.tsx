'use client';

import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react';
import {
  BookOpen,
  Building2,
  GraduationCap,
  Layers3,
  Loader2,
  Pencil,
  Plus,
  RefreshCw,
  Search,
  Trash2,
  X,
} from 'lucide-react';
import api from '@/lib/api';
import { Modal } from '@/components/ui/Modal';

interface Branch {
  id: string;
  name: string;
  code: string;
  is_active: boolean;
}

interface Grade {
  id: string;
  organization_id: string;
  branch_id: string;
  name: string;
}

interface Section {
  id: string;
  organization_id: string;
  branch_id: string;
  grade_id: string;
  name: string;
}

interface Subject {
  id: string;
  organization_id: string;
  name: string;
  code: string;
}

type Tab = 'grades' | 'sections' | 'subjects';

export default function AcademicManagementPage() {
  const [branches, setBranches] = useState<Branch[]>([]);
  const [grades, setGrades] = useState<Grade[]>([]);
  const [sections, setSections] = useState<Section[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);

  const [activeTab, setActiveTab] = useState<Tab>('grades');
  const [search, setSearch] = useState('');
  const [branchFilter, setBranchFilter] = useState('all');

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadData = useCallback(async () => {
    setLoading(true);
    setError('');

    try {
      const [gradeRes, sectionRes, subjectRes, branchRes] =
        await Promise.all([
          api.get('/academic-mgmt/grades'),
          api.get('/academic-mgmt/sections'),
          api.get('/academic-mgmt/subjects'),
          api.get('/branches/'),
        ]);

      setGrades(gradeRes.data);
      setSections(sectionRes.data);
      setSubjects(subjectRes.data);
      setBranches(branchRes.data);
    } catch {
      setError('Unable to load academic management data.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const branchName = (id: string) =>
    branches.find((branch) => branch.id === id)?.name ?? '—';

  const gradeName = (id: string) =>
    grades.find((grade) => grade.id === id)?.name ?? '—';

  return (
    <div>
      <div className="mb-6 flex flex-col justify-between gap-4 lg:flex-row lg:items-center">
        <div>
          <h1 className="page-title">Academic Management</h1>
          <p className="page-description">
            Configure grades, sections and subjects across your school.
          </p>
        </div>

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
      </div>

      <div className="mb-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <SummaryCard
          label="Branches"
          value={branches.length}
          icon={Building2}
        />

        <SummaryCard
          label="Grades"
          value={grades.length}
          icon={GraduationCap}
        />

        <SummaryCard
          label="Sections"
          value={sections.length}
          icon={Layers3}
        />

        <SummaryCard
          label="Subjects"
          value={subjects.length}
          icon={BookOpen}
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

      <div className="card overflow-hidden">
        <div className="border-b border-slate-200 px-4 pt-4">
          <div className="flex gap-1 overflow-x-auto">
            <TabButton
              active={activeTab === 'grades'}
              onClick={() => {
                setActiveTab('grades');
                setSearch('');
              }}
              icon={GraduationCap}
              label="Grades"
              count={grades.length}
            />

            <TabButton
              active={activeTab === 'sections'}
              onClick={() => {
                setActiveTab('sections');
                setSearch('');
              }}
              icon={Layers3}
              label="Sections"
              count={sections.length}
            />

            <TabButton
              active={activeTab === 'subjects'}
              onClick={() => {
                setActiveTab('subjects');
                setSearch('');
              }}
              icon={BookOpen}
              label="Subjects"
              count={subjects.length}
            />
          </div>
        </div>

        <div className="p-4">
          <div className="mb-4 flex flex-col gap-3 md:flex-row">
            <div className="relative flex-1">
              <Search
                size={17}
                className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
              />

              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder={`Search ${activeTab}...`}
                className="input pl-10"
              />
            </div>

            {activeTab !== 'subjects' && (
              <select
                value={branchFilter}
                onChange={(e) => setBranchFilter(e.target.value)}
                className="input md:w-56"
              >
                <option value="all">All branches</option>

                {branches.map((branch) => (
                  <option key={branch.id} value={branch.id}>
                    {branch.name}
                  </option>
                ))}
              </select>
            )}
          </div>

          {activeTab === 'grades' && (
            <GradeManager
              branches={branches}
              grades={grades}
              search={search}
              branchFilter={branchFilter}
              branchName={branchName}
              loading={loading}
              reload={loadData}
            />
          )}

          {activeTab === 'sections' && (
            <SectionManager
              branches={branches}
              grades={grades}
              sections={sections}
              search={search}
              branchFilter={branchFilter}
              branchName={branchName}
              gradeName={gradeName}
              loading={loading}
              reload={loadData}
            />
          )}

          {activeTab === 'subjects' && (
            <SubjectManager
              subjects={subjects}
              search={search}
              loading={loading}
              reload={loadData}
            />
          )}
        </div>
      </div>
    </div>
  );
}

function GradeManager({
  branches,
  grades,
  search,
  branchFilter,
  branchName,
  loading,
  reload,
}: {
  branches: Branch[];
  grades: Grade[];
  search: string;
  branchFilter: string;
  branchName: (id: string) => string;
  loading: boolean;
  reload: () => Promise<void>;
}) {
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Grade | null>(null);
  const [name, setName] = useState('');
  const [branchId, setBranchId] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [formError, setFormError] = useState('');

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();

    return grades.filter(
      (grade) =>
        (!q || grade.name.toLowerCase().includes(q)) &&
        (branchFilter === 'all' ||
          grade.branch_id === branchFilter),
    );
  }, [grades, search, branchFilter]);

  const openCreate = () => {
    setEditing(null);
    setName('');
    setBranchId('');
    setFormError('');
    setModalOpen(true);
  };

  const openEdit = (grade: Grade) => {
    setEditing(grade);
    setName(grade.name);
    setBranchId(grade.branch_id);
    setFormError('');
    setModalOpen(true);
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();

    if (!name.trim() || !branchId) {
      setFormError('Grade name and branch are required.');
      return;
    }

    setSubmitting(true);
    setFormError('');

    try {
      const payload = {
        name: name.trim(),
        branch_id: branchId,
      };

      if (editing) {
        await api.put(
          `/academic-mgmt/grades/${editing.id}`,
          payload,
        );
      } else {
        await api.post('/academic-mgmt/grades', payload);
      }

      setModalOpen(false);
      await reload();
    } catch {
      setFormError('Unable to save the grade.');
    } finally {
      setSubmitting(false);
    }
  };

  const remove = async (grade: Grade) => {
    if (
      !window.confirm(
        `Delete grade "${grade.name}"?\n\nThis may affect related academic records.`,
      )
    ) {
      return;
    }

    setDeletingId(grade.id);

    try {
      await api.delete(`/academic-mgmt/grades/${grade.id}`);
      await reload();
    } catch {
      window.alert(
        'Unable to delete this grade. It may be used by another record.',
      );
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <>
      <ManagerHeader
        title="Grades"
        description="Manage class and grade levels for each branch."
        buttonLabel="Add Grade"
        onAdd={openCreate}
      />

      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Grade</th>
              <th>Branch</th>
              <th className="text-right">Actions</th>
            </tr>
          </thead>

          <tbody>
            {loading ? (
              <LoadingRow columns={3} />
            ) : filtered.length === 0 ? (
              <EmptyRow
                columns={3}
                icon={GraduationCap}
                title="No grades found"
              />
            ) : (
              filtered.map((grade) => (
                <tr key={grade.id}>
                  <td>
                    <div className="font-medium text-slate-900">
                      {grade.name}
                    </div>
                  </td>

                  <td>{branchName(grade.branch_id)}</td>

                  <td>
                    <ActionButtons
                      editing={() => openEdit(grade)}
                      deleting={() => void remove(grade)}
                      deletingNow={deletingId === grade.id}
                    />
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <Modal
        isOpen={modalOpen}
        onClose={() => !submitting && setModalOpen(false)}
        title={editing ? 'Edit Grade' : 'Add Grade'}
      >
        <form onSubmit={submit} className="space-y-5">
          <FormError message={formError} />

          <Field label="Grade Name">
            <input
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="input"
              placeholder="e.g. Grade 10"
            />
          </Field>

          <Field label="Branch">
            <select
              required
              value={branchId}
              onChange={(e) => setBranchId(e.target.value)}
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

          <ModalActions
            submitting={submitting}
            editing={Boolean(editing)}
            onCancel={() => setModalOpen(false)}
          />
        </form>
      </Modal>
    </>
  );
}

function SectionManager({
  branches,
  grades,
  sections,
  search,
  branchFilter,
  branchName,
  gradeName,
  loading,
  reload,
}: {
  branches: Branch[];
  grades: Grade[];
  sections: Section[];
  search: string;
  branchFilter: string;
  branchName: (id: string) => string;
  gradeName: (id: string) => string;
  loading: boolean;
  reload: () => Promise<void>;
}) {
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Section | null>(null);
  const [name, setName] = useState('');
  const [branchId, setBranchId] = useState('');
  const [gradeId, setGradeId] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [formError, setFormError] = useState('');

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();

    return sections.filter(
      (section) =>
        (!q ||
          section.name.toLowerCase().includes(q) ||
          gradeName(section.grade_id)
            .toLowerCase()
            .includes(q)) &&
        (branchFilter === 'all' ||
          section.branch_id === branchFilter),
    );
  }, [sections, search, branchFilter, gradeName]);

  const availableGrades = grades.filter(
    (grade) => !branchId || grade.branch_id === branchId,
  );

  const openCreate = () => {
    setEditing(null);
    setName('');
    setBranchId('');
    setGradeId('');
    setFormError('');
    setModalOpen(true);
  };

  const openEdit = (section: Section) => {
    setEditing(section);
    setName(section.name);
    setBranchId(section.branch_id);
    setGradeId(section.grade_id);
    setFormError('');
    setModalOpen(true);
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();

    if (!name.trim() || !branchId || !gradeId) {
      setFormError('Section name, branch and grade are required.');
      return;
    }

    setSubmitting(true);
    setFormError('');

    try {
      const payload = {
        name: name.trim(),
        branch_id: branchId,
        grade_id: gradeId,
      };

      if (editing) {
        await api.put(
          `/academic-mgmt/sections/${editing.id}`,
          payload,
        );
      } else {
        await api.post('/academic-mgmt/sections', payload);
      }

      setModalOpen(false);
      await reload();
    } catch {
      setFormError('Unable to save the section.');
    } finally {
      setSubmitting(false);
    }
  };

  const remove = async (section: Section) => {
    if (
      !window.confirm(
        `Delete section "${section.name}"?\n\nThis may affect related academic records.`,
      )
    ) {
      return;
    }

    setDeletingId(section.id);

    try {
      await api.delete(
        `/academic-mgmt/sections/${section.id}`,
      );
      await reload();
    } catch {
      window.alert(
        'Unable to delete this section. It may be used by another record.',
      );
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <>
      <ManagerHeader
        title="Sections"
        description="Create sections under branch-specific grades."
        buttonLabel="Add Section"
        onAdd={openCreate}
      />

      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Section</th>
              <th>Grade</th>
              <th>Branch</th>
              <th className="text-right">Actions</th>
            </tr>
          </thead>

          <tbody>
            {loading ? (
              <LoadingRow columns={4} />
            ) : filtered.length === 0 ? (
              <EmptyRow
                columns={4}
                icon={Layers3}
                title="No sections found"
              />
            ) : (
              filtered.map((section) => (
                <tr key={section.id}>
                  <td>
                    <div className="font-medium text-slate-900">
                      {section.name}
                    </div>
                  </td>

                  <td>{gradeName(section.grade_id)}</td>
                  <td>{branchName(section.branch_id)}</td>

                  <td>
                    <ActionButtons
                      editing={() => openEdit(section)}
                      deleting={() => void remove(section)}
                      deletingNow={deletingId === section.id}
                    />
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <Modal
        isOpen={modalOpen}
        onClose={() => !submitting && setModalOpen(false)}
        title={editing ? 'Edit Section' : 'Add Section'}
      >
        <form onSubmit={submit} className="space-y-5">
          <FormError message={formError} />

          <Field label="Section Name">
            <input
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="input"
              placeholder="e.g. Section A"
            />
          </Field>

          <Field label="Branch">
            <select
              required
              value={branchId}
              onChange={(e) => {
                setBranchId(e.target.value);
                setGradeId('');
              }}
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

          <Field label="Grade">
            <select
              required
              value={gradeId}
              onChange={(e) => setGradeId(e.target.value)}
              disabled={!branchId}
              className="input disabled:bg-slate-100"
            >
              <option value="">
                {branchId
                  ? 'Select grade'
                  : 'Select branch first'}
              </option>

              {availableGrades.map((grade) => (
                <option key={grade.id} value={grade.id}>
                  {grade.name}
                </option>
              ))}
            </select>
          </Field>

          <ModalActions
            submitting={submitting}
            editing={Boolean(editing)}
            onCancel={() => setModalOpen(false)}
          />
        </form>
      </Modal>
    </>
  );
}

function SubjectManager({
  subjects,
  search,
  loading,
  reload,
}: {
  subjects: Subject[];
  search: string;
  loading: boolean;
  reload: () => Promise<void>;
}) {
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Subject | null>(null);
  const [name, setName] = useState('');
  const [code, setCode] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [formError, setFormError] = useState('');

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();

    return subjects.filter(
      (subject) =>
        !q ||
        subject.name.toLowerCase().includes(q) ||
        subject.code.toLowerCase().includes(q),
    );
  }, [subjects, search]);

  const openCreate = () => {
    setEditing(null);
    setName('');
    setCode('');
    setFormError('');
    setModalOpen(true);
  };

  const openEdit = (subject: Subject) => {
    setEditing(subject);
    setName(subject.name);
    setCode(subject.code);
    setFormError('');
    setModalOpen(true);
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();

    if (!name.trim() || !code.trim()) {
      setFormError('Subject name and code are required.');
      return;
    }

    setSubmitting(true);
    setFormError('');

    try {
      const payload = {
        name: name.trim(),
        code: code.trim().toUpperCase(),
      };

      if (editing) {
        await api.put(
          `/academic-mgmt/subjects/${editing.id}`,
          payload,
        );
      } else {
        await api.post('/academic-mgmt/subjects', payload);
      }

      setModalOpen(false);
      await reload();
    } catch {
      setFormError('Unable to save the subject.');
    } finally {
      setSubmitting(false);
    }
  };

  const remove = async (subject: Subject) => {
    if (
      !window.confirm(
        `Delete subject "${subject.name}" (${subject.code})?`,
      )
    ) {
      return;
    }

    setDeletingId(subject.id);

    try {
      await api.delete(
        `/academic-mgmt/subjects/${subject.id}`,
      );
      await reload();
    } catch {
      window.alert(
        'Unable to delete this subject. It may be used by another record.',
      );
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <>
      <ManagerHeader
        title="Subjects"
        description="Maintain the master list of academic subjects."
        buttonLabel="Add Subject"
        onAdd={openCreate}
      />

      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Subject</th>
              <th>Code</th>
              <th className="text-right">Actions</th>
            </tr>
          </thead>

          <tbody>
            {loading ? (
              <LoadingRow columns={3} />
            ) : filtered.length === 0 ? (
              <EmptyRow
                columns={3}
                icon={BookOpen}
                title="No subjects found"
              />
            ) : (
              filtered.map((subject) => (
                <tr key={subject.id}>
                  <td>
                    <div className="font-medium text-slate-900">
                      {subject.name}
                    </div>
                  </td>

                  <td>
                    <span className="rounded-md bg-slate-100 px-2 py-1 font-mono text-xs font-semibold text-slate-600">
                      {subject.code}
                    </span>
                  </td>

                  <td>
                    <ActionButtons
                      editing={() => openEdit(subject)}
                      deleting={() => void remove(subject)}
                      deletingNow={deletingId === subject.id}
                    />
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <Modal
        isOpen={modalOpen}
        onClose={() => !submitting && setModalOpen(false)}
        title={editing ? 'Edit Subject' : 'Add Subject'}
      >
        <form onSubmit={submit} className="space-y-5">
          <FormError message={formError} />

          <Field label="Subject Name">
            <input
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="input"
              placeholder="e.g. Mathematics"
            />
          </Field>

          <Field label="Subject Code">
            <input
              required
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="input"
              placeholder="e.g. MATH"
            />
          </Field>

          <ModalActions
            submitting={submitting}
            editing={Boolean(editing)}
            onCancel={() => setModalOpen(false)}
          />
        </form>
      </Modal>
    </>
  );
}

function ManagerHeader({
  title,
  description,
  buttonLabel,
  onAdd,
}: {
  title: string;
  description: string;
  buttonLabel: string;
  onAdd: () => void;
}) {
  return (
    <div className="mb-4 flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
      <div>
        <h2 className="font-semibold text-slate-900">
          {title}
        </h2>

        <p className="mt-0.5 text-sm text-slate-500">
          {description}
        </p>
      </div>

      <button
        type="button"
        onClick={onAdd}
        className="btn-primary"
      >
        <Plus size={16} />
        {buttonLabel}
      </button>
    </div>
  );
}

function TabButton({
  active,
  onClick,
  icon: Icon,
  label,
  count,
}: {
  active: boolean;
  onClick: () => void;
  icon: React.ElementType;
  label: string;
  count: number;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex items-center gap-2 whitespace-nowrap border-b-2 px-4 py-3 text-sm font-medium transition ${
        active
          ? 'border-blue-600 text-blue-600'
          : 'border-transparent text-slate-500 hover:text-slate-800'
      }`}
    >
      <Icon size={16} />
      {label}

      <span
        className={`rounded-full px-2 py-0.5 text-xs ${
          active
            ? 'bg-blue-50 text-blue-600'
            : 'bg-slate-100 text-slate-500'
        }`}
      >
        {count}
      </span>
    </button>
  );
}

function ActionButtons({
  editing,
  deleting,
  deletingNow,
}: {
  editing: () => void;
  deleting: () => void;
  deletingNow: boolean;
}) {
  return (
    <div className="flex justify-end gap-1">
      <button
        type="button"
        onClick={editing}
        title="Edit"
        className="rounded-md p-2 text-slate-500 transition hover:bg-blue-50 hover:text-blue-600"
      >
        <Pencil size={16} />
      </button>

      <button
        type="button"
        onClick={deleting}
        disabled={deletingNow}
        title="Delete"
        className="rounded-md p-2 text-slate-500 transition hover:bg-red-50 hover:text-red-600 disabled:opacity-50"
      >
        {deletingNow ? (
          <Loader2 size={16} className="animate-spin" />
        ) : (
          <Trash2 size={16} />
        )}
      </button>
    </div>
  );
}

function LoadingRow({ columns }: { columns: number }) {
  return (
    <tr>
      <td colSpan={columns}>
        <div className="flex items-center justify-center gap-2 py-14 text-slate-500">
          <Loader2 size={19} className="animate-spin" />
          Loading...
        </div>
      </td>
    </tr>
  );
}

function EmptyRow({
  columns,
  icon: Icon,
  title,
}: {
  columns: number;
  icon: React.ElementType;
  title: string;
}) {
  return (
    <tr>
      <td colSpan={columns}>
        <div className="py-14 text-center">
          <div className="mx-auto mb-3 flex h-11 w-11 items-center justify-center rounded-full bg-slate-100 text-slate-400">
            <Icon size={21} />
          </div>

          <div className="font-medium text-slate-700">
            {title}
          </div>

          <div className="mt-1 text-sm text-slate-400">
            Create a record to get started.
          </div>
        </div>
      </td>
    </tr>
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

function FormError({ message }: { message: string }) {
  if (!message) return null;

  return (
    <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
      {message}
    </div>
  );
}

function ModalActions({
  submitting,
  editing,
  onCancel,
}: {
  submitting: boolean;
  editing: boolean;
  onCancel: () => void;
}) {
  return (
    <div className="flex justify-end gap-2 border-t border-slate-100 pt-4">
      <button
        type="button"
        onClick={onCancel}
        disabled={submitting}
        className="btn-secondary"
      >
        <X size={16} />
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
            Saving...
          </>
        ) : editing ? (
          <>
            <Pencil size={16} />
            Update
          </>
        ) : (
          <>
            <Plus size={16} />
            Create
          </>
        )}
      </button>
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
