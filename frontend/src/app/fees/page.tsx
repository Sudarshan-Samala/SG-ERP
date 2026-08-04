'use client';
import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { PageHeader } from '@/components/ui/PageHeader';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { LoadingSkeleton } from '@/components/ui/LoadingSkeleton';

interface Student { id: string; student_name: string; }
interface Invoice { id: string; student_id: string; amount_due: number; due_date: string; status: string; }

export default function FeesPage() {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  const [formData, setFormData] = useState({
      student_id: '',
      amount_due: '',
      due_date: new Date().toISOString().split('T')[0]
  });

  const fetchData = async () => {
    setLoading(true);
    try {
      const [iRes, sRes] = await Promise.all([
        api.get('/fees/invoices'),
        api.get('/students/')
      ]);
      setInvoices(iRes.data);
      setStudents(sRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const handleSubmit = async () => {
    await api.post('/fees/invoices', { 
        student_id: formData.student_id, 
        amount_due: parseInt(formData.amount_due), 
        due_date: new Date(formData.due_date).toISOString(), 
        status: 'UNPAID' 
    });
    setIsModalOpen(false);
    setFormData({ student_id: '', amount_due: '', due_date: new Date().toISOString().split('T')[0] });
    fetchData();
  };

  if (loading) return <div className="p-6"><LoadingSkeleton /></div>;

  return (
    <div className="p-6">
      <PageHeader 
        title="Fee Management" 
        description="Manage student invoices and payments."
        action={<Button onClick={() => setIsModalOpen(true)}>Create Invoice</Button>}
      />

      <div className="bg-white rounded-lg shadow-sm border mt-6">
        <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
                <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Student</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Amount Due</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Due Date</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
                {invoices.map((i) => (
                <tr key={i.id}>
                    <td className="px-6 py-4 text-sm">{students.find(s => s.id === i.student_id)?.student_name || i.student_id}</td>
                    <td className="px-6 py-4 text-sm">{i.amount_due}</td>
                    <td className="px-6 py-4 text-sm">{new Date(i.due_date).toLocaleDateString()}</td>
                    <td className="px-6 py-4 text-sm">{i.status}</td>
                </tr>
                ))}
            </tbody>
        </table>
      </div>

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Create Invoice">
        <div className="space-y-4">
            <select value={formData.student_id} onChange={e => setFormData({...formData, student_id: e.target.value})} className="w-full border p-2 rounded">
                <option value="">Select Student</option>
                {students.map(s => <option key={s.id} value={s.id}>{s.student_name}</option>)}
            </select>
            <input type="number" value={formData.amount_due} onChange={e => setFormData({...formData, amount_due: e.target.value})} placeholder="Amount" className="w-full border p-2 rounded" />
            <input type="date" value={formData.due_date} onChange={e => setFormData({...formData, due_date: e.target.value})} className="w-full border p-2 rounded" />
            <div className="flex justify-end gap-2">
                <Button variant="secondary" onClick={() => setIsModalOpen(false)}>Cancel</Button>
                <Button onClick={handleSubmit}>Create</Button>
            </div>
        </div>
      </Modal>
    </div>
  );
}
