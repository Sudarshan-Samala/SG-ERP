'use client';
import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { PageHeader } from '@/components/ui/PageHeader';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';

export default function BranchesPage() {
  const [branches, setBranches] = useState([]);
  const [name, setName] = useState('');
  const [code, setCode] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const fetchBranches = () => api.get('/branches/').then(res => setBranches(res.data));

  useEffect(() => { fetchBranches(); }, []);

  const handleSubmit = async () => {
    if (editingId) {
        await api.put(`/branches/${editingId}`, { name, code });
        setEditingId(null);
    } else {
        await api.post('/branches/', { name, code });
    }
    setName('');
    setCode('');
    setIsModalOpen(false);
    fetchBranches();
  };

  return (
    <div className="p-6">
      <PageHeader 
        title="Branches" 
        description="Manage school branches."
        action={<Button onClick={() => { setName(''); setCode(''); setEditingId(null); setIsModalOpen(true); }}>Add Branch</Button>}
      />

      <div className="bg-white rounded-lg shadow-sm border">
        <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
                <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Code</th>
                    <th className="px-6 py-3"></th>
                </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
                {branches.map((b: any) => (
                <tr key={b.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{b.name}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{b.code}</td>
                    <td className="px-6 py-4 text-right text-sm font-medium">
                        <button onClick={() => { setEditingId(b.id); setName(b.name); setCode(b.code); setIsModalOpen(true); }} className="text-blue-600 hover:text-blue-900 mr-4">Edit</button>
                        <button onClick={async () => { if (confirm('Delete this branch?')) { await api.delete(`/branches/${b.id}`); fetchBranches(); } }} className="text-red-600 hover:text-red-900">Delete</button>
                    </td>
                </tr>
                ))}
            </tbody>
        </table>
      </div>

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title={editingId ? 'Edit Branch' : 'Add Branch'}>
        <div className="space-y-4">
            <input value={name} onChange={e => setName(e.target.value)} placeholder="Branch Name" className="w-full border border-gray-300 rounded-md p-2" />
            <input value={code} onChange={e => setCode(e.target.value)} placeholder="Branch Code" className="w-full border border-gray-300 rounded-md p-2" />
            <div className="flex justify-end gap-2">
                <Button variant="secondary" onClick={() => setIsModalOpen(false)}>Cancel</Button>
                <Button onClick={handleSubmit}>{editingId ? 'Update' : 'Create'}</Button>
            </div>
        </div>
      </Modal>
    </div>
  );
}
