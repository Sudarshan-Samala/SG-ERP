'use client';

import Link from 'next/link';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { Bell, CheckCheck, RefreshCw } from 'lucide-react';
import api, { apiErrorMessage } from '@/lib/api';
import { PageHeader } from '@/components/ui/PageHeader';
import { Button } from '@/components/ui/Button';

type Notification = { id:string; title:string; message:string; category:string; link?:string|null; is_read:boolean; created_at:string };

export default function NotificationsPage(){
 const [items,setItems]=useState<Notification[]>([]); const [loading,setLoading]=useState(true); const [error,setError]=useState(''); const [unreadOnly,setUnreadOnly]=useState(false);
 const load=useCallback(async()=>{setLoading(true);setError('');try{setItems((await api.get('/notifications/',{params:{unread_only:unreadOnly}})).data);}catch(e){setError(apiErrorMessage(e,'Unable to load notifications.'));}finally{setLoading(false);}},[unreadOnly]);
 useEffect(()=>{void load();},[load]);
 const unread=useMemo(()=>items.filter(i=>!i.is_read).length,[items]);
 const markRead=async(id:string)=>{try{await api.patch(`/notifications/${id}/read`);setItems(x=>x.map(i=>i.id===id?{...i,is_read:true}:i));}catch(e){setError(apiErrorMessage(e,'Unable to update notification.'));}};
 const markAll=async()=>{try{await api.post('/notifications/read-all');setItems(x=>x.map(i=>({...i,is_read:true})));}catch(e){setError(apiErrorMessage(e,'Unable to mark notifications as read.'));}};
 return <div className="space-y-6"><PageHeader title="Notifications" description="Your secure ERP alerts, workflow updates and operational reminders."/>
  <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><div className="flex gap-2"><button className={`btn-secondary ${!unreadOnly?'border-blue-300 bg-blue-50':''}`} onClick={()=>setUnreadOnly(false)}>All</button><button className={`btn-secondary ${unreadOnly?'border-blue-300 bg-blue-50':''}`} onClick={()=>setUnreadOnly(true)}>Unread {unread>0?`(${unread})`:''}</button></div><div className="flex gap-2"><Button variant="secondary" onClick={()=>void load()} disabled={loading}><RefreshCw size={16} className={loading?'animate-spin':''}/>Refresh</Button><Button variant="secondary" onClick={markAll} disabled={items.length===0||unread===0}><CheckCheck size={16}/>Mark all read</Button></div></div>
  {error&&<div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>}
  <div className="card overflow-hidden">{loading?<div className="p-10 text-center text-slate-500">Loading notifications…</div>:items.length===0?<div className="p-12 text-center"><Bell size={34} className="mx-auto text-slate-300"/><h2 className="mt-3 font-semibold">You are all caught up</h2><p className="mt-1 text-sm text-slate-500">New workflow and operational notifications will appear here.</p></div>:<div className="divide-y divide-slate-100">{items.map(item=><div key={item.id} className={`p-5 ${item.is_read?'bg-white':'bg-blue-50/40'}`}><div className="flex flex-col gap-3 sm:flex-row sm:justify-between"><div className="min-w-0"><div className="flex items-center gap-2"><span className="font-semibold text-slate-900">{item.title}</span>{!item.is_read&&<span className="h-2 w-2 rounded-full bg-blue-600"/>}<span className="badge-info">{item.category}</span></div><p className="mt-2 text-sm text-slate-600">{item.message}</p><p className="mt-2 text-xs text-slate-400">{new Date(item.created_at).toLocaleString()}</p></div><div className="flex shrink-0 items-center gap-2">{item.link&&<Link className="btn-secondary" href={item.link}>Open</Link>}{!item.is_read&&<button className="btn-secondary" onClick={()=>void markRead(item.id)}>Mark read</button>}</div></div></div>)}</div>}</div>
 </div>;
}
