import React, { useEffect, useState } from 'react';
import { getPerformanceSummary, getTrades } from '@/api/client';

export default function Performance() {
  const [summary, setSummary] = useState<any>(null);
  const [trades, setTrades] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [perfRes, tradeRes] = await Promise.all([
          getPerformanceSummary(),
          getTrades()
        ]);
        setSummary(perfRes.data);
        setTrades(tradeRes.data);
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading || !summary) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-orange-600"></div>
      </div>
    );
  }

  const winCount = trades.filter(t => t.pnl > 0).length;
  const lossCount = trades.filter(t => t.pnl < 0).length;

  return (
    <div className="max-w-7xl mx-auto space-y-8 pb-10">
      <div>
        <h1 className="text-3xl font-bold text-slate-900">Performance Metrics</h1>
        <p className="mt-2 text-slate-600">Track and analyze your trading metrics.</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
          <p className="text-sm font-medium text-slate-500 uppercase tracking-widest">Total Equity</p>
          <p className="text-3xl font-bold text-emerald-600 mt-2">${summary.total_pnl?.toFixed(2) || '0.00'}</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
          <p className="text-sm font-medium text-slate-500 uppercase tracking-widest">Win Rate</p>
          <p className="text-3xl font-bold text-slate-900 mt-2">{summary.win_rate?.toFixed(1) || '0.0'}%</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
          <p className="text-sm font-medium text-slate-500 uppercase tracking-widest">Total Trades</p>
          <p className="text-3xl font-bold text-slate-900 mt-2">{summary.total_trades || 0}</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
          <p className="text-sm font-medium text-slate-500 uppercase tracking-widest">Avg Trade</p>
          <p className="text-3xl font-bold text-slate-900 mt-2">${(summary.total_pnl / (summary.total_trades || 1)).toFixed(2)}</p>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 lg:p-8">
        <h3 className="text-lg font-bold text-slate-900 mb-6">Trade Distribution</h3>
        <div className="space-y-6 max-w-2xl">
          <div>
            <div className="flex justify-between text-sm font-medium text-slate-700 mb-2">
              <span>Winning Trades ({winCount})</span>
              <span className="text-emerald-600 font-bold">{((winCount/(trades.length||1))*100).toFixed(0)}%</span>
            </div>
            <div className="w-full h-4 bg-slate-100 rounded-full overflow-hidden">
              <div className="h-full bg-emerald-500" style={{ width: `${(winCount / (trades.length || 1)) * 100}%` }} />
            </div>
          </div>
          <div>
            <div className="flex justify-between text-sm font-medium text-slate-700 mb-2">
              <span>Losing Trades ({lossCount})</span>
              <span className="text-rose-600 font-bold">{((lossCount/(trades.length||1))*100).toFixed(0)}%</span>
            </div>
            <div className="w-full h-4 bg-slate-100 rounded-full overflow-hidden">
              <div className="h-full bg-rose-500" style={{ width: `${(lossCount / (trades.length || 1)) * 100}%` }} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
