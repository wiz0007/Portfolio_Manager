import React, { useState, useEffect } from 'react';
import { 
  Check, 
  X, 
  AlertCircle, 
  Loader2, 
  RefreshCw, 
  FileQuestion
} from 'lucide-react';
import { marketDataApi } from '../api/marketDataApi';
import { InstrumentRequest } from '../types';

export const InstrumentRequestsQueue: React.FC = () => {
  const [requests, setRequests] = useState<InstrumentRequest[]>([]);
  const [statusFilter, setStatusFilter] = useState('PENDING');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Approval modal state
  const [approvingReq, setApprovingReq] = useState<InstrumentRequest | null>(null);
  const [approvedSymbol, setApprovedSymbol] = useState('');
  const [approvedName, setApprovedName] = useState('');
  const [approvedExchange, setApprovedExchange] = useState('NSE');
  const [cadence, setCadence] = useState('EVERY_TRADING_DAY');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Reject modal state
  const [rejectingReq, setRejectingReq] = useState<InstrumentRequest | null>(null);
  const [rejectionReason, setRejectionReason] = useState('');

  const loadRequests = async (filter?: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const res: any = await marketDataApi.getInstrumentRequests(filter || statusFilter);
      const list = Array.isArray(res) ? res : res.results || [];
      setRequests(list);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load instrument requests.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadRequests(statusFilter);
  }, [statusFilter]);

  const handleOpenApprove = (req: InstrumentRequest) => {
    setApprovingReq(req);
    setApprovedSymbol(req.symbol || '');
    setApprovedName(req.raw_name || '');
    setApprovedExchange(req.exchange || 'NSE');
    setCadence('EVERY_TRADING_DAY');
  };

  const handleConfirmApprove = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!approvingReq) return;

    setIsSubmitting(true);
    setError(null);
    try {
      await marketDataApi.approveInstrumentRequest(approvingReq.id, {
        symbol: approvedSymbol.trim().toUpperCase(),
        name: approvedName.trim(),
        asset_class: approvingReq.asset_class,
        exchange: approvedExchange.trim().toUpperCase(),
        cadence,
        price_type: 'LTP',
        unit: 'UNITS',
        freshness_hours: 24,
      });
      setApprovingReq(null);
      loadRequests();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to approve instrument request.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleConfirmReject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rejectingReq || !rejectionReason.trim()) return;

    setIsSubmitting(true);
    setError(null);
    try {
      await marketDataApi.rejectInstrumentRequest(rejectingReq.id, rejectionReason.trim());
      setRejectingReq(null);
      setRejectionReason('');
      loadRequests();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to reject instrument request.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-5 rounded-2xl border border-theme-border bg-theme-surface">
        <div>
          <div className="flex items-center gap-2">
            <FileQuestion className="h-5 w-5 text-theme-primary" />
            <h2 className="text-base font-bold text-theme-text">Unlisted Instrument Requests Queue</h2>
          </div>
          <p className="text-xs text-theme-text-muted mt-1">
            Review user-submitted instruments, verify exchange ticker identity, and activate price coverage.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-1.5 rounded-xl border border-theme-border bg-theme-bg text-theme-text text-xs focus:outline-none focus:ring-2 focus:ring-theme-primary/40"
          >
            <option value="PENDING">Pending Review</option>
            <option value="APPROVED">Approved</option>
            <option value="MATCHED">Matched</option>
            <option value="REJECTED">Rejected</option>
          </select>

          <button
            onClick={() => loadRequests()}
            disabled={isLoading}
            className="p-2 rounded-xl border border-theme-border text-theme-text-muted hover:text-theme-text hover:bg-theme-hover"
            title="Refresh Requests"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl border border-rose-500/20 bg-rose-500/10 flex items-start gap-3 text-sm text-rose-400">
          <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Requests Table */}
      <div className="rounded-2xl border border-theme-border bg-theme-surface overflow-hidden shadow-sm">
        {isLoading ? (
          <div className="py-16 flex flex-col items-center justify-center">
            <Loader2 className="h-8 w-8 text-theme-primary animate-spin mb-2" />
            <span className="text-xs text-theme-text-muted">Loading instrument requests...</span>
          </div>
        ) : requests.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-theme-border bg-theme-bg/50 text-theme-text-muted font-semibold uppercase tracking-wider text-[11px]">
                  <th className="py-3 px-4">Requested Instrument</th>
                  <th className="py-3 px-4">Class</th>
                  <th className="py-3 px-4">Symbol / Exchange</th>
                  <th className="py-3 px-4">Submitted By</th>
                  <th className="py-3 px-4">Date</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-theme-border">
                {requests.map((req) => (
                  <tr key={req.id} className="hover:bg-theme-hover/50 transition-colors">
                    <td className="py-3 px-4">
                      <div className="font-bold text-theme-text">{req.raw_name}</div>
                      {req.notes && <div className="text-[11px] text-theme-text-muted truncate max-w-xs">{req.notes}</div>}
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-theme-bg text-theme-text-muted border border-theme-border">
                        {req.asset_class}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono">
                      {req.symbol || '-'} {req.exchange ? `(${req.exchange})` : ''}
                    </td>
                    <td className="py-3 px-4 text-theme-text-muted">
                      {req.user_email}
                    </td>
                    <td className="py-3 px-4 text-theme-text-muted font-mono">
                      {new Date(req.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold ${
                        req.status === 'PENDING'
                          ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                          : req.status === 'APPROVED'
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                          : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                      }`}>
                        {req.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      {req.status === 'PENDING' ? (
                        <div className="inline-flex items-center gap-1.5">
                          <button
                            onClick={() => handleOpenApprove(req)}
                            className="px-2.5 py-1 rounded-lg bg-emerald-600/10 hover:bg-emerald-600/20 text-emerald-400 border border-emerald-500/20 text-[11px] font-semibold inline-flex items-center gap-1"
                          >
                            <Check className="h-3 w-3" /> Approve
                          </button>
                          <button
                            onClick={() => {
                              setRejectingReq(req);
                              setRejectionReason('');
                            }}
                            className="px-2.5 py-1 rounded-lg bg-rose-600/10 hover:bg-rose-600/20 text-rose-400 border border-rose-500/20 text-[11px] font-semibold inline-flex items-center gap-1"
                          >
                            <X className="h-3 w-3" /> Reject
                          </button>
                        </div>
                      ) : (
                        <span className="text-theme-text-muted text-[11px]">Reviewed</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-12 text-center text-sm text-theme-text-muted">
            No instrument requests found matching status "{statusFilter}".
          </div>
        )}
      </div>

      {/* Approval Modal */}
      {approvingReq && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
          <div className="relative w-full max-w-md p-6 rounded-2xl border border-theme-border bg-theme-surface shadow-2xl">
            <h3 className="text-base font-bold text-theme-text mb-1">Approve Canonical Instrument</h3>
            <p className="text-xs text-theme-text-muted mb-4">
              Creates the canonical instrument and activates an active daily price coverage policy atomically.
            </p>

            <form onSubmit={handleConfirmApprove} className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-theme-text mb-1">Canonical Symbol</label>
                <input
                  type="text"
                  value={approvedSymbol}
                  onChange={(e) => setApprovedSymbol(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-theme-border bg-theme-bg text-theme-text font-mono uppercase"
                  required
                />
              </div>

              <div>
                <label className="block font-semibold text-theme-text mb-1">Canonical Name</label>
                <input
                  type="text"
                  value={approvedName}
                  onChange={(e) => setApprovedName(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-theme-border bg-theme-bg text-theme-text"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-theme-text mb-1">Exchange</label>
                  <input
                    type="text"
                    value={approvedExchange}
                    onChange={(e) => setApprovedExchange(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-theme-border bg-theme-bg text-theme-text uppercase"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-theme-text mb-1">Collection Cadence</label>
                  <select
                    value={cadence}
                    onChange={(e) => setCadence(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-theme-border bg-theme-bg text-theme-text"
                  >
                    <option value="EVERY_TRADING_DAY">Every Trading Day</option>
                    <option value="EVERY_BUSINESS_DAY">Every Business Day</option>
                    <option value="WEEKLY">Weekly</option>
                    <option value="MONTHLY">Monthly</option>
                  </select>
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-4 border-t border-theme-border">
                <button
                  type="button"
                  onClick={() => setApprovingReq(null)}
                  disabled={isSubmitting}
                  className="px-3 py-1.5 rounded-xl border border-theme-border text-theme-text font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold flex items-center gap-1"
                >
                  {isSubmitting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Check className="h-3.5 w-3.5" />}
                  Confirm Approval
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Reject Modal */}
      {rejectingReq && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
          <div className="relative w-full max-w-md p-6 rounded-2xl border border-theme-border bg-theme-surface shadow-2xl">
            <h3 className="text-base font-bold text-theme-text mb-1">Reject Instrument Request</h3>
            <p className="text-xs text-theme-text-muted mb-4">
              Provide an actionable explanation for why this instrument cannot be cataloged.
            </p>

            <form onSubmit={handleConfirmReject} className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-theme-text mb-1">Rejection Reason</label>
                <textarea
                  value={rejectionReason}
                  onChange={(e) => setRejectionReason(e.target.value)}
                  placeholder="e.g. Unverified private token, invalid exchange ticker..."
                  rows={3}
                  className="w-full px-3 py-2 rounded-xl border border-theme-border bg-theme-bg text-theme-text resize-none"
                  required
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-4 border-t border-theme-border">
                <button
                  type="button"
                  onClick={() => setRejectingReq(null)}
                  disabled={isSubmitting}
                  className="px-3 py-1.5 rounded-xl border border-theme-border text-theme-text font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting || !rejectionReason.trim()}
                  className="px-3 py-1.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-semibold flex items-center gap-1 disabled:opacity-50"
                >
                  {isSubmitting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <X className="h-3.5 w-3.5" />}
                  Confirm Rejection
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
