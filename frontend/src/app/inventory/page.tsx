'use client';
import { useState, useEffect } from 'react';
import api from '@/lib/api';
import { PageHeader } from '@/components/ui/PageHeader';
import { Button } from '@/components/ui/Button';
import { LoadingSkeleton } from '@/components/ui/LoadingSkeleton';

interface InventoryItem {
    id: string;
    name: string;
    quantity: number;
}

interface Asset {
    id: string;
    name: string;
    asset_tag: string;
    status: 'DEPLOYED' | 'REPAIR' | 'DISPOSED';
}

export default function InventoryAssetsPage() {
    const [activeTab, setActiveTab] = useState<'inventory' | 'assets'>('inventory');
    const [inventory, setInventory] = useState<InventoryItem[]>([]);
    const [assets, setAssets] = useState<Asset[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [invRes, astRes] = await Promise.all([
                api.get('/inventory-assets/inventory'),
                api.get('/inventory-assets/assets')
            ]);
            setInventory(invRes.data);
            setAssets(astRes.data);
        } catch (err) {
            console.error("Failed to fetch data", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchData(); }, []);

    const totalInventoryQuantity = inventory.reduce((sum, item) => sum + item.quantity, 0);
    const assetStats = {
        total: assets.length,
        deployed: assets.filter(a => a.status === 'DEPLOYED').length,
        repair: assets.filter(a => a.status === 'REPAIR').length,
        disposed: assets.filter(a => a.status === 'DISPOSED').length,
    };

    if (loading) return <div className="p-6"><LoadingSkeleton /></div>;

    return (
        <div className="p-6">
            <PageHeader title="Inventory & Assets" description="Manage school resources." />
            
            <div className="flex gap-4 mt-6">
                <Button variant={activeTab === 'inventory' ? 'primary' : 'secondary'} onClick={() => setActiveTab('inventory')}>Inventory</Button>
                <Button variant={activeTab === 'assets' ? 'primary' : 'secondary'} onClick={() => setActiveTab('assets')}>Assets</Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-6">
                {activeTab === 'inventory' ? (
                    <>
                        <div className="card p-4"><h3>Items</h3><p className="text-2xl">{inventory.length}</p></div>
                        <div className="card p-4"><h3>Total Qty</h3><p className="text-2xl">{totalInventoryQuantity}</p></div>
                    </>
                ) : (
                    <>
                        <div className="card p-4"><h3>Total Assets</h3><p className="text-2xl">{assetStats.total}</p></div>
                        <div className="card p-4 text-green-600"><h3>Deployed</h3><p className="text-2xl">{assetStats.deployed}</p></div>
                        <div className="card p-4 text-yellow-600"><h3>Repair</h3><p className="text-2xl">{assetStats.repair}</p></div>
                        <div className="card p-4 text-red-600"><h3>Disposed</h3><p className="text-2xl">{assetStats.disposed}</p></div>
                    </>
                )}
            </div>

            <div className="mt-6 bg-white p-6 rounded-lg border">
                {activeTab === 'inventory' ? (
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Quantity</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                            {inventory.map(item => (
                                <tr key={item.id}>
                                    <td className="px-6 py-4">{item.name}</td>
                                    <td className="px-6 py-4">{item.quantity}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                ) : (
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tag</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                            {assets.map(asset => (
                                <tr key={asset.id}>
                                    <td className="px-6 py-4">{asset.name}</td>
                                    <td className="px-6 py-4">{asset.asset_tag}</td>
                                    <td className="px-6 py-4"><span className="px-2 py-1 rounded text-xs bg-gray-100">{asset.status}</span></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    );
}
