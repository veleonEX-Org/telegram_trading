import React, { useEffect, useState, useCallback } from 'react';
import { getSignals, executeSignal } from '@/api/client';
import { Zap, RefreshCw, TrendingUp, TrendingDown, Clock, CheckCircle, AlertCircle } from 'lucide-react';

interface Signal {
  id: number;
  signal_order_id: string;
  symbol: string;
  direction: string;
  signal_lot: number;
  action: string;
  timestamp: string;
  executed: number;
}

type ExecutionState = 'idle' | 'loading' | 'success' | 'error';

export default function Signals() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [loading, setLoading] = useState(true);
  const [executionStates, setExecutionStates] = useState<Record<number, ExecutionState>>({});
  const [filter, setFilter] = useState<'ALL' | 'OPEN' | 'CLOSE'>('ALL');

  const fetchSignals = useCallback(async () => {
    try {
      const res = await getSignals();
      setSignals(res.data);
    } catch (err) {
      console.error('Failed to fetch signals', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSignals();
  }, [fetchSignals]);

  const handleExecute = async (signal: Signal) => {
    setExecutionStates((prev) => ({ ...prev, [signal.id]: 'loading' }));
    try {
      await executeSignal(signal.id);
      setExecutionStates((prev) => ({ ...prev, [signal.id]: 'success' }));
      // Reset button after 4s
      setTimeout(() => {
        setExecutionStates((prev) => ({ ...prev, [signal.id]: 'idle' }));
      }, 4000);
    } catch (err: any) {
      console.error('Execution failed', err);
      setExecutionStates((prev) => ({ ...prev, [signal.id]: 'error' }));
      setTimeout(() => {
        setExecutionStates((prev) => ({ ...prev, [signal.id]: 'idle' }));
      }, 4000);
    }
  };

  const filtered = signals.filter((s) => filter === 'ALL' || s.action === filter);

  const openCount = signals.filter((s) => s.action === 'OPEN').length;
  const closeCount = signals.filter((s) => s.action === 'CLOSE').length;
  const executedCount = signals.filter((s) => s.executed === 1).length;

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-orange-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-8 pb-10">
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-3">
            <span className="inline-flex items-center justify-center w-10 h-10 rounded-xl bg-orange-100">
              <Zap className="w-5 h-5 text-orange-600" />
            </span>
            Trade Signals
          </h1>
          <p className="mt-2 text-slate-500">
            All signals received from Telegram. Click <strong>Trade Now</strong> to manually execute an OPEN signal.
          </p>
        </div>
        <button
          onClick={() => { setLoading(true); fetchSignals(); }}
          className="flex items-center gap-2 px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium rounded-lg transition-colors text-sm"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Total Signals</p>
          <p className="text-3xl font-bold text-slate-900">{signals.length}</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">OPEN Signals</p>
          <p className="text-3xl font-bold text-emerald-600">{openCount}</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Executed</p>
          <p className="text-3xl font-bold text-orange-600">{executedCount}</p>
        </div>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-2">
        {(['ALL', 'OPEN', 'CLOSE'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setFilter(tab)}
            className={`px-4 py-2 rounded-lg text-sm font-semibold transition-colors ${
              filter === tab
                ? 'bg-orange-600 text-white shadow-sm'
                : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Signals Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto w-full">
          <table className="w-full text-left whitespace-nowrap">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Symbol</th>
                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Direction</th>
                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Action</th>
                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Lot</th>
                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Time</th>
                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filtered.map((signal) => {
                const execState = executionStates[signal.id] || 'idle';
                const isOpen = signal.action === 'OPEN';

                return (
                  <tr key={signal.id} className="hover:bg-slate-50 transition-colors">
                    {/* Symbol */}
                    <td className="px-6 py-4">
                      <span className="text-sm font-bold text-slate-900">{signal.symbol}</span>
                      <span className="ml-2 text-[10px] text-slate-400 font-mono">#{signal.signal_order_id.slice(-6)}</span>
                    </td>

                    {/* Direction */}
                    <td className="px-6 py-4">
                      <div className={`inline-flex items-center gap-1.5 font-semibold text-sm ${signal.direction === 'BUY' ? 'text-emerald-600' : 'text-rose-600'}`}>
                        {signal.direction === 'BUY' ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                        {signal.direction}
                      </div>
                    </td>

                    {/* Action */}
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold uppercase ${
                        isOpen
                          ? 'bg-emerald-100 text-emerald-700'
                          : 'bg-rose-100 text-rose-700'
                      }`}>
                        {isOpen ? <Zap className="w-3 h-3" /> : <AlertCircle className="w-3 h-3" />}
                        {signal.action}
                      </span>
                    </td>

                    {/* Lot */}
                    <td className="px-6 py-4 text-sm text-slate-600 font-medium">
                      {signal.signal_lot ?? '—'}
                    </td>

                    {/* Time */}
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-1.5 text-xs text-slate-500">
                        <Clock className="w-3.5 h-3.5" />
                        {signal.timestamp
                          ? new Date(signal.timestamp).toLocaleString(undefined, {
                              dateStyle: 'medium',
                              timeStyle: 'short',
                            })
                          : '—'}
                      </div>
                    </td>

                    {/* Executed badge */}
                    <td className="px-6 py-4">
                      {signal.executed === 1 ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold bg-orange-100 text-orange-700">
                          <CheckCircle className="w-3 h-3" />
                          Executed
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold bg-slate-100 text-slate-500">
                          Pending
                        </span>
                      )}
                    </td>

                    {/* Trade Now button */}
                    <td className="px-6 py-4 text-right">
                      {isOpen ? (
                        <button
                          id={`execute-signal-${signal.id}`}
                          disabled={execState === 'loading' || execState === 'success'}
                          onClick={() => handleExecute(signal)}
                          className={`inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-bold transition-all duration-200 ${
                            execState === 'loading'
                              ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                              : execState === 'success'
                              ? 'bg-emerald-100 text-emerald-700 cursor-default'
                              : execState === 'error'
                              ? 'bg-rose-100 text-rose-700 hover:bg-rose-200'
                              : 'bg-orange-600 text-white hover:bg-orange-700 shadow-sm hover:shadow-md active:scale-95'
                          }`}
                        >
                          {execState === 'loading' && (
                            <span className="w-3.5 h-3.5 rounded-full border-2 border-slate-300 border-t-slate-500 animate-spin" />
                          )}
                          {execState === 'success' && <CheckCircle className="w-3.5 h-3.5" />}
                          {execState === 'error' && <AlertCircle className="w-3.5 h-3.5" />}
                          {execState === 'idle' && <Zap className="w-3.5 h-3.5" />}
                          {execState === 'loading' ? 'Sending...' : execState === 'success' ? 'Sent!' : execState === 'error' ? 'Failed' : 'Trade Now'}
                        </button>
                      ) : (
                        <span className="text-xs text-slate-300 italic">—</span>
                      )}
                    </td>
                  </tr>
                );
              })}

              {filtered.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-6 py-16 text-center">
                    <div className="flex flex-col items-center gap-3 text-slate-400">
                      <Zap className="w-10 h-10 opacity-30" />
                      <p className="text-sm font-medium">No signals found.</p>
                      <p className="text-xs">Signals will appear here as Telegram messages are received.</p>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
