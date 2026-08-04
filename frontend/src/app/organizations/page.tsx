'use client';
import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { PageHeader } from '@/components/ui/PageHeader';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';

export default function OrganizationsPage() {
  const [orgs, setOrgs] = useState([]);
  const [name, setName] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const fetchOrgs = () => api.get('/organizations/').then(res => setOrgs(res.data));

  useEffect(() => { fetchOrgs(); }, []);

  const handleSubmit = async () => {
    if (editingId) {
        await api.put(`/organizations/${editingId}`, { name });
        setEditingId(null);
    } else {
        await api.post('/organizations/', { name });
    }
    setName('');
    setIsModalOpen(false);
    fetchOrgs();
  };

  return (
    <div className="p-6">
      <PageHeader 
        title="Organizations" 
        description="Manage school organizations."
        action={<Button onClick={() => { setName(''); setEditingId(null); setIsModalOpen(true); }}>Add Organization</Button>}
      />

      <div className="bg-white rounded-lg shadow-sm border">
        <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
                <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                    <th className="px-6 py-3"></th>
                </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
                {orgs.map((org: any) => (
                <tr key={org.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{org.name}</td>
                    <td className="px-6 py-4 text-right text-sm font-medium">
                        <button onClick={() => { setEditingId(org.id); setName(org.name); setIsModalOpen(true); }} className="text-blue-600 hover:text-blue-900 mr-4">Edit</button>
                        <button onClick={async () => { if (confirm('Delete this organization?')) { await api.delete(`/organizations/${org.id}`); fetchOrgs(); } }} className="text-red-600 hover:text-red-900">Delete</button>
                    </td>
                </tr>
                ))}
            </tbody>
        </table>
      </div>

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title={editingId ? 'Edit Organization' : 'Add Organization'}>
        <div className="space-y-4">
            <input value={name} onChange={e => setName(e.target.value)} placeholder="Organization Name" className="w-full border border-gray-300 rounded-md p-2" />
            <div className="flex justify-end gap-2">
                <Button variant="secondary" onClick={() => setIsModalOpen(false)}>Cancel</Button>
                <Button onClick={handleSubmit}>{editingId ? 'Update' : 'Create'}</Button>
            </div>
        </div>
      </Modal>
    </div>
  );
}
