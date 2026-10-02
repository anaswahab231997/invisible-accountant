import React from 'react';

const clients = [
  { id: '1', name: 'Dave Jenkins', business: 'Jenkins Plumbing', mtdStatus: 'Compliant', lastSubmission: '12 Sep 2026', unreviewedReceipts: 0 },
  { id: '2', name: 'Sarah Miller', business: 'Miller Floral', mtdStatus: 'Action Required', lastSubmission: '10 Sep 2026', unreviewedReceipts: 3 },
  { id: '3', name: 'John Smith', business: 'Smith Construction', mtdStatus: 'Compliant', lastSubmission: '14 Sep 2026', unreviewedReceipts: 1 },
  { id: '4', name: 'Emma Watson', business: 'Watson Consulting', mtdStatus: 'Overdue', lastSubmission: '01 Aug 2026', unreviewedReceipts: 12 },
];

export function Dashboard() {
  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm transition-shadow hover:shadow-md">
          <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest">Total Managed Clients</h3>
          <p className="mt-3 text-4xl font-extrabold text-[#0F172A] tracking-tight">482</p>
          <p className="text-sm text-slate-400 mt-2 font-medium">B2B Wholesale Tier</p>
        </div>
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm border-l-4 border-l-[#D4AF37] transition-shadow hover:shadow-md">
          <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest">AI Auto-Reconciled (30d)</h3>
          <p className="mt-3 text-4xl font-extrabold text-[#0F172A] tracking-tight">£142,590</p>
          <p className="text-sm text-green-600 mt-2 font-semibold flex items-center">
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>
            +12% vs last month
          </p>
        </div>
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm border-l-4 border-l-amber-500 transition-shadow hover:shadow-md">
          <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest">Auditor Flags (Duality)</h3>
          <p className="mt-3 text-4xl font-extrabold text-[#0F172A] tracking-tight">4</p>
          <p className="text-sm text-amber-600 mt-2 font-semibold">Requires partner review</p>
        </div>
      </div>

      {/* Main Table */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="px-6 py-5 border-b border-slate-200 flex justify-between items-center bg-slate-50/50">
          <div>
            <h3 className="text-lg font-bold text-[#0F172A]">MTD Phase 2 Readiness Matrix</h3>
            <p className="text-sm text-slate-500 mt-0.5">Live feed of client compliance statuses</p>
          </div>
          <button className="bg-[#1D4ED8] hover:bg-blue-800 text-white px-4 py-2.5 rounded-lg text-sm font-semibold transition-all shadow-sm hover:shadow active:scale-95">
            Sync HMRC Gateway
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left text-slate-600">
            <thead className="text-xs text-slate-500 uppercase bg-white border-b border-slate-200">
              <tr>
                <th className="px-6 py-4 font-bold tracking-wider">Client Entity</th>
                <th className="px-6 py-4 font-bold tracking-wider">MTD Status</th>
                <th className="px-6 py-4 font-bold tracking-wider">Unreviewed Items</th>
                <th className="px-6 py-4 font-bold tracking-wider">Last Sync</th>
                <th className="px-6 py-4 font-bold tracking-wider text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {clients.map((client) => (
                <tr key={client.id} className="hover:bg-slate-50/80 transition-colors group">
                  <td className="px-6 py-4">
                    <div className="font-bold text-[#0F172A] text-base">{client.business}</div>
                    <div className="text-slate-500 text-sm mt-0.5">{client.name}</div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-3 py-1.5 rounded-full text-xs font-bold border shadow-sm ${
                      client.mtdStatus === 'Compliant' ? 'bg-green-50 text-green-700 border-green-200' :
                      client.mtdStatus === 'Action Required' ? 'bg-amber-50 text-amber-700 border-amber-200' :
                      'bg-red-50 text-red-700 border-red-200'
                    }`}>
                      {client.mtdStatus}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    {client.unreviewedReceipts > 0 ? (
                      <span className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-amber-100 text-amber-800 font-bold text-xs ring-2 ring-white shadow-sm">
                        {client.unreviewedReceipts}
                      </span>
                    ) : (
                      <span className="text-slate-300 font-medium">-</span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-slate-500 font-mono text-xs font-medium">
                    {client.lastSubmission}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button className="text-[#1D4ED8] opacity-80 group-hover:opacity-100 font-bold text-sm transition-all hover:underline">
                      View Ledger &rarr;
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
