'use client';
import Link from 'next/link';
import { useCallback,useEffect,useMemo,useState } from 'react';
import { GraduationCap,Users,Headphones,RefreshCw,ClipboardCheck,IndianRupee,Bell,ArrowRight } from 'lucide-react';
import api,{apiErrorMessage} from '@/lib/api';
import { useAuth } from '@/lib/auth-context';

type Stats={students?:number;employees?:number;open_tickets?:number;attendance_marked_today?:number;present_today?:number;outstanding_fees?:number;fees_collected?:number};
const money=(n:number)=>new Intl.NumberFormat('en-IN',{style:'currency',currency:'INR',maximumFractionDigits:0}).format(n);
export default function DashboardPage(){const{user,can}=useAuth();const[stats,setStats]=useState<Stats>({});const[loading,setLoading]=useState(true);const[error,setError]=useState('');
 const load=useCallback(async()=>{setLoading(true);setError('');try{setStats((await api.get('/dashboard/summary')).data);}catch(e){setError(apiErrorMessage(e,'Unable to load dashboard information.'));}finally{setLoading(false);}},[]);useEffect(()=>{void load();},[load]);
 const cards=useMemo(()=>[
  stats.students!==undefined&&{label:'Students',value:stats.students,icon:GraduationCap,href:'/students'},
  stats.employees!==undefined&&{label:'Employees',value:stats.employees,icon:Users,href:'/hr'},
  stats.attendance_marked_today!==undefined&&{label:'Present Today',value:`${stats.present_today||0} / ${stats.attendance_marked_today||0}`,icon:ClipboardCheck,href:'/attendance'},
  stats.outstanding_fees!==undefined&&{label:'Outstanding Fees',value:money(stats.outstanding_fees),icon:IndianRupee,href:'/fees'},
  stats.fees_collected!==undefined&&{label:'Fees Collected',value:money(stats.fees_collected),icon:IndianRupee,href:'/finance'},
  stats.open_tickets!==undefined&&{label:'Open Tickets',value:stats.open_tickets,icon:Headphones,href:'/helpdesk'},
 ].filter(Boolean) as {label:string;value:string|number;icon:React.ElementType;href:string}[],[stats]);
 const actions=[can('students.create')&&['Add student','/students'],can('attendance.mark')&&['Mark attendance','/attendance'],can('fees.invoice.create')&&['Create invoice','/fees'],can('helpdesk.create')&&['Raise ticket','/helpdesk'],can('rbac.manage')&&['Manage access','/access-control']].filter(Boolean) as string[][];
 return <div className="space-y-6"><div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center"><div><h1 className="page-title">Dashboard</h1><p className="page-description">Welcome {user?.full_name||user?.email||'back'}. Metrics reflect only data you are authorized to view.</p></div><button onClick={()=>void load()} disabled={loading} className="btn-secondary self-start"><RefreshCw size={16} className={loading?'animate-spin':''}/>Refresh</button></div>
 {error&&<div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}
 <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">{loading?[1,2,3].map(i=><div key={i} className="card h-36 animate-pulse bg-slate-100"/>):cards.length===0?<div className="card col-span-full p-8 text-center text-slate-500">No dashboard metrics are available for your current permissions.</div>:cards.map(c=>{const I=c.icon;return <Link key={c.label} href={c.href} className="card p-5 transition hover:-translate-y-0.5 hover:shadow-md"><div className="flex items-center justify-between"><div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-50 text-blue-600"><I size={20}/></div><ArrowRight size={17} className="text-slate-300"/></div><div className="mt-5 text-sm font-medium text-slate-500">{c.label}</div><div className="mt-1 text-2xl font-bold text-slate-900">{c.value}</div></Link>})}</div>
 <div className="grid gap-6 lg:grid-cols-3"><section className="card p-5 lg:col-span-2"><h2 className="font-semibold">Quick Actions</h2><p className="mt-1 text-sm text-slate-500">Only actions allowed by your role are shown.</p><div className="mt-4 grid gap-3 sm:grid-cols-2">{actions.length?actions.map(([label,href])=><Link key={label} href={href} className="flex items-center justify-between rounded-lg border border-slate-200 p-4 text-sm font-semibold hover:border-blue-200 hover:bg-blue-50/40"><span>{label}</span><ArrowRight size={16}/></Link>):<p className="text-sm text-slate-500">No management actions assigned.</p>}</div></section><section className="card p-5"><div className="flex items-center gap-2"><Bell size={19} className="text-blue-600"/><h2 className="font-semibold">Notification Center</h2></div><p className="mt-2 text-sm text-slate-500">Review workflow updates and operational alerts from one place.</p><Link href="/notifications" className="btn-secondary mt-5 inline-flex">View notifications<ArrowRight size={16}/></Link><div className="mt-5 border-t pt-4 text-xs text-slate-500">Access: {user?.is_superuser?'Superuser':`${user?.branches.length||0} assigned branch(es)`}</div></section></div></div>;
}
