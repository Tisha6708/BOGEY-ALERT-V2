import { Bell, Search, ShieldCheck } from "lucide-react";

export default function Topbar() {
  return (
    <header className="fixed left-0 right-0 top-0 z-30 h-20 border-b border-slate-800 bg-[#070b12]/95 px-4 backdrop-blur sm:px-6 lg:left-64 lg:px-8">
      <div className="flex h-full items-center justify-end">
        <div className="flex items-center gap-3 sm:gap-5">

          {/* Search */}
          <div className="hidden items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/50 px-3 py-2 sm:flex">
            <Search size={16} className="text-slate-500" />

            <input
              placeholder="Search..."
              className="w-28 bg-transparent text-sm text-white outline-none placeholder:text-slate-600 md:w-40"
            />
          </div>

          {/* Notifications */}
          <button className="relative rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-white">
            <Bell size={19} />
            <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-red-500" />
          </button>

          {/* User */}
          <div className="flex items-center gap-3 border-l border-slate-800 pl-3 sm:pl-5">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-cyan-500/10">
              <ShieldCheck size={18} className="text-cyan-400" />
            </div>

            <div className="hidden sm:block">
              <p className="text-sm font-medium text-white">
                Security Analyst
              </p>

              <p className="text-[10px] text-slate-500">ADMIN</p>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}