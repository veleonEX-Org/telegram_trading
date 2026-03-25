import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { Home, History, Activity, Settings, Search, LogOut, Menu, X, Globe, Terminal, Database } from 'lucide-react';
import { getSystemStatus } from '@/api/client';

export default function Layout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [systemStatus, setSystemStatus] = useState({ telegram_connected: false, mt5_connected: false, db_connected: false });

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await getSystemStatus();
        setSystemStatus(res.data);
      } catch (e) {
        // fail silently for layout interval
      }
    };
    fetchStatus();
    const interval = setInterval(fetchStatus, 180000); // 3 minutes
    return () => clearInterval(interval);
  }, []);

  const navigation = [
    { name: 'Dashboard', href: '/', icon: Home },
    { name: 'Trades', href: '/trades', icon: History },
    { name: 'Performance', href: '/performance', icon: Activity },
    { name: 'Settings', href: '/settings', icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Mobile Overlay */}
      {mobileMenuOpen && (
        <div 
          className="fixed inset-0 bg-slate-900/50 z-40 lg:hidden"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`fixed inset-y-0 left-0 z-50 w-64 bg-slate-900 text-slate-300 flex flex-col transform transition-transform duration-200 ease-in-out lg:translate-x-0 ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="flex flex-col border-b border-slate-800 pb-6">
          <div className="flex items-center justify-between h-20 px-6">
            <h1 className="text-xl font-bold text-white tracking-wide">VELEONEX</h1>
            <button className="lg:hidden text-slate-400 hover:text-white" onClick={() => setMobileMenuOpen(false)}>
              <X className="w-6 h-6" />
            </button>
          </div>
          
          {/* Connection Indicators in Sidebar */}
          <div className="px-5 space-y-1.5 mt-2">
            <div className="flex items-center justify-between bg-slate-800/40 px-3 py-1.5 rounded-lg border border-slate-700/30">
              <div className="flex items-center gap-2">
                 <Globe className="w-3.5 h-3.5 text-slate-500" />
                 <span className="text-[10px] font-bold text-slate-400 uppercase tracking-tight">Telegram</span>
              </div>
              <div className={`w-2 h-2 rounded-full shadow-sm ${systemStatus.telegram_connected ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
            </div>
            <div className="flex items-center justify-between bg-slate-800/40 px-3 py-1.5 rounded-lg border border-slate-700/30">
              <div className="flex items-center gap-2">
                 <Terminal className="w-3.5 h-3.5 text-slate-500" />
                 <span className="text-[10px] font-bold text-slate-400 uppercase tracking-tight">MT5 Node</span>
              </div>
              <div className={`w-2 h-2 rounded-full shadow-sm ${systemStatus.mt5_connected ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
            </div>
            <div className="flex items-center justify-between bg-slate-800/40 px-3 py-1.5 rounded-lg border border-slate-700/30">
              <div className="flex items-center gap-2">
                 <Database className="w-3.5 h-3.5 text-slate-500" />
                 <span className="text-[10px] font-bold text-slate-400 uppercase tracking-tight">SQLite DB</span>
              </div>
              <div className={`w-2 h-2 rounded-full shadow-sm ${systemStatus.db_connected ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
            </div>
          </div>
        </div>

        <nav className="flex-1 px-4 py-8 space-y-2 overflow-y-auto">
          {navigation.map((item) => {
            const isActive = router.pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setMobileMenuOpen(false)}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                  isActive 
                    ? 'bg-orange-600 text-white shadow-md' 
                    : 'hover:bg-slate-800 hover:text-white'
                }`}
              >
                <item.icon className={`w-5 h-5 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                <span className="font-medium">{item.name}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 lg:ml-64 flex flex-col min-h-screen min-w-0">
        {/* Header */}
        <header className="h-20 bg-white border-b border-slate-200 flex items-center justify-between px-4 lg:px-8 sticky top-0 z-30 shrink-0">
          <div className="flex items-center gap-4 flex-1">
            <button className="lg:hidden text-slate-500 hover:text-slate-900" onClick={() => setMobileMenuOpen(true)}>
              <Menu className="w-6 h-6" />
            </button>
            <div className="relative w-full max-w-md hidden sm:block">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <input 
                type="text"
                placeholder="Search anything..."
                className="w-full bg-slate-100 border-none rounded-lg py-2.5 pl-10 pr-4 text-sm text-slate-900 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-orange-500"
              />
            </div>
          </div>
          <button className="flex items-center gap-2 text-slate-500 hover:text-slate-900 font-medium shrink-0 ml-4">
            <LogOut className="w-5 h-5 hidden sm:block" />
            <span>Logout</span>
          </button>
        </header>

        {/* Page Content */}
        <main className="flex-1 p-4 lg:p-8 overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
