'use client';
import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { PageHeader } from '@/components/ui/PageHeader';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { LoadingSkeleton } from '@/components/ui/LoadingSkeleton';

export default function ExamsPage() {
  const [exams, setExams] = useState<any[]>([]);
  const [examTypes, setExamTypes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [confirmDialog, setConfirmDialog] = useState<{isOpen: boolean, id?: string}>({isOpen: false});
  
  // New state for form
  const [formData, setFormData] = useState({
      name: '',
      exam_type_id: '',
      start_date: '',
      end_date: ''
  });

  const fetchData = async () => {
    setLoading(true);
    const [examsRes, typesRes] = await Promise.all([
        api.get('/exams/'),
        api.get('/exams/types')
    ]);
    setExams(examsRes.data);
    setExamTypes(typesRes.data);
    setLoading(false);
  };

  useEffect(() => { fetchData(); }, []);

  const handleSubmit = async () => {
    await api.post('/exams/', formData);
    setIsModalOpen(false);
    setFormData({ name: '', exam_type_id: '', start_date: '', end_date: '' });
    fetchData();
  };

  if (loading) return <div className="p-6"><LoadingSkeleton /></div>;

  return (
    <div className="p-6">
      <PageHeader 
        title="Exams" 
        description="Manage school exams."
        action={<Button onClick={() => setIsModalOpen(true)}>Add Exam</Button>}
      />

      <div className="bg-white rounded-lg shadow-sm border mt-6">
        <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
                <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Exam Type</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Start Date</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">End Date</th>
                    <th className="px-6 py-3"></th>
                </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
                {exams.map((e: any) => (
                <tr key={e.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{e.name}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {examTypes.find(t => t.id === e.exam_type_id)?.name || e.exam_type_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{new Date(e.start_date).toLocaleDateString()}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{new Date(e.end_date).toLocaleDateString()}</td>
                    <td className="px-6 py-4 text-right text-sm font-medium">
                        <button onClick={() => setConfirmDialog({isOpen: true, id: e.id})} className="text-red-600 hover:text-red-900">Delete</button>
                    </td>
                </tr>
                ))}
            </tbody>
        </table>
      </div>

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Add Exam">
        <div className="space-y-4">
            <input value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} placeholder="Exam Name" className="w-full border border-gray-300 rounded-md p-2" />
            <select value={formData.exam_type_id} onChange={e => setFormData({...formData, exam_type_id: e.target.value})} className="w-full border border-gray-300 rounded-md p-2">
                <option value="">Select Exam Type</option>
                {examTypes.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
            </select>
            <input type="date" value={formData.start_date} onChange={e => setFormData({...formData, start_date: e.target.value})} className="w-full border border-gray-300 rounded-md p-2" />
            <input type="date" value={formData.end_date} onChange={e => setFormData({...formData, end_date: e.target.value})} className="w-full border border-gray-300 rounded-md p-2" />
            <div className="flex justify-end gap-2">
                <Button variant="secondary" onClick={() => setIsModalOpen(false)}>Cancel</Button>
                <Button onClick={handleSubmit}>Create</Button>
            </div>
        </div>
      </Modal>

      <ConfirmDialog 
        isOpen={confirmDialog.isOpen} 
        onClose={() => setConfirmDialog({isOpen: false})} 
        onConfirm={async () => { await api.delete(`/exams/${confirmDialog.id}`); setConfirmDialog({isOpen: false}); fetchData(); }}
        title="Delete Exam"
        message="Are you sure you want to delete this exam?"
      />
    </div>
  );
}
