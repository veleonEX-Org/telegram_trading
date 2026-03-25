import React, { useEffect, useState } from 'react';
import { getPerformanceSummary, getSystemStatus } from '@/api/client';
import { Activity, DollarSign, Target, Globe, Terminal, Calendar, Database } from 'lucide-react';

export default function Dashboard() {
  const [summary, setSummary] = useState<any>(null);
  const [systemStatus, setSystemStatus] = useState({ 
    telegram_connected: false, 
    mt5_connected: false, 
    db_connected: false,
    margin_level: 0, 
    balance: 0, 
    equity: 0 
  });
  const [loading, setLoading] = useState(true);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [perfRes, statusRes] = await Promise.all([
          getPerformanceSummary(startDate || undefined, endDate || undefined),
          getSystemStatus()
        ]);
        setSummary(perfRes.data);
        setSystemStatus(statusRes.data);
      } catch (error) {
        console.error("Error fetching dashboard data:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
    const interval = setInterval(fetchData, 180000); // 3 minutes
    return () => clearInterval(interval);
  }, [startDate, endDate]);

  if (loading || !summary) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-orange-600"></div>
      </div>
    );
  }

  const stats = [
    { name: 'Current Balance', value: `$${systemStatus.balance?.toFixed(2) || '0.00'}`, icon: DollarSign, color: 'text-indigo-600', bg: 'bg-indigo-100' },
    { name: 'Equity', value: `$${systemStatus.equity?.toFixed(2) || '0.00'}`, icon: DollarSign, color: 'text-blue-600', bg: 'bg-blue-100' },
    { name: 'Total Profit', value: `$${summary?.total_pnl?.toFixed(2) || '0.00'}`, icon: DollarSign, color: 'text-emerald-600', bg: 'bg-emerald-100' },
    { name: 'Win Rate', value: `${summary?.win_rate?.toFixed(1) || '0.0'}%`, icon: Activity, color: 'text-orange-600', bg: 'bg-orange-100' },
    { name: 'Max DD (Total)', value: `${summary?.max_drawdown?.toFixed(1) || '0.0'}%`, icon: Target, color: 'text-rose-600', bg: 'bg-rose-100' },
    { name: 'Margin Level', value: systemStatus.margin_level > 0 ? `${systemStatus.margin_level.toFixed(0)}%` : 'N/A', icon: Terminal, color: 'text-indigo-600', bg: 'bg-indigo-100' },
  ];

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Dashboard</h1>
          <p className="mt-2 text-slate-600">Welcome back. Here is your system overview.</p>
        </div>
        
        <div className="flex items-center gap-3 bg-white p-2 rounded-lg border border-slate-200">
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-slate-400" />
            <input 
              type="date" 
              value={startDate} 
              onChange={(e) => setStartDate(e.target.value)}
              className="text-xs font-medium text-slate-600 border-none focus:ring-0 cursor-pointer"
            />
          </div>
          <span className="text-slate-300">|</span>
          <div className="flex items-center gap-2">
            <input 
              type="date" 
              value={endDate} 
              onChange={(e) => setEndDate(e.target.value)}
              className="text-xs font-medium text-slate-600 border-none focus:ring-0 cursor-pointer"
            />
          </div>
          {(startDate || endDate) && (
            <button 
              onClick={() => { setStartDate(''); setEndDate(''); }}
              className="text-xs font-bold text-rose-500 hover:text-rose-600 px-2"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex items-center justify-between hover:bg-slate-50 transition-colors cursor-default">
           <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 text-blue-600 rounded-lg shrink-0">
                <Globe className="w-5 h-5" />
              </div>
              <div>
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Signal Source</p>
                <h3 className="text-base font-bold text-slate-800">Telegram</h3>
              </div>
           </div>
           <div className="flex items-center gap-2 bg-slate-50 px-3 py-1 rounded-full border border-slate-200">
             <div className={`w-2 h-2 rounded-full ${systemStatus.telegram_connected ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
             <span className="text-[10px] font-bold text-slate-600 uppercase">
                {systemStatus.telegram_connected ? 'Live' : 'Down'}
             </span>
           </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex items-center justify-between hover:bg-slate-50 transition-colors cursor-default">
           <div className="flex items-center gap-3">
              <div className="p-2 bg-indigo-100 text-indigo-600 rounded-lg shrink-0">
                <Terminal className="w-5 h-5" />
              </div>
              <div>
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Execution Bridge</p>
                <h3 className="text-base font-bold text-slate-800">MT5 Node</h3>
              </div>
           </div>
           <div className="flex items-center gap-2 bg-slate-50 px-3 py-1 rounded-full border border-slate-200">
             <div className={`w-2 h-2 rounded-full ${systemStatus.mt5_connected ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
             <span className="text-[10px] font-bold text-slate-600 uppercase">
                {systemStatus.mt5_connected ? 'Live' : 'Down'}
             </span>
           </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex items-center justify-between hover:bg-slate-50 transition-colors cursor-default">
           <div className="flex items-center gap-3">
              <div className="p-2 bg-emerald-100 text-emerald-600 rounded-lg shrink-0">
                <Database className="w-5 h-5" />
              </div>
              <div>
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Persistence</p>
                <h3 className="text-base font-bold text-slate-800">Local DB</h3>
              </div>
           </div>
           <div className="flex items-center gap-2 bg-slate-50 px-3 py-1 rounded-full border border-slate-200">
             <div className={`w-2 h-2 rounded-full ${systemStatus.db_connected ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
             <span className="text-[10px] font-bold text-slate-600 uppercase">
                {systemStatus.db_connected ? 'Live' : 'Down'}
             </span>
           </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
        {stats.map((stat, i) => (
          <div key={i} className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm flex items-center justify-between">
             <div>
               <p className="text-sm font-medium text-slate-500">{stat.name}</p>
               <h3 className="text-3xl font-bold text-slate-900 mt-2">{stat.value}</h3>
             </div>
             <div className={`w-14 h-14 rounded-full flex items-center justify-center ${stat.bg} shrink-0 ml-4`}>
               <stat.icon className={`w-7 h-7 ${stat.color}`} />
             </div>
          </div>
        ))}
      </div>

      <div className="mt-8 bg-white rounded-xl border border-slate-200 shadow-sm p-6 lg:p-8">
        <h3 className="text-lg font-bold text-slate-900 border-b border-slate-100 pb-4 mb-4">System Overview</h3>
        <p className="text-slate-600 text-sm leading-relaxed mb-4">
          The trading edge is currently active and monitoring incoming signals from your configured Telegram groups and channels. 
        </p>
        <p className="text-slate-600 text-sm leading-relaxed">
          All trades are automatically forwarded to the connected MetaTrader terminal according to your active risk settings. Do not close the Python backend terminal to keep these services active.
        </p>
      </div>
    </div>
  );
}
