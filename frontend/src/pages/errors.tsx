import React, { useEffect, useState, useCallback } from 'react';
import { getErrors, dismissError } from '@/api/client';
import {
  AlertTriangle, RefreshCw, TrendingUp, TrendingDown,
  Clock, Wifi, WifiOff, XCircle, CheckCircle, Zap, X
} from 'lucide-react';

interface TradeError {
  id: number;
  signal_order_id: string;
  symbol: string;
  direction: string;
  signal_lot: number;
  action: string;
  timestamp: string;
  executed: number;
  error_message: string;
  error_at: string;
  error_type: 'hard' | 'connection';
}

export default function ErrorsPage() {
  const [errors, setErrors] = useState<TradeError[]>([]);
  const [loading, setLoading] = useState(true);
  const [dismissing, setDismissing] = useState<Record<number, boolean>>({});
  const [filter, setFilter] = useState<'ALL' | 'hard' | 'connection'>('ALL');

  const fetchErrors = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getErrors();
      setErrors(res.data);
    } catch (err) {
      console.error('Failed to load errors', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchErrors();
  }, [fetchErrors]);

  const handleDismiss = async (id: number) => {
    setDismissing((prev) => ({ ...prev, [id]: true }));
    try {
      await dismissError(id);
      setErrors((prev) => prev.filter((e) => e.id !== id));
    } catch (err) {
      console.error('Dismiss failed', err);
    } finally {
      setDismissing((prev) => ({ ...prev, [id]: false }));
    }
  };

  const filtered = errors.filter((e) => filter === 'ALL' || e.error_type === filter);
  const hardCount = errors.filter((e) => e.error_type === 'hard').length;
  const connCount = errors.filter((e) => e.error_type === 'connection').length;

  const formatTime = (iso: string | null) => {
    if (!iso) return '—';
    return new Date(iso).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
  };

  return (
    <div className="max-w-7xl mx-auto space-y-8 pb-10">
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-3">
            <span className="inline-flex items-center justify-center w-10 h-10 rounded-xl bg-rose-100">
              <AlertTriangle className="w-5 h-5 text-rose-600" />
            </span>
            Trade Errors
          </h1>
          <p className="mt-2 text-slate-500">
            Signals that failed to execute in MetaTrader 5.{' '}
            <span className="font-medium text-amber-600">Connection errors</span> are retried automatically within 5 min.{' '}
            <span className="font-medium text-rose-600">Hard errors</span> require manual review.
          </p>
        </div>
        <button
          onClick={fetchErrors}
          className="flex items-center gap-2 px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium rounded-lg transition-colors text-sm"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Total Errors</p>
          <p className="text-3xl font-bold text-slate-900">{errors.length}</p>
        </div>
        <div className="bg-white rounded-xl border border-rose-100 shadow-sm p-5">
          <p className="text-xs font-semibold text-rose-400 uppercase tracking-wider mb-1">Hard Errors</p>
          <p className="text-3xl font-bold text-rose-600">{hardCount}</p>
          <p className="text-[11px] text-slate-400 mt-1">MT5 rejected the trade</p>
        </div>
        <div className="bg-white rounded-xl border border-amber-100 shadow-sm p-5">
          <p className="text-xs font-semibold text-amber-500 uppercase tracking-wider mb-1">Connection Errors</p>
          <p className="text-3xl font-bold text-amber-600">{connCount}</p>
          <p className="text-[11px] text-slate-400 mt-1">Network / broker unreachable</p>
        </div>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-2 flex-wrap">
        {(['ALL', 'hard', 'connection'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setFilter(tab)}
            className={`px-4 py-2 rounded-lg text-sm font-semibold transition-colors ${
              filter === tab
                ? 'bg-rose-600 text-white shadow-sm'
                : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'
            }`}
          >
            {tab === 'ALL' ? 'All Errors' : tab === 'hard' ? '⛔ Hard Errors' : '📡 Connection Errors'}
          </button>
        ))}
      </div>

      {/* Explainer banner */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-start gap-3">
        <AlertTriangle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
        <div className="text-sm text-amber-800 space-y-1">
          <p><strong>Connection Errors</strong> — The MT5 node was unreachable when the signal arrived. The system will retry automatically during the 5-minute window. Older OPEN signals expire automatically; CLOSE signals retry indefinitely until the node is back online.</p>
          <p><strong>Hard Errors</strong> — MT5 rejected the order (e.g. invalid volume, trading disabled, market closed). These require manual review. Dismiss them once you have noted the issue.</p>
        </div>
      </div>

      {/* Error Table */}
      {loading ? (
        <div className="flex justify-center items-center h-48">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-rose-600" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-16 flex flex-col items-center gap-3 text-slate-400">
          <CheckCircle className="w-12 h-12 text-emerald-400" />
          <p className="text-base font-semibold text-slate-600">No errors found</p>
          <p className="text-sm">All signals have been processed successfully.</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto w-full">
            <table className="w-full text-left whitespace-nowrap">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Signal</th>
                  <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Direction</th>
                  <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Action</th>
                  <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Error Type</th>
                  <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Reason</th>
                  <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Failed At</th>
                  <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filtered.map((err) => (
                  <tr key={err.id} className={`hover:bg-slate-50 transition-colors ${err.error_type === 'hard' ? 'bg-rose-50/30' : 'bg-amber-50/20'}`}>
                    {/* Symbol + ID */}
                    <td className="px-6 py-4">
                      <span className="text-sm font-bold text-slate-900">{err.symbol}</span>
                      <span className="ml-2 text-[10px] text-slate-400 font-mono">
                        #{err.signal_order_id.slice(-6)}
                      </span>
                      <div className="text-[10px] text-slate-400 mt-0.5 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatTime(err.timestamp)}
                      </div>
                    </td>

                    {/* Direction */}
                    <td className="px-6 py-4">
                      <div className={`inline-flex items-center gap-1.5 font-semibold text-sm ${err.direction === 'BUY' ? 'text-emerald-600' : 'text-rose-600'}`}>
                        {err.direction === 'BUY'
                          ? <TrendingUp className="w-4 h-4" />
                          : <TrendingDown className="w-4 h-4" />}
                        {err.direction}
                      </div>
                    </td>

                    {/* Action */}
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold uppercase ${
                        err.action === 'OPEN'
                          ? 'bg-emerald-100 text-emerald-700'
                          : 'bg-rose-100 text-rose-700'
                      }`}>
                        {err.action === 'OPEN' ? <Zap className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                        {err.action}
                      </span>
                    </td>

                    {/* Error type badge */}
                    <td className="px-6 py-4">
                      {err.error_type === 'hard' ? (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-rose-100 text-rose-700">
                          <XCircle className="w-3 h-3" />
                          Hard Error
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-700">
                          <WifiOff className="w-3 h-3" />
                          Connection
                        </span>
                      )}
                    </td>

                    {/* Error message */}
                    <td className="px-6 py-4 max-w-xs">
                      <p className="text-xs text-slate-600 leading-relaxed break-words whitespace-normal">
                        {err.error_message || '—'}
                      </p>
                    </td>

                    {/* Failed at */}
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-1.5 text-xs text-slate-500">
                        <Clock className="w-3.5 h-3.5" />
                        {formatTime(err.error_at)}
                      </div>
                    </td>

                    {/* Dismiss */}
                    <td className="px-6 py-4 text-right">
                      <button
                        id={`dismiss-error-${err.id}`}
                        disabled={dismissing[err.id]}
                        onClick={() => handleDismiss(err.id)}
                        title="Dismiss this error"
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-100 hover:bg-rose-100 text-slate-600 hover:text-rose-700 transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {dismissing[err.id]
                          ? <span className="w-3.5 h-3.5 rounded-full border-2 border-slate-300 border-t-slate-500 animate-spin" />
                          : <X className="w-3.5 h-3.5" />}
                        Dismiss
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
