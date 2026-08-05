'use client';

import { useEffect, useMemo, useState } from 'react';
import { CalendarDays, CheckCircle2, Clock3, Search, UserCheck, UserX } from 'lucide-react';
import api, { apiErrorMessage } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import { PageHeader } from '@/components/ui/PageHeader';
import { Button } from '@/components/ui/Button';

interface Student { id: string; branch_id: string; student_name: string; admission_number: string }
interface Branch { id: string; name: string; code: string }
interface Attendance { id: string; branch_id: string; student_id: string; date: string; status: string }
const today = new Date().toISOString().slice(0, 10);

export default function AttendancePage() {
  const { can } = useAuth();
  const [attendance, setAttendance] = useState<Attendance[]>([]); const [students, setStudents] = useState<Student[]>([]); const [branches, setBranches] = useState<Branch[]>([]);
  const [branchId, setBranchId] = useState(''); const [studentId, setStudentId] = useState(''); const [date, setDate] = useState(today); const [status, setStatus] = useState('PRESENT'); const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true); const [submitting, setSubmitting] = useState(false); const [error, setError] = useState(''); const [success, setSuccess] = useState('');
  const canMark = can('attendance.mark');

  useEffect(() => { void (async () => { try { const [studentRes, branchRes] = await Promise.all([api.get('/students/'), api.get('/branches/')]); setStudents(studentRes.data); setBranches(branchRes.data); } catch (err) { setError(apiErrorMessage(err, 'Unable to load students or branches.')); } })(); }, []);
  useEffect(() => { void (async () => { setLoading(true); setError(''); try { const params: Record<string,string|number>={limit:100}; if(branchId) params.branch_id=branchId; if(date) params.date=`${date}T00:00:00`; const res=await api.get('/attendance/',{params}); setAttendance(res.data); } catch(err){setError(apiErrorMessage(err,'Unable to load attendance records.'));} finally{setLoading(false);} })(); }, [branchId,date]);

  const filteredStudents=useMemo(()=>branchId?students.filter(s=>s.branch_id===branchId):students,[students,branchId]);
  const studentMap=useMemo(()=>new Map(students.map(s=>[s.id,s])),[students]); const branchMap=useMemo(()=>new Map(branches.map(b=>[b.id,b])),[branches]);
  const visibleAttendance=useMemo(()=>{const q=search.trim().toLowerCase(); return !q?attendance:attendance.filter(r=>{const s=studentMap.get(r.student_id);return s?.student_name.toLowerCase().includes(q)||s?.admission_number.toLowerCase().includes(q);});},[attendance,search,studentMap]);
  const summary=useMemo(()=>attendance.reduce((r,a)=>{r.total++; const v=a.status.toUpperCase(); if(v==='PRESENT')r.present++; if(v==='ABSENT')r.absent++; if(v==='LATE')r.late++; return r;},{total:0,present:0,absent:0,late:0}),[attendance]);

  const handleSubmit=async()=>{setError('');setSuccess(''); if(!studentId)return setError('Please select a student.'); if(!date)return setError('Please select an attendance date.'); if(date>today)return setError('Attendance cannot be marked for a future date.'); const student=students.find(s=>s.id===studentId); if(!student)return setError('Selected student could not be found.'); setSubmitting(true); try{await api.post('/attendance/',{branch_id:student.branch_id,student_id:student.id,date:`${date}T00:00:00`,status});setSuccess(`Attendance marked successfully for ${student.student_name}.`);setStudentId(''); const params:Record<string,string|number>={limit:100,date:`${date}T00:00:00`};if(branchId)params.branch_id=branchId;setAttendance((await api.get('/attendance/',{params})).data);}catch(err){setError(apiErrorMessage(err,'Unable to mark attendance. Please try again.'));}finally{setSubmitting(false);}};

  return <div className="space-y-6"><PageHeader title="Attendance" description="Track daily attendance with branch-aware access and clear status summaries."/>
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"><SummaryCard label="Marked" value={summary.total} icon={<UserCheck size={20}/>}/><SummaryCard label="Present" value={summary.present} icon={<CheckCircle2 size={20}/>}/><SummaryCard label="Absent" value={summary.absent} icon={<UserX size={20}/>}/><SummaryCard label="Late" value={summary.late} icon={<Clock3 size={20}/>}/></div>
    {canMark && <div className="card p-5"><div className="mb-5 flex items-center gap-2"><CalendarDays size={20} className="text-blue-600"/><div><h2 className="font-semibold text-slate-900">Mark Attendance</h2><p className="text-sm text-slate-500">Only accessible branches and students are available.</p></div></div>
      {error&&<Alert tone="error">{error}</Alert>}{success&&<Alert tone="success">{success}</Alert>}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4"><Field label="Branch"><select className="input" value={branchId} onChange={e=>{setBranchId(e.target.value);setStudentId('');}}><option value="">All accessible branches</option>{branches.map(b=><option key={b.id} value={b.id}>{b.name}</option>)}</select></Field><Field label="Student"><select className="input" value={studentId} onChange={e=>{setStudentId(e.target.value);const s=students.find(x=>x.id===e.target.value);if(s)setBranchId(s.branch_id);}}><option value="">Select student</option>{filteredStudents.map(s=><option key={s.id} value={s.id}>{s.student_name} · {s.admission_number}</option>)}</select></Field><Field label="Date"><input type="date" max={today} className="input" value={date} onChange={e=>setDate(e.target.value)}/></Field><Field label="Status"><select className="input" value={status} onChange={e=>setStatus(e.target.value)}><option value="PRESENT">Present</option><option value="ABSENT">Absent</option><option value="LATE">Late</option></select></Field></div><div className="mt-5 flex justify-end"><Button onClick={handleSubmit} disabled={submitting||students.length===0}><UserCheck size={17}/>{submitting?'Saving...':'Mark Attendance'}</Button></div></div>}
    {!canMark && error&&<Alert tone="error">{error}</Alert>}
    <div><div className="mb-4 flex flex-col justify-between gap-3 sm:flex-row sm:items-center"><div><h2 className="font-semibold text-slate-900">Attendance Records</h2><p className="text-sm text-slate-500">Records for {formatDisplayDate(date)}</p></div><div className="relative w-full sm:w-72"><Search size={17} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"/><input className="input pl-9" placeholder="Search student..." value={search} onChange={e=>setSearch(e.target.value)}/></div></div>
      <div className="table-wrap"><table className="data-table"><thead><tr><th>Student</th><th>Admission #</th><th>Branch</th><th>Date</th><th>Status</th></tr></thead><tbody>{loading?<tr><td colSpan={5} className="py-10 text-center">Loading attendance...</td></tr>:visibleAttendance.length===0?<tr><td colSpan={5} className="py-12 text-center"><CalendarDays size={32} className="mx-auto mb-3 text-slate-300"/><p className="font-medium text-slate-700">No attendance records</p><p className="mt-1 text-sm text-slate-500">Change the date or branch, or mark attendance if you have permission.</p></td></tr>:visibleAttendance.map(r=>{const s=studentMap.get(r.student_id);const b=branchMap.get(r.branch_id);return <tr key={r.id}><td className="font-medium text-slate-900">{s?.student_name||'Unknown student'}</td><td>{s?.admission_number||'—'}</td><td>{b?.name||'—'}</td><td>{new Date(r.date).toLocaleDateString()}</td><td><StatusBadge status={r.status}/></td></tr>;})}</tbody></table></div></div>
  </div>;
}
function Field({label,children}:{label:string;children:React.ReactNode}){return <div><label className="label">{label}</label>{children}</div>}
function Alert({tone,children}:{tone:'error'|'success';children:React.ReactNode}){return <div className={`mb-4 rounded-md border px-4 py-3 text-sm ${tone==='error'?'border-red-200 bg-red-50 text-red-700':'border-emerald-200 bg-emerald-50 text-emerald-700'}`}>{children}</div>}
function SummaryCard({label,value,icon}:{label:string;value:number;icon:React.ReactNode}){return <div className="card p-5"><div className="flex items-center justify-between"><div><p className="text-sm font-medium text-slate-500">{label}</p><p className="mt-2 text-3xl font-bold tracking-tight text-slate-900">{value}</p></div><div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-100 text-slate-600">{icon}</div></div></div>}
function StatusBadge({status}:{status:string}){const n=status.toUpperCase();if(n==='PRESENT')return <span className="badge-success">Present</span>;if(n==='ABSENT')return <span className="badge-danger">Absent</span>;if(n==='LATE')return <span className="badge-warning">Late</span>;return <span className="badge-info">{status}</span>}
function formatDisplayDate(value:string){if(!value)return 'selected date';const[y,m,d]=value.split('-').map(Number);return new Date(y,m-1,d).toLocaleDateString(undefined,{day:'numeric',month:'long',year:'numeric'});}
