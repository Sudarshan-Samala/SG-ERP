'use client';
import { useEffect, useState } from 'react';
import api from '@/lib/api';

export default function DocumentsPage() {
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const [name, setName] = useState('');
  const [category, setCategory] = useState('POLICY');
  const [file, setFile] = useState<File | null>(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await api.get('/documents/'); // Need to implement GET in backend
      setDocs(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const uploadDoc = async () => {
    if (!file) return;
    const formData = new FormData();
    formData.append('name', name);
    formData.append('category', category);
    formData.append('file', file);
    await api.post('/documents/', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
    setFile(null);
    fetchData();
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="p-4">
      <h1 className="text-xl font-bold">Document Management</h1>
      <div className="mt-4 grid grid-cols-1 gap-2">
        <input value={name} onChange={e => setName(e.target.value)} placeholder="Name" className="border p-2" />
        <select value={category} onChange={e => setCategory(e.target.value)} className="border p-2">
            <option value="POLICY">Policy</option>
            <option value="CERTIFICATE">Certificate</option>
            <option value="CONTRACT">Contract</option>
        </select>
        <input type="file" onChange={e => setFile(e.target.files?.[0] || null)} className="border p-2" />
        <button onClick={uploadDoc} className="bg-green-500 text-white p-2">Upload Document</button>
      </div>
      <ul className="mt-4">
        {docs.map((d: any) => <li key={d.id} className="border-b p-2">{d.name} ({d.category})</li>)}
      </ul>
    </div>
  );
}
