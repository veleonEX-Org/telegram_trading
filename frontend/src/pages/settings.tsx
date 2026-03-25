import React, { useEffect, useState } from 'react';
import { getSettings, updateSetting } from '@/api/client';

const SETTING_DESCRIPTIONS: Record<string, string> = {
  allow_trading: 'Master switch. When false, signals are still parsed but nothing executes on your MT5.',
  base_balance: 'Your theoretical starting balance. Your lot size is scaled proportionally based on your real balance compared to this base.',
  min_balance_guard: 'Severe equity protection. If your live MT5 balance falls below this number, lot sizes become 0.0 and trades are safely rejected.',
  max_lot: 'The maximum allowed lot size for a single position. Even if the maths say larger, the software will cap the risk here.',
  magic_number: 'The unique integer ID that MT5 attaches to these copied trades so it can close them appropriately without affecting your other EAs.',
  telegram_group_link: 'The URL or invite link of the Telegram source group where signals derive from.'
};

export default function Settings() {
  const [settings, setSettings] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    setLoading(true);
    try {
      const response = await getSettings();
      setSettings(response.data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (key: string, value: string) => {
    try {
      await updateSetting(key, value);
      setSettings(prev => prev.map(s => s.key === key ? { ...s, value } : s));
      alert(`Setting saved: ${key} = ${value}`);
    } catch (error) {
      alert(`Error saving setting: ${key}`);
      console.error(error);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-orange-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-10">
      <div>
        <h1 className="text-3xl font-bold text-slate-900">Settings</h1>
        <p className="mt-2 text-slate-600">Manage your system configurations.</p>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm">
        <div className="divide-y divide-slate-200">
          {settings.map((setting) => (
            <div key={setting.key} className="p-6 flex flex-col md:flex-row md:items-center justify-between gap-6 hover:bg-slate-50 transition-colors group first:rounded-t-xl last:rounded-b-xl">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
                    {setting.key.replace(/_/g, ' ')}
                  </h3>
                  <div className="relative flex items-center justify-center">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5 text-slate-400 hover:text-orange-500 cursor-help transition-colors">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
                    </svg>
                    {/* Optional: Add custom pure CSS tooltip on hover instead of native browser title attribute for better appearance */}
                    <div className="absolute left-1/2 -top-2 -translate-x-1/2 -translate-y-full px-3 py-2 bg-slate-900 text-white text-xs rounded shadow-lg w-max max-w-xs opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10 pointer-events-none before:content-[''] before:absolute before:left-1/2 before:top-full before:-translate-x-1/2 before:border-4 before:border-transparent before:border-t-slate-900">
                      {SETTING_DESCRIPTIONS[setting.key] || 'Configuration parameter'}
                    </div>
                  </div>
                </div>
                <p className="text-xs text-slate-500 mt-1 font-mono">{setting.key}</p>
              </div>
              <div className="flex items-center shrink-0">
                {setting.key === 'allow_trading' ? (
                  <button
                    onClick={() => {
                      const currentVal = String(setting.value).toLowerCase() === 'true';
                      handleSave(setting.key, String(!currentVal));
                    }}
                    className={`relative inline-flex h-8 w-14 lg:w-16 items-center rounded-full transition-colors flex-shrink-0 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2 ${
                      String(setting.value).toLowerCase() === 'true' ? 'bg-orange-600' : 'bg-slate-300'
                    }`}
                  >
                    <span 
                      className={`inline-block h-6 w-6 transform rounded-full bg-white transition-transform shadow flex-shrink-0 ${
                        String(setting.value).toLowerCase() === 'true' ? 'translate-x-7 lg:translate-x-9' : 'translate-x-1'
                      }`} 
                    />
                  </button>
                ) : (
                  <div className="flex w-full md:w-auto gap-2">
                    <input 
                      type="text"
                      defaultValue={setting.value}
                      className="w-full md:w-64 border border-slate-300 rounded-lg px-4 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-orange-500 transition-shadow disabled:bg-slate-50"
                    />
                    <button 
                      onClick={(e) => {
                        const input = e.currentTarget.previousElementSibling as HTMLInputElement;
                        handleSave(setting.key, input.value);
                      }}
                      className="bg-slate-900 text-white px-5 py-2 flex-shrink-0 rounded-lg text-sm font-medium hover:bg-slate-800 transition-colors focus:outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2"
                    >
                      Save
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
          {settings.length === 0 && (
            <div className="p-8 text-center text-slate-500">No settings found.</div>
          )}
        </div>
      </div>
    </div>
  );
}
