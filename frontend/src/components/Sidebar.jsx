import { useState } from "react";
import {
  LayoutDashboard,
  ShieldAlert,
  Activity,
  Monitor,
  FileSearch,
  AlertOctagon,
  Menu,
  X,
} from "lucide-react";

const menuItems = [
  {
    id: "dashboard",
    icon: LayoutDashboard,
    label: "Dashboard",
  },
  {
    id: "alerts",
    icon: ShieldAlert,
    label: "Threat Alerts",
  },
  {
    id: "behavior",
    icon: Activity,
    label: "Behavior Analysis",
  },
  {
    id: "endpoints",
    icon: Monitor,
    label: "Endpoints",
  },
  {
    id: "investigations",
    icon: FileSearch,
    label: "Investigations",
  },
  {
    id: "exceptions",
    icon: AlertOctagon,
    label: "Exceptions",
  },
];

export default function Sidebar({
  activePage = "dashboard",
  onNavigate,
}) {
  const [open, setOpen] = useState(false);

  function handleNavigation(page) {
    onNavigate?.(page);
    setOpen(false);
  }

  return (
    <>
      {/* Mobile menu button */}
      <button
        onClick={() => setOpen(true)}
        className="fixed left-4 top-4 z-50 rounded-lg border border-slate-700 bg-[#0a0f18] p-2.5 text-slate-300 lg:hidden"
        aria-label="Open navigation"
      >
        <Menu size={20} />
      </button>

      {/* Mobile overlay */}
      {open && (
        <div
          onClick={() => setOpen(false)}
          className="fixed inset-0 z-40 bg-black/60 lg:hidden"
        />
      )}

      <aside
        className={`fixed left-0 top-0 z-50 h-screen w-64 border-r border-slate-800 bg-[#0a0f18] transition-transform duration-300 ${
          open
            ? "translate-x-0"
            : "-translate-x-full lg:translate-x-0"
        }`}
      >
        {/* Logo */}
        <div className="flex h-20 items-center justify-between border-b border-slate-800 px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-500/10">
              <ShieldAlert
                className="text-cyan-400"
                size={23}
              />
            </div>

            <div>
              <h1 className="text-lg font-bold tracking-wide">
                BOGEY
                <span className="text-cyan-400">
                  -ALERT
                </span>
              </h1>

              <p className="text-[10px] uppercase tracking-[0.2em] text-slate-500">
                Security Intelligence
              </p>
            </div>
          </div>

          <button
            onClick={() => setOpen(false)}
            className="text-slate-500 hover:text-white lg:hidden"
            aria-label="Close navigation"
          >
            <X size={20} />
          </button>
        </div>

        {/* Navigation */}
        <nav className="p-4">
          <p className="mb-3 px-3 text-[10px] font-semibold uppercase tracking-widest text-slate-600">
            Monitoring
          </p>

          <div className="space-y-1">
            {menuItems.map((item) => {
              const Icon = item.icon;
              const active = activePage === item.id;

              return (
                <button
                  key={item.id}
                  onClick={() => handleNavigation(item.id)}
                  className={`flex w-full items-center gap-3 rounded-lg px-3 py-3 text-sm transition ${
                    active
                      ? "bg-cyan-500/10 text-cyan-400"
                      : "text-slate-400 hover:bg-slate-800/60 hover:text-white"
                  }`}
                >
                  <Icon size={18} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </div>
        </nav>

        {/* System status */}
        <div className="absolute bottom-5 left-4 right-4 rounded-xl border border-slate-800 bg-slate-900/50 p-4">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_8px_#34d399]" />

            <span className="text-xs font-medium text-emerald-400">
              System Online
            </span>
          </div>

          <p className="mt-2 text-[11px] text-slate-500">
            Monitoring services operational
          </p>
        </div>
      </aside>
    </>
  );
}