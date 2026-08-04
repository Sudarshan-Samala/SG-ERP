'use client';
import { useEffect, useState } from 'react';
import api from '@/lib/api';

export default function CommunicationPage() {
  const [comms, setComms] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const [recipient_type, setRecipientType] = useState('ALL');
  const [channel, setChannel] = useState('IN_APP');
  const [content, setContent] = useState('');

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await api.get('/communication/');
      setComms(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const sendComm = async () => {
    await api.post('/communication/', { recipient_type, channel, content });
    setContent('');
    fetchData();
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="p-4">
      <h1 className="text-xl font-bold">Communication Hub</h1>
      <div className="mt-4 grid grid-cols-1 gap-2">
        <select value={recipient_type} onChange={e => setRecipientType(e.target.value)} className="border p-2">
            <option value="ALL">All</option>
            <option value="GRADE">Grade</option>
            <option value="BRANCH">Branch</option>
        </select>
        <select value={channel} onChange={e => setChannel(e.target.value)} className="border p-2">
            <option value="IN_APP">In App</option>
            <option value="SMS">SMS</option>
            <option value="EMAIL">Email</option>
        </select>
        <textarea value={content} onChange={e => setContent(e.target.value)} placeholder="Content" className="border p-2" />
        <button onClick={sendComm} className="bg-green-500 text-white p-2">Send Communication</button>
      </div>
      <ul className="mt-4">
        {comms.map((c: any) => <li key={c.id} className="border-b p-2">{c.content} - {c.status}</li>)}
      </ul>
    </div>
  );
}
