import React, { useEffect, useState } from 'react';
import { getTrades } from '@/api/client';

export default function Trades() {
  const [trades, setTrades] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await getTrades();
        setTrades(response.data.reverse());
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-orange-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-8 pb-10">
      <div>
        <h1 className="text-3xl font-bold text-slate-900">Trade History</h1>
        <p className="mt-2 text-slate-600">A complete log of all executed trades.</p>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto w-full">
          <table className="w-full text-left whitespace-nowrap">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Symbol</th>
                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Type</th>
                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Volume</th>
                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Entry</th>
                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Exit</th>
                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">PnL</th>
                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {trades.map((trade) => (
                <tr key={trade.id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-6 py-4 text-sm font-bold text-slate-900">{trade.symbol}</td>
                  <td className="px-6 py-4 text-sm font-medium">
                    <span className={trade.direction === 'BUY' ? 'text-emerald-600' : 'text-rose-600'}>
                      {trade.direction}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-600 font-medium">{trade.executed_lot}</td>
                  <td className="px-6 py-4 text-sm text-slate-600">{trade.open_price?.toFixed(5)}</td>
                  <td className="px-6 py-4 text-sm text-slate-600">{trade.close_price?.toFixed(5) || '-'}</td>
                  <td className="px-6 py-4 text-sm font-bold">
                      <span className={trade.pnl > 0 ? 'text-emerald-600' : trade.pnl < 0 ? 'text-rose-600' : 'text-slate-600'}>
                        {trade.pnl > 0 ? '+' : ''}{trade.pnl?.toFixed(2)}
                      </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-right">
                    <span className={`inline-block px-3 py-1 rounded-full text-xs font-bold uppercase ${trade.status === 'OPEN' ? 'bg-blue-100 text-blue-700' : 'bg-slate-100 text-slate-600'}`}>
                      {trade.status}
                    </span>
                  </td>
                </tr>
              ))}
              {trades.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-slate-500 text-sm">No trades found.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
