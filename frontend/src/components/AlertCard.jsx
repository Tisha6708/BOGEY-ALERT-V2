import {
  AlertTriangle,
  ChevronRight,
  Clock,
  ShieldCheck,
} from "lucide-react";

export default function AlertCard({ alert, onInvestigate }) {
  const isHigh = alert.risk_level === "HIGH";
  const isMedium = alert.risk_level === "MEDIUM";

  const riskColor = isHigh
    ? "text-red-400"
    : isMedium
      ? "text-yellow-400"
      : "text-emerald-400";

  const riskBg = isHigh
    ? "bg-red-500/10 border-red-500/20"
    : isMedium
      ? "bg-yellow-500/10 border-yellow-500/20"
      : "bg-emerald-500/10 border-emerald-500/20";

  return (
    <div className={`rounded-xl border p-4 sm:p-5 ${riskBg}`}>
      <div className="flex flex-col gap-5">

        {/* Top section */}
        <div className="flex items-start justify-between gap-4">

          <div className="flex min-w-0 gap-3 sm:gap-4">
            <div className="hidden shrink-0 rounded-lg bg-red-500/10 p-3 sm:block">
              <AlertTriangle
                size={22}
                className={riskColor}
              />
            </div>

            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <h3 className="font-semibold text-white">
                  Security Alert #{alert.id}
                </h3>

                <span
                  className={`rounded-md px-2 py-1 text-[10px] font-bold ${riskBg} ${riskColor}`}
                >
                  {alert.risk_level}
                </span>
              </div>

              <p className="mt-2 text-sm text-slate-400">
                Employee{" "}
                <span className="font-medium text-white">
                  EMP_{String(alert.employee_id).padStart(3, "0")}
                </span>{" "}
                triggered a behavioral security alert.
              </p>
            </div>
          </div>

          <div className="shrink-0 text-right">
            <p className={`text-2xl font-bold ${riskColor}`}>
              {alert.risk_score}
            </p>
            <p className="text-[10px] uppercase tracking-wider text-slate-600">
              Risk Score
            </p>
          </div>
        </div>

        {/* Reasons */}
        <div className="rounded-lg border border-slate-800/80 bg-black/10 p-3">
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
            Detection Reasons
          </p>

          <div className="space-y-2">
            {alert.reasons?.slice(0, 3).map((reason, index) => (
              <div
                key={index}
                className="flex gap-2 text-xs leading-5 text-slate-400"
              >
                <span className="mt-2 h-1 w-1 shrink-0 rounded-full bg-slate-500" />
                <span>{reason}</span>
              </div>
            ))}
          </div>

          {alert.reasons?.length > 3 && (
            <p className="mt-2 text-[11px] text-cyan-400">
              +{alert.reasons.length - 3} additional indicators
            </p>
          )}
        </div>

        {/* Metadata */}
        <div className="flex flex-wrap gap-x-6 gap-y-3 text-xs">

          <div className="flex items-center gap-2 text-slate-500">
            <ShieldCheck size={14} />
            Device {alert.device_id}
          </div>

          <div className="flex items-center gap-2 text-slate-500">
            <AlertTriangle size={14} />
            Window {alert.behavioral_window_id}
          </div>

          <div className="flex items-center gap-2 text-slate-500">
            <Clock size={14} />
            {new Date(alert.created_at).toLocaleString()}
          </div>

        </div>

        {/* Action */}
        <div className="flex justify-end border-t border-slate-800/70 pt-4">
          <button
            onClick={() => onInvestigate(alert)}
            className="flex items-center gap-2 rounded-lg border border-slate-700 px-4 py-2 text-xs font-medium text-slate-300 transition hover:border-cyan-500/40 hover:bg-cyan-500/5 hover:text-cyan-400"
          >
            Investigate
            <ChevronRight size={15} />
          </button>
        </div>

      </div>
    </div>
  );
}