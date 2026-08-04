'use client';
import { useEffect, useState } from 'react';
import api from '@/lib/api';

export default function HelpdeskPage() {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const [subject, setSubject] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState('LOW');

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await api.get('/helpdesk/'); // Need a GET endpoint for tickets
      setTickets(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const createTicket = async () => {
    await api.post('/helpdesk/', { subject, description, priority });
    fetchData();
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="p-4">
      <h1 className="text-xl font-bold">IT Helpdesk</h1>
      <div className="mt-4 grid grid-cols-1 gap-2">
        <input value={subject} onChange={e => setSubject(e.target.value)} placeholder="Subject" className="border p-2" />
        <textarea value={description} onChange={e => setDescription(e.target.value)} placeholder="Description" className="border p-2" />
        <select value={priority} onChange={e => setPriority(e.target.value)} className="border p-2">
            <option value="LOW">Low</option>
            <option value="MEDIUM">Medium</option>
            <option value="HIGH">High</option>
        </select>
        <button onClick={createTicket} className="bg-green-500 text-white p-2">Create Ticket</button>
      </div>
      <ul className="mt-4">
        {tickets.map((t: any) => <li key={t.id} className="border-b p-2">{t.subject} - {t.status}</li>)}
      </ul>
    </div>
  );
}
