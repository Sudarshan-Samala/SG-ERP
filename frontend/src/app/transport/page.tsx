'use client';
import { useEffect, useState } from 'react';
import api from '@/lib/api';

export default function TransportPage() {
  const [vehicles, setVehicles] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const [number, setNumber] = useState('');
  const [capacity, setCapacity] = useState('');

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await api.get('/transport/vehicles');
      setVehicles(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const createVehicle = async () => {
    await api.post('/transport/vehicles', { number, capacity: parseInt(capacity) });
    fetchData();
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="p-4">
      <h1 className="text-xl font-bold">Transport Management</h1>
      <div className="mt-4 flex gap-2">
        <input value={number} onChange={e => setNumber(e.target.value)} placeholder="Vehicle Number" className="border p-2" />
        <input type="number" value={capacity} onChange={e => setCapacity(e.target.value)} placeholder="Capacity" className="border p-2" />
        <button onClick={createVehicle} className="bg-green-500 text-white p-2">Create Vehicle</button>
      </div>
      <ul className="mt-4">
        {vehicles.map((v: any) => <li key={v.id} className="border-b p-2">{v.number} - Capacity: {v.capacity}</li>)}
      </ul>
    </div>
  );
}
