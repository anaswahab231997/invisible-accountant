import React from 'react';

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen bg-slate-50 font-sans">
      {/* Sidebar - Oxford Blue */}
      <div className="w-64 bg-[#0F172A] text-white flex flex-col shadow-2xl z-10">
        <div className="p-6 border-b border-slate-700/50">
          <h1 className="text-xl font-bold tracking-tight text-[#D4AF37]">Invisible Accountant</h1>
          <p className="text-xs text-slate-400 mt-1 uppercase tracking-widest font-semibold">Partner Portal</p>
        </div>
        <nav className="flex-1 p-4 space-y-2 mt-4">
          <a href="#" className="flex items-center space-x-3 bg-slate-800/80 text-[#D4AF37] px-3 py-2.5 rounded-md font-medium border-l-2 border-[#D4AF37] shadow-inner">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" /></svg>
            <span>Compliance Matrix</span>
          </a>
          <a href="#" className="flex items-center space-x-3 text-slate-300 hover:text-white px-3 py-2.5 rounded-md font-medium transition-all hover:bg-slate-800/50">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" /></svg>
            <span>Sole Trader Directory</span>
          </a>
          <a href="#" className="flex items-center space-x-3 text-slate-300 hover:text-white px-3 py-2.5 rounded-md font-medium transition-all hover:bg-slate-800/50">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
            <span>HMRC Batch MTD</span>
          </a>
        </nav>
        <div className="p-5 border-t border-slate-700/50 bg-slate-900/50">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 bg-slate-700 rounded-full flex items-center justify-center text-sm font-bold text-[#D4AF37] shadow-inner">HS</div>
            <div>
              <p className="text-sm font-semibold text-slate-200">Harold Sharp Ltd</p>
              <p className="text-[10px] text-slate-400 font-mono mt-0.5">ASA: 9948-UK-MTD</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden bg-[#F8FAFC]">
        <header className="bg-white shadow-sm border-b border-slate-200 z-0">
          <div className="px-8 py-5 flex justify-between items-center">
            <div>
                <h2 className="text-2xl font-bold text-[#0F172A] tracking-tight">Practice Dashboard</h2>
                <p className="text-sm text-slate-500 mt-1">Real-time MTD AI categorization feed</p>
            </div>
            <div className="flex items-center space-x-4">
                <span className="bg-green-50 text-green-700 text-xs font-bold px-3 py-1.5 rounded-full border border-green-200 flex items-center shadow-sm">
                  <span className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></span>
                  HMRC Gateway: Live
                </span>
            </div>
          </div>
        </header>
        <main className="flex-1 overflow-auto p-8">
          <div className="max-w-6xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
