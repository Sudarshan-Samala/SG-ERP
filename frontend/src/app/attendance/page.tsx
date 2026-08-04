'use client';

import { useEffect, useMemo, useState } from 'react';
import {
  CalendarDays,
  CheckCircle2,
  Clock3,
  Search,
  UserCheck,
  UserX,
} from 'lucide-react';

import api from '@/lib/api';
import { PageHeader } from '@/components/ui/PageHeader';
import { Button } from '@/components/ui/Button';

interface Student {
  id: string;
  branch_id: string;
  student_name: string;
  admission_number: string;
}

interface Branch {
  id: string;
  name: string;
  code: string;
}

interface Attendance {
  id: string;
  branch_id: string;
  student_id: string;
  date: string;
  status: string;
}

const today = new Date().toISOString().slice(0, 10);

export default function AttendancePage() {
  const [attendance, setAttendance] = useState<Attendance[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [branches, setBranches] = useState<Branch[]>([]);

  const [branchId, setBranchId] = useState('');
  const [studentId, setStudentId] = useState('');
  const [date, setDate] = useState(today);
  const [status, setStatus] = useState('PRESENT');
  const [search, setSearch] = useState('');

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const loadReferenceData = async () => {
    try {
      const [studentRes, branchRes] = await Promise.all([
        api.get('/students/'),
        api.get('/branches/'),
      ]);

      setStudents(studentRes.data);
      setBranches(branchRes.data);
    } catch {
      setError('Unable to load students or branches.');
    }
  };

  const loadAttendance = async () => {
    setLoading(true);

    try {
      const params: Record<string, string | number> = {
        limit: 100,
      };

      if (branchId) params.branch_id = branchId;

      if (date) {
        params.date = `${date}T00:00:00`;
      }

      const res = await api.get('/attendance/', { params });
      setAttendance(res.data);
    } catch {
      setError('Unable to load attendance records.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadReferenceData();
  }, []);

  useEffect(() => {
    void loadAttendance();
  }, [branchId, date]);

  const filteredStudents = useMemo(() => {
    if (!branchId) return students;

    return students.filter((student) => student.branch_id === branchId);
  }, [students, branchId]);

  const studentMap = useMemo(
    () => new Map(students.map((student) => [student.id, student])),
    [students],
  );

  const branchMap = useMemo(
    () => new Map(branches.map((branch) => [branch.id, branch])),
    [branches],
  );

  const visibleAttendance = useMemo(() => {
    const query = search.trim().toLowerCase();

    if (!query) return attendance;

    return attendance.filter((record) => {
      const student = studentMap.get(record.student_id);

      return (
        student?.student_name.toLowerCase().includes(query) ||
        student?.admission_number.toLowerCase().includes(query)
      );
    });
  }, [attendance, search, studentMap]);

  const summary = useMemo(() => {
    return attendance.reduce(
      (result, record) => {
        const value = record.status.toUpperCase();

        result.total += 1;

        if (value === 'PRESENT') result.present += 1;
        if (value === 'ABSENT') result.absent += 1;
        if (value === 'LATE') result.late += 1;

        return result;
      },
      {
        total: 0,
        present: 0,
        absent: 0,
        late: 0,
      },
    );
  }, [attendance]);

  const handleBranchChange = (value: string) => {
    setBranchId(value);
    setStudentId('');
    setError('');
    setSuccess('');
  };

  const handleStudentChange = (value: string) => {
    setStudentId(value);

    const student = students.find((item) => item.id === value);

    if (student) {
      setBranchId(student.branch_id);
    }

    setError('');
    setSuccess('');
  };

  const handleSubmit = async () => {
    setError('');
    setSuccess('');

    if (!studentId) {
      setError('Please select a student.');
      return;
    }

    if (!date) {
      setError('Please select an attendance date.');
      return;
    }

    const student = students.find((item) => item.id === studentId);

    if (!student) {
      setError('Selected student could not be found.');
      return;
    }

    setSubmitting(true);

    try {
      await api.post('/attendance/', {
        branch_id: student.branch_id,
        student_id: student.id,
        date: `${date}T00:00:00`,
        status,
      });

      setSuccess(
        `Attendance marked successfully for ${student.student_name}.`,
      );

      setStudentId('');
      setStatus('PRESENT');

      await loadAttendance();
    } catch (err: any) {
      if (err?.response?.status === 409) {
        setError(
          err.response.data?.detail ||
            'Attendance has already been marked for this student on this date.',
        );
      } else if (err?.response?.data?.detail) {
        setError(
          typeof err.response.data.detail === 'string'
            ? err.response.data.detail
            : 'Unable to mark attendance.',
        );
      } else {
        setError('Unable to mark attendance. Please try again.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Attendance"
        description="Track and manage daily student attendance."
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <SummaryCard
          label="Marked"
          value={summary.total}
          icon={<UserCheck size={20} />}
        />

        <SummaryCard
          label="Present"
          value={summary.present}
          icon={<CheckCircle2 size={20} />}
        />

        <SummaryCard
          label="Absent"
          value={summary.absent}
          icon={<UserX size={20} />}
        />

        <SummaryCard
          label="Late"
          value={summary.late}
          icon={<Clock3 size={20} />}
        />
      </div>

      <div className="card p-5">
        <div className="mb-5 flex items-center gap-2">
          <CalendarDays size={20} className="text-blue-600" />

          <div>
            <h2 className="font-semibold text-slate-900">
              Mark Attendance
            </h2>

            <p className="text-sm text-slate-500">
              Select a branch, student, date and attendance status.
            </p>
          </div>
        </div>

        {error && (
          <div className="mb-4 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {success && (
          <div className="mb-4 rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
            {success}
          </div>
        )}

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <div>
            <label className="label">Branch</label>

            <select
              className="input"
              value={branchId}
              onChange={(e) => handleBranchChange(e.target.value)}
            >
              <option value="">All branches</option>

              {branches.map((branch) => (
                <option key={branch.id} value={branch.id}>
                  {branch.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="label">Student</label>

            <select
              className="input"
              value={studentId}
              onChange={(e) => handleStudentChange(e.target.value)}
            >
              <option value="">Select student</option>

              {filteredStudents.map((student) => (
                <option key={student.id} value={student.id}>
                  {student.student_name} · {student.admission_number}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="label">Date</label>

            <input
              type="date"
              className="input"
              value={date}
              onChange={(e) => {
                setDate(e.target.value);
                setError('');
                setSuccess('');
              }}
            />
          </div>

          <div>
            <label className="label">Status</label>

            <select
              className="input"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
            >
              <option value="PRESENT">Present</option>
              <option value="ABSENT">Absent</option>
              <option value="LATE">Late</option>
            </select>
          </div>
        </div>

        <div className="mt-5 flex justify-end">
          <Button
            onClick={handleSubmit}
            disabled={submitting || students.length === 0}
          >
            <UserCheck size={17} />
            {submitting ? 'Saving...' : 'Mark Attendance'}
          </Button>
        </div>

        {students.length === 0 && (
          <p className="mt-3 text-right text-sm text-amber-600">
            Create at least one student before marking attendance.
          </p>
        )}
      </div>

      <div>
        <div className="mb-4 flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
          <div>
            <h2 className="font-semibold text-slate-900">
              Attendance Records
            </h2>

            <p className="text-sm text-slate-500">
              Records for {formatDisplayDate(date)}
            </p>
          </div>

          <div className="relative w-full sm:w-72">
            <Search
              size={17}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
            />

            <input
              className="input pl-9"
              placeholder="Search student..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>

        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Student</th>
                <th>Admission #</th>
                <th>Branch</th>
                <th>Date</th>
                <th>Status</th>
              </tr>
            </thead>

            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={5} className="py-10 text-center">
                    Loading attendance...
                  </td>
                </tr>
              ) : visibleAttendance.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-12 text-center">
                    <div className="mx-auto flex max-w-sm flex-col items-center">
                      <CalendarDays
                        size={32}
                        className="mb-3 text-slate-300"
                      />

                      <p className="font-medium text-slate-700">
                        No attendance records
                      </p>

                      <p className="mt-1 text-sm text-slate-500">
                        No attendance has been marked for the selected
                        date and branch.
                      </p>
                    </div>
                  </td>
                </tr>
              ) : (
                visibleAttendance.map((record) => {
                  const student = studentMap.get(record.student_id);
                  const branch = branchMap.get(record.branch_id);

                  return (
                    <tr key={record.id}>
                      <td className="font-medium text-slate-900">
                        {student?.student_name || 'Unknown student'}
                      </td>

                      <td>
                        {student?.admission_number || '—'}
                      </td>

                      <td>{branch?.name || '—'}</td>

                      <td>
                        {new Date(record.date).toLocaleDateString()}
                      </td>

                      <td>
                        <StatusBadge status={record.status} />
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function SummaryCard({
  label,
  value,
  icon,
}: {
  label: string;
  value: number;
  icon: React.ReactNode;
}) {
  return (
    <div className="card p-5">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-slate-500">{label}</p>

          <p className="mt-2 text-3xl font-bold tracking-tight text-slate-900">
            {value}
          </p>
        </div>

        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-100 text-slate-600">
          {icon}
        </div>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const normalized = status.toUpperCase();

  if (normalized === 'PRESENT') {
    return <span className="badge-success">Present</span>;
  }

  if (normalized === 'ABSENT') {
    return <span className="badge-danger">Absent</span>;
  }

  if (normalized === 'LATE') {
    return <span className="badge-warning">Late</span>;
  }

  return <span className="badge-info">{status}</span>;
}

function formatDisplayDate(value: string) {
  if (!value) return 'selected date';

  const [year, month, day] = value.split('-').map(Number);

  return new Date(year, month - 1, day).toLocaleDateString(undefined, {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}
