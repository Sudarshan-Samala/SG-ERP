'use client';

import { useEffect, useMemo, useState } from 'react';
import api from '@/lib/api';

type Permission = { id: string; name: string; description?: string };
type Role = { id: string; name: string; permissions: Permission[] };
type User = { id: string; email: string; full_name?: string; is_superuser?: boolean; roles?: Role[] };

export default function AccessControlPage() {
  const [roles, setRoles] = useState<Role[]>([]);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [selectedUser, setSelectedUser] = useState('');
  const [selectedRoles, setSelectedRoles] = useState<string[]>([]);
  const [roleName, setRoleName] = useState('');
  const [rolePermissions, setRolePermissions] = useState<string[]>([]);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true); setMessage('');
    try {
      const [r, p, u] = await Promise.all([api.get('/rbac/'), api.get('/rbac/permissions'), api.get('/users/')]);
      setRoles(r.data); setPermissions(p.data); setUsers(u.data.filter((user: User) => !user.is_superuser));
    } catch (error: any) {
      setMessage(error?.response?.status === 403 ? 'You do not have permission to manage access control.' : 'Unable to load access control data.');
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const permissionGroups = useMemo(() => permissions.reduce<Record<string, Permission[]>>((groups, permission) => {
    const module = permission.name.split('.')[0].toUpperCase();
    (groups[module] ||= []).push(permission); return groups;
  }, {}), [permissions]);

  const chooseUser = (id: string) => {
    setSelectedUser(id);
    const user = users.find(item => item.id === id);
    setSelectedRoles(user?.roles?.map(role => role.id) || []);
  };

  const createRole = async () => {
    if (roleName.trim().length < 2) return setMessage('Enter a role name.');
    try {
      await api.post('/rbac/', { name: roleName.trim(), permission_names: rolePermissions });
      setRoleName(''); setRolePermissions([]); setMessage('Role created successfully.'); await load();
    } catch (error: any) { setMessage(error?.response?.data?.detail || 'Unable to create role.'); }
  };

  const saveUserRoles = async () => {
    if (!selectedUser) return setMessage('Select a user first.');
    try {
      await api.put(`/rbac/users/${selectedUser}/roles`, { role_ids: selectedRoles });
      setMessage('User roles updated successfully.'); await load();
    } catch (error: any) { setMessage(error?.response?.data?.detail || 'Unable to update user roles.'); }
  };

  if (loading) return <div className="rounded-xl border bg-white p-8 text-slate-500">Loading access control…</div>;

  return <div className="space-y-6">
    <div><h1 className="text-2xl font-bold text-slate-900">Access Control</h1><p className="mt-1 text-sm text-slate-500">Create tenant roles and assign least-privilege access to ERP users.</p></div>
    {message && <div className="rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700">{message}</div>}
    <div className="grid gap-6 xl:grid-cols-2">
      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="font-semibold">Create role</h2>
        <input className="mt-4 w-full rounded-lg border border-slate-300 px-3 py-2" placeholder="Role name" value={roleName} onChange={e => setRoleName(e.target.value)} />
        <div className="mt-4 space-y-4">{Object.entries(permissionGroups).map(([group, items]) => <div key={group}><div className="mb-2 text-xs font-bold text-slate-400">{group}</div><div className="grid gap-2 sm:grid-cols-2">{items.map(permission => <label key={permission.id} className="flex gap-2 rounded-lg border p-3 text-sm"><input type="checkbox" checked={rolePermissions.includes(permission.name)} onChange={e => setRolePermissions(current => e.target.checked ? [...current, permission.name] : current.filter(x => x !== permission.name))}/><span><b>{permission.name}</b><span className="block text-xs text-slate-500">{permission.description}</span></span></label>)}</div></div>)}</div>
        <button onClick={createRole} className="mt-5 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700">Create role</button>
      </section>
      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="font-semibold">Assign user roles</h2>
        <select className="mt-4 w-full rounded-lg border border-slate-300 px-3 py-2" value={selectedUser} onChange={e => chooseUser(e.target.value)}><option value="">Select user</option>{users.map(user => <option key={user.id} value={user.id}>{user.full_name || user.email} — {user.email}</option>)}</select>
        <div className="mt-4 space-y-2">{roles.map(role => <label key={role.id} className="flex items-start gap-3 rounded-lg border border-slate-200 p-3"><input className="mt-1" type="checkbox" checked={selectedRoles.includes(role.id)} onChange={e => setSelectedRoles(current => e.target.checked ? [...current, role.id] : current.filter(x => x !== role.id))}/><span><span className="font-medium">{role.name}</span><span className="block text-xs text-slate-500">{role.permissions?.length || 0} permissions</span></span></label>)}</div>
        <button onClick={saveUserRoles} className="mt-5 rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800">Save assignments</button>
      </section>
    </div>
  </div>;
}
