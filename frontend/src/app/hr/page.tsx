'use client';
import { useEffect, useState } from 'react';
import api from '@/lib/api';

export default function HRPage() {
  const [employees, setEmployees] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const [user_id, setUserId] = useState('');
  const [employee_id, setEmployeeId] = useState('');
  const [department, setDepartment] = useState('');
  const [designation, setDesignation] = useState('');

  const fetchData = async () => {
    setLoading(true);
    try {
      const [eRes, uRes] = await Promise.all([
        api.get('/hr/employees'),
        api.get('/users/')
      ]);
      setEmployees(eRes.data);
      setUsers(uRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const createEmployee = async () => {
    await api.post('/hr/employees', { user_id, employee_id, department, designation });
    fetchData();
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="p-4">
      <h1 className="text-xl font-bold">HR Management</h1>
      <div className="mt-4 grid grid-cols-2 gap-2">
        <select value={user_id} onChange={e => setUserId(e.target.value)} className="border p-2 col-span-2">
            <option value="">Select User</option>
            {users.map((u: any) => <option key={u.id} value={u.id}>{u.email}</option>)}
        </select>
        <input value={employee_id} onChange={e => setEmployeeId(e.target.value)} placeholder="Employee ID" className="border p-2" />
        <input value={department} onChange={e => setDepartment(e.target.value)} placeholder="Department" className="border p-2" />
        <input value={designation} onChange={e => setDesignation(e.target.value)} placeholder="Designation" className="border p-2 col-span-2" />
        <button onClick={createEmployee} className="bg-green-500 text-white p-2 col-span-2">Create Employee</button>
      </div>
      <ul className="mt-4">
        {employees.map((e: any) => <li key={e.id} className="border-b p-2">{e.employee_id} - {e.designation} ({e.department})</li>)}
      </ul>
    </div>
  );
}
